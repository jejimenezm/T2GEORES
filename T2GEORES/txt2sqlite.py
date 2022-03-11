from T2GEORES import geometry as geomtr
import sqlite3
import os
import pandas as pd
import json

def checktable(table_name,c):
	"""It verifies the existance of a table on the sqlite database

	Parameters
	----------
	table_name : str
	  Table name
	c : cursor
	  Conection to the database

	Returns
	-------
	int
		check: if table exists returns 1

	Examples
	--------
	>>>  checktable(table_name,c)
	"""

	query="SELECT COUNT(name) from sqlite_master WHERE type='table' AND name='%s'"%(table_name)
	c.execute(query)
	if c.fetchone()[0]==1:
		check=1
	else:
		check=0
	return check

def db_creation(input_dictionary):
	"""It creates a sqlite databa base 

	Parameters
	----------
	input_dictionary : dictionary
	  Dictionary contaning the path and name of database on keyword 'db_path', usually on '../input/'

	Returns
	-------
	database
		name: database on desire path

	Note
	----
	The tables: wells, survey, PT, mh, drawdown, cooling, wellfeedzone, t2wellblock, t2wellsource, layers and t2PTout are generated

	Examples
	--------
	>>> db_creation(input_dictionary)
	"""

	db_path=input_dictionary['db_path']

	if not os.path.isfile(db_path):
		conn=sqlite3.connect(db_path)
		c = conn.cursor()

		# Create table - wells
		if checktable('wells',c)==0:
			c.execute('''CREATE TABLE wells
		             ([well] TEXT PRIMARY KEY,
		              [type] TEXT,
		              [east] REAL,
		              [north] REAL,
		              [elevation] REAL,
		              [lnr_init] REAL,
		              [lnr_end] REAL,
		              [lnr_D] TEXT,
		              [ptube_init] REAL,
		              [ptube_end] REAL,
		              [ptube_D] TEXT,
		              [drilldate] datetime)''')

		#Create table - survey
		if checktable('survey',c)==0:
			c.execute('''CREATE TABLE  survey
						 ([well] TEXT,
						 [MeasuredDepth] REAL,
						 [Delta_east] REAL,
						 [Delta_north] REAL)''')

		#Create table - PT
		if checktable('PT',c)==0:
			c.execute('''CREATE TABLE  PT
						 ([well] TEXT,
						 [MeasuredDepth] REAL,
						 [Pressure] REAL,
						 [Temperature] REAL)''')

		#Create table - raw mh
		if checktable('mh',c)==0:
			c.execute('''CREATE TABLE  mh
						 ([well] TEXT,
						 [type] TEXT,
						 [date_time] datetime,
						 [steam_flow] REAL,
						 [liquid_flow] REAL,
						 [flowing_enthalpy] REAL,
						 [well_head_pressure] REAL)''')

		#Create table - filtered mh
		if checktable('mh_f',c)==0:
			c.execute('''CREATE TABLE  mh_f
						 ([well] TEXT,
						 [status] TEXT,
						 [date_time] datetime,
						 [steam_flow] REAL,
						 [liquid_flow] REAL,
						 [flowing_enthalpy] REAL,
						 [well_head_pressure] REAL)''')

		#Create table - drawdown
		if checktable('drawdown',c)==0:
			c.execute('''CREATE TABLE  drawdown
						 ([well] TEXT,
						 [date_time] datetime,
						 [TVD] REAL,
						 [pressure] REAL)''')

		#Create table - cooling
		if checktable('cooling',c)==0:
			c.execute('''CREATE TABLE  cooling
						 ([well] TEXT,
						 [date_time] datetime,
						 [TVD] REAL,
						 [temp] REAL)''')

		#Create table - wellfeedzone
		if checktable('wellfeedzone',c)==0:
			c.execute('''CREATE TABLE  wellfeedzone
						 ([well] TEXT,
						 [MeasuredDepth] REAL,
						 [contribution] REAL)''')

		#Create table - TOUGH2 well block(correlative)
		if checktable('t2wellblock',c)==0:
			c.execute('''CREATE TABLE  t2wellblock
						 ([well] TEXT PRIMARY KEY,
						 [blockcorr] TEXT)''')

		#Create table - TOUGH2 well source
		if checktable('t2wellsource',c)==0:
			c.execute('''CREATE TABLE  t2wellsource
						 ([well] TEXT,
						 [blockcorr] TEXT ,
						 [rocktype] TEXT ,
						 [flow_type] TEXT ,
						 [source_nickname] TEXT PRIMARY KEY)''')

		#Create table - layers levels
		if checktable('layers',c)==0:
			c.execute('''CREATE TABLE  layers
						 ([correlative] TEXT PRIMARY KEY,
						 [top] REAL,
						 [middle] REAL,
						 [bottom] REAL)''')
			
		#Create table - stores ELEME section of mesh
		if checktable('ELEME',c)==0:
			c.execute('''CREATE TABLE  ELEME
						 ([model_version] REAL,
						 [model_output_timestamp] timestamp,
						 [ELEME] TEXT,
						 [NSEQ] REAL,
						 [NADD] REAL,
						 [MA1] REAL,
						 [MA2] REAL,
						 [VOLX] REAL,
						 [AHTX] REAL,
						 [PMX] REAL,
						 [X] REAL,
						 [Y] REAL,
						 [Z] REAL,
						 [LAYER_N] REAL,
						 [h] REAL)''')

		#Create table - stores CONNE section of mesh
		if checktable('CONNE',c)==0:
			c.execute('''CREATE TABLE  CONNE
						 ([model_version] REAL,
						 [model_output_timestamp] timestamp,
						 [ELEME1] TEXT,
						 [ELEME2] TEXT,
						 [NSEQ] REAL,
						 [NAD1] REAL,
						 [NAD2] REAL,
						 [ISOT] REAL,
						 [D1] REAL,
						 [D2] REAL,
						 [AREAX] REAL,
						 [BETAX] REAL,
						 [SIGX] REAL)''')

		#Create table - stores segment
		if checktable('segment',c)==0:
			c.execute('''CREATE TABLE  segment
						 ([model_version] REAL,
						 [model_output_timestamp] timestamp,
						 [x1] REAL,
						 [y1] REAL,
						 [x2] REAL,
						 [y2] REAL,
						 [redundant] REAL,
						 [ELEME1] TEXT,
						 [ELEME2] TEXT)''')

		#Create table - PT out
		if checktable('t2PTout',c)==0:
			c.execute('''CREATE TABLE  t2PTout
						 ([blockcorr] TEXT PRIMARY KEY,
						 [x] REAL,
						 [y] REAL,
						 [z] REAL,
						 [index] REAL,
						 [P] REAL,
						 [T] REAL,
						 [SG] REAL,
						 [SW] REAL,
						 [X1] REAL,
						 [X2] REAL,
						 [PCAP] REAL,
						 [DG] REAL,
						 [DW] REAL)''')

		#Create table - stores flows TOUGH2 output section
		if checktable('t2FLOWSout',c)==0:
			c.execute('''CREATE TABLE  t2FLOWSout
						 ([model_version] REAL,
						 [model_output_timestamp] timestamp,
						 [ELEME1] TEXT,
						 [ELEME2] TEXT,
						 [INDEX] INT,
						 [FHEAT] REAL,
						 [FLOH] REAL,
						 [FLOF] REAL,
						 [FLOG] REAL,
						 [FLOAQ] REAL,
						 [FLOWTR2] REAL,
						 [VELG] REAL,
						 [VELAQ] REAL,
						 [TURB_COEFF] REAL,
						 [model_time] REAL)''')

		#Create table - stores flows directions from every block
		if checktable('t2FLOWVectors',c)==0:
			c.execute('''CREATE TABLE  t2FLOWVectors
						 ([model_version] REAL,
						 [model_output_timestamp] timestamp,
						 [ELEME] TEXT,
						 [FHEAT_x] REAL,
						 [FHEAT_y] REAL,
						 [FHEAT_z] REAL,
						 [FLOH_x] REAL,
						 [FLOH_y] REAL,
						 [FLOH_z] REAL,
						 [FLOF_x] REAL,
						 [FLOF_y] REAL,
						 [FLOF_z] REAL,
						 [FLOG_x] REAL,
						 [FLOG_y] REAL,
						 [FLOG_z] REAL,
						 [FLOAQ_x] REAL,
						 [FLOAQ_y] REAL,
						 [FLOAQ_z] REAL,
						 [FLOWTR2_x] REAL,
						 [FLOWTR2_y] REAL,
						 [FLOWTR2_z] REAL,
						 [VELG_x] REAL,
						 [VELG_y] REAL,
						 [VELG_z] REAL,
						 [VELAQ_x] REAL,
						 [VELAQ_y] REAL,
						 [VELAQ_z] REAL,
						 [TURB_COEFF_x] REAL,
						 [TURB_COEFF_y] REAL,
						 [TURB_COEFF_z] REAL,
						 [model_time] REAL)''')

		conn.commit()
		conn.close()

