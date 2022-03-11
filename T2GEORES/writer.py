from T2GEORES import formats as formats
import numpy as np
from datetime import datetime
import sys
import os
import pandas as pd
import sqlite3
import json

def converter(value,format_t2,def_value):
	"""Returns the input value on the specified format

	Parameters
	----------
	value : float-str
	  Parameter to be written
	format_t2 : dictionary
	  Contains the format and default values for every variable
	def_value : bool
	  True in case the default values is used

	Note
	----
	format_t2 comes from the file formats.py. In case a new type of section is included, the variable name needs to be specified on the file

	"""
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

def def_value_selector(section,key,input_dictionary,rocks=False):
	"""Evaluate if the necessary parameter has been defined on the input file

	Parameters
	----------
	section : str
	  Section from TOUGH2 file such as PARAMETER, RPCAP, etc.
	key : str
	  Parameter to evaluate
	input_dictionary : dictionary
	  Dictionary with the defined input information

	"""

	try:
		if not rocks:
			value=input_dictionary[section][key]
			def_value=False
		else:
			value=input_dictionary['ROCKS'][section][key]
			def_value=False
	except KeyError:
		if not rocks:
			value=formats.formats_t2[section][key][0]
			def_value=True
		else:
			value=formats.formats_t2['ROCKS'][key][0]
			def_value=True
	return value,def_value

def FCG_file_checker(name):
	"""Evaluate if the the file defining the FOFT, COFT or GOFT section exits or if it contains more than 100 lines

	Parameters
	----------
	name : str
	  Name of the file to check

	Note
	----
	Print messages are expected

	Returns
	-------
	str
	  string : string containing 100 lines of the selected file
	bool
	  isfile : True if the file exits

	"""

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
	"""Return the difference in seconds

	Parameters
	----------
	ref : datetime
	  Model's reference time
	date : datetime
	  An arbitrary time

	Returns
	-------
	int
	  diff_seconds : difference in seconds

	"""

	if isinstance(date, datetime) and isinstance(ref, datetime):
		diff_seconds=(date-ref).total_seconds()
	else:
		sys.exit("ref or date values are not datetime type")
	return diff_seconds

def PARAM_writer(input_dictionary):
	"""Return the PARAM section

	Parameters
	----------
	input_dictionary : dictionary
	  Dictionary with the defined parameter information

	Returns
	-------
	str
	  string : string containing PARAM section

	"""
	string="PARAM----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"
	params_levels=[1,2,3,4]
	for level in params_levels:
		for key in formats.formats_t2['PARAMETERS']:
			if formats.formats_t2['PARAMETERS'][key][2]==level:
				if key=='RE1' and 'DELTEN' in input_dictionary['PARAMETERS'] and input_dictionary['PARAMETERS']['DELTEN']<0 :
					for index, time_step in enumerate(input_dictionary['PARAMETERS']['DELTEN_LIST']):
						string+=converter(time_step,formats.formats_t2['DELTEN_LIST_FORMAT'][1],False)
						if (index+1)%8==0:
							string+='\n'
					string+='\n'

				value,def_value=def_value_selector('PARAMETERS',key,input_dictionary)

				if not isinstance(value,list):
					string+=converter(value,formats.formats_t2['PARAMETERS'][key][1],def_value)
				else:
					for cnt, var in enumerate(value):
						string+=converter(var,formats.formats_t2['PARAMETERS'][key][cnt][2],def_value)
		string+='\n'
	string+="\n"
	return string

