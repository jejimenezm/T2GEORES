from T2GEORES import writer as t2w
from T2GEORES import formats as formats
from T2GEORES import geometry as geomtr
from T2GEORES import txt2sqlite as txt2sql
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates
import locale
from iapws import IAPWS97
locale.setlocale(locale.LC_TIME, 'en_US.utf8') 

def write_t2_format_gener(var_array,time_array,var_type,var_enthalpy,type_flow,input_dictionary):
	"""It generates the block of time, flow and enthalpy for each flow

	Parameters
	----------
	var_array : array
	  Contains the flow data
	time_array : array
	  Contains the time data on datetime format
	input_dictionary   :dictionary
	  It contains the reference date on datatime format
	var_type	:str
	  It indicates the type of well producer 'R' or injector 'R'
	var_enthalpy :array
	  Contains the flowing enthalpy data
	type_flow :str
	  It defines the type of flow on the well. 'constant' adds a zero flow before the start of well production at -infinity and keeps the value of the flow to the infinity, 'shutdown' closes the well after the last record, 'invariable'
	  'invariable' writes the GENER section for every well as it is written on the input file

	Returns
	-------
	str
	  string_P: contains the defined format for the GENER section for a particular producer well.
	str
	  string_R : contains the defined format for the GENER section for a particular injector well.
	int
	  cnt_P : defines the number of flows records on every string_P for each producer well
	int
	  cnt_R : defines the number of flows records on every string_R for each injector well
	  

	Attention
	---------
	The legth of  var_array, time_array and var_enthalpy must be the same

	Note
	----
	For every well a value of flow zero is set on time -1E50 and before the first record. This function is used by write_gener_from_sqlite() as it does not produce any output file by itself.

	"""
	ref_date=input_dictionary['ref_date']
	string_time_R=''
	string_flow_R=''
	string_enthalpy_R=''
	string_time_P=''
	string_flow_P=''

	t_min=-1E50
	t_max=1E50
	flow_min=0
	enthalpy_min=500E3
	time_zero=(time_array[0]-ref_date).total_seconds()

	#It when type flow shutdown is used, the well flow is set to zero on after the last record plus this value
	extra_time=365.25*24*3600/2

	if type_flow=="invariable":
		cnt_P=1
		cnt_R=1
	elif type_flow=="constant" or type_flow=="shutdown":
		string_time_P+='%14.6E'%t_min
		string_flow_P+='%14.6E'%flow_min
		string_time_R+='%14.6E'%t_min
		string_flow_R+='%14.6E'%flow_min
		string_enthalpy_R+='%14.6E'%enthalpy_min

		string_time_P+='%14.6E'%time_zero
		string_flow_P+='%14.6E'%flow_min
		string_time_R+='%14.6E'%time_zero
		string_flow_R+='%14.6E'%flow_min
		string_enthalpy_R+='%14.6E'%enthalpy_min

		cnt_P=2
		cnt_R=2


	if len(var_array)==len(time_array):
		for n in range(len(var_type)):
			timex=(time_array[n]-ref_date).total_seconds()
			if var_type[n]=='P':
				well_type="P"
				string_time_P+='%14.6E'%timex
				string_flow_P+='%14.6E'%-var_array[n]
				last_flow=-var_array[n]
				cnt_P+=1
				if cnt_P%4==0 and n!=(len(var_type)-1):
					string_time_P+='\n'
					string_flow_P+='\n'
				

			if var_type[n]=='R':
				well_type="R"
				string_time_R+='%14.6E'%timex
				string_flow_R+='%14.6E'%var_array[n]
				string_enthalpy_R+='%14.6E'%var_enthalpy[n]
				last_flow=var_array[n]
				last_enthalpy=var_enthalpy[n]
				cnt_R+=1
				if cnt_R%4==0 and n!=(len(var_type)-1):
					string_time_R+='\n'
					string_flow_R+='\n'
					string_enthalpy_R+='\n'
			last_time=timex

		if type_flow=="invariable":
			pass
		elif type_flow=="constant":
			if cnt_R>3:
				if cnt_R%4==0:
					string_time_R+='\n'
					string_flow_R+='\n'
					string_enthalpy_R+='\n'
				cnt_R+=1
				string_time_R+='%14.6E'%t_max
				string_flow_R+='%14.6E'%last_flow
				string_enthalpy_R+='%14.6E'%last_enthalpy

			if cnt_P>3:
				if cnt_P%4==0:
					string_time_P+='\n'
					string_flow_P+='\n'
				string_time_P+='%14.6E'%t_max
				string_flow_P+='%14.6E'%last_flow
				cnt_P+=1

		elif type_flow=="shutdown":
			if cnt_R>3:
				if cnt_R%4==0:
					string_time_R+='\n'
					string_flow_R+='\n'
					string_enthalpy_R+='\n'

				cnt_R+=2

				string_time_R+='%14.6E'%(last_time+extra_time)
				string_flow_R+='%14.6E'%flow_min
				string_enthalpy_R+='%14.6E'%last_enthalpy

				string_time_R+='%14.6E'%t_max
				string_flow_R+='%14.6E'%flow_min
				string_enthalpy_R+='%14.6E'%last_enthalpy

			if cnt_P>3:
				if cnt_P%4==0:
					string_time_P+='\n'
					string_flow_P+='\n'
				
				cnt_P+=2

				string_time_P+='%14.6E'%(last_time+extra_time)
				string_flow_P+='%14.6E'%flow_min

				string_time_P+='%14.6E'%t_max
				string_flow_P+='%14.6E'%flow_min

		if cnt_R==2 or cnt_R==3:
			string_time_R=''
			string_flow_R=''
			string_enthalpy_R=''

		if cnt_P==2 or cnt_P==3:
			string_time_P=''
			string_flow_P=''

		string_time_P+='\n'
		string_flow_P+='\n'
		string_time_R+='\n'
		string_flow_R+='\n'
		string_enthalpy_R+='\n'

		string_P=string_time_P+string_flow_P
		string_R=string_time_R+string_flow_R+string_enthalpy_R
		return string_P, string_R, cnt_P, cnt_R
	else:
		print("Time and variable array must have the same length")