def insert_wells_sqlite(input_dictionary):
	"""It stores the data contain on the ubication.csv file and stores it on the database

	Parameters
	----------
	input_dictionary: dictionary
	  Dictionary containing the path and name of database and the path of the input file

	Note
	----
	The well name is written as primary key. Thus, if the coordinates of the file ubication.csv change, it is better to 
	eliminate the records and rerun this function again. Some print are expected.

	Examples
	--------
	>>>  insert_wells_sqlite(input_dictionary)
	"""

	db_path=input_dictionary['db_path']
	source_txt=input_dictionary['source_txt']

	conn=sqlite3.connect(db_path)
	c = conn.cursor()

	wells=pd.read_csv(source_txt+'ubication.csv')

	wells['drilldate'] = pd.to_datetime(wells['drilldate'],format="%Y%m%d")

	for  index,row in wells.iterrows():
		try:
			q="INSERT INTO wells(well,type,east,north,elevation,drilldate) VALUES ('%s','%s',%s,%s,%s,'%s')"%\
			(row['well'],row['type'],row['east'],row['north'],row['masl'],row['drilldate'])
			c.execute(q)
			conn.commit()
		except sqlite3.IntegrityError:
			print("The well %s is already on the database")
	conn.close()

def insert_feedzone_to_sqlite(input_dictionary):
	"""It stores the data contain on the ubication.csv file and stores it on the database

	Parameters
	----------
	input_dictionary: dictionary
	  Dictionary containing the path and name of database and the path of the input file

	Examples
	--------
	>>>  insert_feedzone_to_sqlite(input_dictionary)
	"""

	db_path=input_dictionary['db_path']
	source_txt=input_dictionary['source_txt']

	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	feedzones=pd.read_csv(source_txt+'well_feedzone.csv',delimiter=',')


	for index,row in feedzones.iterrows():
		q="INSERT INTO wellfeedzone(well,MeasuredDepth,contribution) VALUES ('%s',%s,%s)"%\
		(row['well'],row['MD'],row['contribution'])
		c.execute(q)
		conn.commit()
	conn.close()

