from formats import formats_t2
from model_conf import input_data
import numpy as np
from datetime import datetime
import sys
import os
import pandas as pd
import sqlite3

def converter(value,format_t2,def_value):
	if 's' in format_t2:
		if value==None:
			eq_str_len=int(format_t2.replace(">","").replace("s",""))
			value=" "*eq_str_len
		else:
			value=str(value)
	elif 'E' in format_t2 and def_value:
		if value==None:
			eq_str_len=int(format_t2.split('.')[0].split('>')[1])
			value=" "*eq_str_len
			format_t2=">%ss"%eq_str_len
	elif 'd' in format_t2 and def_value:
		if value==None:
			eq_str_len=int(format_t2.split('d')[0].split('>')[1])
			value=" "*eq_str_len
			format_t2=">%ss"%eq_str_len
	output=format(value,format_t2)

	return output

def def_value_selector(section,key,input_dictionary):
	try:
		value=input_dictionary[section][key]
		def_value=False
	except KeyError:
		value=formats_t2[section][key][0]
		def_value=True
	return value,def_value

def FCG_file_checker(name):
	string=""
	if os.path.isfile("../model/t2/sources/%s"%name):
		with open("../model/t2/sources/%s"%name) as file:
			isfile=True
			for cnt,line in enumerate(file.readlines()[:]):
				if cnt+1<100:
					string+="%s"%line
				else:
					print("Values above E%s(100) will not be printed, %s is not included"%(name,line))
	else:
		print("Error message: the %s file on ../model/t2/sources/%s is not prepared"%(name,name))
		isfile=False
	string+="\n"	
	return string,isfile

def diff_seconds(ref,date):
	#Both should be datetime
	if isinstance(date, datetime) and isinstance(ref, datetime):
		diff_seconds=(date-ref).total_seconds()
	else:
		sys.exit("ref or date values are not datetime type")
	return diff_seconds

def PARAM_writer():
	string="PARAM----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"
	params_levels=[1,2,3,4]
	for level in params_levels:
		for key in formats_t2['PARAMETERS']:
			if formats_t2['PARAMETERS'][key][2]==level:
				if key=='RE1' and 'DELTEN' in input_data['PARAMETERS'] and input_data['PARAMETERS']['DELTEN']<0 :
					for index, time_step in enumerate(input_data['PARAMETERS']['DELTEN_LIST']):
						string+=converter(time_step,formats_t2['DELTEN_LIST_FORMAT'][1],False)
						if (index+1)%8==0:
							string+='\n'
					string+='\n'

				value,def_value=def_value_selector('PARAMETERS',key)

				if not isinstance(value,list):
					string+=converter(value,formats_t2['PARAMETERS'][key][1],def_value)
				else:
					for cnt, var in enumerate(value):
						string+=converter(var,formats_t2['PARAMETERS'][key][cnt][2],def_value)
		string+='\n'
	string+="\n"
	return string

def TIMES_writer(input_dictionary=input_data):
	string="TIMES----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"

	if any(input_dictionary['TIMES']['TIMES_N']):
		len_times=len(input_dictionary['TIMES']['TIMES_N'])
		input_dictionary['TIMES']['ITI']=len_times
		input_dictionary['TIMES']['ITE']=len_times
		if len_times>100:
			sys.exit("ITI cannot be higher than 100, reduce the number of times")
	for key in formats_t2['TIMES']:

		value,def_value=def_value_selector('TIMES',key,input_dictionary)

		if not isinstance(value,np.ndarray):
			string+=converter(value,formats_t2['TIMES'][key][1],def_value)
		else:
			string+='\n'
			for index, var in enumerate(value):
				string+=converter(diff_seconds(input_dictionary['ref_date'],var),formats_t2['TIMES']['TIMES_N'][1],False)
				if (index+1)%8==0:
					string+='\n'
	string+="\n\n"
	return string

