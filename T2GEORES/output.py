import numpy as np
import shutil
import os
import csv
from datetime import datetime, timedelta
import pandas as pd
import os
import sys
from model_conf import *
import sqlite3
import subprocess
import json
from model_conf import input_data,geners
import re

"""
Se encarga de la extraccion de informacion de un archivo de salida TOUGH2 v6.x
"""

def write_PT_from_t2output(db_path=input_data['db_path'],wells=[i for x in ['WELLS','MAKE_UP_WELLS','NOT_PRODUCING_WELL'] for i in input_data[x]]):
	"""Escribe la ultima linea de salida del archivo t2.out relativa a cada bloque de pozo

	Parameters
	----------
	db_path : str
	  Direccion de base de datos sqlite, tomado de model_conf

	Returns
	-------
	file
	  {well_name}_PT.txt: archivo de texto que contiene la informacion relacionado con bloques de todas la capas relacionados a un pozo

	Attention
	---------
	Genera los bloques a extraer de la base de datos sqlite

	Note
	----
	Se auxilia del archivo shell shell/write_PT.sh
	Examples
	--------
	>>> write_PT_from_t2output(db_path)
	"""

	t2_output_file="../model/t2/t2.out"
	if os.path.isfile(t2_output_file):
		pass
	else:
		return "Theres is not t2.out file on t2/t2.out"

	output_headers=[]
	with open(t2_output_file,'r') as t2_file:
		t2_output_array = t2_file.readlines()
		for line_i, line in enumerate(t2_output_array):
			if "OUTPUT DATA AFTER" in line.rstrip():
				output_headers.append(line_i)

	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	#Listing all the wells and assigning them to a well

	blocks_wells={}
	wells_data={}

	data_layer=pd.read_sql_query("SELECT correlative FROM layers ORDER BY  middle DESC;",conn)

	for name in sorted(wells):
		wells_data[name]=""
		data_block=pd.read_sql_query("SELECT blockcorr FROM t2wellblock  WHERE well='%s' ORDER BY blockcorr;"%name,conn)
		if len(data_block)>0:
			for n in data_layer['correlative'].values:
				blocks_wells[n+data_block['blockcorr'].values[0]]=name
	
	for line in t2_output_array[output_headers[-1]:-1]:
		for block in blocks_wells:
			if  block in line.split() and len(line.split())==11:
				wells_data[blocks_wells[block]]+="%s\n"%(','.join(line.split()))

	for well in wells_data:
		file_out=open("../output/PT/txt/%s_PT.dat"%(well), "w")
		file_out.write("ELEM,INDEX,P,T,SG,SW,X(WAT1),X(WAT2),PCAP,DG,DW\n")
		file_out.write(wells_data[well])
		file_out.close()

	conn.close()
	
def from_sav_to_json(sav_version='sav1'):
	"""Escribre un json con las propiedades de salida de los archivo .sav o .sav1 (P,T) para cada bloque, identificandolos de forma espacial
	
	Parameters
	----------
	src_file : str
	  Nombre de archivo sav, puede ser t2.sav o t2.sav1

	Returns
	-------
	file
	  PT_json_from_sav.txt : en direccion  "../output/PT/json/PT_json_from_sav.txt"

	Attention
	---------
	Utiliza el archivo "../mesh/to_steinar/in" como criterio para atribuir coordenadas a cada bloque

	Examples
	--------
	>>> from_sav_to_json("t2.sav1")
	"""

	output_sav_file="../model/t2/t2.%s"%sav_version

	with open('../mesh/ELEME.json') as file:
	  	blocks_position=json.load(file)

	eleme_dict={}
	for block in blocks_position:
		eleme_dict[block]=[blocks_position[block]['X'],blocks_position[block]['Y'],blocks_position[block]['Z']]

	#Creates a string from .sav file
	savfile=open(output_sav_file,"r")
	savstring=[]
	for linesav in savfile:
		savstring.append(linesav.rstrip())
	savfile.close()

	if os.path.isfile(output_sav_file):
		t2_sav_file=open(output_sav_file, "r")
		contidion_found=False
		for t2_sav_line in t2_sav_file:
			if  t2_sav_line[0:5] in  eleme_dict.keys():
				contidion_found=True
				block=t2_sav_line[0:5]
				continue
			if contidion_found:
				eleme_dict[block].extend([float(i) for i in t2_sav_line.split()])
				contidion_found=False
		t2_sav_file.close()

	eleme_pd=pd.DataFrame.from_dict(eleme_dict,orient='index', columns=['X', 'Y','Z','P','T'])
	eleme_pd.to_json("../output/PT/json/PT_json_from_sav.txt",orient="index",indent=2)

