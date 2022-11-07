import numpy as np
import shutil
import os
import csv
import pandas as pd
import sys
import sqlite3
import subprocess
import json
import datetime
import re
from T2GEORES import formats as formats
from T2GEORES import geometry as geometry
from iapws import IAPWS97

def write_PT_from_t2output(input_dictionary):
	"""It writes the parameter for every block from every well from the last output file of TOUGH2 simulation

	Parameters
	----------
	input_dictionary : dictionary
	 Dictionary contaning the path and name of database on keyword 'db_path', list of wells under the keywords 'WELLS', 'MAKE_UP_WELLS' and 'NOT_PRODUCING_WELL'

	Returns
	-------
	file
	  {well_name}_PT.txt: file containing the information for every block from every well

	Attention
	---------
	The layers and well block need  to be on the databse

	Examples
	--------
	>>> write_PT_from_t2output(input_dictionary)
	"""

	wells=[]

	for key in ['WELLS','MAKE_UP_WELLS','NOT_PRODUCING_WELL']:
		try:
			for well in input_dictionary[key]:
				wells.append(well)
		except KeyError:
			pass

	db_path=input_dictionary['db_path']

	t2_output_file="../model/t2/t2.out"
	if os.path.isfile(t2_output_file):
		pass
	else:
		return "Theres is not t2.out file on t2/t2.out"

	#Extracts all the times the line 'OUTPUT DATA AFTER' was printed
	output_headers=[]
	with open(t2_output_file,'r') as t2_file:
		t2_output_array = t2_file.readlines()
		for line_i, line in enumerate(t2_output_array):
			if "OUTPUT DATA AFTER" in line.rstrip():
				output_headers.append(line_i)

	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	#Create a dictionary containing all the blocks in a well

	blocks_wells={}
	wells_data={}

	data_layer=pd.read_sql_query("SELECT correlative FROM layers ORDER BY  middle DESC;",conn)
	for name in sorted(wells):
		wells_data[name]=""
		data_block=pd.read_sql_query("SELECT blockcorr FROM t2wellblock  WHERE well='%s' ORDER BY blockcorr;"%name,conn)
		if len(data_block)>0:
			for n in data_layer['correlative'].values:
				blocks_wells[n+data_block['blockcorr'].values[0]]=name
	
	#Select the last line of TOUGH2 output file
	for line in t2_output_array[output_headers[-1]:-1]:
		for block in blocks_wells:
			if  block in line.split() and len(line.split())==12: #11
				wells_data[blocks_wells[block]]+="%s\n"%(','.join(line.split()))

	#Writes an output file for every well
	for well in wells_data:
		file_out=open("../output/PT/txt/%s_PT.dat"%(well), "w")
		file_out.write("ELEM,INDEX,P,T,SG,SW,X(WAT1),X(WAT2),PCAP,DG,DW,LOG(PERM)\n")
		file_out.write(wells_data[well])
		file_out.close()

	conn.close()
	
def from_sav_to_json(sav_version='sav1'):
	"""It writes a json file with temperature and pressure data from the specified .sav for every block including coordinates
	
	Parameters
	----------
	sav_version : str
	  Extension of sav file, i.e. sav, sav1, sav2, etc.

	Returns
	-------
	file
	  PT_json_from_sav.txt : on  ../output/PT/json/

	Attention
	---------
	The ELEME.json file needs to be updated

	Examples
	--------
	>>> from_sav_to_json(sav_version='sav1')
	"""

	output_sav_file="../model/t2/%s"%sav_version

	#Generates a dictionary with block as keyword and x,y,z coordinates
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

	#Stores Pressure and Temperature on the dictionary
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
	eleme_pd.to_json("../output/PT/json/PT_json_from_sav.json",orient="index",indent=2)

def PTjson_to_sqlite(input_dictionary,source='t2',):
	"""It stores the defined json file into the database on the table t2PTout
	
	Parameters
	----------
	source : str
	  It can be 't2' or 'sav'
	input_dictionary : dictionary
	 Dictionary contaning the path and name of database on keyword 'db_path'.

	Examples
	--------
	>>> PTjson_to_sqlite("t2")
	"""

	db_path=input_dictionary['db_path']

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

def write_PT_of_wells_from_t2output_in_time(input_dictionary):
	"""It generates file containing the evolution of every block on every well

	Extrae la evolucion de los bloques relacionados de todos los pozos en la direccion "../output/PT/evol"
	
	Parameters
	----------
	input_dictionary : dictionary
	  Dictionary contaning the path and name of database on keyword 'db_path', list of wells under the keywords 'WELLS', 'MAKE_UP_WELLS' and 'NOT_PRODUCING_WELL'

	Returns
	-------
	file
	  {well}_PT_{layer}.txt : on  ../output/PT/evol

	Examples
	--------
	>>> write_PT_of_wells_from_t2output_in_time(input_dictionary)
	"""

	db_path=input_dictionary['db_path']

	wells=[]

	for key in ['WELLS','MAKE_UP_WELLS','NOT_PRODUCING_WELL']:
		try:
			for well in input_dictionary[key]:
				wells.append(well)
		except KeyError:
			pass

	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	blocks_wells={}
	blocks_data={}

	#Generates a dictionary with the blocks on a well as a keyword 
	data_layer=pd.read_sql_query("SELECT correlative FROM layers ORDER BY  middle DESC;",conn)
	for name in sorted(wells):
		data_block=pd.read_sql_query("SELECT blockcorr FROM t2wellblock  WHERE well='%s' ORDER BY blockcorr;"%name,conn)
		if len(data_block)>0:
			for n in data_layer['correlative'].values:
				blocks_wells[n+data_block['blockcorr'].values[0]]=name
				blocks_data[n+data_block['blockcorr'].values[0]]=""

	#Explore the TOUGH2 output file line by line and store the information if the block list generated on the previous step is on the line.
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

	#Store the data from the dictionary in files
	for block in blocks_data:
		evol_file_out=open("../output/PT/evol/%s_PT_%s_evol.dat"%(blocks_wells[block],block[0]), "w")
		evol_file_out.write("ELEM,INDEX,P,T,SG,SW,X(WAT1),X(WAT2),PCAP,DG,DW,TIME\n")
		evol_file_out.write(blocks_data[block])
		evol_file_out.close()	
	conn.close()

