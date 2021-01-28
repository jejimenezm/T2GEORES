from model_conf import *
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
import writer as t2w
from formats import formats_t2
import geometry as geomtr
import txt2sqlite as txt2sql
import matplotlib.pyplot as plt

def write_t2_format_gener(var_array,time_array,var_type,var_enthalpy,type_flow,input_dictionary):
	"""It generaates the block of time, flow and enthalpy for each flow

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

def write_t2_format_gener_dates(var_array,time_array,var_type,var_enthalpy,type_flow):
	"""It generaates the block of time, flow and enthalpy for each flow on datetime format

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
	string_time_R=''
	string_flow_R=''
	string_enthalpy_R=''
	string_time_P=''
	string_flow_P=''

	t_min='-infinity'
	t_max='infinity'
	flow_min=0
	enthalpy_min=500E3
	time_zero=0

	#It when type flow shutdown is used, the well flow is set to zero on after the last record plus this value
	extra_time=365.25*24*3600/2

	if type_flow=="invariable":
		cnt_P=1
		cnt_R=1
	elif type_flow=="constant" or type_flow=="shutdown":

		string_P+=format(t_min,'>20s')
		string_P+=format(flow_min,'>10s')+'\n'

		string_P+=format(time_array[0].strftime("%Y-%M-%d_00:00:00"),'<20s')
		string_P+=format(time_zero,'>10s')+'\n'

		string_R+=format(t_min,'>20s')
		string_R+=format(flow_min,'>10s')
		string_R+=format(enthalpy_min,'>10.3E')+'\n'

		string_R+=format(t_min,'>20s')
		string_R+=format(time_array[0].strftime("%Y-%M-%d_00:00:00"),'<20s')
		string_R+=format(enthalpy_min,'>10.3E')+'\n'

		cnt_P=2
		cnt_R=2

	if len(var_array)==len(time_array):
		for n in range(len(var_type)):
			if var_type[n]=='P':
				string_P+=format(time_array[n].strftime("%Y-%M-%d_00:00:00"),'<20s')
				string_P+=format(-var_array[n],'>10.6E')+'\n'
				last_flow=var_array[n]
				cnt_P+=1
			elif var_type[n]=='R':
				string_P+=format(time_array[n].strftime("%Y-%M-%d_00:00:00"),'<20s')
				string_P+=format(var_array[n],'>10.6E')
				string_P+=format(var_enthalpy[n],'>10.6E')+'\n'
				last_flow=var_array[n]
				last_enthalpy=var_enthalpy[n]
				cnt_R+=1
			last_time=time_array[n]

		if type_flow=="invariable":
			pass
		elif type_flow=="constant":
			if cnt_R>3:
				string_P+='\n'
				cnt_R+=1
				string_R+=format(t_max,'>20s')
				string_R+=format(last_flow,'>10.6E')
				string_R+=format(last_enthalpy,'>10.6E')+'\n'
			if cnt_P>3:
				string_P+=format(t_max,'>20s')
				string_P+=format(-last_flow,'>10.6E')+'\n'
				cnt_P+=1
		elif type_flow=="shutdown":

			if cnt_R>3:
				cnt_R+=2

				string_R+=format((time_array[n]+extra_time).strftime("%Y-%M-%d_00:00:00"),'<20s')
				string_R+=format(last_flow,'>10.6E')
				string_R+=format(last_enthalpy,'>10.6E')+'\n'

				string_R+=format(t_max,'>20s')
				string_R+=format(flow_min,'>10.6E')
				string_R+=format(last_enthalpy,'>10.6E')+'\n'

			if cnt_P>3:
				cnt_P+=2
				string_P+=format((time_array[n]+extra_time).strftime("%Y-%M-%d_00:00:00"),'<20s')
				string_P+=format(-last_flow,'>10.6E')+'\n'

				string_P+=format(t_max,'>20s')
				string_P+=format(-flow_min,'>10.6E')+'\n'

		if cnt_R==2 or cnt_R==3:
			string_R=''

		if cnt_P==2 or cnt_P==3:
			string_P=''

		string_P+='\n'
		string_R+='\n'
		return string_P, string_R, cnt_P, cnt_R
	else:
		print("Time and variable array must have the same length")