def PTjson_to_sqlite(source='t2',db_path=input_data['db_path']):
	"""Escribe la salida de extract_json_from_t2out o from_sav_to_json a base de datos sqlite
	
	Parameters
	----------
	source : str
	  Puede ser t2 o sav

	Note
	----
	Escribe en la tabla t2PTout

	Examples
	--------
	>>> PTjson_to_sqlite("t2")
	"""

	conn=sqlite3.connect(db_path)
	c=conn.cursor()
	if source=="t2":
		if os.path.isfile("../output/PT/json/PT_json.txt"):
			with open("../output/PT/json/PT_json.txt") as f:
				data=json.load(f)
			for element in sorted(data):
				try:
					q="INSERT INTO t2PTout(blockcorr,x,y,z,'index',P,T,SG,SW,X1,X2,PCAP,DG,DW) \
					VALUES ('%s',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"%(element,	data[element]['X'],data[element]['Y'],data[element]['Z'],data[element]['INDEX'],\
																			data[element]['P'],data[element]['T'],data[element]['SG'],\
																			data[element]['SW'],data[element]['X(WAT1)'],data[element]['X(WAT2)'],\
																			data[element]['PCAP'],data[element]['DG'],data[element]['DW'])

					c.execute(q)
				except sqlite3.IntegrityError:
					q="UPDATE t2PTout SET \
					x=%s, \
					y=%s, \
					z=%s, \
					'index'=%s, \
					P=%s, \
					T=%s, \
					SG=%s, \
					SW=%s, \
					X1=%s, \
					X2=%s, \
					PCAP=%s, \
					DG=%s, \
					DW=%s \
					WHERE blockcorr='%s'"%(	data[element]['X'],data[element]['Y'],data[element]['Z'],data[element]['INDEX'],\
											data[element]['P'],data[element]['T'],data[element]['SG'],\
											data[element]['SW'],data[element]['X(WAT1)'],data[element]['X(WAT2)'],\
											data[element]['PCAP'],data[element]['DG'],data[element]['DW'],element)
					c.execute(q)
				conn.commit()
	elif source=="sav":
		if os.path.isfile("../output/PT/json/PT_json_from_sav.txt"):
			with open("../output/PT/json/PT_json_from_sav.txt") as f:
				data=json.load(f)
			for element in sorted(data):
				try:
					q="INSERT INTO t2PTout(blockcorr,x,y,z,P,T) \
					VALUES ('%s',%s,%s,%s,%s,%s)"%(element,\
												   data[element]['X'],data[element]['Y'],data[element]['Z'],\
												   data[element]['P'],data[element]['T'])
					c.execute(q)
				except sqlite3.IntegrityError:
					q="UPDATE t2PTout SET \
					x=%s, \
					y=%s, \
					z=%s, \
					P=%s, \
					T=%s \
					WHERE blockcorr='%s'"%(data[element]['ELEM'],\
										   data[element]['X'],data[element]['Y'],data[element]['Z'],\
										   data[element]['P'],data[element]['T'],data[element]['ELEM'])
					c.execute(q)
				conn.commit()

	conn.close()