def insert_survey_to_sqlite(input_dictionary):
	"""It stores all the data contain on the subfolder survey from the input file folder.

	Parameters
	----------
	input_dictionary: dictionary
	  Dictionary containing the path and name of database and the path of the input file

	Note
	----
	The survey for every well must have the next headers MeasuredDepth,Delta_north,Delta_east

	Examples
	--------
	>>>  insert_survey_to_sqlite(input_dictionary)
	"""

	db_path=input_dictionary['db_path']
	source_txt=input_dictionary['source_txt']

	conn=sqlite3.connect(db_path)
	c=conn.cursor()
	
	for f in os.listdir(source_txt+'survey/'):
		if os.path.isfile(os.path.join(source_txt, 'survey/',f)):
			well_name=f.replace("'","").replace("_MD.dat","")
			well_file=os.path.join(source_txt, 'survey/',f)
			survey=pd.read_csv(well_file)
			for index, row in survey.iterrows():
				q="INSERT INTO survey(well,MeasuredDepth,Delta_north,Delta_east) VALUES ('%s',%s,%s,%s)"%\
				(well_name,row['MeasuredDepth'],row['Delta_north'],row['Delta_east'])
				c.execute(q)
				conn.commit()
	conn.close()

def insert_PT_to_sqlite(input_dictionary):
	"""It stores all the data contain on the subfolder PT from the input file folder.

	Parameters
	----------
	input_dictionary: dictionary
	  Dictionary containing the path and name of database and the path of the input file

	Note
	----
	The PT for every well must have the next headers MD,P,T. The file name must be well_MDPT.dat

	Examples
	--------
	>>>  insert_PT_to_sqlite(input_dictionary)
	"""

	db_path=input_dictionary['db_path']
	source_txt=input_dictionary['source_txt']

	conn=sqlite3.connect(db_path)
	c=conn.cursor()
	for f in os.listdir(source_txt+'PT'):
		if os.path.isfile(source_txt+'PT/'+f):
			if '_MDPT' in f:
				well_name=f.replace("'","").replace("_MDPT.dat","")
				if os.path.isfile(source_txt+'PT/'+f):
					PT=pd.read_csv(source_txt+'PT/'+f)
					for index, row in PT.iterrows():
						q="INSERT INTO PT(well,MeasuredDepth,Pressure,Temperature) VALUES ('%s',%s,%s,%s)"%\
						(well_name,row['MD'],row['P'],row['T'])
						c.execute(q)
						conn.commit()
	conn.close()