def TIMES_writer(input_dictionary):
	"""Return the TIMES section

	Parameters
	----------
	input_dictionary : dictionary
	  Dictionary with the defined TIMES information

	Returns
	-------
	str
	  string : string containing the TIMES section

	"""

	string="TIMES----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"

	if any(input_dictionary['TIMES']['TIMES_N']):
		len_times=len(input_dictionary['TIMES']['TIMES_N'])
		input_dictionary['TIMES']['ITI']=len_times
		input_dictionary['TIMES']['ITE']=len_times
		if len_times>100:
			sys.exit("ITI cannot be higher than 100, reduce the number of times")
	for key in formats.formats_t2['TIMES']:

		value,def_value=def_value_selector('TIMES',key,input_dictionary)

		if not isinstance(value,np.ndarray):
			string+=converter(value,formats.formats_t2['TIMES'][key][1],def_value)
		else:
			string+='\n'
			for index, var in enumerate(value):
				string+=converter(diff_seconds(input_dictionary['ref_date'],var),formats.formats_t2['TIMES']['TIMES_N'][1],False)
				if (index+1)%8==0:
					string+='\n'
	string+="\n\n"
	return string

def wells_track_blocks_to_FOFT(input_dictionary,wells):
	"""It creates the FOFT section base on the well track

	Parameters
	----------
	input_dictionary : dictionary
	  Dictionary with the data base location information
	wells: list
	  Wells to include on the FOFT section

	Returns
	-------
	file
	  FOFT: on ../model/t2/sources
	  
	Attention
	---------
	This function could have more than 100 elements depending on the number of layers and wells defined. For TOUGH2 6.x it is preffereable to use well_sources_to_FOFT

	Examples
	--------
	>>> wells_track_blocks_to_FOFT(input_dictionary)
	"""

	conn=sqlite3.connect(input_dictionary['db_path'])
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

def well_sources_to_FOFT(input_dictionary,wells):
	""""It creates the FOFT section base on the well feedzone position

	Parameters
	----------
	input_dictionary : dictionary
	  Dictionary with the data base location information
	wells: list
	  Wells to include on the FOFT section

	Returns
	-------
	file
	  FOFT: on ../model/t2/sources

	Examples
	--------
	>>> well_sources_to_FOFT(input_dictionary)
	"""

	conn=sqlite3.connect(input_dictionary['db_path'])
	c=conn.cursor()

	string=""
	for name in sorted(wells):
		data_block=pd.read_sql_query("SELECT blockcorr FROM t2wellsource WHERE well='%s';"%name,conn)
		string+="%s\n"%(data_block['blockcorr'].values[0])
	conn.close()
	file=open("../model/t2/sources/FOFT",'w')
	file.write(string)
	file.close()

def FOFT_writer(input_dictionary):
	""""It wraps up the section FOFT

	Returns
	-------
	str
	  output: contains the FOFT section

	"""
	string,isfile=FCG_file_checker('FOFT')
	if isfile:
		output="""FOFT ----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"""
		output+=string
	else:
		output=""
	return output

def COFT_writer(input_dictionary):
	""""It wraps up the section COFT

	Returns
	-------
	str
	  output: contains the COFT section

	"""
	string,isfile=FCG_file_checker('COFT')
	if isfile:
		output="""COFT ----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"""
		output+=string
	else:
		output=""
	return output

def source_to_GOFT(input_dictionary):
	""""It creates the GOFT section base on the well feedzone position nickname

	Parameters
	----------
	input_dictionary : dictionary
	  Dictionary with the data base location information

	Returns
	-------
	file
	  GOFT: on ../model/t2/sources

	Examples
	--------
	>>> source_to_GOFT(input_dictionary)
	"""


	conn=sqlite3.connect(input_dictionary['db_path'])
	c=conn.cursor()

	data_blockcorr=pd.read_sql_query("SELECT source_nickname FROM t2wellsource WHERE source_nickname LIKE 'SRC%';",conn)

	string=""
	for n in sorted(data_blockcorr['source_nickname'].values):
		string+="%s\n"%(n)

	conn.close()
	file=open("../model/t2/sources/GOFT",'w')
	file.write(string)
	file.close()

def GOFT_writer(input_dictionary):
	""""It wraps up the section COFT

	Returns
	-------
	str
	  output: contains the COFT section

	"""
	string,isfile=FCG_file_checker('GOFT')
	if isfile:
		output="""GOFT ----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"""
		output+=string
	else:
		output=""
	return output