def write_t2_format_gener_dates(var_array,time_array,var_type,var_enthalpy,type_flow, def_T, min_days, time_between_months):
	"""It generates the block of time, flow and enthalpy for each flow on datetime format

	Parameters
	----------
	var_array : array
	  Contains the flow data
	time_array : array
	  Contains the time data on datetime format
	var_type	:str
	  It indicates the type of well producer 'R' or injector 'R'
	var_enthalpy :array
	  Contains the flowing enthalpy data
	type_flow :str
	  It defines the type of flow on the well. 'constant' adds a zero flow before the start of well production at -infinity and keeps the value of the flow to the infinity, 'shutdown' closes the well after the last record, 'invariable'
	  'invariable' writes the GENER section for every well as it is written on the input file
	def_T: flot
	  Default temperature value for injector wells with no flowing enthalpy provided.

	Returns
	-------
	str
	  string_P: contains the defined format for the GENER section for a particular producer well.
	str
	  string_R : contains the defined format for the GENER section for a particular injector well.
	int
	  cnt_P : defines the number of flows records on every string_P for each producer well
	int
	  cnt_R : defines the number of flows records on every string_R for each injector well
	  

	Attention
	---------
	The legth of  var_array, time_array and var_enthalpy must be the same

	Note
	----
	For every well a value of flow zero is set on time -infinity and before the first record. This function is used by the function write_gener_from_sqlite() as it does not produce any output file by itself.


	"""
	string_P=''
	string_R=''

	t_min='-infinity'
	t_max='infinity'
	flow_min=0
	enthalpy_min=500E3
	time_zero=0
	now = datetime.now()

	#It when type flow shutdown is used, the well flow is set to zero on after the last record plus this value
	extra_time=365.25*time_between_months*3600*24/2


	if type_flow=="invariable":
		cnt_P=1
		cnt_R=1
	elif type_flow=="constant" or type_flow=="shutdown":

		string_P+=format(t_min,'>20s')
		string_P+=format(flow_min,'>10.3E')+'\n'

		ind = 0
		for ix, vx in enumerate(var_type):
			if vx == 'P':
				ind = ix
				break
    
		string_P+=format((time_array[ind]-timedelta(days=min_days)).strftime("%Y-%m-%d_%H:%M:%S"),'>20s')
		string_P+=format(flow_min,'>10.3E')+'\n'

		string_R+=format(t_min,'>20s')
		string_R+=format(flow_min,'>10.3E')
		string_R+=format(enthalpy_min,'>10.3E')+'\n'

		ind = 0
		for ix, vx in enumerate(var_type):
			if vx == 'R':
				ind = ix
				break

		string_R+=format((time_array[ind]-timedelta(days=min_days)).strftime("%Y-%m-%d_%H:%M:%S"),'>20s')
		string_R+=format(flow_min,'>10.3E')
		string_R+=format(enthalpy_min,'>10.3E')+'\n'

		cnt_P=2
		cnt_R=2

	if len(var_array)==len(time_array):
		for n in range(len(var_type)):
			if 'P' in var_type[n]:

				now_flow_P = var_array[n]
				now_time_P = time_array[n]

				if n >= 1 and 'last_time_P' in locals():
					if (now_time_P-last_time_P).total_seconds()>=(extra_time) :
						string_P += format((last_time_P + timedelta(days=min_days)).strftime("%Y-%m-%d_%H:%M:%S"),'>20s')
						string_P += format(0.0,'>10.2E')+'\n'
						cnt_P+=1

						string_P += format((now_time_P - timedelta(days=min_days)).strftime("%Y-%m-%d_%H:%M:%S"),'>20s')
						string_P += format(0.0,'>10.2E')+'\n'
						cnt_P+=1

				string_P+=format(now_time_P.strftime("%Y-%m-%d_%H:%M:%S"),'>20s')
				string_P+=format(-now_flow_P,'>10.2E')+'\n'
				cnt_P+=1

				last_flow_P = var_array[n]
				last_time_P = time_array[n]
				

			elif 'R' in var_type[n]:

				now_flow_R = var_array[n]
				now_time_R = time_array[n]

				if var_enthalpy[n] == 0.0:
					var_enthalpy[n] = IAPWS97(T=(def_T+273.15),x=0).h*1E3

				if n >= 1 and 'last_time_R' in locals():

					if (now_time_R-last_time_R).total_seconds()>=(extra_time) :

						string_R += format((last_time_R + timedelta(days=min_days)).strftime("%Y-%m-%d_%H:%M:%S"),'>20s')
						string_R += format(0.0,'>10.3E')
						string_R += format(var_enthalpy[n],'>10.3E')+'\n'
						cnt_R+=1

						print(now_time_R, last_time_R)

						string_R += format((now_time_R - timedelta(days=min_days)).strftime("%Y-%m-%d_%H:%M:%S"),'>20s')
						string_R += format(0.0,'>10.2E')
						string_R+=format(var_enthalpy[n],'>10.3E')+'\n'
						cnt_R+=1

				string_R+=format(time_array[n].strftime("%Y-%m-%d_%H:%M:%S"),'>20s')
				string_R+=format(var_array[n],'>10.3E')
				string_R+=format(var_enthalpy[n],'>10.3E')+'\n'
				cnt_R+=1

				last_flow_R=var_array[n]
				last_time_R=time_array[n]
				last_enthalpy=var_enthalpy[n]

			last_time=time_array[n]

		if type_flow=="invariable":
			pass
		elif type_flow=="constant":
			if cnt_R>3:
				if (now-last_time_R).total_seconds()>=(extra_time):
					cnt_R+=1
					string_R+=format((last_time_R+timedelta(days=min_days)).strftime("%Y-%m-%d_%H:%M:%S"),'>20s')
					last_flow_R = 0
					string_R += format(last_flow_R,'>10.2E')
					string_R += format(last_enthalpy,'>10.3E')+'\n'

				string_R+=format(t_max,'>20s')
				string_R+=format(last_flow_R,'>10.2E')
				string_R+=format(last_enthalpy,'>10.3E')+'\n'
				cnt_R+=1

			if cnt_P>3:

				if (now-last_time_P).total_seconds()>=(extra_time):
					last_flow_P = 0
					string_P += format((last_time_P+timedelta(days=min_days)).strftime("%Y-%m-%d_%H:%M:%S"),'>20s')
					string_P += format(-last_flow_P,'>10.2E')+'\n'
					cnt_P += 1

				string_P+=format(t_max,'>20s')
				string_P+=format(-last_flow_P,'>10.2E')+'\n'
				cnt_P+=1
		elif type_flow=="shutdown":

			if cnt_R>3:
				cnt_R+=2

				string_R+=format((time_array[n]+extra_time).strftime("%d-%b-%Y_%H:%M:%S"),'>20s')
				string_R+=format(last_flow_R,'>10.3E')
				string_R+=format(last_enthalpy,'>10.3E')+'\n'

				string_R+=format(t_max,'>20s')
				string_R+=format(flow_min,'>10.3E')
				string_R+=format(last_enthalpy,'>10.3E')+'\n'

			if cnt_P>3:
				cnt_P+=2
				string_P+=format((time_array[n]+extra_time).strftime("%d-%b-%Y_%H:%M:%S"),'>20s')
				string_P+=format(-last_flow_P,'>10.2E')+'\n'

				string_P+=format(t_max,'>20s')
				string_P+=format(-flow_min,'>10.2E')+'\n'

		if cnt_R==2 or cnt_R==3:
			string_R=''

		if cnt_P==2 or cnt_P==3:
			string_P=''

		#string_P+='\n'
		#string_R+='\n'

		return string_P, string_R, cnt_P, cnt_R
	else:
		print("Time and variable array must have the same length")