def write_PT_of_wells_from_t2output_in_time(db_path=input_data['db_path'],wells=[i for x in ['WELLS','MAKE_UP_WELLS','NOT_PRODUCING_WELL'] for i in input_data[x]]):
	"""Extrae la evolucion de los bloques relacionados de todos los pozos en la direccion "../output/PT/evol"
	
	Parameters
	----------
	db_path : str
	  Direccion de base de datos sqlite, tomado de model_conf

	Note
	----
	Se auxilia del archivo shell blocks_evol_times.sh

	Examples
	--------
	>>> write_PT_of_wells_from_t2output_in_time(db_path)
	"""

	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	blocks_wells={}
	blocks_data={}

	data_layer=pd.read_sql_query("SELECT correlative FROM layers ORDER BY  middle DESC;",conn)

	for name in sorted(wells):
		data_block=pd.read_sql_query("SELECT blockcorr FROM t2wellblock  WHERE well='%s' ORDER BY blockcorr;"%name,conn)
		if len(data_block)>0:
			for n in data_layer['correlative'].values:
				blocks_wells[n+data_block['blockcorr'].values[0]]=name
				blocks_data[n+data_block['blockcorr'].values[0]]=""

	output_t2_file="../model/t2/t2.out"
	if os.path.isfile(output_t2_file):
		t2_file=open(output_t2_file, "r")
		for t2_line in t2_file:
			if "OUTPUT DATA AFTER" in t2_line:
				time=t2_line.rstrip().split(" ")[-2]
			if len(t2_line.split())==11 and t2_line.split()[0] in blocks_data.keys():
				t2_array=t2_line.rstrip().split(" ")
				data_list= list(filter(None, t2_array))
				data_list.append(time)
				blocks_data[t2_line.split()[0]]+=','.join(data_list)+'\n'
		t2_file.close()
	else:
		sys.exit("The file %s or directory do not exist"%output_t2_file)

	for block in blocks_data:
		evol_file_out=open("../output/PT/evol/%s_PT_%s_evol.dat"%(blocks_wells[block],block[0]), "w")
		evol_file_out.write("ELEM,INDEX,P,T,SG,SW,X(WAT1),X(WAT2),PCAP,DG,DW,TIME\n")
		evol_file_out.write(blocks_data[block])
		evol_file_out.close()	
	conn.close()

def gen_evol():
	"""Extrae la evolucion (Flujo y entalpia) de las fuentes o sumideros "GEN" en la direccion "../output/mh/txt"

	Note
	----
	Se auxilia del archivo shell gen_evol.sh

	Examples
	--------
	>>> gen_evol()
	"""
	"""Extrae la evolucion (Flujo y entalpia) de las fuentes o sumideros "SRC" (Estas se relacionan con cada pozo)en la direccion "../output/mh/txt"
	
	Note
	----
	Se auxilia del archivo shell src_evol.sh

	Examples
	--------
	>>> src_evol()
	"""

	conn=sqlite3.connect(input_data['db_path'])
	c=conn.cursor()
	data_source=pd.read_sql_query("SELECT well,blockcorr,source_nickname FROM t2wellsource WHERE  source_nickname LIKE'GEN*' ORDER BY source_nickname;",conn)

	final_t2=""
	output_fi_file="../model/t2/t2.out"

	dictionary_files={}

	for n in range(len(data_source)):
		well=data_source['well'][n]
		blockcorr=data_source['blockcorr'][n]
		source=data_source['source_nickname'][n]
		dictionary_files[well]={'filename':"../output/mh/txt/%s_%s_%s_evol_mh.dat"%(well,blockcorr,source),'file_container':"",'blockcorr':blockcorr,'source':source}
		dictionary_files[well]['file_container']+="ELEMENT,SOURCEINDEX,GENERATION RATE,ENTHALPY,X1,X2,FF(GAS),FF(AQ.),P(WB),TIME\n"

	output_t2_file="../model/t2/t2.out"
	if os.path.isfile(output_t2_file):
		t2_file=open(output_t2_file, "r")
		for t2_line in t2_file:
			if "OUTPUT DATA AFTER" in t2_line:
				time=t2_line.rstrip().split(" ")[-2]
			for well in dictionary_files:
				if dictionary_files[well]['blockcorr'] in t2_line and dictionary_files[well]['source'] in t2_line:
					t2_array=t2_line.rstrip().split(" ")
					str_list = list(filter(None, t2_array))
					str_list.append(time)
					dictionary_files[well]['file_container']+=','.join(str_list)+'\n'
		t2_file.close()
	else:
		sys.exit("The file %s or directory do not exist"%output_t2_file)

	for well in dictionary_files:
		t2_file_out=open(dictionary_files[well]['filename'], "w")
		t2_file_out.write(dictionary_files[well]['file_container'])
		t2_file_out.close()	

	conn.close()

