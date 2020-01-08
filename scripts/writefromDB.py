import psycopg2
from model_conf import *
from iapws import IAPWS97
import t2resfun as t2r
import numpy as np


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

	for name in wells:

		file_mh=open('../input/mh/%s_mh.dat'%name,'w')
		file_mh.write("type,date-time,steam,liquid,enthalpy,WHPabs\n")

		q_flow="""SELECT DISTINCT "CodStatus" as status,
		 		  date_trunc('%s',to_timestamp(concat("Fecha",' 00:00:00'),'YYYYMMDD HH24:MI:SS')::timestamp without time zone) as date_f, \
		          avg("FlujoAgua"+"FlujoVapor") as total_flow, avg("h"), avg("PresionCabezal"), avg("FlujoVapor"), avg("FlujoAgua")\
		          from "tOperacionPozo" \
		          WHERE "NombrePozo"='%s'\
		          AND "Fecha">%s GROUP BY date_f, status ORDER BY date_f """%(interval,name,ref_date)
		cur.execute(q_flow)

		var_mh=np.array(cur.fetchall())

		q_ubication="""SELECT "fElevacion" FROM "tUbicacionPozo" WHERE "vNombrePozo"='%s' """%name
		cur.execute(q_ubication)
		var_ubication=cur.fetchall()[0][0]

		patm=t2r.patmfromelev(var_ubication)

		for n_mh in range(len(var_mh)):
			#print name, var_mh[n_mh][2], var_mh[n_mh][1], var_mh[n_mh][3]
			if var_mh[n_mh][0] in status_rein:
				status='R'
			if var_mh[n_mh][0] in status_prod:
				status='P'

			if var_mh[n_mh][2]>0: #Flow bigger than 0
				if (var_mh[n_mh][3] is None and var_mh[n_mh][4]>0) or (var_mh[n_mh][3]==0 and var_mh[n_mh][4]>0):
					C0=IAPWS97(P=float(var_mh[n_mh][4]+patm)/100,x=0)
					var_mh[n_mh][3]=C0.h
				elif var_mh[n_mh][3] is None and var_mh[n_mh][4]==0:
					C0=IAPWS97(T=120+273.15,x=0)
					var_mh[n_mh][3]=C0.h
				elif var_mh[n_mh][3]==0 and var_mh[n_mh][4]>0:
					C0=IAPWS97(P=float(var_mh[n_mh][5]+patm)/10,x=0)
					var_mh[n_mh][3]=C0.h
				string_x="%s,%s,%.2f,%.2f,%.2f,%.2f\n"%(status, \
	                                                        str(var_mh[n_mh][1]),float(var_mh[n_mh][5]), \
	                                                        float(var_mh[n_mh][6]), float(var_mh[n_mh][3]), \
	                                                        float(float(var_mh[n_mh][4])+patm))
				file_mh.write(string_x)

		file_mh.close()


#interval : millennium,century,decade,year,quarter,month,week,day,hour,minute,second,milliseconds,microseconds
write_mh_to_txt_from_GMS(wells,cur,'week')
#write_PT_to_txt_from_GMS(wells,cur)
#write_ubication_to_txt_from_GMS(wells,cur)
#write_survey_to_txt_from_GMS(wells,cur)