def insert_drawdown_to_sqlite(input_dictionary):
	"""It stores all the data contain on the subfolder drawdown from the input file folder.

	Parameters
	----------
	input_dictionary: dictionary
	  Dictionary containing the path and name of database and the path of the input file

	Note
	----
	The drawdown register on every well must have the next headers datetime,TVD,pressure. The file name must be well_DD.dat

	Examples
	--------
	>>>  insert_drawdown_to_sqlite(input_dictionary)
	"""

	db_path=input_dictionary['db_path']
	source_txt=input_dictionary['source_txt']

	conn=sqlite3.connect(db_path)
	c=conn.cursor()
	for f in os.listdir(source_txt+'drawdown'):
		well_name=f.replace("'","").replace("_DD.dat","")
		if os.path.isfile(source_txt+'drawdown/'+f) and f!='p_res.csv':
			DD=pd.read_csv(source_txt+'drawdown/'+f)
			DD['well'] = well_name
			DD.rename(columns={'datetime': 'date_time', 'temperature': 'temp'}, inplace=True)
			DD.to_sql('drawdown',if_exists='append',con=conn,index=False)
			
	conn.close()

def insert_cooling_to_sqlite(input_dictionary):
	"""It stores all the data contain on the subfolder cooling from the input file folder.

	Parameters
	----------
	input_dictionary: dictionary
	  Dictionary containing the path and name of database and the path of the input file

	Note
	----
	The cooling register on every well must have the next headers datetime,TVD,temperature. The file name must be well_C.dat

	Examples
	--------
	>>>  insert_cooling_to_sqlite(input_dictionary)
	"""


	db_path=input_dictionary['db_path']
	source_txt=input_dictionary['source_txt']

	conn=sqlite3.connect(db_path)
	c=conn.cursor()
	for f in os.listdir(source_txt+'cooling'):
		well_name=f.replace("'","").replace("_C.dat","")
		if os.path.isfile(source_txt+'cooling/'+f):
			CC=pd.read_csv(source_txt+'cooling/'+f)
			CC['well'] = well_name
			CC.rename(columns={'datetime': 'date_time', 'temperature': 'temp'}, inplace=True)
			CC.to_sql('cooling',if_exists='append',con=conn,index=False)
			
	conn.close()

