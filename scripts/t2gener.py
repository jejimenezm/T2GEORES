import t2resfun as t2r
from model_conf import *
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os

def write_t2_format_gener(var_array,time_array,ref_date,var_type,var_enthalpy,type_flow):
	string_time_R=''
	string_flow_R=''
	string_enthalpy_R=''
	string_time_P=''
	string_flow_P=''

	t_min=-1E50
	t_max=1E50
	flow_min=0
	enthalpy_min=500E3
	time_zero=0

	time_plus_the_last=365.25*24*3600/2


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

		cnt_P=3
		cnt_R=3


	if len(var_array)==len(time_array):
		for n in range(len(var_type)):
			timex=(time_array[n]-ref_date).total_seconds()
			if var_type[n]=='P':
				well_type="P"
				string_time_P+='%14.6E'%timex
				string_flow_P+='%14.6E'%-var_array[n]
				last_flow=-var_array[n]
				if cnt_P%4==0 and n!=(len(var_type)-1):
					string_time_P+='\n'
					string_flow_P+='\n'
				cnt_P+=1

			if var_type[n]=='R':
				well_type="R"
				string_time_R+='%14.6E'%timex
				string_flow_R+='%14.6E'%var_array[n]
				string_enthalpy_R+='%14.6E'%var_enthalpy[n]
				last_flow=var_array[n]
				last_enthalpy=var_enthalpy[n]
				if cnt_R%4==0 and n!=(len(var_type)-1):
					string_time_R+='\n'
					string_flow_R+='\n'
					string_enthalpy_R+='\n'
				cnt_R+=1

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

				string_time_R+='%14.6E'%(last_time+time_plus_the_last)
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

				string_time_P+='%14.6E'%(last_time+time_plus_the_last)
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
		print "Time and variable array must have the same length"

def write_gener_from_sqlite(db_path,wells,type_flow):
	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	gener=''
	source_corr_num=10

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

		x,y,masl_depth=t2r.MD_to_TVD(name,wellfeedzone)

		for feedn in range(len(porcentage)):

			#Create t the block name for each feedzone
			q_layer="SELECT correlative FROM layers where top>%s and bottom<%s"%(masl_depth[feedn],masl_depth[feedn])

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

			P,R, LTAB_P, LTAB_R= write_t2_format_gener(data['m_total'].values*porcentage[feedn],dates,ref_date,data['type'],data['flowing_enthalpy'],type_flow)


			if type_flow=="invariable":
				condition=1
			elif type_flow=="constant":
				condition=3
			elif type_flow=="shutdown":
				condition=4


			if LTAB_R>condition:
				gener+="%s%s                %4d     MASSi\n"%(source_block,source_corr,LTAB_R-1)
				gener+=R
				source_corr_num+=1

			if LTAB_P>condition:
				gener+="%s%s                %4d     MASS\n"%(source_block,source_corr,LTAB_P-1)
				gener+=P
				source_corr_num+=1
			
			try:
				q="INSERT INTO t2wellsource(well,blockcorr,source_nickname) VALUES ('%s','%s','%s')"%(name,source_block,source_corr)
				c.execute(q)
				conn.commit()
			except sqlite3.IntegrityError:
				print """Two reasons:
						 1-There is already a SOURCE nickname assign to this block (%s),
						 	in this case is better to erase the table content on table t2wellsource, 
						 	be sure about the data on wellfeedzone table
						 	and rerun this function
						 2-Skip the message if you are just updating the flowrates"""%source_block
	conn.close()
	gener_file=open('../model/t2/sources/GENER_PROD','w')
	gener_file.write(gener)
	gener_file.close()

def write_geners_to_txt_and_sqlite(db_path,geners):
	#Bug, if the file already exits it appends the line and mantain the values
	#Constant values from model_conf.py

	#TYPE: HEAT, MASS, DELV

	string=""

	skip=False

	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	for dictionary in geners:
		try:
		 	dictionary['empty'][0]==1
		except KeyError:
			try:
				for index, key in enumerate(dictionary):
					if len(dictionary[key])==3:
						skip=False
						if dictionary[key][1]!=None and 's' in dictionary[key][2]:
							string+=format(str(dictionary[key][1]),"%s"%dictionary[key][2])
						elif 's' not in dictionary[key][2] and dictionary[key][1]!=None:
							string+=format(dictionary[key][1],"%s"%dictionary[key][2])
						elif dictionary[key][1]==None and 'E' not in dictionary[key][2]:
							string+=format("","%s"%dictionary[key][2])
						elif dictionary[key][1]==None and 'E' in dictionary[key][2]:
							string+=format("",">%ss"%dictionary[key][2].split('.')[0].split('>')[1])
					else:
						skip=True
				if not skip:
					string+="\n"
				
				#if update matters
				"""
				if os.path.isfile('../model/t2/sources/GENER_SOURCES'):
					file=open('../model/t2/sources/GENER_SOURCES','a')
				else:
					file=open('../model/t2/sources/GENER_SOURCES','w')
				"""
				
				file=open('../model/t2/sources/GENER_SOURCES','w')
				file.write(string)
				file.close()

				q="INSERT INTO t2wellsource(well,blockcorr,source_nickname) VALUES ('%s','%s','%s')"%(dictionary[9][1],dictionary[1][1],dictionary[2][1]+str(dictionary[3][1]))
				c.execute(q)
				conn.commit()

			except sqlite3.IntegrityError:
				print "The blockcorr %s is already used by another source"%(dictionary[1][1])

	geners_sql=pd.read_sql_query("SELECT source_nickname  FROM t2wellsource WHERE source_nickname like 'GEN%';",conn)
	
	list_preve_gener=[]

	for k in range(len(geners_sql)):
		list_preve_gener.append(str(geners_sql['source_nickname'].values[k]).replace("u",""))

	list_gener_on_model=[]
	for dictionary in geners:
		try:
		 	dictionary['empty'][0]==1
		except KeyError:
			list_gener_on_model.append(dictionary[2][1]+str(dictionary[3][1]))


	for j in list_preve_gener:
		if j not in list_gener_on_model:
			print j
			q="DELETE FROM  t2wellsource WHERE git remorte source_nickname='%s'"%(j)
			c.execute(q)
			conn.commit()

	conn.close()

db_path='../input/model.db'


type_flow="constant" # "constant" "shutdown" "invariable"

write_gener_from_sqlite(db_path,wells,type_flow)
#write_geners_to_txt_and_sqlite(db_path,geners)