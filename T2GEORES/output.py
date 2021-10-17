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

	output_sav_file="../model/t2/t2.%s"%sav_version

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
	compare1="#  OBSERVATION   AT TIME [sec]     MEASURED     COMPUTED     RESIDUAL     WEIGHT C.O.F [%]    STD. DEV.    Yi      Wi    DWi +/-"
	compare2=" Residual Plots"

	data = pd.DataFrame(columns=["NUMBER","OBSERVATION","TIME","MEASURED","COMPUTED","RESIDUAL","WEIGHT","C.O.F","STD.DEV"])

	#Extracts the data based on compare1 and compare2
	output_headers=[]
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

	#Stores the date into the corresponding column
	output_headers=output_headers[1:-3][::2]
	for values in output_headers:
		data_i = values.split()
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


#not documented
def normal_directions(input_dictionary,block,block2):
	"""
	not documented
	"""
	conn=sqlite3.connect(input_dictionary['db_path'])
	points=pd.read_sql_query("SELECT x1,y1,x2,y2,ELEME1,ELEME2 FROM segment WHERE ELEME1='%s' AND ELEME2='%s';"%(block,block2),conn)
	conn.close()
	if block[0]!=block2[0]:
		vectors=[]
		if (formats.formats_t2['LAYERS'][block[0]]-formats.formats_t2['LAYERS'][block2[0]])>0:
			duz=-1
		else:
			duz=1
		dux=0
		duy=0
		points=pd.DataFrame([[dux,duy,duz]],columns=['dux','duy','duz'])
	elif block[0]==block2[0]:
		points['dx']=points['x2']-points['x1']
		points['dy']=points['y2']-points['y1']
		points['r']=(points['dx']**2+points['dy']**2)**0.5
		points['ux']=points['dx']/points['r']
		points['uy']=points['dy']/points['r']
		points['dux']=-points['uy']
		points['duy']=points['ux']
		points['duz']=0
	return points

def output_flows(input_dictionary):
	"""
	Read the .out file from the standard TOUGH2 file and store the data into a database. It includes the model version and timestamp.
	"""

	conn=sqlite3.connect(input_dictionary['db_path'])
	elements=pd.read_sql_query("SELECT DISTINCT ELEME FROM ELEME WHERE model_version=%d;"%(input_dictionary['model_version']),conn)
	elements_list=elements['ELEME'].values.tolist()
	conn.close()

	column_names=['ELEME1', 'ELEME2', 'INDEX','FHEAT','FLOH','FLOF','FLOG','FLOAQ','FLOWTR2','VELG','VELAQ','TURB_COEFF','model_time','model_version','model_output_timestamp']

	time_now=datetime.datetime.now()

	output_t2_file="../model/t2/t2.out"

	bulk_data=[]

	allow=False
	allowed_line=1E50
	if os.path.isfile(output_t2_file):
		t2_file=open(output_t2_file, "r")
		for n,t2_line in enumerate(t2_file):
			if "OUTPUT DATA AFTER" in t2_line:
				time=t2_line.rstrip().split(" ")[-2]
				fix_data=[time,input_dictionary['model_version'],time_now]
				allow=True

			if t2_line=="                          (W)        (J/KG)        (KG/S)       (KG/S)       (KG/S)       (KG/S)        (M/S)        (M/S)        (1/M)\n":
				allowed_line=n+2

			if t2_line==" ELEMENT SOURCE INDEX      GENERATION RATE     ENTHALPY      X1           X2          FF(GAS)      FF(AQ.)         P(WB)\n":
				allow=False
				allowed_line=1E50

			if allow and n>=allowed_line:
				content=t2_line.split()
				if len(content)==12 and content[0]!='ELEM1':
					data_list= list(filter(None, content))
					data_list.extend(fix_data)
					bulk_data.append(data_list)

			"""
			Previous logic
			#if len(t2_line.split())==12 and elements.ELEME.str.count(t2_line.split()[0]).sum()==1 and elements.ELEME.str.count(t2_line.split()[1]).sum()==1:
			#if len(t2_line.split())==12 and bool(re.match("^[A-Z][A-Z][0-9][0-9][0-9]$",str(t2_line.split()[0]))) and bool(re.match("^[A-Z][A-Z][0-9][0-9][0-9]$",str(t2_line.split()[1]))): #3000s
			if len(t2_line.split())==12 and len(t2_line.split()[0])==5 and not(any(y in t2_line.split() for y in ['ELEM1','GENER'] )): #2950s #t2_line.split()[0] in elements_list and t2_line.split()[1] in elements_list: #3500s
				#print(t2_line.split())
				t2_array=t2_line.rstrip().split(" ")
				data_list= list(filter(None, t2_array))
				data_list.extend(fix_data)
				data_line={}

				for i,name in enumerate(column_names):
					try:
						data_line[name]=float(data_list[i])
					except (ValueError,TypeError):
						data_line[name]=data_list[i]
				
				flows_df=flows_df.append(data_line,ignore_index=True)
			"""
		flows_df = pd.DataFrame(bulk_data,columns = column_names)
		t2_file.close()

		#Writing the dataframe to the database

		conn=sqlite3.connect(input_dictionary['db_path'])
		flows_df.to_sql('t2FLOWSout',if_exists='append',con=conn,index=False)
		conn.close()

	else:
		sys.exit("The file %s or directory do not exist"%output_t2_file)