def src_evol():
	"""Extrae la evolucion (Flujo y entalpia) de las fuentes o sumideros "SRC" (Estas se relacionan con cada pozo)en la direccion "../output/mh/txt"
	
	Note
	----
	Se auxilia del archivo shell src_evol.sh

	Examples
	--------
	>>> src_evol()
	"""

	conn=sqlite3.connect(input_data['db_path'])
	c=conn.cursor()
	data_source=pd.read_sql_query("SELECT well,blockcorr,source_nickname FROM t2wellsource WHERE  source_nickname NOT LIKE'GEN*' ORDER BY source_nickname;",conn)

	final_t2=""
	output_fi_file="../model/t2/t2.out"

	dictionary_files={}

	for n in range(len(data_source)):
		well=data_source['well'][n]
		blockcorr=data_source['blockcorr'][n]
		source=data_source['source_nickname'][n]
		dictionary_files[well]={'filename':"../output/mh/txt/%s_%s_%s_evol_mh.dat"%(well,blockcorr,source),'file_container':"",'blockcorr':blockcorr,'source':source}
		dictionary_files[well]['file_container']+="ELEMENT,SOURCEINDEX,GENERATION RATE,ENTHALPY,X1,X2,FF(GAS),FF(AQ.),P(WB),TIME\n"

	output_t2_file="../model/t2/t2.out"
	if os.path.isfile(output_t2_file):
		t2_file=open(output_t2_file, "r")
		for t2_line in t2_file:
			if "OUTPUT DATA AFTER" in t2_line:
				time=t2_line.rstrip().split(" ")[-2]
			for well in dictionary_files:
				if dictionary_files[well]['blockcorr'] in t2_line and dictionary_files[well]['source'] in t2_line:
					t2_array=t2_line.rstrip().split(" ")
					str_list = list(filter(None, t2_array))
					str_list.append(time)
					dictionary_files[well]['file_container']+=','.join(str_list)+'\n'
		t2_file.close()
	else:
		sys.exit("The file %s or directory do not exist"%output_t2_file)

	for well in dictionary_files:
		t2_file_out=open(dictionary_files[well]['filename'], "w")
		t2_file_out.write(dictionary_files[well]['file_container'])
		t2_file_out.close()	

	conn.close()

def write_PT_from_t2output_from_prod(db_path=input_data['db_path'],wells=[i for x in ['WELLS','MAKE_UP_WELLS','NOT_PRODUCING_WELL'] for i in input_data[x]],sav_version='sav1'):
	"""Escribe la presion y temperatura para un pozo a partir de la salida del estado de produccion, utiliza el archivo .sav1, generado a partir del uso de STEADY-STATE y  RESTART TIME en el archivo itough2

	Parameters
	----------
	db_path : str
	  Direccion de base de datos sqlite, tomado de model_conf

	Returns
	-------
	file
	  {well_name}_PT.txt: archivo de texto que contiene la informacion relacionado con bloques de todas la capas relacionados a un pozo

	Attention
	---------
	Genera los bloques a extraer de la base de datos sqlite

	Note
	----
	Se auxilia del archivo shell shell/write_PT_from_prod.sh
	Examples
	--------
	>>> write_PT_from_t2output_from_prod(db_path)
	"""


	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	#Listing all the wells and assigning them to a well

	blocks_wells={}
	wells_data={}
	blocks_dictionary={}

	data_layer=pd.read_sql_query("SELECT correlative FROM layers ORDER BY  middle DESC;",conn)

	for name in sorted(wells):
		wells_data[name]=""
		data_block=pd.read_sql_query("SELECT blockcorr FROM t2wellblock  WHERE well='%s' ORDER BY blockcorr;"%name,conn)
		if len(data_block)>0:
			for n in data_layer['correlative'].values:
				blocks_wells[n+data_block['blockcorr'].values[0]]=name

	
	output_sav_file="../model/t2/t2.%s"%sav_version
	if os.path.isfile(output_sav_file):
		t2_sav_file=open(output_sav_file, "r")
		contidion_found=False
		for t2_sav_line in t2_sav_file:
			if  t2_sav_line[0:5] in  blocks_wells.keys():
				contidion_found=True
				well=blocks_wells[t2_sav_line[0:5]]
				block=t2_sav_line[0:5]
				continue
			if contidion_found:
				wells_data[well]+="%s%s"%(block,','.join(t2_sav_line.split(" ")))
				contidion_found=False
		t2_sav_file.close()

	for well in wells_data:
		file_out=open("../output/PT/txt/%s_PT.dat"%(well), "w")
		file_out.write("ELEM,P,T\n")
		file_out.write(wells_data[well])
		file_out.close()

	conn.close()

