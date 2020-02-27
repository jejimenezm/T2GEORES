import sqlite3
import os
import pandas as pd
import json
from model_conf import *
import t2resfun as t2r

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
						 [blockcorr] TEXT PRIMARY KEY,
						 [source_nickname] TEXT)''')

		#Create table - layers levels
		if checktable('layers',c)==0:
			c.execute('''CREATE TABLE  layers
						 ([correlative] TEXT PRIMARY KEY,
						 [top] REAL,
						 [middle] REAL,
						 [bottom] REAL)''')

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

def insert_drawdown_to_sqlite(db_path,source_txt):
	conn=sqlite3.connect(db_path)
	c=conn.cursor()
	for f in os.listdir(source_txt+'drawdown'):
		well_name=f.replace("'","").replace("_DD.dat","")
		C=pd.read_csv(source_txt+'drawdown/'+f)
		for index, row in C.iterrows():
			q="INSERT INTO drawdown(well,date_time,TVD,pressure) VALUES ('%s','%s',%s,%s)"%\
			(well_name,row['datetime'],row['TVD'],row['pressure'])
			c.execute(q)
			conn.commit()
	conn.close()

def insert_cooling_to_sqlite(db_path,source_txt):
	conn=sqlite3.connect(db_path)
	c=conn.cursor()
	for f in os.listdir(source_txt+'cooling'):
		well_name=f.replace("'","").replace("_C.dat","")
		DD=pd.read_csv(source_txt+'cooling/'+f)
		for index, row in DD.iterrows():
			q="INSERT INTO cooling(well,date_time,TVD,temp) VALUES ('%s','%s',%s,%s)"%\
			(well_name,row['datetime'],row['TVD'],row['temperature'])
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

def insert_wellblock_to_sqlite(db_path,source_txt,wells):
	#Takes the well names from model_conf.py and read the well_correlative.txt on the mesh folder

	if os.path.isfile('../mesh/wells_correlative.txt'):

		with open('../mesh/wells_correlative.txt') as json_file:
		    wells_correlative=json.load(json_file)
		
		conn=sqlite3.connect(db_path)
		c=conn.cursor()

		for name in wells:
			try:
				blocknumer=wells_correlative[name][0]
				q="INSERT INTO t2wellblock(well,blockcorr) VALUES ('%s','%s')"%(name,blocknumer)
				c.execute(q)
				conn.commit()
			except KeyError:
				pass
			except sqlite3.IntegrityError:
				print "The block  number is already assing for the well: %s"%name
		conn.close()

	else:
		print "The file well_correlative.txt do not exists"

def insert_layers_to_sqlite(db_path,source_txt):

	top,correlative,middle,bottom=t2r.vertical_layer(layers,z0_level)
	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	for n in range(len(top)):
		q="INSERT INTO layers(correlative,top,middle,bottom) VALUES ('%s',%s,%s,%s)"\
			%(correlative[n],top[n],middle[n],bottom[n])
		try:
			c.execute(q)
			conn.commit()
		except sqlite3.IntegrityError:
			print "The layer %s is already define, correlative is a PRIMARY KEY"%correlative[n]
	conn.close()

"""
def sqlite_to_json(db_path,source_txt):

	levels={'wells':['well'],
			'survey':['well','MeasuredDepth'],
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

		#Select the columns that are not part of the levels
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

		lv2=levels[lv]
		
		prev_result=[]

		for nln in range(len(lv2)):
			if cnt==0:
				query="SELECT DISTINCT %s from %s"%(lv2[nln],lv)
				cnt+=1
			else:
				query="SELECT DISTINCT %s from %s"%(lv2[nln],lv)
			print query
			c.execute(query)
			rows=c.fetchall()
			dict_keys=[]
			for row in rows:
				dict_keys.append(str(row[0]))

			dict_of_wells_on_table=dict((n,{}) for n in dict_keys)
			print dict_of_wells_on_table

			if nln==0:
				dict_to_json[lv]=dict_of_wells_on_table
			else:
				str_dict="dict_to_json[lv]"
				for nd in range(nln):
					strx="[lv2[%s]]"%(nd)
					str_dict+=strx
				print str_dict
				str_dict+="=dict((n,{}) for n in dict_keys)"
				print eval(str_dict)
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
insert_drawdown_to_sqlite(db_path,source_txt)
insert_cooling_to_sqlite(db_path,source_txt)

insert_wellblock_to_sqlite(db_path,source_txt,wells)

insert_layers_to_sqlite(db_path,source_txt)
"""


#sqlite_to_json(db_path,source_txt)