def flow_direction(input_dictionary):
	"""
	not documented
	"""
	conn=sqlite3.connect(input_dictionary['db_path'])
	elements=pd.read_sql_query("SELECT DISTINCT ELEME FROM ELEME WHERE model_version=%d;"%(input_dictionary['model_version']),conn)
	elements_list=elements['ELEME'].values.tolist()
	
	flows_dict={}

	for element in elements_list:

		#print("PRE DIRECTIONS",datetime.datetime.now())
		directions=normal_directions(input_dictionary,element)
		#print("AFTER DIRECTIONS",datetime.datetime.now())
		
		#Direction 1
		#print("PRE query flow",datetime.datetime.now())
		flow_data=pd.read_sql_query("SELECT * FROM t2FLOWSout WHERE ELEME1='%s'AND model_time=-3359500000.0"%element,conn)
		#print("AFTER query flow",datetime.datetime.now())

		flow_data['flow_x']=0
		flow_data['flow_y']=0

		#print("PRE FIRST LOOP",datetime.datetime.now())
		for index, row in flow_data.iterrows(): #horizontal

			if row['ELEME2'][0]!=row['ELEME1'][0]:
				#Establish the direction of the flow
				if (formats.formats_t2['LAYERS'][row['ELEME1'][0]]-formats.formats_t2['LAYERS'][row['ELEME2'][0]])>0:
					uy=-1
				else:
					uy=1

				#It is necessary to check if the right position of ELEME1 and ELEME2 exists
				if element==row['ELEME1']:
					flow_data.loc[(flow_data['ELEME1']==row['ELEME1']) & (flow_data['ELEME2']==row['ELEME2']),"flow_y"]=uy*row['FLOF']
				else:
					flow_data.loc[(flow_data['ELEME1']==row['ELEME2']) & (flow_data['ELEME2']==row['ELEME1']),"flow_y"]=-uy*row['FLOF']

			else:

				ux=float(directions.loc[ (directions['ELEME1']==row['ELEME1']) & (directions['ELEME2']==row['ELEME2'])]['dux'])
				uy=float(directions.loc[ (directions['ELEME1']==row['ELEME1']) & (directions['ELEME2']==row['ELEME2'])]['duy'])
				
				flux=float(flow_data.loc[(flow_data['ELEME1']==row['ELEME1']) & (flow_data['ELEME2']==row['ELEME2'])]['FLOF'])
				
				flow_data.loc[(flow_data['ELEME1']==row['ELEME1']) & (flow_data['ELEME2']==row['ELEME2']),"flow_x"]=ux*flux
				flow_data.loc[(flow_data['ELEME1']==row['ELEME1']) & (flow_data['ELEME2']==row['ELEME2']),"flow_y"]=uy*flux
		#print("AFTER FIRST LOOP",datetime.datetime.now())


		#Direction 2
		flow_data2=pd.read_sql_query("SELECT * FROM t2FLOWSout WHERE ELEME2='%s' AND model_time=-3359500000.0"%element,conn)
		flow_data.append(flow_data2)

		#print("PRE SECOND LOOP",datetime.datetime.now())

		for index, row in flow_data.iterrows(): #horizontal

			if row['ELEME2'][0]!=row['ELEME1'][0]:
				#Establish the direction of the flow
				if (formats.formats_t2['LAYERS'][row['ELEME1'][0]]-formats.formats_t2['LAYERS'][row['ELEME2'][0]])>0:
					uy=-1
				else:
					uy=1

				#It is necessary to check if the right position of ELEME1 and ELEME2 exists
				if element==row['ELEME1']:
					flow_data.loc[(flow_data['ELEME1']==row['ELEME1']) & (flow_data['ELEME2']==row['ELEME2']),"flow_y"]=uy*row['FLOF']
				else:
					flow_data.loc[(flow_data['ELEME1']==row['ELEME2']) & (flow_data['ELEME2']==row['ELEME1']),"flow_y"]=-uy*row['FLOF']

			else:

				ux=float(directions.loc[ (directions['ELEME1']==row['ELEME1']) & (directions['ELEME2']==row['ELEME2'])]['dux'])
				uy=float(directions.loc[ (directions['ELEME1']==row['ELEME1']) & (directions['ELEME2']==row['ELEME2'])]['duy'])
				
				flux=float(flow_data.loc[(flow_data['ELEME1']==row['ELEME1']) & (flow_data['ELEME2']==row['ELEME2'])]['FLOF'])
				
				flow_data.loc[(flow_data['ELEME1']==row['ELEME1']) & (flow_data['ELEME2']==row['ELEME2']),"flow_x"]=ux*flux
				flow_data.loc[(flow_data['ELEME1']==row['ELEME1']) & (flow_data['ELEME2']==row['ELEME2']),"flow_y"]=uy*flux
		#print("AFTER SECOND LOOP",datetime.datetime.now())

		#print("PRE CALCS",datetime.datetime.now())
		sum_flowx=flow_data['flow_x'].sum()
		sum_flowy=flow_data['flow_y'].sum()
		flows_dict[element]=[sum_flowx,sum_flowy,(sum_flowx**2+sum_flowy**2)**0.5]
		#print("AFTER CALCS",datetime.datetime.now())
		#print(element,flows_dict[element])

	flows=pd.DataFrame.from_dict(flows_dict,orient='index',columns=['flow_x','flow_y','flow_mag'])
	#left_side=flow_data.loc[flow_data['ELEME1']==element]
	#right_side=flow_data.loc[flow_data['ELEME2']==element]
	flows.to_csv('directions.csv')
	conn.close()

