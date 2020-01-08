import sqlite3
import os
import pandas as pd
import json

def checktable(table_name,c):
	query="SELECT COUNT(name) from sqlite_master WHERE type='table' AND name='%s'"%(table_name)
	c.execute(query)
	if c.fetchone()[0]==1:
		check=1
	else:
		check=0
	return check

def db_creation(db_path):
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

		#Create table - wellfeedzone
		if checktable('wellfeedzone',c)==0:
			c.execute('''CREATE TABLE  wellfeedzone
						 ([well] TEXT,
						 [MeasuredDepth] REAL,
						 [porcentage] REAL)''')

		#Create table - TOUGH2 well block(correlative)
		if checktable('t2wellblock',c)==0:
			c.execute('''CREATE TABLE  t2wellblock
						 ([well] TEXT,
						 [blockcorr] TEXT)''')

		#Create table - TOUGH2 well source
		if checktable('t2wellsource',c)==0:
			c.execute('''CREATE TABLE  t2wellsource
						 ([well] TEXT,
						 [blockcorr] TEXT,
						 [source_nickname] TEXT)''')

		conn.commit()
		conn.close()

def insert_wells_sqlite(db_path,source_txt):
	conn=sqlite3.connect(db_path)
	c = conn.cursor()

	wells=pd.read_csv(source_txt+'ubication.csv')

	wells['drilldate'] = pd.to_datetime(wells['drilldate'],format="%Y%m%d")

	for  index,row in wells.iterrows():
		q="INSERT INTO wells(well,type,east,north,elevation,drilldate) VALUES ('%s','%s',%s,%s,%s,'%s')"%\
		(row['well'],row['type'],row['east'],row['north'],row['elevation'],row['drilldate'])
		c.execute(q)
		conn.commit()

	conn.close()

def insert_feedzone_to_sqlite(db_path,source_txt):

	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	feedzones=pd.read_csv(source_txt+'well_feedzone.csv')

	for index,row in feedzones.iterrows():
		q="INSERT INTO wellfeedzone(well,MeasuredDepth,porcentage) VALUES ('%s',%s,%s)"%\
		(row['well'],row['MeasuredDepth'],row['porcentage'])
		c.execute(q)
		conn.commit()
	conn.close()

def insert_survey_to_sqlite(db_path,source_txt):

	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	for f in os.listdir(source_txt+'survey'):
		well_name=f.replace("'","").replace("_MD.dat","")
		survey=pd.read_csv(source_txt+'survey/'+f)
		for index, row in survey.iterrows():
			q="INSERT INTO survey(well,MeasuredDepth,Delta_north,Delta_east) VALUES ('%s',%s,%s,%s)"%\
			(well_name,row['MeasuredDepth'],row['Delta_north'],row['Delta_east'])
			c.execute(q)
			conn.commit()
	conn.close()

def insert_PT_to_sqlite(db_path,source_txt):

	conn=sqlite3.connect(db_path)
	c=conn.cursor()
	for f in os.listdir(source_txt+'PT'):
		well_name=f.replace("'","").replace("_MDPT.dat","")
		PT=pd.read_csv(source_txt+'PT/'+f)
		for index, row in PT.iterrows():
			q="INSERT INTO PT(well,MeasuredDepth,Pressure,Temperature) VALUES ('%s',%s,%s,%s)"%\
			(well_name,row['MD'],row['P'],row['T'])
			c.execute(q)
			conn.commit()
	conn.close()





def insert_mh_to_sqlite(db_path,source_txt):

	conn=sqlite3.connect(db_path)
	c=conn.cursor()
	for f in os.listdir(source_txt+'mh'):
		well_name=f.replace("'","").replace("_mh.dat","")
		mh=pd.read_csv(source_txt+'mh/'+f)
		for index, row in mh.iterrows():
			q="INSERT INTO mh(well,type,date_time,steam_flow,liquid_flow,flowing_enthalpy,well_head_pressure) VALUES ('%s','%s','%s',%s,%s,%s,%s)"%\
			(well_name,row['type'],row['date-time'],row['steam'],row['liquid'],row['enthalpy'],row['WHPabs'])
			c.execute(q)
			conn.commit()
	conn.close()



def sqlite_to_json(db_path,source_txt):

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

				for nv in dict_keys:
					query="SELECT * from %s WHERE %s='%s'"%(lv,lv2,nv)

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

							query="SELECT %s from %s WHERE %s='%s'"%(q_string[0:-1],lv,lv2,nv)

							conn=sqlite3.connect(db_path)
							conn.row_factory = sqlite3.Row
							c=conn.cursor()
							rows=c.execute(query).fetchall()

							dict_to_json[lv][prev_result][nv]=[dict(ix) for ix in rows]

						"""
						print query
						conn=sqlite3.connect(db_path)
						conn.row_factory = sqlite3.Row
						c=conn.cursor()
						rows=c.execute(query).fetchall()

						dict_to_json[lv][nv]=[dict(ix) for ix in rows]
						"""
				


	with open(source_txt+'model.json', 'w') as jlines:
		json.dump(dict_to_json, jlines,indent=4,sort_keys=True)
	

	conn.close()


	"""


	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	query="SELECT name from sqlite_master WHERE type='table' "
	c.execute(query)
	rows=c.fetchall()

	tables=[]
	for row in rows:
		tables.append(str(row[0]))

	dict_to_json=dict((n,{}) for n in tables)

	for table_name in tables:

		#Writes the wells as an ID with empty values into a dictionary
		conn=sqlite3.connect(db_path)
		c=conn.cursor()
		query="SELECT DISTINCT well from %s"%table_name
		c.execute(query)
		rows=c.fetchall()
		wells=[]
		for row in rows:
			wells.append(str(row[0]))

		dict_of_wells_on_table=dict((n,{}) for n in wells)
		dict_to_json[table_name]=dict_of_wells_on_table

		#Writes the data from a certain well into an nested dictionary 
		conn=sqlite3.connect(db_path)
		conn.row_factory = dict_factory
		cur1=conn.cursor()

		#The issue till now is the values are written like unicode when unpack
		for well in wells:
			rows=cur1.execute("SELECT * FROM %s where well='%s'"%(table_name,well)).fetchall()

			#rows_s= [tuple(map(str,eachTuple)) for eachTuple in rows]

			#print rows[0:-1]
			#print rows

			#dict_to_json[table_name][well]=dict((str(key), str(value)) for key, value in rows[0:-1].items())

			#dict_to_json[table_name][well]=format(rows[0:-1]).replace(" u'", "'").replace("'", "\"")

			dict_to_json[table_name][well]=json.dumps([dict(ix) for ix in rows])
	
			#jlines.write(format(rows).replace(" u'", "'").replace("'", "\""))

	#Writes the dictionary into a json
	with open(source_txt+'model.json', 'w') as jlines:
		json.dump(dict_to_json, jlines,indent=4,sort_keys=True)

	conn.close()
	"""


db_path='../input/model.db'
source_txt='../input/'

"""
db_creation(db_path)
insert_mh_to_sqlite(db_path,source_txt)
insert_survey_to_sqlite(db_path,source_txt)
insert_feedzone_to_sqlite(db_path,source_txt)
insert_wells_sqlite(db_path,source_txt)
insert_PT_to_sqlite(db_path,source_txt)
"""
sqlite_to_json(db_path,source_txt)