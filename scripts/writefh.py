import psycopg2
from cga_hall_dict import *
import matplotlib.pyplot as plt
from geometry_functions import *
from layers import *
from matplotlib.backends.backend_pdf import PdfPages
import datetime
import os
from scipy import stats
import json
from iapws import IAPWS97

def sourcegen(feed,wells_correlative,layers,well,source_dict):
	block=wells_correlative[well][0]
	for n in layers:
		if  (layers[n][4]<=feed) and (feed<=layers[n][3]):
			block_source_name=layers[n][0]+block
			nickname_prefix='SRC'
			try: 
				next_source_value=max([int(n[3:])  for n in source_dict.values()])
			except ValueError:
				next_source_value=10
			"""
			if next_source_value<10:
				next_source_value+=10
			else:
			"""
			next_source_value+=1
			nickname=nickname_prefix+str(next_source_value)
	return block_source_name, nickname

with open('wells_correlative.txt') as json_file:
    wells_correlative=json.load(json_file)

campo='CGA'
fecha_ref=19750101

replace=['AH4_dict','AH32_dict']
status_rein=['HOTREI','REINYECTOR']
status_prod=['PRODUCTOR']
#now 32ST

if campo=='CGA':
	dictlist=['AH1_dict', 'AH4BIS_dict','AH2_dict', 'AH5_dict',\
	 'AH7_dict', 'AH6_dict', 'AH16A_dict', 'AH17_dict', \
	 'AH19_dict', 'AH20_dict', 'AH21_dict', 'AH22_dict', \
	 'AH23_dict', 'AH24_dict', 'AH26_dict', 'AH27_dict', \
	 'AH28_dict', 'AH29_dict', 'AH31_dict',  \
	 'AH32_dict', 'AH33B_dict', 'AH33C_dict', 'AH34_dict',\
	 'AH34A_dict', 'AH35A_dict', 'AH35B_dict', 'AH35C_dict', \
	 'AH2_dict', 'AH18_dict', 'AH33A_dict', 'CH7_dict', \
	 'CH7BIS_dict', 'CH9_dict', 'CH9A_dict', 'CH9B_dict', 'CH10_dict']

elif campo=='CGB':
	dictlist=['TR1_dict','TR10_dict','TR10A_dict','TR11_dict','TR11A_dict','TR11C_dict',\
	'TR11ST_dict','TR12_dict','TR12A_dict','TR14_dict','TR14A_dict','TR14B_dict','TR15_dict',\
	'TR17_dict','TR17A_dict','TR17B_dict','TR17C_dict','TR18_dict','TR18A_dict','TR18B_dict',\
	'TR19_dict','TR19A_dict','TR19B_dict','TR19C_dict','TR1A_dict','TR1B_dict','TR1C_dict',\
	'TR2_dict','TR3_dict','TR4_dict','TR4A_dict','TR4B_dict','TR4C_dict','TR5_dict','TR5A_dict',\
	'TR5B_dict','TR5C_dict','TR5D_dict','TR7_dict','TR8_dict','TR8A_dict','TR9_dict']


#Conexion a la base de datos
con=psycopg2.connect(dbname='postgres', host='127.0.0.1',port=5432, user='postgres', password='erick')
cur=con.cursor()

source_dict={}

file_gen=open('to_prod_model/gener.dat','w')



for filesnames in dictlist:

	nompozo=eval("%s['name']"%(filesnames))
	if nompozo[0]=='A':
		condition='PROD'
	elif nompozo[0]=='C':
		condition=='REIN'
	feedzone=eval("%s['feedzone']"%(filesnames))
	q0="""SELECT DISTINCT "CodStatus" as status, substring(to_char("tOperacionPozo"."Fecha",'99999999'),1,5) as year, \
				 substring(to_char("tOperacionPozo"."Fecha",'99999999'),6,2) as month, \
	               avg("FlujoAgua"+"FlujoVapor") as total_flow, avg("h"), avg("PresionCabezal")\
	               from "tOperacionPozo" \
	               WHERE "NombrePozo"='%s'\
	               AND "Fecha">%s GROUP BY year, month, status ORDER BY year, month """%(nompozo,fecha_ref)

	cur.execute(q0)
	var0 =cur.fetchall()

	x_feed, y_feed, feedzoneTVD=MD_to_TVD_one_point(filesnames,feedzone)
	block_source_name, nickname=sourcegen(feedzoneTVD,wells_correlative,layers,nompozo,source_dict)

	source_dict[block_source_name]=nickname
	try:
		cod=np.array(var0)[:,0]
		year=np.array(var0)[:,1]
		month=np.array(var0)[:,2]
		flows=np.array(var0)[:,3]
		h_flow=np.array(var0)[:,4]
		P=np.array(var0)[:,5]

		print  nompozo

		file=open('to_prod_model/%s_flow.dat'%nompozo,'w')

		file_gen.write("%s%s\n"%(block_source_name,nickname))
		file.write("%s%s\n"%(block_source_name,nickname))
		for n in range(len(year)):
			if flows[n]>0:
				if cod[n] in status_prod:
					sign=-1
				elif cod[n] in status_rein:
					sign=1
				if (h_flow[n] is None and P[n]>0) or (h_flow[n]==0 and P[n]>0):
					C0=IAPWS97(P=float(P[n])/10,x=0)
					h_flow[n]=C0.h
				elif h_flow[n] is None and P[n]==0:
					C0=IAPWS97(T=120+273.15,x=0)
					h_flow[n]=C0.h
				elif h_flow[n]==0  and P[n]>0:
					C0=IAPWS97(P=float(P[n])/10,x=0)
					h_flow[n]=C0.h

				if h_flow[n] is not None:
					string=" %s-%s-%s_00:00:00 %9.2E %9.2E\n"%(year[n],month[n],"01",sign*float(flows[n]),float(h_flow[n])*1E3)
				file.write(string)
				file_gen.write(string)
		file.close()

	except IndexError:
		pass