def write_gener_from_sqlite(type_flow,input_dictionary,make_up=False, def_inj_T = None, min_days = 0.000001, time_between_months = 120):
	"""It is the main function on this module, it writes the GENER section from the mh input files

	Parameters
	----------
	input_dictionary: dictionary
	  Dictionary containing the path and name of database, the reference date on datime format and  TOUGH2 version under the key t2_ver, if lower than 7, conventional 4 columns for GENER is used. For 7 or higher, DATES are used.
	wells : array
	  Wells to be included
	type_flow :str
	  It defines the type of flow on the well. 'constant' adds a zero flow before the start of well production at -infinity and keeps the value of the flow to the infinity, 'shutdown' closes the well after the last record, 'invariable'
	  'invariable' writes the GENER section for every well as it is written on the input file
	make_up : bool
	   If True the output file is written on GENER_MAKEUP. Otherwise, on GENER_PROD
	def_inj_T : dictionary
	  Defines the default temperature for the injector wells when there is no flowing enthalpy provided.
		
	Returns
	-------
	file
	  GENER_PROD:  a text file on '../model/t2/sources/'

	Attention
	---------
	All the information comes from the sqlite databse. If there are some other sources or sinks define with the prefix SRC, they should be written first on the database
	by executing write_geners_to_txt_and_sqlite(). Thus, the next correlatative will be +1 for the first well


	Examples
	--------
	>>> write_gener_from_sqlite(input_dictionary,type_flow='constant')
	"""

	types='WELLS'
	wells=[]
	try:
		for well in input_dictionary[types]:
			wells.append(well)
	except KeyError:
			pass

	db_path=input_dictionary['db_path']
	t2_ver=float(input_dictionary['VERSION'][0:3])

	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	gener=''

	source_corr_num=10 #The first source value will have this correlative


	for name in sorted(wells):

		try:
			def_T = def_inj_T[name]
		except (KeyError,TypeError):
			def_T = None

		data=pd.read_sql_query("SELECT type,date_time,steam_flow+liquid_flow as m_total,flowing_enthalpy,well_head_pressure\
		 FROM mh WHERE well='%s';"%name,conn)
        
		print(data)

		dates_func=lambda datesX: datetime.strptime(datesX, "%Y-%m-%d_%H:%M:%S")
		#Read file cooling
		dates=list(map(dates_func,data['date_time']))

		q_wf="SELECT MeasuredDepth,contribution from wellfeedzone WHERE well='%s'"%name
		c.execute(q_wf)
		rows=c.fetchall()
		
		wellfeedzone=[]
		contribution=[]
		for row in rows:
			wellfeedzone.append(row[0])
			contribution.append(row[1])

		x,y,masl_depth=geomtr.MD_to_TVD(name,wellfeedzone)

		for feedn in range(len(contribution)):

			#Create t the block name for each feedzone
			q_layer="SELECT correlative FROM layers where top>=%s and bottom<%s"%(masl_depth[feedn],masl_depth[feedn])

			c.execute(q_layer)
			rows=c.fetchall()
			for row in rows:
				layer_corr=row[0]

			q_corr="SELECT blockcorr FROM t2wellblock WHERE well='%s'"%(name)

			c.execute(q_corr)
			rows=c.fetchall()
			for row in rows:
				blockcorr=row[0]

			source_block=layer_corr+blockcorr #Block name for feedzone

			#Generates the source nickname

			#Extracts the maximum value of the source names
			q_corr="SELECT max(substr(source_nickname,4,2)) FROM t2wellsource"

			c.execute(q_corr)
			rows=c.fetchall()
			for row in rows:
				source_last=row[0]

			#If there is not sources name it creates one base on the increment
			if source_last==None:
				source_corr="SRC%s"%source_corr_num
				source_corr_R=source_corr
			else:

				#If there  is something,  it looks for that block source nickname
				q_corr_sqlite="SELECT source_nickname FROM t2wellsource where blockcorr='%s'"%source_block
                

				c.execute(q_corr_sqlite)
				conn.commit()
				rows=c.fetchall()

				if len(rows)>1:
					for ix, row in enumerate(rows):
						if ix ==0:
							source_corr_num_sqlite=row[0]
						else:
							source_corr_num_sqlite_R=row[0]
				else:
					for row in rows:
						source_corr_num_sqlite = row[0]
						source_corr_num_sqlite_R = row[0]


				#if the block is already on the database, it creates a new name
				if len(rows)==0:
					source_corr_num=int(source_last)+1
					source_corr="SRC%s"%source_corr_num
					source_corr_R=source_corr
				else:
					#If the block name exists it takes that value
					if len(rows)>1:
						source_corr = source_corr_num_sqlite
						source_corr_R = source_corr_num_sqlite_R
					else:
						source_corr = source_corr_num_sqlite
						source_corr_R = source_corr_num_sqlite

				print(source_corr, source_corr_R)

			if t2_ver<7:
				P,R, LTAB_P, LTAB_R = write_t2_format_gener(data['m_total'].values*contribution[feedn], dates, data['type'], data['flowing_enthalpy']*1E3, type_flow, input_dictionary=input_dictionary,min_days=min_days, time_between_months= time_between_months)
			else:
				P,R, LTAB_P, LTAB_R = write_t2_format_gener_dates(data['m_total'].values*contribution[feedn], dates, data['type'], data['flowing_enthalpy']*1E3, type_flow, def_T,min_days = min_days, time_between_months= time_between_months)

			if type_flow=="invariable":
				condition=1
			elif type_flow=="constant":
				condition=2
			elif type_flow=="shutdown":
				condition=4

			r_check=False
			
			if LTAB_R>condition:
				if input_dictionary['MOMOP']['MOP2_32'] == 0 or input_dictionary['MOMOP']['MOP2_32'] == None :
					gener+="%s%s                %4d     MASSi\n"%(source_block,source_corr_R,LTAB_R)
				elif input_dictionary['MOMOP']['MOP2_32'] == 1:
					gener+="%s%s                %4d     MASSi                     2.400E+07  5.00E+06\n"%(source_block,source_corr_R,LTAB_R)
				elif input_dictionary['MOMOP']['MOP2_32'] == 2:
					gener+="%s%s                %4d     MASSi                     2.000E+05\n"%(source_block,source_corr_R,LTAB_R)
				gener+=R
				try:
					q="INSERT INTO t2wellsource(well,blockcorr,source_nickname,flow_type) VALUES ('%s','%s','%s','R')"%(name,source_block,source_corr_R)
					c.execute(q)
					conn.commit()
					r_check=True
				except sqlite3.IntegrityError:
					print("""Two reasons:
							 1-There is already a SOURCE nickname assign to this block (%s),
							 	in this case is better to erase the table content on table t2wellsource, 
							 	be sure about the data on wellfeedzone table
							 	and rerun this function
							 2-Skip the message if you are just updating the flowrates"""%source_block)

			p_check=False
			if LTAB_P>condition:
				if r_check:
					source_corr_num+=1
					source_corr="SRC%s"%source_corr_num
				if input_dictionary['MOMOP']['MOP2_32'] == 0 or input_dictionary['MOMOP']['MOP2_32'] == None :
					gener+="%s%s                %4d     MASS\n"%(source_block,source_corr,LTAB_P)
				elif input_dictionary['MOMOP']['MOP2_32'] == 1:
					gener+="%s%s                %4d     MASS                      8.00E+05  2.00E+05\n"%(source_block,source_corr,LTAB_P)
				elif input_dictionary['MOMOP']['MOP2_32'] == 2:
					gener+="%s%s                %4d     MASS                      2.00E+05\n"%(source_block,source_corr,LTAB_P)

				gener+=P
				try:
					q="INSERT INTO t2wellsource(well,blockcorr,source_nickname,flow_type) VALUES ('%s','%s','%s','P')"%(name,source_block,source_corr)
					c.execute(q)
					conn.commit()
					p_check=True
				except sqlite3.IntegrityError:
					print("""Two reasons:
							 1-There is already a SOURCE nickname assign to this block (%s),
							 	in this case is better to erase the table content on table t2wellsource, 
							 	be sure about the data on wellfeedzone table
							 	and rerun this function
							 2-Skip the message if you are just updating the flowrates"""%source_block)

			#Insert feedzones for new wells and wells with no flow during history, in case it is need it
			if not (r_check or p_check):
				try:
					q="INSERT INTO t2wellsource(well,blockcorr,source_nickname) VALUES ('%s','%s','%s')"%(name,source_block,source_corr)
					c.execute(q)
					conn.commit()
				except sqlite3.IntegrityError:
					print("""Two reasons:
							 1-There is already a SOURCE nickname assign to this block (%s),
							 	in this case is better to erase the table content on table t2wellsource, 
							 	be sure about the data on wellfeedzone table
							 	and rerun this function
							 2-Skip the message if you are just updating the flowrates"""%source_block)
	conn.close()
	if make_up:
		gener_file=open('../model/t2/sources/GENER_MAKEUP','w')
	else:
		gener_file=open('../model/t2/sources/GENER_PROD','w')
	gener_file.write(gener)
	gener_file.close()