def SOLVR_writer(input_dictionary):
	""""It wraps up the section SOLVR

	Returns
	-------
	str
	  output: contains the SOLVR section


	"""
	string="SOLVR----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"
	
	cnt=0
	for key in formats.formats_t2['SOLVR']:
		value,def_value=def_value_selector('SOLVR',key,input_dictionary)
		if def_value: cnt+=1 
		string+=converter(value,formats.formats_t2['SOLVR'][key][1],def_value)
	string+="\n\n"

	if cnt==len(formats.formats_t2['SOLVR']):
		string=""
	return string

def GENER_adder(input_dictionary):
	""""It takes all the GENER section created depending on the type of run production or natural defined on the input dictionary

	Parameters
	----------
	input_dictionary : dictionary
	  Dictionary specficing the type of run

	Returns
	-------
	str
	  string : string containing the GENER section

	"""
	string="GENER----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"
	if os.path.isfile("../model/t2/sources/GENER_SOURCES") and input_dictionary['TYPE_RUN'] in ['natural','production']:
		with open("../model/t2/sources/GENER_SOURCES") as gener_source_file:
			for line in gener_source_file.readlines()[:]:
				string+="%s"%line
		if input_dictionary['TYPE_RUN']=='natural':
			string+="\n"
		elif input_dictionary['TYPE_RUN']=='production':
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

def RPCAP_writer(input_dictionary):
	""""It wraps up the section RPCAP

	Parameters
	----------
	input_dictionary : dictionary
	  Dictionary containing the RPCAP information

	Returns
	-------
	str
	  output: contains the RPCAP section

	"""
	string="RPCAP----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"
	params_levels=[1,2]
	for level in params_levels:
		for key in formats.formats_t2['RPCAP']:
			if formats.formats_t2['RPCAP'][key][2]==level:
				value,def_value=def_value_selector('RPCAP',key,input_dictionary)
				string+=converter(value,formats.formats_t2['RPCAP'][key][1],def_value)
		string+='\n'
	string+="\n"
	return string

def MULTI_writer(input_dictionary):
	""""It wraps up the section MULTI

	Parameters
	----------
	input_dictionary : dictionary
	  Dictionary containing the MULTI information

	Returns
	-------
	str
	  output: contains the MULTI section

	"""
	string="MULTI----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"
	cnt=0
	for key in formats.formats_t2['MULTI']:
		value,def_value=def_value_selector('MULTI',key,input_dictionary)
		if def_value: cnt+=1 
		string+=converter(value,formats.formats_t2['MULTI'][key][1],def_value)
	string+="\n\n"

	if cnt==len(formats.formats_t2['MULTI']):
		string=""
	return string

def TITLE_writer(input_dictionary):
	""""It writes the TITLE of TOUGH2 file

	Parameters
	----------
	input_dictionary : dictionary
	  Dictionary containing the TITLE information

	Returns
	-------
	str
	  output: contains the TITLE section
	"""

	try:
		value=input_dictionary['TITLE']
	except KeyError:
		value=formats.formats_t2['TITLE'][0]
	return  value[0:80].ljust(80) +'\n'