def insert_raw_mh_to_sqlite(input_dictionary):
	"""It stores all the data contain on the subfolder mh from the input file folder.

	Parameters
	----------
	input_dictionary: dictionary
	  Dictionary containing the path and name of database and the path of the input file

	Note
	----
	Every file contains information about the flow rate and flowing enthalpy of the wells. Every register must contain the next headers:
	type,date-time,steam,liquid,enthalpy,WHPabs. The file name must be name well_mh.dat

	Examples
	--------
	>>>  insert_mh_to_sqlite(input_dictionary)
	"""
	db_path=input_dictionary['db_path']
	source_txt=input_dictionary['source_txt']
	conn=sqlite3.connect(db_path)
	c=conn.cursor()
	for f in os.listdir(source_txt+'mh'):
		print(f)
		well_name=f.replace("'","").replace("_mh.dat","")
		if os.path.isfile(source_txt+'mh/'+f):
			mh=pd.read_csv(source_txt+'mh/'+f)
			mh['well'] = well_name
			mh.rename(columns={'steam': 'steam_flow', 'liquid': 'liquid_flow', 'enthalpy': 'flowing_enthalpy',  'WHPabs': 'well_head_pressure', 'status': 'type'}, inplace=True)
			mh.to_sql('mh',if_exists='append',con=conn,index=False)
			conn.close()

def insert_filtered_mh_to_sqlite(input_dictionary, single_well = None):
	"""It stores all the data contain on the subfolder mh from the input file folder.

	Parameters
	----------
	input_dictionary: dictionary
	  Dictionary containing the path and name of database and the path of the input file

	Note
	----
	Every file contains information about the flow rate and flowing enthalpy of the wells. Every register must contain the next headers:
	type,date-time,steam,liquid,enthalpy,WHPabs. The file name must be name well_mh.dat

	Examples
	--------
	>>>  insert_mh_to_sqlite(input_dictionary)
	"""

	db_path=input_dictionary['db_path']
	source_txt=input_dictionary['source_txt']

	conn=sqlite3.connect(db_path)
	c=conn.cursor()
	if single_well == None:
		for f in os.listdir(source_txt+'mh/filtered'):
			print(f)
			well_name=f.replace("'","").replace("_week_avg.csv","")
			if os.path.isfile(source_txt+'mh/filtered/'+f) and well_name in input_dictionary['WELLS']:
				mh=pd.read_csv(source_txt+'mh/filtered/'+f)
				mh['well'] = well_name
				mh.rename(columns={'steam': 'steam_flow', 'liquid': 'liquid_flow', 'enthalpy': 'flowing_enthalpy',  'WHPabs': 'well_head_pressure'}, inplace=True)
				mh.to_sql('mh_f',if_exists='append',con=conn,index=False)
	else:
		file_name = single_well + "_week_avg.csv"
		if os.path.isfile(source_txt+'mh/filtered/'+file_name) and single_well in input_dictionary['WELLS']:
			mh=pd.read_csv(source_txt+'mh/filtered/'+file_name)
			mh['well'] = single_well
			mh.rename(columns={'steam': 'steam_flow', 'liquid': 'liquid_flow', 'enthalpy': 'flowing_enthalpy',  'WHPabs': 'well_head_pressure'}, inplace=True)
			mh.to_sql('mh_f',if_exists='append',con=conn,index=False)
			
	conn.close()

def replace_mh(wells_to_replace,input_dictionary):
	"""It stores all the data contain on the subfolder mh from the input file folder from some selected wells

	Parameters
	----------
	input_dictionary: dictionary
	  Dictionary containing the path and name of database and the path of the input file
	wells_to_replace: list
	  Contains the data from the wells which flow data will be replace

	Note
	----
	Every file contains information about the flow rate and flowing enthalpy of the wells. Every register must contain the next headers:
	type,date-time,steam,liquid,enthalpy,WHPabs. The file name must be name well_mh.dat

	Examples
	--------
	>>>  replace_mh(wells_to_replace=['WELL-1','WELL-2'],input_dictionary)
	"""

	db_path=input_dictionary['db_path']
	source_txt=input_dictionary['source_txt']

	conn=sqlite3.connect(db_path)
	c=conn.cursor()
	for f in os.listdir(source_txt+'mh'):
		well_name=f.replace("'","").replace("_mh.dat","")
		if well_name in wells_to_replace:
			q="DELETE FROM mh WHERE well='%s'"%well_name
			c.execute(q)
			conn.commit()
			if os.path.isfile(source_txt+'mh/'+f):
				print(source_txt+'mh/'+f)
				mh=pd.read_csv(source_txt+'mh/'+f)
				for index, row in mh.iterrows():
					q="INSERT INTO mh(well,type,date_time,steam_flow,liquid_flow,flowing_enthalpy,well_head_pressure) VALUES ('%s','%s','%s',%s,%s,%s,%s)"%\
					(well_name,row['type'],row['date-time'],row['steam'],row['liquid'],row['enthalpy'],row['WHPabs'])
					c.execute(q)
					conn.commit()
	conn.close()