def gen_evol(input_dictionary):
	"""It generates an output file containing flow and flowing enthalpy for each GEN element. As a convention the library it is suggested to use GEN for any source/sink that is not a well

	Parameters
	----------
	input_dictionary : dictionary
	 Dictionary contaning the path and name of database on keyword 'db_path'.

	Returns
	-------
	file
	  {GEN}_{BLOCK}_{NICKNAME}.txt : on  ../output/mh/txt

	"""

	db_path=input_dictionary['db_path']

	#List the GEN elements
	conn=sqlite3.connect(db_path)
	c=conn.cursor()
	data_source=pd.read_sql_query("SELECT well,blockcorr,source_nickname FROM t2wellsource WHERE  source_nickname LIKE'GEN*' ORDER BY source_nickname;",conn)
	final_t2=""
	output_fi_file="../model/t2/t2.out"

	#Initialize a dictionary containing the file path and name.
	dictionary_files={}
	for n in range(len(data_source)):
		well=data_source['well'][n]
		blockcorr=data_source['blockcorr'][n]
		source=data_source['source_nickname'][n]
		dictionary_files[well]={'filename':"../output/mh/txt/%s_%s_%s_evol_mh.dat"%(well,blockcorr,source),'file_container':"",'blockcorr':blockcorr,'source':source}
		dictionary_files[well]['file_container']+="ELEMENT,SOURCEINDEX,GENERATION RATE,ENTHALPY,X1,X2,FF(GAS),FF(AQ.),P(WB),TIME\n"

	#It reads the TOUGH2 output file line by line and store the data from each GEN element
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

	#Creates a file for every GEN elemen
	for well in dictionary_files:
		t2_file_out=open(dictionary_files[well]['filename'], "w")
		t2_file_out.write(dictionary_files[well]['file_container'])
		t2_file_out.close()	

	conn.close()

def src_evol(input_dictionary):
	"""It generates an output file containing flow and flowing enthalpy for each SRC element. As a convention the library it is suggested to use SRC for any source/sink that is a well

	Parameters
	----------
	input_dictionary : dictionary
	 Dictionary contaning the path and name of database on keyword 'db_path'.

	Returns
	-------
	file
	  {GEN}_{BLOCK}_{NICKNAME}.txt : on  ../output/mh/txt

	"""

	#See comment for gen_evol

	db_path=input_dictionary['db_path']

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

def write_PT_from_t2output_from_prod(input_dictionary,sav_version='sav1'):
	"""It writes a pressure and temperature comming from block on every well in the specified .sav file.

	Parameters
	----------
	input_dictionary : dictionary
	 Dictionary contaning the path and name of database on keyword 'db_path'.
	sav_version : str
	  Extension of sav file, i.e. sav, sav1, sav2, etc.

	Returns
	-------
	file
	  {well_name}_PT.txt: it contains the pressure and temperature information for every well

	"""

	db_path=input_dictionary['db_path']

	wells=[]

	for key in ['WELLS','MAKE_UP_WELLS','NOT_PRODUCING_WELL']:
		try:
			for well in input_dictionary[key]:
				wells.append(well)
		except KeyError:
			pass

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