def extract_from_t2out(json_output=False):
	"""Escribre un csv con todas las propiedades de salida (ELEM,P,T,SG,SW,X(WAT1),X(WAT2),PCAP,DG,DW) del archivo t2.out para cada bloque, junto con su identificacion espacial

	Returns
	-------
	file
	  PT.csv : en direccion  '../output/PT/csv/PT_json.txt'

	Attention
	---------
	Utiliza el archivo "../mesh/to_steinar/in" como criterio para atribuir coordenadas a cada bloque

	Examples
	--------
	>>> extract_json_from_t2out(db_path)
	"""
	
	eleme_dict={}

	ELEME_file='../mesh/ELEME.json'
	if os.path.isfile(ELEME_file):
		with open(ELEME_file) as file:
		  	blocks_position=json.load(file)

		for block in blocks_position:
			eleme_dict[block]=[blocks_position[block]['X'],blocks_position[block]['Y'],blocks_position[block]['Z']]
	else:
		return "The file %s does not exist"%ELEME_file

	last=""
	if os.path.isfile("../model/t2/t2.out"):
		t2file=open("../model/t2/t2.out","r")
	else:
		return "Theres is not t2.out file on t2/t2.out"


	cnt=0
	t2string=[]
	#It finds the last section where OUTPUT DATA AFTER was printed and uses it to know where to start to extract data. But also converts every line of the file into an element in an array
	for linet2 in t2file:
		cnt+=1
		t2string.append(linet2.rstrip())
		if "OUTPUT DATA AFTER" in linet2.rstrip():
			last=linet2.rstrip().split(",")
			line=cnt
	t2file.close()

	high_iteration=[int(s) for s in last[0].split() if s.isdigit()]

	for elementx in eleme_dict:
		cnt2=0
		for lineout in t2string[line+cnt2:-1]:
			if " @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"==lineout:
				cnt2+=1
			elif cnt2>2:
				break
			elif elementx in lineout:
				lineselect=lineout.split()
				eleme_dict[elementx].extend(lineselect)
				break

	csv_columns=['X','Y','Z','ELEM','INDEX','P','T','SG','SW','X(WAT1)','X(WAT2)','PCAP','DG','DW']

	if json_output:
		eleme_pd=pd.DataFrame.from_dict(eleme_dict,orient='index',columns=csv_columns)
		dtype= {'X':'float',
				 'Y':'float',
				 'Z':'float',
				 'ELEM':'str',
				 'INDEX':'float',
				 'P':'float',
				 'T':'float',
				 'SG':'float',
				 'SW':'float',
				 'X(WAT1)':'float',
				 'X(WAT2)':'float',
				 'PCAP':'float',
				 'DG':'float',
				 'DW':'float'}
		eleme_pd= eleme_pd.astype(dtype)
		eleme_pd.to_json("../output/PT/json/PT_json.txt",orient="index",indent=2)

	with open("../output/PT/csv/PT.csv",'w') as file:
		file.write(','.join(csv_columns))
		file.write('\n')
		for key in eleme_dict.keys():
			string=""
			for d in eleme_dict[key]:
				string+="%s,"%(d)
			file.write(string[0:-2])
			file.write('\n')
	file.close()

#extract_json_from_t2out()

#from_sav_to_json("t2.sav1")

#write_PT_of_wells_from_t2output_in_time(db_path)
#PTjson_to_sqlite(source="t2")#source="sav",t2

#gen_evol()

#src_evol()


"""
CHINAMECA
"""

#write_PT_from_t2output(db_path)

#extract_json_from_t2out()

#src_evol()
#write_PT_of_wells_from_t2output_in_time(db_path)

#Sostenibilidad Ahuachapan

#**---Comparacion en estado natural

#write_PT_from_t2output(db_path)

#**--

#**--Comparacion completa de avance, en estado de produccion

#gen_evol()

#src_evol()

#write_PT_of_wells_from_t2output_in_time(db_path)

#write_PT_from_t2output_from_prod(db_path)

#from_sav_to_json("t2.sav1")

#**--

#extract_csv_from_t2out()

#src_evol()

#gen_evol()

#write_PT_from_t2output_from_prod(json_output=True)

#extract_csv_from_t2out()

#write_PT_from_t2output()

#from_sav_to_json()

#write_PT_of_wells_from_t2output_in_time()

#extract_from_t2out(json_output=True)

#PTjson_to_sqlite(source='sav')