import psycopg2
from pylab import *
from cga_hall_dict import *
from scipy import interpolate
from iapws import IAPWS97
import math
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from geometry_functions import *

campo = 'CGA'
points_num = 100
fecha = 20150101
slice_depth=0
badprof_P=['AH-21','AH-22','CH-7BIS','AH-8','AH-27','AH-23','AH-17']

if campo=='CGA':
	dictlist=['AH1_dict','AH10_dict','AH11_dict',\
	'AH13_dict','AH14_dict','AH15_dict','AH16_dict','AH16A_dict',\
	'AH17_dict','AH18_dict','AH19_dict','AH2_dict','AH20_dict',\
	'AH21_dict','AH22_dict','AH23_dict','AH24_dict','AH25_dict',\
	'AH26_dict','AH27_dict','AH28_dict','AH29_dict','AH3_dict',\
	'AH30_dict','AH31_dict','AH32_dict','AH33A_dict','AH33B_dict',\
	'AH33C_dict','AH34_dict','AH34A_dict','AH34B_dict','AH35A_dict',\
	'AH35B_dict','AH35C_dict','AH35D_dict','AH36_dict','AH4_dict',\
	'AH4BIS_dict','AH5_dict','AH6_dict','AH7_dict','AH8_dict','AH9_dict',\
	'CH1_dict','CH7_dict','CH7BIS_dict','CH8_dict','CH9_dict','CH9A_dict',\
	'CH9B_dict','CHA_dict','CHA1_dict','CHD_dict']

"""
elif campo=='CGB':
	dictlist=['TR1_dict','TR10_dict','TR10A_dict','TR11_dict','TR11A_dict','TR11C_dict',\
	'TR11ST_dict','TR12_dict','TR12A_dict','TR14_dict','TR14A_dict','TR14B_dict','TR15_dict',\
	'TR17_dict','TR17A_dict','TR17B_dict','TR17C_dict','TR18_dict','TR18A_dict','TR18B_dict',\
	'TR19_dict','TR19A_dict','TR19B_dict','TR19C_dict','TR1A_dict','TR1B_dict','TR1C_dict',\
	'TR2_dict','TR3_dict','TR4_dict','TR4A_dict','TR4B_dict','TR4C_dict','TR5_dict','TR5A_dict',\
	'TR5B_dict','TR5C_dict','TR5D_dict','TR7_dict','TR8_dict','TR8A_dict','TR9_dict']
"""

fig= plt.figure(figsize=(8, 20))
fig2= plt.figure(figsize=(8, 20))

widths = [1,1,1,1,1]
heights = [3,3,3,3,3,3,3,3,3,3]

#fig.subplots_adjust(hspace=2, wspace=0.5)
#fig.tight_layout()

gs = gridspec.GridSpec(nrows=10, ncols=5, width_ratios=widths, height_ratios=heights,hspace=0.4, wspace=0.5)
gsp = gridspec.GridSpec(nrows=10, ncols=5, width_ratios=widths, height_ratios=heights,hspace=0.4, wspace=0.5)


con=psycopg2.connect(dbname='postgres', host='127.0.0.1',port=5432, user='postgres', password='erick')
cur=con.cursor()

yet=0

cnt=0

#Input file for leapfrog, Temperature
file_temp_leap_temp=open('to_leapfrog/temperature/well_temperature.csv','w')
string_leap_temp="WELL_ID,Depth,Temperature\n"
file_temp_leap_temp.write(string_leap_temp)

#Input file for leapfrog, Pressure
file_temp_leap_pressure=open('to_leapfrog/pressure/well_pressure.csv','w')
string_leap_pressure="WELL_ID,Depth,Pressure\n"
file_temp_leap_pressure.write(string_leap_pressure)

#Input file for slice, temperature
file_temp_slice=open('to_model/slices/temperature_natural_%smasl.csv'%(slice_depth),'w')
string_file_temp_slice="X,Y,Z,T\n"
file_temp_slice.write(string_file_temp_slice)


