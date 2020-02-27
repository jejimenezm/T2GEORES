import psycopg2
from model_conf import *
from iapws import IAPWS97
import t2resfun as t2r
import numpy as np
from scipy import interpolate
import os
import datetime

#wells_dict[n['name']]=[n['drill'],n['PT_sel']]

wells={'CH-7BIS': [19910226, 19950507],
	 'AH-7': [19700224, 19740409],
	 'AH-1': [19680601, 19710129],
	 'AH-2': [19730906, 19750410],
	 'AH-34A': [19970922, 19991021],
	 'AH-5': [19700630, 19700721],
	 'AH-6': [19700224, 19740419],
	 'AH-34B': [19971214, 19980918],
	 'AH-8': [19720918, 19920909],
	 'AH-9': [19700518, 19770617],
	 'CH-9A': [20071222, 20181207],
	 'CH-9B': [20180901, 20181011],
	 'AH-30': [19790217, 19840201],
	 'AH-31': [19810929, 19900301],
	 'AH-32': [19811231, 19851125],
	 'AH-34': [19970703, 19991007],
	 'AH-36': [19990616, 20000921],
	 'AH-4BIS': [19970503, 19970609],
	 'CH-1':[19680422,19690513],
	 'CH-7': [19890723, 19950119],
	 'AH-18': [19770524, 19831109],
	 'AH-19': [19780228, 19880212],
	 'CH-8': [19900307, 19971210],
	 'AH-13': [19740114, 19770920],
	 'CH-D': [19930609, 19970423],
	 'AH-11': [19730111, 19740424],
	 'AH-16': [19740805, 19760526],
	 'AH-17': [19760830, 19880707],
	 'AH-14': [19740512, 19780208],
	 'AH-15': [19741019, 19880810],
	 'AH-35D': [20150111, 20181003],
	 'AH-35B': [19980906, 19990414],
	 'AH-35C': [20070515, 20120628],
	 'AH-35A': [19980615, 19980703],
	 'AH-16A': [19980318, 19980324],
	 'AH-33A': [19970825, 20000202],
	 'AH-33B': [19970930, 19991116],
	 'AH-33C': [20070830, 20120623],
	 'CH-9': [19901125, 19920928],
	 'AH-27': [19780429, 19890210],
	 'AH-26': [19751230, 19880726],
	 'AH-25': [19750827, 19761020],
	 'AH-24': [19750623, 19760617],
	 'AH-23': [19770910, 19900816],
	 'AH-22': [19750421, 19860516],
	 'AH-21': [19750304, 19940811],
	 'AH-20': [19741220, 19750228],
	 'AH-29': [19760211, 19900405],
	 'AH-28': [19781129, 19790423]}

non_selected_PT='AH-4'

"""
'AH-4':[19720804,]
"""

con=psycopg2.connect(dbname='GMS', host='10.0.16.5',port=5432, user='andrea')
cur=con.cursor()


def write_survey_to_txt_from_GMS(wells,cur):
	for well_name in wells:
		q_geometry="""SELECT "fProfundidadMD","fIncrementoNorte",\
		                     "fIncrementoEste" FROM "tDesviacionPozo"\
		              WHERE "vNombrePozo"='%s' ORDER BY "fProfundidadMD" """%well_name
		cur.execute(q_geometry)
		var_geometry=cur.fetchall()
		file_geometry=open('../input/survey/%s_MD.dat'%well_name,'w')
		file_geometry.write("MeasuredDepth,Delta_north,Delta_east\n")
	    
		for var in var_geometry:
			file_geometry.write("%s,%s,%s\n"%(var[0],var[1],var[2]))
		file_geometry.close()

def write_ubication_to_txt_from_GMS(wells,cur):
	file_ubicacion=open('../input/ubication.csv','w')
	file_ubicacion.write("East,North,masl\n")
	for well_name in wells:
		q_ubication="""SELECT "fDistanciaE","fDistanciaN", "fElevacion" FROM "tUbicacionPozo" WHERE "vNombrePozo"='%s' """%well_name
		cur.execute(q_ubication)

		var_ubication=cur.fetchall()[0]

		string_x="%s,%s,%s,%s\n"%(well_name,var_ubication[0],var_ubication[1],var_ubication[2])
		file_ubicacion.write(string_x)
	file_ubicacion.close()