def def_gener_selector(block,key,geners):
	"""If gener block is not completely define, the default value is use

	Parameters
	----------
	block : str
	  Referes to the mesh
	key : str
	  Referes to a GENER parameters
	geners : dictionary
	  Contains the neccesary information to define a sink/source. g.e. 'DA110':{'SL':'GEN','NS':10,'TYPE':'MASS','GX':1,'EX':1.1E6},

	Returns
	-------
	value
	  float: the selecte value for a parameter
	def_value
	  bool: if True the default value is used

	Attention
	---------
	No data is needed from sqlite

	"""
	try:
		value=geners[block][key]
		def_value=False
	except KeyError:
		value=formats.formats_t2['GENER'][key][0]
		def_value=True
	return value,def_value

def write_geners_to_txt_and_sqlite(input_dictionary,geners):
	"""It writes the GENER section for the constant sink/sources from the model  on a text file and at the sqlite database

	Parameters
	----------
	input_dictionary: dictionary
	  Dictionary containing the path and name of database and the path of the input file
	geners : dictionary
	  Contains the neccesary information to define every constant sink/source on the model. g.e.'DA110':{'SL':'GEN','NS':10,'TYPE':'MASS','GX':1,'EX':1.1E6}

	Returns
	-------
	file
	  GENER_SOURCES: text file on  '../model/t2/sources/GENER_SOURCES'
	  
	Attention
	---------
	Every time the function is executed it overwrites the file

	Examples
	--------
	>>> write_geners_to_txt_and_sqlite(input_dictionary,geners)
	"""

	db_path=input_dictionary['db_path']

	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	list_geners=[]

	string=""
	for gener_i in geners:
		string+=t2w.converter(gener_i,formats.formats_t2['GENER']['BLOCK'][1],def_value=False)
		list_geners.append(geners[gener_i]['SL']+str(geners[gener_i]['NS']))
		for index, key in enumerate(formats.formats_t2['GENER']):
			if index!=0:
				value,def_value=def_gener_selector(gener_i,key,geners)
				string+=t2w.converter(value,formats.formats_t2['GENER'][key][1],def_value)
		try:
			q="INSERT INTO t2wellsource(well,blockcorr,source_nickname) VALUES ('%s','%s','%s')"%(geners[gener_i]['TYPE'],gener_i,geners[gener_i]['SL']+str(geners[gener_i]['NS']))
			c.execute(q)
			conn.commit()
		except sqlite3.IntegrityError:
			print("The blockcorr %s is already used by another source"%(gener_i))
		string+='\n'

	file=open('../model/t2/sources/GENER_SOURCES','w')
	file.write(string)
	file.close()

	#As the sources defined on geners are the only allowed any other source not included  dictionary will be erased
	list_geners_string=''.join(["'%s',"%str(i) for i in list_geners])
	query="DELETE FROM t2wellsource WHERE source_nickname NOT IN (%s) AND source_nickname LIKE'GEN*' "%(list_geners_string[0:-1])
	c.execute(query)
	conn.commit()

	conn.close()