def source_to_FOFT(db_path=input_data['db_path']):
	"""Crea la seccion FOFT a partir de las fuentes en los pozos

	Parameters
	----------
	db_path : str
	  Direccion de base de datos sqlite, tomado de model_conf

	Returns
	-------
	file
	  FOFT: en ../model/t2/sources
	  
	Examples
	--------
	>>> write_well_sources_from_sqlite_to_FOFT(db_path)
	"""

	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	data_blockcorr=pd.read_sql_query("SELECT blockcorr FROM t2wellsource WHERE source_nickname LIKE 'SRC%';",conn)

	string=""
	for n in sorted(data_blockcorr['blockcorr'].values):
		string+="%s\n"%(n)

	conn.close()
	file=open("../model/t2/sources/FOFT",'w')
	file.write(string)
	file.close()

def wells_track_blocks_to_FOFT(db_path=input_data['db_path']):
	"""Crea la seccion FOFT a partir de la trayectoria del pozo

	Parameters
	----------
	db_path : str
	  Direccion de base de datos sqlite, tomado de model_conf

	Returns
	-------
	file
	  FOFT: en ../model/t2/sources
	  
	Attention
	---------
	En general esta funcion contendra mas de 100 elementos por lo que para la version 6.x de TOUGH2 se recomienda utilizar la funcion write_well_sources_from_sqlite_to_FOFT

	Examples
	--------
	>>> write_wells_track_blocks_from_sqlite_to_FOFT(db_path)
	"""

	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	data_layer=pd.read_sql_query("SELECT correlative FROM layers ORDER BY middle;",conn)

	string=""
	for name in sorted(wells):
		data_block=pd.read_sql_query("SELECT blockcorr FROM t2wellblock  WHERE well='%s' ORDER BY blockcorr;"%name,conn)
		if len(data_block)>0:
			for n in sorted(data_layer['correlative'].values):
				string+="%s\n"%(n+data_block['blockcorr'].values[0])
	conn.close()
	file=open("../model/t2/sources/FOFT",'w')
	file.write(string)
	file.close()

def FOFT_writer():
	string,isfile=FCG_file_checker('FOFT')
	if isfile:
		output="""FOFT ----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"""
		output+=string
	else:
		output=""
	return output

def COFT_writer():
	string,isfile=FCG_file_checker('COFT')
	if isfile:
		output="""COFT ----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"""
		output+=string
	else:
		output=""
	return output

def source_to_GOFT(db_path=input_data['db_path']):
	"""Crea la seccion FOFT a partir de las fuentes en los pozos

	Parameters
	----------
	db_path : str
	  Direccion de base de datos sqlite, tomado de model_conf

	Returns
	-------
	file
	  FOFT: en ../model/t2/sources
	  
	Examples
	--------
	>>> write_well_sources_from_sqlite_to_FOFT(db_path)
	"""

	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	data_blockcorr=pd.read_sql_query("SELECT source_nickname FROM t2wellsource WHERE source_nickname LIKE 'SRC%';",conn)

	string=""
	for n in sorted(data_blockcorr['source_nickname'].values):
		string+="%s\n"%(n)

	conn.close()
	file=open("../model/t2/sources/GOFT",'w')
	file.write(string)
	file.close()

def GOFT_writer():
	string,isfile=FCG_file_checker('GOFT')
	if isfile:
		output="""GOFT ----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"""
		output+=string
	else:
		output=""
	return output

def SOLVR_writer():
	string="SOLVR----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"
	
	cnt=0
	for key in formats_t2['SOLVR']:
		value,def_value=def_value_selector('SOLVR',key)
		if def_value: cnt+=1 
		string+=converter(value,formats_t2['SOLVR'][key][1],def_value)
	string+="\n\n"

	if cnt==len(formats_t2['SOLVR']):
		string=""
	return string