def write_PT_to_txt_from_GMS(wells,cur):

	for n in wells:
		q_incorr="""SELECT "iNCorr", "iFecha","vStatusPozo", "cTipoMedicion" FROM "tInformacionPerfilesPT" WHERE "vNombrePozo"='%s' \
		AND ("vStatusPozo"='SHUT-IN' OR "vStatusPozo"='BLEED' OR "vStatusPozo"='PURGADO' OR "vStatusPozo"='CERRADO' \
		OR "vStatusPozo"='MONITOR' or "vStatusPozo"='PERFORACION' OR  "vStatusPozo"='PRODUCTOR' or "vStatusPozo"='MONIT' \
		 OR "vStatusPozo"='HOTREI' OR "vStatusPozo"='INYECTOR') AND "cTipoMedicion"!='PRES' \
		AND "iFecha"=%s """ % (n,wells[n][1])

		file_PT=open('../input/PT/%s_MDPT.dat'%n,'w')

		file_PT.write("MD,P,T\n")

		cur.execute(q_incorr)
		corr=cur.fetchall()[0][0]

		q_PT = """SELECT "fProfundidadMD", "fPresion", "fTemperatura" FROM "tPerfilesPT" WHERE "iNCorr"=%s ORDER BY "fProfundidadMD" """% (corr)  # De existir genera el query
		cur.execute(q_PT)

		var_PT=cur.fetchall()

		for n_pt in range(len(var_PT)):
			string_v="%s,%s,%s\n"%(var_PT[n_pt][0],var_PT[n_pt][1],var_PT[n_pt][2])
			file_PT.write(string_v)
		file_PT.close()

def write_mh_to_txt_from_GMS(wells,cur,interval):
	status_rein=['HOTREI','INYECTOR']
	status_prod=['PRODUCTOR']

	if interval=='month':
		dt_forth=datetime.timedelta(days=365.25/24)
		criterion=31
	elif interval=='week':
		dt_forth=datetime.timedelta(days=3.5)
		criterion=31
	elif interval=='year':
		dt_forth=datetime.timedelta(days=365.25)
		criterion=365.25
	elif interval=='quarter':
		dt_forth=datetime.timedelta(days=365.25/4)
		criterion=365.25/4

	dt_back=datetime.timedelta(seconds=1)


	for name in wells:

		file_mh=open('../input/mh/%s_mh.dat'%name,'w')
		file_mh.write("type,date-time,steam,liquid,enthalpy,WHPabs\n")


		q_ubication="""SELECT "fElevacion" FROM "tUbicacionPozo" WHERE "vNombrePozo"='%s' """%name
		cur.execute(q_ubication)
		var_ubication=cur.fetchall()[0][0]

		patm=t2r.patmfromelev(var_ubication)

		q_flow="""SELECT DISTINCT "CodStatus" as status,
	 		  date_trunc('%s',to_timestamp(concat("Fecha",' 00:00:00'),'YYYYMMDD HH24:MI:SS')::timestamp without time zone) as date_f, \
	          avg("FlujoAgua"+"FlujoVapor") as total_flow, avg("h"), avg("PresionCabezal"), avg("FlujoVapor"), avg("FlujoAgua")\
	          from "tOperacionPozo" \
	          WHERE "NombrePozo"='%s'\
	          AND "Fecha">%s GROUP BY date_f, status ORDER BY date_f """%(interval,name,ref_date.strftime("%Y%m%d"))

		cur.execute(q_flow)
		
		var_mh=np.array(cur.fetchall())

		if len(var_mh)>0:

			dates_db=var_mh[:,1].tolist()
			flows_db=(var_mh[:,5]+var_mh[:,6]).tolist()

			types=var_mh[:,0].tolist()
			enthalpy=var_mh[:,3].tolist()
			WHPabs=var_mh[:,4].tolist()
			steam=var_mh[:,5].tolist()
			water=var_mh[:,6].tolist()

			max_len=len(dates_db)

			for n in range(len(dates_db)):

				if n==0:
					dates_db.append(dates_db[n]-dt_forth)
					flows_db.append(0)
					types.append(types[n])
					enthalpy.append(enthalpy[n])
					WHPabs.append(0)
					steam.append(0)
					water.append(0)
				elif flows_db[n]>0 :
					if (enthalpy[n] is None and WHPabs[n]>0) or (enthalpy[n]==0 and WHPabs[n]>0):
						C0=IAPWS97(P=float(WHPabs[n]+patm)/100,x=0)
						enthalpy[n]=C0.h
					elif enthalpy[n] is None and WHPabs[n]==0:
						C0=IAPWS97(T=120+273.15,x=0)
						enthalpy[n]=C0.h
					elif enthalpy[n]==0 and WHPabs[n]>0:
						C0=IAPWS97(P=float(WHPabs[n]+patm)/10,x=0)
						enthalpy[n]=C0.h
					if interval=='year' and dates_db[n].year%4==0:
						criterion=366

					if (dates_db[n+1]-dates_db[n]).days>criterion and flows_db[n+1]>0:
						dates_db.append(dates_db[n]+dt_forth)
						flows_db.append(flows_db[n])
						types.append(types[n])
						enthalpy.append(enthalpy[n])
						WHPabs.append(WHPabs[n])
						steam.append(steam[n])
						water.append(water[n])


						dates_db.append(dates_db[n]+dt_forth+dt_back)
						flows_db.append(0)
						types.append(types[n])
						enthalpy.append(enthalpy[n])
						WHPabs.append(0)
						steam.append(0)
						water.append(0)


						dates_db.append(dates_db[n+1]-dt_forth)
						flows_db.append(flows_db[n+1])
						types.append(types[n+1])

						if enthalpy[n+1]==None:
							C0=IAPWS97(T=120+273.15,x=0)
							enthalpy.append(C0.h)
						else:
							enthalpy.append(enthalpy[n+1])

						WHPabs.append(WHPabs[n+1])
						steam.append(steam[n+1])
						water.append(water[n+1])

						dates_db.append(dates_db[n+1]-dt_forth-dt_back)
						flows_db.append(0)
						types.append(types[n+1])

						if enthalpy[n+1]==None:
							C0=IAPWS97(T=120+273.15,x=0)
							enthalpy.append(C0.h)
						else:
							enthalpy.append(enthalpy[n+1])
						WHPabs.append(0)
						steam.append(0)
						water.append(0)

					if flows_db[n-1]==0:
						
						dates_db.append(dates_db[n]-dt_forth)
						flows_db.append(flows_db[n])
						types.append(types[n])

						if enthalpy[n]==None:
							C0=IAPWS97(T=120+273.15,x=0)
							enthalpy.append(C0.h)
						else:
							enthalpy.append(enthalpy[n])

						WHPabs.append(WHPabs[n])
						steam.append(steam[n])
						water.append(water[n])

						dates_db.append(dates_db[n]-dt_forth-dt_back)
						flows_db.append(0)
						types.append(types[n])
						enthalpy.append(enthalpy[n])
						WHPabs.append(0)
						steam.append(0)
						water.append(0)

					if flows_db[n+1]==0 and n+1<max_len:
						dates_db.append(dates_db[n]+dt_forth)
						flows_db.append(flows_db[n])
						types.append(types[n])
						enthalpy.append(enthalpy[n])
						WHPabs.append(WHPabs[n])
						steam.append(steam[n])
						water.append(water[n])

						dates_db.append(dates_db[n]+dt_forth+dt_back)
						flows_db.append(0)
						types.append(types[n])

						if enthalpy[n]==None:
							C0=IAPWS97(T=120+273.15,x=0)
							enthalpy.append(C0.h)
						else:
							enthalpy.append(enthalpy[n])

						WHPabs.append(0)
						steam.append(0)
						water.append(0)

			unified = np.column_stack([types,dates_db,steam,water,enthalpy,WHPabs])
			unified = unified[np.argsort(unified[:, 1])]

			for nv in range(len(dates_db)):
				if types[nv]in status_rein:
					status='R'
				if types[nv] in status_prod:
					status='P'
				if unified[:,4][nv]!=None:
					string_x="%s,%s,%s,%s,%s,%s\n"%(status,unified[:,1][nv],\
						                        unified[:,2][nv],unified[:,3][nv],unified[:,4][nv],unified[:,5][nv]+patm)
					file_mh.write(string_x)
				else:
					string_x="%s,%s,%s,%s,%s,%s\n"%(unified[:,1][nv],unified[:,2][nv],unified[:,3][nv],unified[:,4][nv],unified[:,5][nv]+patm,name)
					print string_x
			file_mh.close()

