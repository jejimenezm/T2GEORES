import sqlite3
import os
import pandas as pd
import json
import geometry as geomtr


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

		#Create table - mh
		if checktable('mh',c)==0:
			c.execute('''CREATE TABLE  mh
						 ([well] TEXT,
						 [type] TEXT,
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
						 [porcentage] REAL)''')

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
						 [source_nickname] TEXT PRIMARY KEY)''')

		#Create table - layers levels
		if checktable('layers',c)==0:
			c.execute('''CREATE TABLE  layers
						 ([correlative] TEXT PRIMARY KEY,
						 [top] REAL,
						 [middle] REAL,
						 [bottom] REAL)''')

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
		q="INSERT INTO wellfeedzone(well,MeasuredDepth,porcentage) VALUES ('%s',%s,%s)"%\
		(row['well'],row['MeasuredDepth'],row['porcentage'])
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
			C=pd.read_csv(source_txt+'drawdown/'+f)
			for index, row in C.iterrows():
				q="INSERT INTO drawdown(well,date_time,TVD,pressure) VALUES ('%s','%s',%s,%s)"%\
				(well_name,row['datetime'],row['TVD'],row['pressure'])
				c.execute(q)
				conn.commit()
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
			DD=pd.read_csv(source_txt+'cooling/'+f)
			for index, row in DD.iterrows():
				q="INSERT INTO cooling(well,date_time,TVD,temp) VALUES ('%s','%s',%s,%s)"%\
				(well_name,row['datetime'],row['TVD'],row['temperature'])
				c.execute(q)
				conn.commit()
	conn.close()

def insert_mh_to_sqlite(input_dictionary):
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
		well_name=f.replace("'","").replace("_mh.dat","")
		if os.path.isfile(source_txt+'mh/'+f):
			mh=pd.read_csv(source_txt+'mh/'+f)
			for index, row in mh.iterrows():
				q="INSERT INTO mh(well,type,date_time,steam_flow,liquid_flow,flowing_enthalpy,well_head_pressure) VALUES ('%s','%s','%s',%s,%s,%s,%s)"%\
				(well_name,row['type'],row['date-time'],row['steam'],row['liquid'],row['enthalpy'],row['WHPabs'])
				c.execute(q)
				conn.commit()
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

		for name in wells:
			try:
				blocknumer=wells_correlative[name][0]
				q="INSERT INTO t2wellblock(well,blockcorr) VALUES ('%s','%s')"%(name,blocknumer)
				c.execute(q)
				conn.commit()
			except KeyError:
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