def GENER_adder(type_run=input_data['TYPE_RUN']):
	string="GENER----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"

	if os.path.isfile("../model/t2/sources/GENER_SOURCES") and type_run in ['natural','production']:
		with open("../model/t2/sources/GENER_SOURCES") as gener_source_file:
			for line in gener_source_file.readlines()[:]:
				string+="%s"%line
		if type_run=='natural':
			string+="\n"
		elif type_run=='production':
			if os.path.isfile("../model/t2/sources/GENER_PROD"):
				with open("../model/t2/sources/GENER_PROD") as gener_prod_file:
					for line in gener_prod_file.readlines()[:]:
						string+="%s"%line
			else:
				sys.exit("""Error message: the GENER_PROD file on ../model/t2/sources/GENER_PROD is not prepared\n
					        you might want to run write_gener_from_sqlite on t2gener.py file""")
			
			if os.path.isfile("../model/t2/sources/GENER_MAKEUP"):
				with open("../model/t2/sources/GENER_MAKEUP") as gener_prod_file:
					for line in gener_prod_file.readlines()[:]:
						string+="%s"%line
				string+="\n"
			else:
				print("""Error message: the GENER_MAKEUP file on ../model/t2/sources/GENER_MAKEUP is not prepared\n
					        you might want to run write_gener_from_sqlite on t2gener.py file""")
	else:
		sys.exit("""Error message: the GENER_SOURCES file on ..\model\t2\sources\GENER_SOURCES is not prepared\n
			        you might want to run write_geners_to_txt_and_sqlite on t2gener.py file or the type_run is not correct (natural or production)""")

	return string

def RPCAP_writer():
	string="RPCAP----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"
	params_levels=[1,2]
	for level in params_levels:
		for key in formats_t2['RPCAP']:
			if formats_t2['RPCAP'][key][2]==level:
				value,def_value=def_value_selector('RPCAP',key)
				string+=converter(value,formats_t2['RPCAP'][key][1],def_value)
		string+='\n'
	string+="\n"
	return string

def MULTI_writer():
	string="MULTI----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"
	cnt=0
	for key in formats_t2['MULTI']:
		value,def_value=def_value_selector('MULTI',key)
		if def_value: cnt+=1 
		string+=converter(value,formats_t2['MULTI'][key][1],def_value)
	string+="\n\n"

	if cnt==len(formats_t2['MULTI']):
		string=""
	return string

def TITLE_writer():
	try:
		value=input_data['TITLE']
	except KeyError:
		value=formats_t2['TITLE'][1]
	return  value[0:80].ljust(80) +'\n'

def CONNE_from_steinar_to_t2():
	"""Convierte archivo conne de salida de steinar a archivo CONNE en ../model/t2/sources

	Returns
	-------
	file
	  CONNE: conexiones de elementos
	  
	Attention
	---------
	Existen dos diferencias principales, a primera es el formato de steinar (ancho de columnas) y la segunda es la componente de la gravedad en steinar es +1 cuando cuando deberia ser -1 (debido al en como se escriben los bloques). Tambien introduce la cabezera del archivo.

	Examples
	--------
	>>> CONNE_from_steinar_to_t2()
	"""
	source_file="../mesh/to_steinar/conne"
	output_file="../model/t2/sources/CONNE"

	string="CONNE----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"
	if os.path.isfile(source_file):
		with open(source_file) as rock_file:
			for line in rock_file.readlines()[1:]:
				linex=line.split()
				if float(linex[8])<=0:
					string+="%10s%20s%10.3E%10.3E%10.3E%10.2f\n"%(linex[0],int(linex[4]),float(linex[5]),float(linex[6]),float(linex[7]),float(linex[8]))
				else:
					string+="%10s%20s%10.3E%10.3E%10.3E%10.2f\n"%(linex[0],int(linex[4]),float(linex[5]),float(linex[6]),float(linex[7]),-1*float(linex[8]))
		string+='\n'
		file=open(output_file,'w')
		file.write(string)
		file.close()
	else:
		sys.exit("The file %s or directory do not exist"%source_file)