def flow_direction2(input_dictionary):
	"""
	not documented
	"""
	conn=sqlite3.connect(input_dictionary['db_path'])
	elements=pd.read_sql_query("SELECT DISTINCT ELEME FROM ELEME WHERE model_version=%d;"%(input_dictionary['model_version']),conn)
	elements_list=elements['ELEME'].values.tolist()
	
	flows_dict={}

	flow_data=pd.read_sql_query("SELECT * FROM t2FLOWSout WHERE model_time=-3359500000.0",conn)

	flow_data['x_flow']=flow_data.apply(lambda row : normal_directions(input_dictionary,row['ELEME1'],row['ELEME2'])['dux']*row['FLOF'],axis=1)
	flow_data['y_flow']=flow_data.apply(lambda row : normal_directions(input_dictionary,row['ELEME1'],row['ELEME2'])['duy']*row['FLOF'],axis=1)
	flow_data['z_flow']=flow_data.apply(lambda row : normal_directions(input_dictionary,row['ELEME1'],row['ELEME2'])['duz']*row['FLOF'],axis=1)

	#[Finished in 905.5s]

	elements=pd.read_sql_query("SELECT DISTINCT ELEME FROM ELEME WHERE model_version=%d;"%(input_dictionary['model_version']),conn)
	elements_list=elements['ELEME'].values.tolist()

	bulk_data=[]
	time_now=datetime.datetime.now()
	time=-3359500000.0

	for element in elements_list:
		x=flow_data.loc[flow_data['ELEME1']==element,'x_flow'].sum()-flow_data.loc[flow_data['ELEME2']==element,'x_flow'].sum()
		y=flow_data.loc[flow_data['ELEME1']==element,'y_flow'].sum()-flow_data.loc[flow_data['ELEME2']==element,'y_flow'].sum()
		z=flow_data.loc[flow_data['ELEME1']==element,'z_flow'].sum()-flow_data.loc[flow_data['ELEME2']==element,'z_flow'].sum()
		bulk_data.append([element,x,y,z,time,input_dictionary['model_version'],time_now])


	column_names=['ELEME','FLOF_x','FLOF_y','FLOF_z','model_time','model_version','model_output_timestamp']

	flows_df = pd.DataFrame(bulk_data,columns = column_names)

	#Writing the dataframe into the database

	conn=sqlite3.connect(input_dictionary['db_path'])
	flows_df.to_sql('t2FLOWVectors',if_exists='append',con=conn,index=False)
	conn.close()