def sqlite_to_json(input_dictionary):
	"""It exports the database into a single json file

	Parameters
	----------
	input_dictionary: dictionary
	  Dictionary containing the path and name of database and the path of the input file

	Note
	----
	It creates from the tables wells, survey, PT, mh, drawdown, wellfeedzone, t2wellblock and t2wellsource a  json file, using as ID the field well

	Other Parameters
	----------------
	dictionary
		levels : configuration dictionary, indicates the table name, the ID to use and the field to use on each table

	Examples
	--------
	>>>  sqlite_to_json(input_dictionary)
	"""

	db_path=input_dictionary['db_path']
	source_txt=input_dictionary['source_txt']

	levels={'wells':['well'],
			'survey':['well'],
			'PT':['well','MeasuredDepth'],
			'mh':['well','date_time'],
			'drawdown':['well','date_time'],
			'wellfeedzone':['well'],
			't2wellblock':['well'],
			't2wellsource':['well']}

	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	dict_to_json=dict((n,{}) for n in levels.keys())
	
	for lv in levels:
		cnt=0
		for lv2 in levels[lv]:
			
			if len(levels[lv])==1:

				query="SELECT DISTINCT %s from %s"%(lv2,lv)
				c.execute(query)
				rows=c.fetchall()
				dict_keys=[]
				for row in rows:
					dict_keys.append(str(row[0]))

				dict_of_wells_on_table=dict((n,{}) for n in dict_keys)
				dict_to_json[lv]=dict_of_wells_on_table

				query="PRAGMA table_info(%s)"%lv
				c.execute(query)
				rows=c.fetchall()
				colums=[]
				for row in rows:
					colums.append(str(row[1]))

				partq=[]

				q_string=""
				for nv in colums:
					if nv not in levels[lv] :
						partq.append(nv)
						q_string+=" %s,"%(nv)

				for nv in dict_keys:
					query="SELECT %s from %s WHERE %s='%s'"%(q_string[0:-1],lv,lv2,nv)

					conn=sqlite3.connect(db_path)
					conn.row_factory = sqlite3.Row
					c=conn.cursor()
					rows=c.execute(query).fetchall()

					dict_to_json[lv][nv]=[dict(ix) for ix in rows]

			elif len(levels[lv])>1:
				if cnt==0:
					query="SELECT DISTINCT %s from %s"%(lv2,lv)
					prev_key=lv2

					c.execute(query)
					rows=c.fetchall()
					dict_keys=[]
					for row in rows:
						dict_keys.append(str(row[0]))

					dict_of_wells_on_table=dict((n,{}) for n in dict_keys)
					dict_to_json[lv]=dict_of_wells_on_table
					cnt+=1

				else:

					#Extract the colums which are not on the results
					query="PRAGMA table_info(%s)"%lv
					c.execute(query)
					rows=c.fetchall()
					colums=[]
					for row in rows:
						colums.append(str(row[1]))

					partq=[]

					q_string=""
					for nv in colums:
						if nv not in levels[lv] :
							partq.append(nv)
							q_string+=" %s,"%(nv)

					for prev_result in dict_keys:

						query="SELECT DISTINCT %s from %s WHERE %s='%s'"%(lv2,lv,prev_key,prev_result)

						c.execute(query)
						rows=c.fetchall()
						dict_keys=[]
						for row in rows:
							dict_keys.append(str(row[0]))

						dict_of_wells_on_table=dict((n,{}) for n in dict_keys)
						dict_to_json[lv][prev_result]=dict_of_wells_on_table

						for nv in dict_keys:

							query="SELECT %s from %s WHERE %s='%s' AND %s='%s' "%(q_string[0:-1],lv,lv2,nv,prev_key,prev_result)

							conn=sqlite3.connect(db_path)
							conn.row_factory = sqlite3.Row
							c=conn.cursor()
							rows=c.execute(query).fetchall()

							dict_to_json[lv][prev_result][nv]=[dict(ix) for ix in rows]
	
	with open(source_txt+'model.json', 'w') as jlines:
		json.dump(dict_to_json, jlines,indent=4,sort_keys=True)
	

	conn.close()