def create_well_flow(flow_times,input_dictionary,include_gener=True):
  """It creates a mh text file for every well on the input dictionary. These wells need to have been defined on the general input_dictionary before the mesh was created
  
  Parameters
  ----------
  flow_times : dictionary
    e.g. 'WELL-1' : [[datetime(2029,1,1,0,0,0),datetime(2080,1,1,0,0,0)]  #Initial day of operation , [1.5,1.5]  #Steam value for every time step,   [15,15]#Brine value for every time step, [1100,1100] #Flowing enthalpy value for every time step , [7,7]  #WHP, 'P'  #P for producer and I for injector],       
  include_gener: bool
    If True it creates a file GENER_MAKEUP, from which the wells define on this section can be included on the TOUGH2 input file and 
    the data from newly generated file is added/overwritten to the sqlite databse
  input_dictionary: dictionary
	  Dictionary containing the path and name of database and the path of the input file
  
  Returns
  -------
  file
    {well}_mh.dat: it contains the dictionary information on a text file format
  file
 	GENER_MAKEUP: on ../model/t2/t2/SOURCES
  
  Note
  ----
  This function can be use to generate production scenarios on a calibrated model
  """

  for name in flow_times:
    if os.path.isfile('../input/mh/%s_mh.dat'%name):
    	print("Well already exists, data will be overwrite %s"%name)
    else:
    	print("New well added %s"%name)

    file=open('../input/mh/%s_mh.dat'%name,'w')
    file.write("type,well,date_time,steam,liquid,enthalpy,WHPabs\n")
    for n in range(len(flow_times[name][0])):
      date=(flow_times[name][0][n]).strftime("%Y-%m-%d_%H:%M:%S")
      steam=flow_times[name][1][n]
      brine=flow_times[name][2][n]
      enthlapy=flow_times[name][3][n]
      pressure=flow_times[name][4][n]
      type_well=flow_times[name][5]
      string="%s,%s,%s,%s,%s,%s,%s\n"%(type_well,name,date,steam,brine,enthlapy,pressure)
      file.write(string)
    file.close()
  if include_gener:
  	txt2sql.replace_mh(flow_times.keys(),input_dictionary=input_dictionary)
  	write_gener_from_sqlite(type_flow='constant',make_up=True,input_dictionary=input_dictionary)