def CONNE_from_steinar_to_t2():
	"""It takes the CONNE file from steinar and convertir into a CONNE TOUGH2 section (the vertical connections are affected by -1)

	Returns
	-------
	file
	  CONNE: on ../model/t2/sources/
	  
	Attention
	---------
	Comparing with steinar CONNE format the column width changes with the standard TOUGH2 input file

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
	"""It takes the ELEME file from the steinar directory and convert it into a TOUGH2 format with coordinates 

	Returns
	-------
	file
	  ELEME: section from TOUGH2 file
	  
	Attention
	---------
	It adds the head of the section.

	Examples
	--------
	>>> merge_ELEME_and_in_to_t2()
	"""
	eleme_file="../mesh/to_steinar/eleme"
	output_file="../model/t2/sources/ELEME"


	block_eleme_file="../mesh/ELEME.json"
	if os.path.isfile(block_eleme_file):
		with open(block_eleme_file) as file:
			blocks=json.load(file)
	else:
		sys.exit("The file %s or directory do not exist"%block_eleme_file)

	col_eleme=[(0,6),(15,20),(20,30)]

	if os.path.isfile(eleme_file):
		string="ELEME----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"
		data_eleme=pd.read_fwf(eleme_file,colspecs=col_eleme,skiprows=1,header=None,names=['ELEME','MA1','VOLX'])

		for i, row in data_eleme.iterrows():
			data_eleme.at[i,'VOLX'] = blocks[row['ELEME']]['VOLX']

		for i, row in data_eleme.sort_values(by=['VOLX'], ascending=False).iterrows():
			try:
				string+="%5s%10s%5s%10.3E%10s%10s%10.3E%10.3E%10.3E\n"%(row['ELEME'],\
					                                                    " ",\
					                                                row['MA1'],\
					                                                blocks[row['ELEME']]['VOLX'],\
		                                                                       " ",\
		                                                                       " ",\
		                                                            blocks[row['ELEME']]['X'],\
		                                                            blocks[row['ELEME']]['Y'],\
		                                                            blocks[row['ELEME']]['Z'])
			except KeyError:
				pass
		string+='\n'
		file=open(output_file,'w')
		file.write(string)
		file.close()
	else:
		sys.exit("The file %s or directory do not exist"%file_source_file)

def ATM_data():


	block_eleme_file="../mesh/vtu/ELEME.json"
	if os.path.isfile(block_eleme_file):
		with open(block_eleme_file) as file:
			blocks=json.load(file)
	else:
		sys.exit("The file %s or directory do not exist"%block_eleme_file)

	conne_file_st=open('../model/t2/sources/CONNE2','w')  
	conne_file=open('../model/t2/sources/CONNE','r')  
	data_conne=conne_file.readlines()

	for line in data_conne:
		#if both are on the conne line, the line should not exist
		if line[0:5] in blocks.keys() and line[5:10] in blocks.keys():
			conne_file_st.write(line)
		elif line[0:5] not in blocks.keys() and line[5:10] not in blocks.keys() :
			pass
		elif line[0:5] not in blocks.keys():
			if line[0]!=line[5]:
				conne_file_st.write('ATM01'+line[5:10]+'                   3 1.000e-02'+line[40:-1]+'\n')
			else:
				conne_file_st.write('ATM01'+line[5:10]+'                   1 1.000e-02'+line[40:-1]+'\n')
		elif  line[5:10] not in blocks.keys():
			if line[0]!=line[5]:
				conne_file_st.write(line[0:5]+'ATM01'+'                   3'+line[30:41]+'1.000e-02'+line[50:-1]+'\n')
			else:
				conne_file_st.write(line[0:5]+'ATM01'+'                   1'+line[30:41]+'1.000e-02'+line[50:-1]+'\n')

	conne_file_st.close()
	conne_file.close()


	eleme_file_st=open('../model/t2/sources/ELEME2','w')  
	eleme_file=open('../model/t2/sources/ELEME','r')  
	data_eleme=eleme_file.readlines()

	for line in data_eleme:
		if (line[0:5]) in blocks.keys():
			eleme_file_st.write(line)
		else:
			continue
	eleme_file_st.write("ATM01          ATMOS 1.000E+50\n")
	eleme_file_st.close()
	eleme_file.close()



def ELEME_adder(input_dictionary):
	""""It takes the ELEME file from ../model/t2/sources and print it as a string

	Returns
	-------
	str
	  string : string containing the ELEME section

	"""

	source_file="../model/t2/sources/ELEME"
	string=""
	if os.path.isfile(source_file):
		with open(source_file) as eleme_source_file:
			for line in eleme_source_file.readlines()[:]:
				string+="%s"%line
	else:
		sys.exit("The file %s or directory do not exist"%source_file)

	return string

def CONNE_adder(input_dictionary):
	""""It takes the CONNE file from ../model/t2/sources and print it as a string

	Returns
	-------
	str
	  string : string containing the CONNE section

	"""
	source_file="../model/t2/sources/CONNE"
	string=""
	if os.path.isfile(source_file):
		with open(source_file) as conne_source_file:
			for line in conne_source_file.readlines()[:]:
				string+="%s"%line
	else:
		sys.exit("The file %s or directory do not exist"%source_file)
	return string

def OUTPU_writer(input_dictionary):
	""""It writes the OUTPU of TOUGH2 file

	Parameters
	----------
	input_dictionary : dictionary
	  Dictionary containing the OUTPU information

	Returns
	-------
	str
	  output: contains the OUTPU section

	Examples
	--------
	'OUTPU':{'FORMAT':['CSV'],'ELEMENT_RELATED':{'ENTHALPY':[1],'SECONDARY':[1,5]},'CONNECTION_RELATED':{'FLOW':[1,2],},'GENER_RELATED':{'GENERATION':[None],'FRACTIONAL FLOW':[1]}}

	"""

	string="OUTPU----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"

	for outpu in input_dictionary['OUTPU']:
		if outpu=='FORMAT':
			string+="%s\n"%(input_dictionary['OUTPU'][outpu])
			n_variables=0
			string_temp=''	
		else:
			for key in input_dictionary['OUTPU'][outpu]:
				print(key)
				if outpu=='FORMAT':
					string+="%s\n"%(key)
					n_variables=0
					string_temp=''
				else:
					string_temp+=format(key,formats.formats_t2['OUTPU']['FORMAT'][0])
					n_variables+=1
					for i,parameter in enumerate(input_dictionary['OUTPU'][outpu][key]):
						try:
							if type(parameter)==formats.formats_t2['OUTPU'][outpu][key][i]:
								if parameter!=None:
									string_temp+=format(str(parameter),formats.formats_t2['OUTPU']['FORMAT'][1])
							else:
								sys.exit("OUTPU %s %s %s not correctly formatted"%(outpu,key,parameter))
						except KeyError:
							sys.exit("Key %s does not exist for OUTPU"%key)
    
					if not all(ft2==type(None) for ft2 in formats.formats_t2['OUTPU'][outpu][key]):
						cnt=0
						for value in formats.formats_t2['OUTPU'][outpu][key]:
							if value!=type(None):
								cnt+=1
						if i!=(cnt-1):
							sys.exit("For the key %s the number of arguments required are not enough"%key)
					string_temp+='\n'
	string=string+str(n_variables)+'\n'+string_temp+'\n'

	return string

def MOMOP_writer(input_dictionary):
	"""Return the MOMOP section

	Parameters
	----------
	input_dictionary : dictionary
	  Dictionary with the defined MOMOP information

	Returns
	-------
	str
	  string : string containing MOMOP section

	"""
	string="MOMOP----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"
	string=''
	for key in formats.formats_t2['MOMOP']:
		if formats.formats_t2['MOMOP'][key][2]==1:
			value,def_value=def_value_selector('MOMOP',key,input_dictionary)
			string+=converter(value,formats.formats_t2['MOMOP'][key][1],def_value)
	string+="\n"
	return string

def ROCKS_writer(input_dictionary):
	"""Return the ROCKS section

	Parameters
	----------
	input_dictionary : dictionary
	  Dictionary with the defined parameter information

	Returns
	-------
	str
	  string : string containing ROCKS section

	Examples
	--------
	Dictionary example::

		input_data={'ROCKS':{
				         'ROCK1':{
						         'MAT':'ROCK1',
						         'DROK':2.65E3,
						         'POR':0.1,
						         'CWET':2.1,
						         'SPHT':850,
						         'PER_X':1E-15,
						         'PER_Y':1E-15,
						         'PER_Z':1E-15,
				                  },
				        }
				}

	"""
	string="ROCKS----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"
	rocks_levels=[1,2,3,4]
	pass_valid=False
	for rock in input_dictionary['ROCKS']:
		for level in rocks_levels:
			break_line=False
			for key in formats.formats_t2['ROCKS']:
				if formats.formats_t2['ROCKS'][key][2]==level:
					if level==1:
						pass_valid=True
						break_line=True
					if 'NAD' in input_dictionary['ROCKS'][rock].keys():
						if input_dictionary['ROCKS'][rock]['NAD']>=1 and level==2:
							pass_valid=True
							break_line=True
						elif input_dictionary['ROCKS'][rock]['NAD']>=2 and level in [3,4]:
							pass_valid=True
							break_line=True
					if pass_valid:
						value,def_value=def_value_selector(rock,key,input_dictionary,rocks=True)
						string+=converter(value,formats.formats_t2['ROCKS'][key][1],def_value)
						pass_valid=False
			if break_line:
				string+='\n'
	string+="\n"
	return string

def t2_input(include_FOFT,include_SOLVR,include_COFT,include_GOFT,include_RPCAP,include_MULTI,include_START,include_TIMES,include_OUTPU,include_MOMOP,input_dictionary):
	""""It creates the FOFT section base on the well feedzone position

	Parameters
	----------
	input_dictionary : dictionary
	  Dictionary with all the necessary information to define a model
	include_FOFT: bool
	  If true includes the FOFT section on the TOUGH2 file
	include_SOLVR: bool
	  If true includes the SOLVR section on the TOUGH2 file
	include_COFT: bool
	  If true includes the COFT section on the TOUGH2 file
	include_GOFT: bool
	  If true includes the GOFT section on the TOUGH2 file
	include_RPCAP: bool
	  If true includes the RPCAP section on the TOUGH2 file
	include_MULTI: bool
	  If true includes the MULTI section on the TOUGH2 file
	include_START: bool
	  If true includes the START sentence is added on the top of PARAM section
	include_OUTPU: bool
	  If true includes the OUTPU section on the TOUGH2 file
	include_TIMES: bool
	  If true includes the TIMES section on the TOUGH2 file
	include_MOMOP: bool
	  If true includes the MOMOP section on the TOUGH2 file

	Returns
	-------
	file
	  t2: on ../model/t2/t2

	Examples
	--------
	>>> t2_input(input_dictionary,include_FOFT=True,include_SOLVR=True,include_COFT=False,include_GOFT=True,include_RPCAP=False,include_MULTI=True,include_START=True,include_MOMOP=True,include_OUTPU=True)
	"""

	secctions=[TITLE_writer,ROCKS_writer,PARAM_writer]

	if_functions_dictionary={'MOMOP':[include_MOMOP,MOMOP_writer],
							 'RPCAP':[include_RPCAP,RPCAP_writer],
							 'MULTI':[include_MULTI,MULTI_writer],
							 'FOFT':[include_FOFT,FOFT_writer],
							 'TIMES':[include_TIMES,TIMES_writer],
							 'SOLVR':[include_SOLVR,SOLVR_writer],
							 'COFT':[include_COFT,COFT_writer],
							 'GOFT':[include_GOFT,GOFT_writer],
							 'OUTPU':[include_OUTPU,OUTPU_writer]}

	for bools in if_functions_dictionary:
		if if_functions_dictionary[bools][0]:
			secctions.append(if_functions_dictionary[bools][1])

	secctions.extend([ELEME_adder,CONNE_adder])
	output=""
	for func in secctions:
		if func==PARAM_writer and include_START:
			output+="START----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"
		output+=func(input_dictionary)

	#output+=GENER_adder(input_dictionary)

	output+="ENDCY----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n"

	input_fi_file="../model/t2/t2"
	t2_file_out=open(input_fi_file, "w")
	t2_file_out.write(output)
	t2_file_out.close()