def insert_wellblock_to_sqlite(input_dictionary):
	"""It stores the file wells_correlative.txt coming from regeo_mesh on the table t2wellblock

	Parameters
	----------
	input_dictionary : dictionary
	  A dictionary containing the  name and path of database ans well types WELLS, MAKE_UP_WELLS and NOT_PRODUCING_WELLS

	Note
	----
	The correlative from each wells just contains four characthers. Some print output are expected.


	Examples
	--------
	>>>  insert_wellblock_to_sqlite(input_dictionary)
	"""

	db_path=input_dictionary['db_path']

	if os.path.isfile('../mesh/wells_correlative.txt'):

		with open('../mesh/wells_correlative.txt',encoding='utf8') as json_file:
		    wells_correlative=json.load(json_file)


		conn=sqlite3.connect(db_path)
		c=conn.cursor()

		types=['WELLS','MAKE_UP_WELLS','NOT_PRODUCING_WELL']
		wells=[]
		for scheme in types:
			try:
				for well in input_dictionary[scheme]:
					wells.append(well)
			except KeyError:
					pass
		print(wells_correlative['P-1'])
		for name in wells:
			try:
				blocknumer=wells_correlative[name][0]
				q="INSERT INTO t2wellblock(well,blockcorr) VALUES ('%s','%s')"%(name,blocknumer)
				c.execute(q)
				conn.commit()
			except KeyError:
				print("Error")
				pass
			except sqlite3.IntegrityError:
				print("The block  number is already assing for the well: %s"%name)
		conn.close()

	else:
		print("The file well_correlative.txt do not exists")

def insert_layers_to_sqlite(input_dictionary):
	"""It stores layers and elevations

	Parameters
	----------
	input_dictionary: dictionary
	  Dictionary containing the path and name of database and the path of the input file

	Note
	----
	The data information comes from the input_dictionary which must have a keyword layer with a similar structure as following: 'LAYERS':{1:['A',100],2:['B', 100]}. Some print output are expected.

	Examples
	--------
	>>>  insert_layers_to_sqlite(input_dictionary)
	"""

	layers_info=geomtr.vertical_layers(input_dictionary)
	top=layers_info['top']
	correlative=layers_info['name']
	middle=layers_info['middle']
	bottom=layers_info['bottom']

	conn=sqlite3.connect(input_dictionary['db_path'])
	c=conn.cursor()

	for n in range(len(top)):
		q="INSERT INTO layers(correlative,top,middle,bottom) VALUES ('%s',%s,%s,%s)"\
			%(correlative[n],top[n],middle[n],bottom[n])
		try:
			c.execute(q)
			conn.commit()
		except sqlite3.IntegrityError:
			print("The layer %s is already define, correlative is a PRIMARY KEY"%correlative[n])
	conn.close()


#Not documented

def src_rocktype(input_dictionary):

	elem_file='../mesh/ELEME.json'

	if os.path.isfile(elem_file):
		with open(elem_file) as file:
		  	blocks=json.load(file)


	db_path=input_dictionary['db_path']

	#List the GEN elements
	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	data_source=pd.read_sql_query("SELECT well, blockcorr,source_nickname FROM t2wellsource ORDER BY source_nickname;",conn)

	
	data_source['rocktype'] = None

	for n in range(len(data_source)):
		blockcorr=data_source['blockcorr'][n]
		rocktype_n = blocks[blockcorr]['MA1']
		data_source['rocktype'][n] = rocktype_n

	data_source.to_sql('t2wellsource',if_exists='replace',con=conn,index=False, index_label = 'source_nickname')

	conn.close()