def plot_makeup_wells(flow_times):
	"""It plots a defined scenario of production including injector wells

	Parameters
	----------
	flow_times : dictionary
	  e.g. 'WELL-1' : [[datetime(2029,1,1,0,0,0),datetime(2080,1,1,0,0,0)]  #Initial day of operation , [1.5,1.5]  #Steam value for every time step,   [15,15]#Brine value for every time step, [1100,1100] #Flowing enthalpy value for every time step , [7,7]  #WHP, 'P'  #P for producer and I for injector],       

	Returns
	-------
	plot
	  wells_flow: horizontal histogram

	Attention
	---------
	No data is needed from sqlite
	"""

	fig = plt.figure(figsize=(10, 6))
	ax = fig.add_subplot(111)

	cnt=1
	y_positions=[]
	well_tick=[]

	well_d = {}
	for well in flow_times:
		data_range = flow_times[well][0]
		d = data_range[0].strftime('%Y-%m-%d')+'_'+well
		well_d[d] = well

	

	for i, dx in enumerate(sorted(well_d)):
		well = well_d[dx]
		if flow_times[well][5]=='12':
			color='r'
			unit = 'Unit 1&2'
		elif flow_times[well][5]=='3':
			color='orange'
			unit = 'Unit 3'

		total_flow = flow_times[well][1][0]+flow_times[well][2][0]

		data_range=flow_times[well][0]
		value=[cnt,cnt]
		y_positions.append(cnt)
		ax.text(data_range[1]-timedelta(days=365*2.2),cnt-1.5,'%.1f kg/s'%total_flow)


		cnt+=5

		ax.plot(data_range, value,color,lw=15, alpha=0.5, label = unit )


		well_tick.append('MK-'+str(i+1).replace("X","").replace("Z",""))
	
	handles, labels = ax.get_legend_handles_labels()
	unique = [(h, l) for i, (h, l) in enumerate(zip(handles, labels)) if l not in labels[:i]]
	fig.legend(*zip(*unique), bbox_to_anchor=(0.25,0.85), bbox_transform=fig.transFigure)

	"""
	for well in flow_times:
		if flow_times[well][5]=='12':
			color='r'
		elif flow_times[well][5]=='3':
			color='orange'

		total_flow = flow_times[well][1][0]+flow_times[well][2][0]

		data_range=flow_times[well][0]
		value=[cnt,cnt]
		y_positions.append(cnt)
		ax.text(data_range[1]-timedelta(days=365*2.3),cnt-1,'%.1f kg/s'%total_flow)


		cnt+=5

		ax.plot(data_range, value,color,lw=15, alpha=0.5)


		well_tick.append(str(well).replace("X","").replace("Z",""))
	"""

	ax.set_xlabel("Time")
	ax.set_ylim([-4,cnt])
	plt.yticks(y_positions, well_tick)
	ax.tick_params(axis='y',which='minor',length=0)
	plt.show()
	fig.savefig('../output/make_up_wells.png',dpi=600)