def write_drawdown_to_txt_from_GMS(wells,cur,depth_TVD):

	for name in wells:

		drawdown=[]
		dates_dd=[]

		q0 = """SELECT "iNCorr", "iFecha","vStatusPozo", "cTipoMedicion" FROM "tInformacionPerfilesPT" WHERE "vNombrePozo"='%s'\
		    AND ("vStatusPozo"='SHUT-IN' OR "vStatusPozo"='BLEED' OR "vStatusPozo"='PURGADO' OR "vStatusPozo"='CERRADO' OR "vStatusPozo"='PRES' OR "vStatusPozo"='TEMP'\
		     OR "vStatusPozo"='MONITOR' or "vStatusPozo"='PERFORACION'  or "vStatusPozo"='MONIT'  OR "vStatusPozo"='HOTREI' OR "vStatusPozo"='INYECTOR' OR "vStatusPozo"='PRODUCTOR')\
		    ORDER BY "iFecha" """ % (name)
		cur.execute(q0)
		var0 =cur.fetchall()
		corr = np.array(var0)[:, 0]
		dates = np.array(var0)[:, 1]

		cnt=0
		for n in range(len(corr)):
			q1 = """SELECT "fProfundidadMD", "fPresion", "fTemperatura" FROM "tPerfilesPT" WHERE "iNCorr"=%s ORDER BY "fProfundidadMD"  """ % (corr[n])
			try:
				cur.execute(q1)
				var0 = cur.fetchall()
				profr = np.array(var0)[:, 0]
				pr = np.array(var0)[:, 1]
				tr = np.array(var0)[:, 2]

				tr= [np.nan if x == 0 else x for x in tr]
				pr= [np.nan if x == 0 else x for x in pr]

				if not np.isnan(np.mean(pr)) and len(pr)>1:
					x_V,y_V,z_V,var_V=t2r.MD_to_TVD_one_var_array(name,pr,profr,100)
					func_var=interpolate.interp1d(z_V,var_V)
					try:
						drawdown.append(func_var(depth_TVD))
						dates_dd.append(dates[n])
						if cnt==0:
							if not os.path.isfile('../input/drawdown/%s_DD.dat'%name):
								file_dd=open('../input/drawdown/%s_DD.dat'%name,'w')
								file_dd.write("datetime,TVD,pressure\n")
								cnt=1
							else:
								file_dd=open('../input/drawdown/%s_DD.dat'%name,'a')
					except ValueError,KeyError:
						print "There's not enough information for  well %s, %s"%(name,dates[n])
						pass

			except IndexError:
				pass

		for x in range(len(drawdown)):
			string="%s,%s,%s\n"%(datetime.strptime(dates_dd[x]+' 00:00:00', "%Y%m%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")\
								,depth_TVD,drawdown[x])
			file_dd.write(string)
		file_dd.close()
	print depth_TVD