def write_gener_from_sqlite(type_flow,input_dictionary,make_up=False):
	"""It is the main function on this modulo, it writes the GENER section from the mh input files

	Parameters
	----------
	input_dictionary: dictionary
	  Dictionary containing the path and name of database, the reference date on datime format and  TOUGH2 version under the key t2_ver, if lower than 7, conventional 4 columns for GENER is used. For 7 or higher, DATES are used.
	wells : array
	  Arreglo con nombre de pozos a ser incluidos en la etapa de produccion
	type_flow :str
	  It defines the type of flow on the well. 'constant' adds a zero flow before the start of well production at -infinity and keeps the value of the flow to the infinity, 'shutdown' closes the well after the last record, 'invariable'
	  'invariable' writes the GENER section for every well as it is written on the input file
	make_up  : bool
	   If True the output file is written on GENER_MAKEUP. Otherwise, on GENER_PROD
		
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
	t2_ver=input_dictionary['t2_ver']

	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	gener=''

	source_corr_num=10 #The first source value will have this correlative


	for name in sorted(wells):
		data=pd.read_sql_query("SELECT type,date_time,steam_flow+liquid_flow as m_total,flowing_enthalpy,well_head_pressure\
		 FROM mh WHERE well='%s';"%name,conn)

		dates_func=lambda datesX: datetime.strptime(datesX, "%Y-%m-%d %H:%M:%S")
		#Read file cooling
		dates=list(map(dates_func,data['date_time']))

		q_wf="SELECT MeasuredDepth,porcentage from wellfeedzone WHERE well='%s'"%name
		c.execute(q_wf)
		rows=c.fetchall()
		
		wellfeedzone=[]
		porcentage=[]
		for row in rows:
			wellfeedzone.append(row[0])
			porcentage.append(row[1])

		x,y,masl_depth=geomtr.MD_to_TVD(name,wellfeedzone)

		for feedn in range(len(porcentage)):

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
			else:

				#If there  is something,  it looks for that block source nickname
				q_corr_sqlite="SELECT source_nickname FROM t2wellsource where blockcorr='%s'"%source_block

				c.execute(q_corr_sqlite)
				conn.commit()
				rows=c.fetchall()
				for row in rows:
					source_corr_num_sqlite=row[0]

				#if the block is already on the database, it creates a new name
				if len(rows)==0:
					source_corr_num=int(source_last)+1
					source_corr="SRC%s"%source_corr_num
				else:
					#If the block name exists it takes that value
					source_corr=source_corr_num_sqlite

			if t2_ver<7:
				P,R, LTAB_P, LTAB_R= write_t2_format_gener(data['m_total'].values*porcentage[feedn],dates,data['type'],data['flowing_enthalpy']*1E3,type_flow,input_dictionary=input_dictionary)
			else:
				P,R, LTAB_P, LTAB_R=write_t2_format_gener_dates(data['m_total'].values*porcentage[feedn],dates,data['type'],data['flowing_enthalpy']*1E3,type_flow)

			if type_flow=="invariable":
				condition=1
			elif type_flow=="constant":
				condition=2
			elif type_flow=="shutdown":
				condition=4

			r_check=False
			
			if LTAB_R>condition:
				if t2_ver<7:
					gener+="%s%s                %4d     MASSi\n"%(source_block,source_corr,LTAB_R)
				else:
					gener+=format(source_block+source_corr,'<10s')
					gener+=format('COUNT','>20s')
					gener+=format('MASSi','>10s')+'\n'
				gener+=R
				try:
					q="INSERT INTO t2wellsource(well,blockcorr,source_nickname) VALUES ('%s','%s','%s')"%(name,source_block,source_corr)
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

				if t2_ver<7:
					gener+="%s%s                %4d     MASS\n"%(source_block,source_corr,LTAB_P)
				else:
					gener+=format(source_block+source_corr,'<10s')
					gener+=format('COUNT','>20s')
					gener+=format('MASS ','>10s')+'\n'
				gener+=P
				try:
					q="INSERT INTO t2wellsource(well,blockcorr,source_nickname) VALUES ('%s','%s','%s')"%(name,source_block,source_corr)
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
		value=formats_t2['GENER'][key][0]
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
	for gener in geners:
		string+=t2w.converter(gener,formats_t2['GENER']['BLOCK'][1],def_value=False)
		list_geners.append(geners[gener]['SL']+str(geners[gener]['NS']))
		for index, key in enumerate(formats_t2['GENER']):
			if index!=0:
				value,def_value=def_gener_selector(gener,key,geners)
				string+=t2w.converter(value,formats_t2['GENER'][key][1],def_value)
		try:
			q="INSERT INTO t2wellsource(well,blockcorr,source_nickname) VALUES ('%s','%s','%s')"%(geners[gener]['TYPE'],gener,geners[gener]['SL']+str(geners[gener]['NS']))
			c.execute(q)
			conn.commit()
		except sqlite3.IntegrityError:
			print("The blockcorr %s is already used by another source"%(gener))
		string+="\n"


	file=open('../model/t2/sources/GENER_SOURCES','w')
	file.write(string)
	file.close()

	#As the sources defined on geners are the only allowed any other source not included  dictionary will be erased
	list_geners_string=''.join(["'%s',"%str(i) for i in list_geners])
	query="DELETE FROM t2wellsource WHERE source_nickname NOT IN (%s) AND  source_nickname LIKE'GEN*' "%(list_geners_string[0:-1])
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
    file.write("type,date-time,steam,liquid,enthalpy,WHPabs\n")
    for n in range(len(flow_times[name][0])):
      date=(flow_times[name][0][n]).strftime("%Y-%m-%d %H:%M:%S")
      steam=flow_times[name][1][n]
      brine=flow_times[name][2][n]
      enthlapy=flow_times[name][3][n]
      pressure=flow_times[name][4][n]
      type_well=flow_times[name][5]
      string="%s,%s,%s,%s,%s,%s\n"%(type_well,date,steam,brine,enthlapy,pressure)
      file.write(string)
  if include_gener:
  	txt2sql.replace_mh(low_times.keys(),db_path=input_dictionary['db_path'],source_txt=input_dictionary['../input/'])
  	write_gener_from_sqlite(type_flow='constant',forecast=True,wells=flow_times.keys(),make_up=True,input_dictionary=input_dictionary)

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

	fig = plt.figure(figsize=(8, 2))
	ax = fig.add_subplot(111)

	cnt=1
	y_positions=[]
	well_tick=[]
	for well in flow_times:
		if well[0]=='P':
			color='r'
		elif well[0]=='I':
			color='b'
		data_range=flow_times[well][0]
		value=[cnt,cnt]
		y_positions.append(cnt)
		cnt+=1
		plt.plot(data_range, value,color,lw=4,alpha=0.5)
		well_tick.append(str(well).replace("X","").replace("Z",""))

	ax.set_xlabel("Time")
	plt.yticks(y_positions, well_tick)
	plt.show()
	fig.savefig('wells_flow.png')