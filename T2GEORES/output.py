import numpy as np
import shutil
import os
import csv
import pandas as pd
import os
import sys
import sqlite3
import subprocess
import json

"""
It extracts the blocks information containing on a TOUGH2 output file.
"""

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
			if  block in line.split() and len(line.split())==11:
				wells_data[blocks_wells[block]]+="%s\n"%(','.join(line.split()))

	#Writes an output file for every well
	for well in wells_data:
		file_out=open("../output/PT/txt/%s_PT.dat"%(well), "w")
		file_out.write("ELEM,INDEX,P,T,SG,SW,X(WAT1),X(WAT2),PCAP,DG,DW\n")
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
	eleme_pd.to_json("../output/PT/json/PT_json_from_sav.txt",orient="index",indent=2)

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