def write_cooling_to_txt_from_GMS(wells,cur,depth_TVD):

	for name in wells:

		cooling=[]
		dates_dd=[]

		q0 = """SELECT "iNCorr", "iFecha","vStatusPozo", "cTipoMedicion" FROM "tInformacionPerfilesPT" WHERE "vNombrePozo"='%s'\
		    AND ("vStatusPozo"='SHUT-IN' OR "vStatusPozo"='BLEED' OR "vStatusPozo"='PURGADO' OR "vStatusPozo"='CERRADO' OR "vStatusPozo"='PRES' OR "vStatusPozo"='TEMP'\
		     OR "vStatusPozo"='MONITOR' or "vStatusPozo"='PERFORACION'  or "vStatusPozo"='MONIT'  OR "vStatusPozo"='HOTREI' OR "vStatusPozo"='INYECTOR' OR "vStatusPozo"='PRODUCTOR')\
		    ORDER BY "iFecha" """ % (name)
		cur.execute(q0)
		var0 =cur.fetchall()
		corr = np.array(var0)[:, 0]
		dates = np.array(var0)[:, 1]

		cnt=0
		for n in range(len(corr)):
			q1 = """SELECT "fProfundidadMD", "fPresion", "fTemperatura" FROM "tPerfilesPT" WHERE "iNCorr"=%s ORDER BY "fProfundidadMD"  """ % (corr[n])
			try:
				cur.execute(q1)
				var0 = cur.fetchall()
				profr = np.array(var0)[:, 0]
				pr = np.array(var0)[:, 1]
				tr = np.array(var0)[:, 2]

				tr= [np.nan if x == 0 else x for x in tr]
				pr= [np.nan if x == 0 else x for x in pr]

				if not np.isnan(np.mean(tr)) and len(tr)>1:
					x_V,y_V,z_V,var_V=t2r.MD_to_TVD_one_var_array(name,tr,profr,100)
					func_var=interpolate.interp1d(z_V,var_V)
					try:
						cooling.append(func_var(depth_TVD))
						dates_dd.append(dates[n])
						if cnt==0:
							if not os.path.isfile('../input/cooling/%s_C.dat'%name):
								file_dd=open('../input/cooling/%s_C.dat'%name,'w')
								file_dd.write("datetime,TVD,temperature\n")
								cnt=1
							else:
								file_dd=open('../input/cooling/%s_C.dat'%name,'a')
					except ValueError,KeyError:
						print "There's not enough information for  well %s, %s"%(name,dates[n])
						pass

			except IndexError:
				pass

		for x in range(len(cooling)):
			string="%s,%s,%s\n"%(datetime.strptime(dates_dd[x]+' 00:00:00', "%Y%m%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")\
								,depth_TVD,cooling[x])
			file_dd.write(string)
		file_dd.close()
	print depth_TVD

"""
depths=[200,100,0,-100,-200]
for d in depths:
	write_cooling_to_txt_from_GMS(wells,cur,d)
"""
#interval : millennium,century,decade,year,quarter,month,week,day,hour,minute,second,milliseconds,microseconds
write_mh_to_txt_from_GMS(wells,cur,'week')
#write_PT_to_txt_from_GMS(wells,cur)
#write_ubication_to_txt_from_GMS(wells,cur)
#write_survey_to_txt_from_GMS(wells,cur)