for filesnames in dictlist:
    try:
        ptdate= int(eval("%s['PT_sel']" % (filesnames)))
        nompozo = eval("%s['name']" % (filesnames))
        drilldate = int(eval("%s['drill']" % (filesnames)))+150000
        profz= eval("%s['zmd']" % (filesnames))[1]
        
        q0 = """SELECT "iNCorr", "iFecha","vStatusPozo", "cTipoMedicion" FROM "tInformacionPerfilesPT" WHERE "vNombrePozo"='%s' \
        AND ("vStatusPozo"='SHUT-IN' OR "vStatusPozo"='BLEED' OR "vStatusPozo"='PURGADO' OR "vStatusPozo"='CERRADO' \
        OR "vStatusPozo"='MONITOR' or "vStatusPozo"='PERFORACION' OR  "vStatusPozo"='PRODUCTOR' or "vStatusPozo"='MONIT' \
         OR "vStatusPozo"='HOTREI' OR "vStatusPozo"='INYECTOR') AND "cTipoMedicion"!='PRES' \
        AND "iFecha"=%s """ % (nompozo,ptdate)
     

        cur.execute(q0)
        var0 =cur.fetchall()
        corr = int(var0[0][0])
        fecha = int(var0[0][1])
        status = str(var0[0][2])
        type_med = str(var0[0][3])

        q1 = """SELECT "fProfundidadMD", "fPresion", "fTemperatura" FROM "tPerfilesPT" WHERE "iNCorr"=%s ORDER BY "fProfundidadMD" """% (corr)  # De existir genera el query
        try:
            cur.execute(q1)
            var0 = cur.fetchall()
            profr = np.array(var0)[:, 0]
            pr = np.array(var0)[:, 1]
            tr = np.array(var0)[:, 2]
            tr= [np.nan if x == 0 else x for x in tr]

            #Plot Temperature
            ax= fig.add_subplot(gs[cnt])
            varT, xT, yT, zT=MT_to_TVD(filesnames,profr,tr,100)


            #Slice
            funcT=interpolate.interp1d(zT,varT)
            funcX=interpolate.interp1d(zT,xT)
            funcY=interpolate.interp1d(zT,yT)

            print nompozo
            try:
                string_temp="%s, %s, %s, %s\n"%(funcX(slice_depth),funcY(slice_depth),slice_depth,funcT(slice_depth))
                file_temp_slice.write(string_temp)
            except ValueError:
                pass

            ax.plot(varT,zT,'-r',linewidth=1,label=str(fecha)+" "+status+" "+type_med)

            fontsizex=5
            ax.set_title("%s"%nompozo,fontsize = 6)
            ax.set_xlabel("Temperature [C]",fontsize = fontsizex)
            ax.set_ylabel('m.a.s.l.',fontsize = fontsizex)
            #plt.gca().invert_yaxis()
            ax.xaxis.tick_top()
            ax.title.set_position([0.5,1.13])
            ax.xaxis.set_label_coords(0.5,1.2)
            ax.tick_params(axis='both', which='major', labelsize=fontsizex,pad=1)
            #plt.draw()

            #Plot pressure
            axp= fig2.add_subplot(gsp[cnt])
            if np.array(pr).mean()>0 and nompozo not in badprof_P:
                varP, xT, yT, zT=MT_to_TVD(filesnames,profr,pr,100)
                axp.plot(varP,zT,'-b',linewidth=1,label=str(fecha)+" "+status+" "+type_med)
            else:

                P0_type = eval("%s['PT0']" % (filesnames))
                if isinstance(P0_type, str):
                    Tmin=np.nanmin(varT)
                else:
                    Tmin=np.nanmean(tr)+P0_type*np.nanstd(tr)

                P0 = eval("%s['P0'][0]" % (filesnames))
                P1 = eval("%s['P0'][1]" % (filesnames))

                D0 = eval("%s['D0'][0]" % (filesnames))
                D1 = eval("%s['D0'][1]" % (filesnames))

                
                Dx,Pmin=water_level_projection(P0,P1,D0,D1,Tmin)
                
                Xx,Yx,TVDx=MD_to_TVD_one_point(filesnames,Dx)

                varP=P_in_TVD_2p(zT,varT,TVDx,Pmin)
                axp.plot(varP,zT,'--b',linewidth=1,label=str(fecha)+" "+status+" "+type_med)

            axp.set_title("%s"%nompozo,fontsize = 6)
            axp.set_xlabel("Pressure [bar]",fontsize = fontsizex)
            axp.set_ylabel('m.a.s.l.',fontsize = fontsizex)
            axp.xaxis.tick_top()
            axp.title.set_position([0.5,1.13])
            axp.xaxis.set_label_coords(0.5,1.2)
            axp.tick_params(axis='both', which='major', labelsize=fontsizex,pad=1)
            plt.draw()

            #Writing temperature for leapfrog

            for n in range(len(profr)):
                if math.isnan(tr[n]):
                    pass
                else:
                    string_leap_temp="%s,%.2f,%.2f\n"%(nompozo,profr[n],tr[n])
                    file_temp_leap_temp.write(string_leap_temp)

            for n in range(len(varP)):
                if math.isnan(varP[n]):
                    pass
                else:
                    string_leap_pressure="%s,%.2f,%.2f\n"%(nompozo,TVD_to_MD_one_point(filesnames,zT[n]),varP[n])
                    file_temp_leap_pressure.write(string_leap_pressure)

            #Writing temperature
            file=open('to_model/logging/temperature/%s_T.dat'%nompozo,'w')
            for n in range(len(varT)):
                if math.isnan(varT[n]):
                    pass
                else:
                    string="%.2f , %.2f , %.2f , %.2f\n"%(xT[n],yT[n],zT[n],varT[n])
                    file.write(string)
            file.close()

            #Writing pressure
            file=open('to_model/logging/pressure/%s_P.dat'%nompozo,'w')
            for n in range(len(varP)):
                string="%.2f , %.2f , %.2f , %.2f\n"%(xT[n],yT[n],zT[n],varP[n])
                file.write(string)
            file.close()

            cnt+=1
        except TypeError:
            pass
    except KeyError:
        pass

file_temp_slice.close()
file_temp_leap_temp.close()
file_temp_leap_pressure.close()
fig.savefig('to_model/images/T_reg_cga.png') 
fig2.savefig('to_model/images/P_reg_cga.png')  
plt.show()