def extract_csv_from_t2out(json_output=False):
	"""It writes the parameter for every block from the last output file of TOUGH2 simulation on csv or json

	Parameters
	----------
	json_output : bool
	  If True a json file is save on ../output/PT/json/

	Returns
	-------
	file
	  PT.csv: on ../output/PT/csv/

	Attention
	---------
	The file ELEME.json needs to be updated
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

def t2_to_json(itime=None,save_full=False):
	"""It creates a severals or a single json file from the output file from the TOUGH2 run

	Parameters
	----------
 	itime: float
	  It defines a time at which a the parameters from the blocks are extracted into json file. Must be on the same units as the TOUGH2 output files (days, seconds, etc.)
	save_full: bool
	  If True it creates a single output json file

	Returns
	-------
	files
	  t2_ouput_{time}.json: on ../output/PT/json/evol/
	file
	  t2_output:  on ../output/PT/json/

	Attention
	---------
	When t2_output is saved, the large could be too large for the system to handle it

	Examples
	--------
	>>> t2_to_json()
	"""

	block__json_file='../mesh/ELEME.json'

	if os.path.isfile(block__json_file):
		with open('../mesh/ELEME.json') as file:
		  	blocks=json.load(file)
	else:
		sys.exit("The file %s or directory do not exist, run ELEM_to_json from regeo_mesh"%output_t2_file)		  	


	parameters={0:"P",1:"T",2:"SG",3:"SW",4:"X(WAT1)",5:"X(WAT2)",6:"PCAP",7:"DG",8:"DW"}

	#Creates a json file for every output time on the TOUGH2 output file
	cnt=0
	output_t2_file="../model/t2/t2.out"
	if os.path.isfile(output_t2_file):
		t2_file=open(output_t2_file, "r")
		for t2_line in t2_file:
			if "OUTPUT DATA AFTER" in t2_line:
				if cnt!=0:
					if itime==None or (itime!=None and float(time)==float(itime)):
						t2_pd=pd.DataFrame.from_dict(data_dictionary,orient='index')
						t2_pd.to_json('../output/PT/json/evol/t2_output_%s.json'%time,orient="index",indent=2)
						if itime!=None and itime==float(itime):
							break
				cnt+=1
				time=t2_line.rstrip().split(" ")[-2]
				data_dictionary={}
				data_dictionary[time]={}
			if len(t2_line.split())==12 and t2_line.split()[0] in blocks.keys():
				t2_array=t2_line.rstrip().split(" ")
				data_list= list(filter(None, t2_array))
				data_dictionary[time][data_list[0]]={}
				for i in parameters:
					data_dictionary[time][data_list[0]][parameters[i]]=float(data_list[i+2])
		t2_file.close()
	else:
		sys.exit("The file %s or directory do not exist"%output_t2_file)

	if save_full:
		#It generates a dictionary with time as key and json file output as value
		src='../output/PT/json/evol/'
		src_files = os.listdir(src)
		files_dictionary={}
		for file_name in src_files:
			time=file_name.split("_")[2].split(".j")[0]
			full_file_name = os.path.join(src, file_name)
			files_dictionary[time]=full_file_name
	
		#It generates a single json output file, for a large model it can be to large for the system memory
		t2_json='../output/PT/json/t2_output.json'
		t2_output_file=open(t2_json,'w')

		t2_output_file.write("{\n")
		for time in sorted(files_dictionary):
			file=open(files_dictionary[time],'r')
			lines=file.readlines()[1:-2]
			for line in lines:
				t2_output_file.write(line)
			t2_output_file.write(",\n")		
		t2_output_file.write("}")
		t2_output_file.close()

def it2COF(input_dictionary):
	"""Extracts the COF value for each block on the OBSERVATION section of the inverse file

	Parameters
	----------
	input_dictionary : dictionary
		Contains the name of the iTOUGH2 file

	Returns
	-------
	file
		COF_PT.json: on the output/PT/json/ folder

	Attention
	---------
	It might changed based on the iTOUGH2 version

	Examples
	--------
	>>> it2COF(input_dictionary)
	"""

	it2_output_file="../model/t2/%s.out"%input_dictionary['iTOUGH2_file']
	if os.path.isfile(it2_output_file):
		pass
	else:
		return "Theres is not %.out file on t2/%s.out"%(input_dictionary['iTOUGH2_file'],input_dictionary['iTOUGH2_file'])

	#First and last line in between the data
	compare1 = " DATASET              DATAPOINTS          MEAN       MEDIAN    STD. DEV.    AVE. DEV.   SKEWNESS   KURTOSIS      M/S    DWA     COF"
	compare2 = " - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -"

	#Empty dataframe
	data = pd.DataFrame(columns=["DATASET","DATAPOINTS","MEAN","MEDIAN","STD. DEV.","AVE. DEV.","SKEWNESS","KURTOSIS","M/S","DWA","COF"])

	#Extracts the data based on compare1 and compare2
	output_headers = []
	with open(it2_output_file,'r') as t2_file:
		it2_output_array = t2_file.readlines()
		save = False
		for line_i, line in enumerate(it2_output_array):

			if compare1 in line.rstrip():
				save = True
			elif compare2 in line.rstrip():
				save = False

			if save:
				output_headers.append(it2_output_array[line_i+1])

	#Stores the date into the appropiate column
	output_headers=output_headers[1:-1]
	for values in output_headers:
		data_i = values.split()
		data = data.append({"DATASET":data_i[0],
							"DATAPOINTS":data_i[2],
							"MEAN":data_i[3],
							"MEDIAN":data_i[4],
							"STD. DEV.":data_i[5],
							"AVE. DEV.":data_i[6],
							"SKEWNESS":data_i[7],
							"KURTOSIS":data_i[8],
							"M/S":data_i[9],
							"DWA":data_i[10],
							"COF":data_i[12]},ignore_index = True)


	data.to_json("../output/PT/json/COF_PT.json",indent=2)

def it2DATASET(input_dictionary):
	"""Extracts the OBSERVATION dataset on the the inverse file

	Parameters
	----------
	input_dictionary : dictionary
		Contains the name of the iTOUGH2 file

	Returns
	-------
	file
		it2_PT.json: on the output/PT/json/ folder

	Attention
	---------
	It might changed based on the iTOUGH2 version

	Examples
	--------
	>>> it2DATASET(input_dictionary)
	"""

	it2_output_file="../model/t2/%s.out"%input_dictionary['iTOUGH2_file']
	if os.path.isfile(it2_output_file):
		pass
	else:
		return "Theres is not %s.out file on t2/%s.out"%(input_dictionary['iTOUGH2_file'],input_dictionary['iTOUGH2_file'])

	#First and last line in between the data
	compare1="    # OBSERVATION   AT TIME [sec]     MEASURED     COMPUTED     RESIDUAL     WEIGHT C.O.F [%]    STD. DEV.    Yi      Wi    DWi +/-"
	compare2=" Residual Plots"
	compare3=":)"

	data = pd.DataFrame(columns=["NUMBER","OBSERVATION","TIME","MEASURED","COMPUTED","RESIDUAL","WEIGHT","C.O.F","STD.DEV"])


	#Extracts the data based on compare1 and compare2
	output_headers=[]
	with open(it2_output_file,'r') as t2_file:
		it2_output_array = t2_file.readlines()
		save = False
		for line_i, line in enumerate(it2_output_array):

			if compare1 in line.rstrip():
				save = True
			elif compare2 in line.rstrip() or compare3 in line.rstrip():
				save = False

			if save and 'ABS.' not in line.rstrip() :
				output_headers.append(it2_output_array[line_i+1])

	#Stores the date into the corresponding column
	output_headers=output_headers[2:-3] #[::2]

	for values in output_headers:
		data_i = values.split()
		if 'AA' not in data_i[1]:
			data = data.append({"NUMBER":data_i[0],
								"OBSERVATION":data_i[1],
								"TIME":data_i[2],
								"MEASURED":data_i[3],
								"COMPUTED":data_i[4],
								"RESIDUAL":data_i[5],
								"WEIGHT":data_i[6],
								"C.O.F":data_i[7],
								"STD":data_i[8]},ignore_index = True)

	data.to_json("../output/PT/json/it2_PT.json",indent=2)

def it2OBJF(input_dictionary):
	"""Extracts the value of the objective function from the output inverse file and append it with the current time

	Parameters
	----------
	input_dictionary : dictionary
		Contains the name of the iTOUGH2 file

	Returns
	-------
	file
		OBJ.json: on the output/PT/json/ folder

	Attention
	---------
	It might changed based on the iTOUGH2 version

	Examples
	--------
	>>> it2OBJF(input_dictionary)
	"""


	it2_output_file="../model/t2/%s.out"%input_dictionary['iTOUGH2_file']
	if os.path.isfile(it2_output_file):
		pass
	else:
		return "Theres is not %s.out file on t2/%s.out"%(input_dictionary['iTOUGH2_file'],input_dictionary['iTOUGH2_file'])

	#First and last line in between the data

	compare1 = "Objective Function"
	compare2 = "=================================================================================================================================="

	#Extracts the data based on compare1 and compare2
	cnt=0
	output_headers=[]
	with open(it2_output_file,'r') as t2_file:
		it2_output_array = t2_file.readlines()
		save = False
		for line_i, line in enumerate(it2_output_array):

			if compare1 in line.rstrip():
				cnt+=1
				save = True
			elif compare2 in line.rstrip():
				save = False

			if cnt == 2 and save:
				output_headers.append(it2_output_array[line_i+1])
	
	OBJ_file = "../output/PT/json/OBJ.json"

	OBJ = pd.read_json(OBJ_file)

	#Add the current time to the file
	OBJ.loc[len(OBJ.index)] = [datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S'), float(output_headers[2][1:-4].split()[6])]

	OBJ.to_json(OBJ_file,indent=2)

def src_csv(input_dictionary, path = None, type_source = 'SRC'):
	"""It generates an output file containing flow and flowing enthalpy for each sources listed in the GENER section in the TOUGH2 input file..
	   It expects to read the TOUGH2_gener.csv file

	Parameters
	----------
	input_dictionary : dictionary
		Dictionary contaning the path and name of database on keyword 'db_path' and the TOUGH2 file name.
	path: str
		In case a the output file is in a different location. Such as a server.
	type_source: str
		Either SRC or GEN

	Returns
	-------
	files
	  {SOURCE}_{BLOCK}_{NICKNAME}.txt : on  ../output/mh/txt for every source
	"""

	db_path=input_dictionary['db_path']
	t2_file_name = input_dictionary['TOUGH2_file']

	if type_source == 'SRC':
		condition = "NOT LIKE'GEN%%'"
	elif type_source == 'GEN%%':
		condition = "LIKE'GEN%%'"
	else:
		condition = "LIKE '%s%%'"%type_source

	#List the SOURCES elements (feedzones)
	conn=sqlite3.connect(db_path)
	c=conn.cursor()
	data_source=pd.read_sql_query("SELECT well,blockcorr,source_nickname FROM t2wellsource WHERE source_nickname %s ORDER BY source_nickname;"%condition,conn)

	#It reads the gener.csv output file line by line and store the data from each GEN element
	poss_names = ["../model/t2/%s_gener.csv"%t2_file_name]
	if path != None:
		poss_names.append(path)

	output_t2_file = None 
	for file in poss_names:
		if os.path.isfile(file):
			output_t2_file = file

	if output_t2_file == None :
		sys.exit("No output file located")
	else:
		#Initialize a dictionary containing the file path and name.
		dictionary_files={}
		for n in range(len(data_source)):
			well=data_source['well'][n]
			blockcorr=data_source['blockcorr'][n]
			source=data_source['source_nickname'][n]
			dictionary_files[source]={'filename':"../output/mh/txt/%s_%s_%s_evol_mh.dat"%(well,blockcorr,source),'file_container':"",'blockcorr':blockcorr,'source':source}

		if os.path.isfile(output_t2_file):
			t2_file=open(output_t2_file, "r")
			for i, t2_line in enumerate(t2_file):
				if i == 0:
					#Extract the header
					t2_array = t2_line.rstrip().split(" ")
					str_list = list(filter(None, t2_array))
					str_list = [val  for val in str_list if '(' not in val or ')' not in val]
					str_list = [val.replace(',',"").replace('"','') for val in str_list[1:] ]
					str_list.append("TIME")

					for source in dictionary_files:
						dictionary_files[source]['file_container']+=','.join(str_list)+'\n'

				if "TIME [sec]" in t2_line:
					#Extract the time 
					try:
						time = t2_line.rstrip().split(" ")[3]
					except IndexError:
						time = t2_line.rstrip().split(" ")[2]


				for source in dictionary_files:
					#Splits each line from the output file and storage it in a dictionary
					if dictionary_files[source]['blockcorr'] in t2_line and dictionary_files[source]['source'] in t2_line:
						
						block = t2_line[14:19]
						
						t2_array = t2_line.rstrip().split(" ")
						str_list = list(filter(None, t2_array))
						str_list = [val.replace(',',"").replace('"','') for val in str_list[1:] ]
						str_list.append(time.replace('"',""))

						str_list[0] = block

						dictionary_files[source]['file_container']+=','.join(str_list)+'\n'
			t2_file.close()
		else:
			sys.exit("The file %s or directory do not exist"%output_t2_file)


		#Writes a file for each key word in the dictionary dictionary_files
		for source in dictionary_files:
			t2_file_out=open(dictionary_files[source]['filename'], "w")
			t2_file_out.write(dictionary_files[source]['file_container'])
			t2_file_out.close()	

	conn.close()

def eleme_CSV(input_dictionary, path = None, cutoff_time = 1E50):
	"""It generates an output file for every element of every well. It is one of the most computationally demanding functions.
	   It expects to read the output from either TOUGH2_eleme.csv or TOUGH2_XYZ.csv files.

	Parameters
	----------
	input_dictionary : dictionary
		Dictionary contaning the path and name of database on keyword 'db_path' and the TOUGH2 file name.
	path: str
		In case a the output file is in a different location. Such as a server.
	cutoff_time: float
		Max time to storage

	Returns
	-------
	files
	  {well}_PT_evol.dat : on  ../output/PT/evol for every well
	"""

	db_path=input_dictionary['db_path']
	t2_file_name = input_dictionary['TOUGH2_file']

	#List the blocks from each well and file location in the dictionary dictionary_files
	conn=sqlite3.connect(db_path)
	c=conn.cursor()
	dictionary_files = {}
	data_block=pd.read_sql_query("SELECT well, blockcorr FROM t2wellblock  ORDER BY blockcorr;",conn)
	if len(data_block)>0:
		for n, blockcorr in enumerate(data_block['blockcorr']):
			dictionary_files[data_block['well'][n]]={'filename':"../output/PT/evol/%s_PT_evol.dat"%(data_block['well'][n]),\
			                                                    'file_container':"",'blockcorr':blockcorr}
	else:
		sys.exit("Store data on the table t2wellblock")
	blocks =  data_block['blockcorr'].tolist()


	#It select the correct output file
	poss_names = ["../model/t2/%s_XYZ.csv"%t2_file_name, "../model/t2/%s_eleme.csv"%t2_file_name]
	if path != None:
		poss_names.append(path)
	output_t2_file = None 
	for file in poss_names:
		if os.path.isfile(file):
			output_t2_file = file

	#It goes line by line extracting the information and storaging it on the right location at the dictionary_files dictionary
	if output_t2_file == None :
		sys.exit("No output file located")
	else:
		t2_file=open(output_t2_file, "r")
		for i, t2_line in enumerate(t2_file):
			if i == 0:
				t2_array=t2_line.rstrip().split(" ")
				str_list = list(filter(None, t2_array))
				str_list = [val  for val in str_list if '(' not in val or ')' not in val]
				str_list = [val.replace(',',"").replace('"','') for val in str_list[1:] ]
				str_list.append("TIME")
				for well in dictionary_files:
					dictionary_files[well]['file_container']+=','.join(str_list)+'\n'
			if "TIME [sec]" in t2_line:
				try:
					time = t2_line.rstrip().split(" ")[3].replace('"','')
				except IndexError:
					time = t2_line.rstrip().split(" ")[2].replace('"','')

			list_bool = [block in t2_line for block in blocks]
			if any(list_bool):

				block = t2_line[14:19]

				t2_array=t2_line.rstrip().split(" ")
				str_list = list(filter(None, t2_array))
				str_list = [val.replace(',',"").replace('"','') for val in str_list[1:] ]
				str_list.append(time.replace('"',""))

				str_list[0] = block

				pos = list_bool.index(True)
				well = data_block.loc[data_block['blockcorr'] == blocks[pos],'well'].iloc[0]
				dictionary_files[well]['file_container']+=','.join(str_list)+'\n'

			if i>10 and float(time) > cutoff_time:
				break

		t2_file.close()

	#Creates a file for every well
	for well in dictionary_files:
		t2_file_out=open(dictionary_files[well]['filename'], "w")
		t2_file_out.write(dictionary_files[well]['file_container'])
		t2_file_out.close()	

	conn.close()

def t2_CSV_to_json(input_dictionary, itime=None, all_times =False, path = None, num = None, output_times = 220, tmin=0, tmax=1E50):
	"""It creates severals or a single json file from the output file from the TOUGH2 run. Each of them for diffent output times.
	   It expects to read the output from either TOUGH2_eleme.csv or TOUGH2_XYZ.csv files.

	Parameters
	----------
 	itime: float
	  It defines a time at which a the parameters from the blocks are extracted into json file. Must be on the same units as the TOUGH2 output files (days, seconds, etc.)
	path: str
		In case a the output file is in a different location. Such as a server.
	input_dictionary : dictionary
		Dictionary contaning the TOUGH2 file name.
	all_times: bool
		If True it saves all the output times (It does not consider itime). If False, it considers itime.
	output_times: int
		It is an stimation of the number of output times in the TOUGH2 file. Due to its large runtime it has not been implemented, in Linux the command: grep 'TIMES' {T2_output_file.csv} | wl -c, would give the right number
	num: int
		Based on a linear spacing it gives the number of output_times that would be store. If None it will store every output time.

	Returns
	-------
	files
	  t2_ouput_{time}.json: on ../output/PT/json/evol/

	Attention
	---------
	When t2_output is saved, the large could be too large for the system to handle it. The file mesh/ELEME.json has to be created
	"""

	t2_file_name = input_dictionary['TOUGH2_file']

	block_json_file='../mesh/ELEME.json'

	if os.path.isfile(block_json_file):
		with open('../mesh/ELEME.json') as file:
		  	blocks=json.load(file)
	else:
		sys.exit("The file %s or directory do not exist, run ELEM_to_json from regeo_mesh"%output_t2_file)		  	

	#It select the correct output file
	poss_names = ["../model/t2/%s_XYZ.csv"%t2_file_name, "../model/t2/%s_eleme.csv"%t2_file_name]
	poss_names.append(path)
	output_t2_file = None 
	for file in poss_names:
		if os.path.isfile(file):
			output_t2_file = file

	if output_t2_file == None :
		sys.exit("No output file located")
	else:
		
		cnt_t = 0

		if num != None:
			positions = np.linspace(0, output_times, num).astype(int)
		else:
			positions = range(output_times)

		t2_file=open(output_t2_file, "r")
		for i, t2_line in enumerate(t2_file):

			#Extract the headers
			if i == 0:
				t2_array=t2_line.rstrip().split(" ")
				param_list = list(filter(None, t2_array))
				param_list = [val  for val in param_list if '(' not in val or ')' not in val]
				param_list = [val.replace(',',"").replace('"','') for val in param_list[1:] ]

			#Extracts the time, save the data into json and breaks the function once the time is larger than specified itime
			if "TIME [sec]" in t2_line:
				if i >10 and cnt_t in positions and time > tmin and time< tmax: #takes the previous time and save it
					t2_pd=pd.DataFrame.from_dict(data_dictionary,orient='index')
					print(time)
					t2_pd.to_json('../output/PT/json/evol/t2_output_%.0f.json'%float(time),orient="index",indent=2)
				
				try:
					time = float(t2_line.rstrip().split(" ")[3].replace('"',""))
					cnt_t += 1
				except IndexError:
					time = float(t2_line.rstrip().split(" ")[2].replace('"',""))
					cnt_t += 1
				print(time)
				data_dictionary= {}	
				data_dictionary[time] = {}

				if not all_times:
					if time > itime:
						break

			#It stores every line into a dictionary, skips the first line and save just the ones listed into the array positions
			if i != 0 and 'TIME' not in t2_line and cnt_t in positions and time > tmin and time< tmax:
				t2_array=t2_line.rstrip().split(" ")
				str_list = list(filter(None, t2_array))
				block = str_list[1].replace('"','').replace(',',"")

				data_dictionary[time][block]={}
				str_list = [val.replace(',',"").replace('"','') for val in str_list[1:] ]
				for n, param in enumerate(param_list):
					try:
						data_dictionary[time][block][param] = float(str_list[n])
					except ValueError:
						data_dictionary[time][block][param] = str_list[n]

def total_enthalpy(wells):
	"""It creates an output file containing the weighted flowing enthalpy from the producing wells.

	Parameters
	----------
 	wells: list
	  Contains the producer wells included in the calculation.

	Returns
	-------
	files
	  total_prod_mh.csv: in input/mh/

	Attention
	---------
	Each file has to be previously storage. It does a forward fill, since it is necessary to have one value at least per day for every well.
	"""

	#Generates empty dataframe
	data_p = pd.DataFrame(columns=['date_time', 'mh', 'm', 'h'])
	
	for well in wells:

		data = pd.DataFrame(columns=['date_time', 'mh', 'm', 'h'])
		
		#Reads the input file
		data_x = pd.read_csv("../input/mh/%s_mh.dat"%well, usecols = ['date_time', 'total_flow', 'enthalpy', 'status', 'steam'])
		#To make sure it does not uses periods of time the well was under injection, it considers just steam flow above zero
		data_x = data_x.loc[data_x['steam'] > 0]
		data_x['date_time'] = pd.to_datetime(data_x['date_time'] , format="%Y-%m-%d_%H:%M:%S")

		#It does the forward filling
		data_ix = data_x.copy()
		data_ix.index = data_ix['date_time']
		del data_ix['date_time']
		data_ii_inter_x = data_ix.resample('D').mean().ffill()
		data_ii_inter_x['date_time'] = data_ii_inter_x.index

		#Stores the product of mass flow rate and enthalpy for each well
		if wells[well]['type'] == 'producer':
			data['mh'] = data_ii_inter_x['total_flow']*data_ii_inter_x['enthalpy']
			data['m'] = data_ii_inter_x['total_flow']
			data['date_time'] = data_ii_inter_x['date_time']
			data_p = data_p.append(data, ignore_index = True)

	#Group whole datafrime by date_time
	data_p = data_p.groupby('date_time').sum()
	#Calculates the weighted enthalpy
	data_p['h'] = data_p['mh']/data_p['m']

	data_p.to_csv('../input/mh/total_prod_mh.csv' , index = True)

def power_i(Px,hx,mx,ESC, atm_p = 0.092):
	"""It calculates an stimated power output and steam saturation, based on a isoenthalpic expansion

	Parameters
	----------
 	Px: float
	  Assumed wellhead pressure
 	hx: float
	  Flowing enthalpy pressure
 	mx: float
	  Mass flow rate
	ESC: float
	  Assumed specific steam consumption
	atm_p: float
	  Atmosphere presure in bar

	Returns
	-------
	array
	  [power, saturation]
	"""
	if mx <= 0:
		try:
			quality = IAPWS97(P=Px+atm_p,h=hx).x
			power = -quality*mx/ESC
		except NotImplementedError:
			print("Out of bounds, Pressure:", Px,"[bar], Enthalpy: ",hx, "[kJ/kg]")
			power = 0
			quality = 0
	else:
		power = 0
		quality = 0
	return [power, quality]

def power(input_dictionary, WHP):
	"""When all the well feedzones are declare as MASS type in the TOUGH2 input file, this functions estimates the power generation based on the assumption of an isoenthalpic expansion from the feedzone to the wellhead.

	Parameters
	----------
 	input_dictionary: dictionary
	  Dictionary contaning the path and name of database on keyword 'db_path'
 	WHP: dictionary
 	  Using the structure: 'well':[WHP, ESC, 'unit', 'masstype']. masstype could be either MASS or FLOWELL

	Returns
	-------
	File
	  units_power.csv: in output/
	"""

	conn=sqlite3.connect(input_dictionary['db_path'])

	#Creating empty dataframes to store power
	data = pd.DataFrame(columns = ['date_time', 'h', 'm','BWP', 'power','unit'])
	
	c=conn.cursor()

	well_sources = pd.read_sql_query("SELECT * FROM t2wellsource WHERE well LIKE 'TR-%'",conn)

	for index, row in well_sources.iterrows(): 
		if str(row['well']) in [*WHP]:

			evol_file = '../output/PT/evol/%s_PT_evol.dat'%row['well']

			data_i = pd.read_csv(evol_file)

			temp_i = data_i.loc[ (data_i['ELEM'] == row ['blockcorr']) & (data_i['TIME'] >=0 ), ['PRES_VAP','TIME']]
			temp_i.reset_index(inplace = True)

			file = "../output/mh/txt/%s_%s_%s_evol_mh.dat"%(row['well'],row['blockcorr'],row['source_nickname'])

			data_mh = pd.read_csv(file)

			times = data_mh['TIME']

			dates=[]
			enthalpy = []
			flow_rate = []
			pressures = []
			power = []
			units = []

			for n in range(len(times)):
				if float(times[n]) >= 0:
					try:
						pressures.append(temp_i['PRES_VAP'][n])
						enthalpy.append(data_mh['ENTH'][n]/1E3)
						flow_rate.append(data_mh['GEN'][n])
						dates.append(input_dictionary['ref_date']+datetime.timedelta(seconds=int(times[n])))
						units.append(WHP[row['well']][2])
						
						if str(row['well']) in [*WHP]:
							power.append(power_i(WHP[row['well']][0]/1E6,data_mh['ENTH'][n]/1E3,data_mh['GEN'][n],WHP[row['well']][1])[0])
						else:
							power.append(np.nan)

					except (OverflowError, KeyError):
						print(times[n],"plus",str(times[n]),"wont be plot")

			input_row = {'date_time': dates,
			                 'h': enthalpy,
			                 'm': flow_rate,
			               'BWP': pressures,
			               'unit': units,
			               'power':power}

			output = pd.DataFrame.from_dict(input_row)

			data = data.append(output, ignore_index = True)


	data_out = data.groupby(['date_time','unit']).sum()
	data_out.to_csv('../output/units_power.csv')

def flowell(input_dictionary, init_values = 100000):
	"""It extracts from the conventional TOUGH2 output file the FLOWELL data for every well.

	Parameters
	----------
 	input_dictionary: dictionary
	  Dictionary contaning the path and name of database on keyword 'db_path', the specified layers and the reference date
 	init_values: int
 	  Number of possible number initial values for FLOWELL output.

	Returns
	-------
	File
	  flowell.json: at output/
	"""

	db_path=input_dictionary['db_path']
	t2_file_name = input_dictionary['TOUGH2_file']

	#Making sure the output file exists
	t2_output_file="../model/t2/%s.out"%t2_file_name
	if os.path.isfile(t2_output_file):
		pass
	else:
		return "Theres is not t2.out file on t2/%s.out"%t2_file_name


	#Extracting information about the layers
	layers_info=geometry.vertical_layers(input_dictionary)
	layer_tb={layers_info['name'][n]:[layers_info['bottom'][n],layers_info['top'][n]] for n in range(len(layers_info['name']))}

	conn=sqlite3.connect(db_path)
	c=conn.cursor()


	sources_data = pd.read_sql_query("SELECT well, source_nickname FROM t2wellsource",conn)

	#Extracting the sources from the TOUGH2 file
	t2_ifile="../model/t2/%s"%t2_file_name
	if os.path.isfile(t2_ifile):
		pass
	else:
		return "Theres is not t2 file"

	sources = []

	#When splitting the SOURCES some of this versions of S{correlative}C could ocurr, the originall is simply SRC
	options = ['SAC','SBC','SCC','SDC','SBB','SDB','SRC']

	with open(t2_ifile,'r') as t2_ifile:
		t2_i_array = t2_ifile.readlines()
		print_io = False
		for line_i, line in enumerate(t2_i_array):
			if "FLOWELL" in line.rstrip():
				print_io = True

			if print_io:
				if  any(src0 in line.rstrip() for src0 in options):
					source = line.rstrip()[0:10]
					sources.append(source)

	cnt_s = {k:0 for k in sources}

	#Initizalizing dictionary
	data = {}
	for n in range(init_values):
		data[n] = {'SOURCE':'',
		           'TIME':0,
		           'ITER':0,
		           'DATA':[]}

	#Extracting information from wellbore simulator from the TOUGH2 output file
	output_headers=[]
	with open(t2_output_file,'r') as t2_file:
		t2_output_array = t2_file.readlines()
		print_io = False
		cnt = 0
		not_include=['=','&',':','*']
		line_x = 1E50
		iter_i = 0

		for line_i, line in enumerate(t2_output_array):
			if line_i > 1:
				#Extracting the printout time
				if " WELLBORE SIMULATOR FLOWELL AT TIME" in line.rstrip():
					time_i = line.rstrip().split('TIME:')[1].split(' SECONDS')[0]

				#Extracting the source
				if ' ------------------------------------------------' in line.rstrip():
					source = line.rstrip().split('------------------------------------------------')[1].split('-')[0]

				#Extracting the iteration number
				if '-----------ITER =' in line.rstrip():
					iter_i = line.rstrip().split(' -----------ITER = ')[1].split(';')[0]
					cnt += 1

				#If this line occurs means in the next line the printout is going to happen
				if '    DEPTH          FLOW ' in line.rstrip():
					print_io = True
					line_x = line_i

				#If any of these lines occurs the printout ends
				if print_io:
					if ' ------------------------------------------------' in line.rstrip():
						print_io = False
					elif '&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&' in line.rstrip():
						print_io = False


				if print_io and line_i > (line_x+1):
					try:
						if not any(s in line.rstrip() for s in not_include):

							data_i = []
							add = False
							for data_in in list(filter(None, line.rstrip().split(' '))):
								#if the source appears, then some especial treatment is needed
								if data_in in sources:
									cnt_s[data_in] = cnt_s[data_in]+1
									source_i = data_in

									#extracts the MD value
									if cnt_s[data_in] % 2 == 1:
										MD = layer_tb[data_in[0]][0]
									elif cnt_s[data_in] % 2 == 0:
										MD = layer_tb[data_in[0]][1]
									
									well = sources_data.loc[sources_data['source_nickname']==data_in[5:10]].iloc[0]['well']
									md = float(geometry.TVD_to_MD(well,MD))
									data_i.append(md)
								else:
									data_i.append(float(data_in))
							
							#On the second line of every feedzone the productivity index is printout, then it is necessary to fill with nan some spaces
							if cnt_s[source_i] % 2 == 1:
								data_i.insert(2,np.nan)

							#Saves the values into the dictionary
							if len(data_i)>0:
								data[cnt]['SOURCE'] = source
								data[cnt]['TIME'] = (input_dictionary['ref_date']+datetime.timedelta(seconds=float(time_i))).strftime("%Y-%m-%d_%H:%M:%S")
								data[cnt]['ITER'] = int(iter_i) - 1 
								data[cnt]['DATA'].append(data_i)

					except UnboundLocalError:
						pass

	df = pd.DataFrame.from_dict(data,orient = 'index')
	df.to_json('../output/flowell.json',orient="split", indent = 4)

def power_from_flowell(input_dictionary, WHP, exceptions):
	"""When all the well feedzones are declare as MASS and FLOWELL type in the TOUGH2 input file, this functions estimates the power generation based on the assumption of an isoenthalpic expansion from the feedzone to the wellhead for the MASS type
	and takes directly the steam saturation at the wellhead when it comes from FLOWELL.

	Parameters
	----------
 	input_dictionary: dictionary
	  Dictionary contaning the path and name of database on keyword 'db_path'
 	WHP: dictionary
 	  Using the structure: 'well':[WHP, ESC, 'unit', 'masstype']. masstype could be either MASS or FLOWELL
 	exceptions: list
 	  List of sources listed as FLOWELL than will be treated as MASS. It occurs when just one period from the wells are calibrate with FLOWELL. 

	Returns
	-------
	File
	  units_power_flowell.csv: in output/

	Attention
	---------
	Functions src_csv() and eleme_CSV() should be ran before executing this function
	"""

	data = pd.DataFrame(columns = ['date_time', 'swh', 'm', 'power', 'unit'])

	conn=sqlite3.connect(input_dictionary['db_path'])
	c=conn.cursor()

	well_sources = pd.read_sql_query("SELECT * FROM t2wellsource WHERE well LIKE 'TR-%' OR well LIKE 'Mk%' ",conn)

	for index, row in well_sources.iterrows(): 
		if str(row['well']) in [*WHP]:
			evol_file = '../output/mh/txt/%s_%s_%s_evol_mh.dat'%(row['well'],row['blockcorr'],row['source_nickname'])
			Pevol = '../output/PT/evol/%s_PT_evol.dat'%row['well']

			if os.path.isfile(evol_file):
				if WHP[row['well']][3] == 'FLOWELL':
						
					if os.path.isfile(evol_file):
						data_i = pd.read_csv(evol_file)

						temp_i = data_i.loc[ data_i['TIME'] >=0 , ['FWH','SWH', 'TIME']]

						if row['source_nickname'] in exceptions:

							if  os.path.isfile(Pevol): 
								print('******************************************************')
								print(row['well'], 'FLOWELL, exception',row['source_nickname'])

								data_i = pd.read_csv(Pevol)

								temp_i = data_i.loc[ (data_i['ELEM'] == row ['blockcorr']) & (data_i['TIME'] >=0 ), ['PRES_VAP','TIME']]
								temp_i.reset_index(inplace = True)

								data_mh = pd.read_csv(evol_file)

								times = data_mh['TIME']

								dates=[]
								flow_rate = []
								swh = []
								power = []
								units = []

								for n in range(len(times)):
									if float(times[n]) >= 0:
										try:
											flow_rate.append(data_mh['GEN'][n])
											dates.append(input_dictionary['ref_date']+datetime.timedelta(seconds=int(times[n])))
											
											if str(row['well']) in [*WHP]:
												t = power_i(WHP[row['well']][0]/1E6,data_mh['ENTH'][n]/1E3,data_mh['GEN'][n],WHP[row['well']][1])
												power.append(t[0])
												swh.append(t[1])
												units.append(WHP[row['well']][2] )
											else:
												power.append(np.nan)

										except (OverflowError, KeyError):
											print(times[n],"plus",str(times[n]),"wont be plot")

								input_row = {'date_time': dates,
								                 'm': flow_rate,
								               'swh': swh,
								               'power':power,
								               'unit':units}

								output = pd.DataFrame.from_dict(input_row)
								data = data.append(output, ignore_index = True)
								print(row['well'], 'FLOWELL, exception',row['source_nickname'])
						else:

							print(row['well'], 'FLOWELL',row['source_nickname'])

							temp_i.reset_index(inplace = True)

							times = temp_i['TIME']

							dates=[]
							swh = []
							flow_rate = []
							power = []
							units = []

							for n in range(len(times)):
								if float(times[n]) >= 0:
									try:
										flow_rate.append(temp_i['FWH'][n])
										dates.append(input_dictionary['ref_date']+datetime.timedelta(seconds=int(times[n])))
										swh.append(temp_i['SWH'][n])
										power.append(temp_i['SWH'][n]*temp_i['FWH'][n]/WHP[row['well']][1])
										units.append(WHP[row['well']][2])

									except (OverflowError, KeyError):
										print(times[n],"plus",str(times[n]),"wont be plot")

							input_row = {'date_time': dates,
							                 'swh': swh,
							                 'm': flow_rate,
							               'power':power,
							               'unit':units}

							output = pd.DataFrame.from_dict(input_row)
							data = data.append(output, ignore_index = True)
							print(row['well'], 'FLOWELL',row['source_nickname'])
				elif WHP[row['well']][3] == 'MASS':

					if  os.path.isfile(Pevol):

						print(row['well'], 'MASS',row['source_nickname'])

						data_i = pd.read_csv(Pevol)

						temp_i = data_i.loc[ (data_i['ELEM'] == row ['blockcorr']) & (data_i['TIME'] >=0 ), ['PRES_VAP','TIME']]
						temp_i.reset_index(inplace = True)

						data_mh = pd.read_csv(evol_file)

						times = data_mh['TIME']

						dates=[]
						flow_rate = []
						swh = []
						power = []
						units = []

						for n in range(len(times)):
							if float(times[n]) >= 0:
								try:
									flow_rate.append(data_mh['GEN'][n])
									dates.append(input_dictionary['ref_date']+datetime.timedelta(seconds=int(times[n])))
									
									if str(row['well']) in [*WHP]:
										t = power_i(WHP[row['well']][0]/1E6,data_mh['ENTH'][n]/1E3,data_mh['GEN'][n],WHP[row['well']][1])
										power.append(t[0])
										swh.append(t[1])
										units.append(WHP[row['well']][2])
									else:
										power.append(np.nan)

								except (OverflowError, KeyError):
									print(times[n],"plus",str(times[n]),"wont be plot")

						input_row = {'date_time': dates,
						                 'm': flow_rate,
						               'swh': swh,
						               'power':power}

						output = pd.DataFrame.from_dict(input_row)

						data = data.append(output, ignore_index = True)

						print(row['well'], 'MASS',row['source_nickname'])

	data_out = data.groupby(['date_time','unit']).sum()
	data_out.to_csv('../output/units_power_flowell.csv')