def splitting_gener(input_dictionary,info,source_i):
	"""
	It splits and prints the GENER definition of a given SOURCE

	Parameters
	----------
	input_dictionary: dictionary
	  Contains the name of the TOUGH2 input file
	info : dictionary
	  Contains as a key the source name and an array with the period ranges as datetimes, e.g.:
	  	'SRC69':{1: [datetime(1970,1,1,0,0,0),datetime(2010,1,1,0,0,0)],2: [datetime(2010,1,1,0,0,0),datetime(2100,1,1,0,0,0)],}
	source_i: str
	  Source name to be split

	Returns
	-------
	str
	  A printout of the splited gener over time
	  
	Attention
	---------
	It has to be manually updated to the gener section

	"""

	t2_file_name = input_dictionary['TOUGH2_file']

	input_fi_file="../model/t2/%s"%t2_file_name

	keywords = ['MASS','MASSi']
	not_allowed = ['DELV']

	data_dict = {'source':[],
				 'block':[],
				 'datetime':[],
				 'm':[],
				 'h':[],
				 'type':[]}

	ref_date_string = datetime(1970,1,1,0,0,0).strftime("%Y-%m-%d_00:00:00")
	ref_date_inf_string = datetime(2099,1,1,0,0,0).strftime("%Y-%m-%d_00:00:00")

	sources = 0
	record = False
	if os.path.isfile(input_fi_file):
		t2_file=open(input_fi_file, "r")
		for t2_line in t2_file:

			if any (x in t2_line for x in keywords):
				try:
					data_lines = float(t2_line[20:31])
					sources += 1
					record = True
					block= t2_line[0:5]
					source = t2_line[5:10]
					type_i = t2_line[30:41]
					continue
				except ValueError:
					data_lines = 0
					pass

			if record and any (x not in t2_line for x in not_allowed) and data_lines > 0:

				if t2_line == '\n':
					break

				date = t2_line[0:21].strip()
				flowrate = float(t2_line[20:31].strip())
				h = t2_line[30:41].strip()

				if date == '-infinity':
					date = ref_date_string
				if date == 'infinity':
					date = ref_date_inf_string

				data_dict['source'].append(source)
				data_dict['block'].append(block)
				data_dict['type'].append(type_i)
				data_dict['datetime'].append(date)
				data_dict['m'].append(float(flowrate))
				data_dict['h'].append(h)

	data = pd.DataFrame.from_dict(data_dict)

	data['datetime'] = pd.to_datetime(data['datetime'] , format="%Y-%m-%d_%H:%M:%S")
	
	data_i = data.loc[data['source']==source_i]

	io = {1:'A',2:'B',3:'C',4:'D'} 

	cnt = 0
	for ix, n in enumerate(info[source_i]):
		data_n = data_i.loc[ (info[source_i][n][0]<=data_i['datetime']) & (info[source_i][n][1]>data_i['datetime'])]
		source_x = source_i.replace('C',io[n])

		print(block+source_x)
		if ix > 0:
			print(format('-infinity','>20s'),format(0.0,'>10.3E'))
			print(format(data_i['datetime'][index].strftime("%Y-%m-%d_00:00:00"),'>20s'),format(0.0,'>10.3E'))

		for index, row in data_n.iterrows():
			if  datetime(1970,1,1,0,0,0) == row['datetime']:
				print(format('-infinity','>20s'),format(float(row['m']),'>10.3E'))
			elif datetime(2099,1,1,0,0,0) == row['datetime']:
				print(format('infinity','>20s'),format(row['m'],'>10.3E'))
			else:
				print(format(row['datetime'].strftime("%Y-%m-%d_00:00:00"),'>20s'),format(row['m'],'>10.3E'))
			cnt+=1

		if cnt < len(data_i['source'].values):
			print(format(data_i['datetime'][index+1].strftime("%Y-%m-%d_00:00:00"),'>20s'),format(0.0,'>10.3E'))
			print(format('infinity','>20s'),format(0.0,'>10.3E'))