def merge_ELEME_and_in_to_t2():
	"""Convierte archivo eleme de salida de steinar a archivo ELEME en ../model/t2/sources

	Returns
	-------
	file
	  ELEME: definicion de los elementos en formato TOUGH2
	  
	Attention
	---------
	El archivo eleme de steinar no contiene xyz por lo que esta funcion introduce las coordenadas al archivo de salida ELEME, asi como la cabezera del mismo.

	Examples
	--------
	>>> conne_from_steinar_to_t2()
	"""
	source_file="../mesh/to_steinar/in"
	eleme_file="../mesh/to_steinar/eleme"
	output_file="../model/t2/sources/ELEME"

	if os.path.isfile(source_file) and os.path.isfile(eleme_file):
		string="ELEME----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"
		data_in=pd.read_csv(source_file,delim_whitespace=True,skiprows=7,header=None,names=['block','li','X','Y','Z','h'])
		data_eleme=pd.read_csv(eleme_file,delim_whitespace=True,skiprows=1,header=None,names=['block','rocktype','vol'])
		data_in.set_index('block')
		data_eleme.set_index('block')

		for n in range(len(data_eleme['block'])):
			selection=data_in.loc[data_in['block']==data_eleme['block'][n]].values.tolist()
			if data_eleme['vol'][n]>0:
				string+="%5s%10s%5s%10.3E%10s%10s%10.3E%10.3E%10.3E\n"%(data_eleme['block'][n],\
	                                                                      " ",\
	                                                data_eleme['rocktype'][n],\
	                                                     data_eleme['vol'][n],\
	                                                                       " ",\
	                                                                       " ",\
	                                                           selection[0][2],\
	                                                           selection[0][3],\
	                                                           selection[0][4])

			else:
				string+="%5s%10s%5s%10s%10s%10.3E%10.3E%10.3E\n"%(data_eleme['block'][n],\
					                                                                      " ",\
					                                                data_eleme['rocktype'][n],\
					                                                                       " ",\
					                                                                       " ",\
					                                                           selection[0][2],\
					                                                           selection[0][3],\
					                                                           selection[0][4])

		string+='\n'
		file=open(output_file,'w')
		file.write(string)
		file.close()
	else:
		sys.exit("The file %s or directory do not exist"%file_source_file)

def ELEME_adder():

	source_file="../model/t2/sources/ELEME"
	string=""
	if os.path.isfile(source_file):
		with open(source_file) as eleme_source_file:
			for line in eleme_source_file.readlines()[:]:
				string+="%s"%line
	else:
		sys.exit("The file %s or directory do not exist"%source_file)

	return string

def CONNE_adder():
	source_file="../model/t2/sources/CONNE"
	string=""
	if os.path.isfile(source_file):
		with open(source_file) as conne_source_file:
			for line in conne_source_file.readlines()[:]:
				string+="%s"%line
	else:
		sys.exit("The file %s or directory do not exist"%source_file)
	return string

def t2_input(include_FOFT,include_SOLVR,include_COFT,include_GOFT,include_RPCAP,include_MULTI,include_START,type_run=input_data['TYPE_RUN']):

	secctions=[TITLE_writer,PARAM_writer,TIMES_writer,ELEME_adder,CONNE_adder]

	if_functions_dictionary={'RPCAP':[include_RPCAP,RPCAP_writer],
							 'MULTI':[include_MULTI,MULTI_writer],
							 'FOFT':[include_FOFT,FOFT_writer],
							 'SOLVR':[include_SOLVR,SOLVR_writer],
							 'COFT':[include_COFT,COFT_writer],
							 'GOFT':[include_GOFT,GOFT_writer]}

	for bools in if_functions_dictionary:
		if if_functions_dictionary[bools][0]:
			secctions.append(if_functions_dictionary[bools][1])

	output=""
	for func in secctions:
		if func==PARAM_writer and include_START:
			output+="START----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"
		output+=func()

	output+=GENER_adder(type_run)

	output+="ENDCY----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"

	input_fi_file="../model/t2/t2"
	t2_file_out=open(input_fi_file, "w")
	t2_file_out.write(output)
	t2_file_out.close()	

#t2_input(include_FOFT=True,include_RPCAP=True,include_SOLVR=True,include_COFT=True,include_GOFT=True,include_MULTI=True,include_START=True,type_run='production')
