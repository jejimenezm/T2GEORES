import t2resfun as t2r
from model_conf import *
import sqlite3
import pandas as pd
from datetime import datetime
import numpy as  np
from scipy import interpolate


def observations_to_it2_PT(db_path,wells,T_DEV,P_DEV):
	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	q_layer="SELECT correlative,middle FROM layers"

	corr_layer=[]
	middle_tvd=[]

	c.execute(q_layer)
	rows=c.fetchall()
	for row in rows:
		corr_layer.append(row[0])
		middle_tvd.append(row[1])

	string=""
	string_T="""	>>TEMPERATURE"""
	string_P="""	>>PRESSURE"""

	for name in sorted(wells):

		q_corr="SELECT blockcorr FROM t2wellblock WHERE well='%s'"%(name)

		c.execute(q_corr)
		rows=c.fetchall()
		for row in rows:
			blockcorr=row[0]

		for tvdn in range(len(middle_tvd)):

			q_PT="SELECT MeasuredDepth, Pressure, Temperature from PT WHERE well='%s' ORDER BY MeasuredDepth"%name
			c.execute(q_PT)
			rows=c.fetchall()
			
			md=[]
			P_md=[]
			T_md=[]
			for row in rows:
				md.append(row[0])
				P_md.append(row[1])
				T_md.append(row[2])

			T_md= [np.nan if x == 0 else x for x in T_md]
			P_md= [np.nan if x == 0 else x for x in P_md]
			
			if not np.isnan(np.mean(T_md)):
				x_V,y_V,z_V,var_V=t2r.MD_to_TVD_one_var_array(name,T_md,md,100)
				func_T=interpolate.interp1d(z_V,var_V)

			try:
				string_T+="""
		>>> ELEMENT : %s
			>>>> ANNOTATION : %s-T-%s
			>>>> DEVIATION  : %s
			>>>> WINDOWS    : 0 2 [SECONDS]
			>>>> DATA
					 1 %s
			<<<<\n"""%(corr_layer[tvdn]+blockcorr,corr_layer[tvdn]+blockcorr,name,T_DEV,func_T(middle_tvd[tvdn]))
			except ValueError:
				pass

			if not np.isnan(np.mean(P_md)) and np.mean(P_md)>0:
				x_V,y_V,z_V,var_V=t2r.MD_to_TVD_one_var_array(name,P_md,md,100)
				func_P=interpolate.interp1d(z_V,var_V)

				try:
					string_P+="""
		>>> ELEMENT : %s
			>>>> ANNOTATION : %s-P-%s
			>>>> FACTOR     : 1.0E5 [bar] - [Pa]
			>>>> DEVIATION  : %s
			>>>> WINDOWS    : 0 2 [SECONDS]
			>>>> DATA
				 1 %s
			<<<<\n"""%(corr_layer[tvdn]+blockcorr,corr_layer[tvdn]+blockcorr,name,P_DEV,func_P(middle_tvd[tvdn]))
				except ValueError:
					pass

	string_T+="		<<<\n"
	string_P+="		<<<\n"
	string+=string_T
	string+=string_P
	observation_file=open('../model/it2/observations_PT.dat','w')
	observation_file.write(string)
	observation_file.close()

def observations_to_it2_h(db_path,wells,h_DEV):

	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	string="	>>ENTHALPY\n"

	for name in sorted(wells):
		q_source="SELECT source_nickname FROM t2wellsource WHERE well='%s'"%name
		c.execute(q_source)
		rows=c.fetchall()
		for row in rows:
			source_nickname=row[0]

		data=pd.read_sql_query("SELECT flowing_enthalpy, date_time FROM mh WHERE well='%s' ORDER BY date_time;"%name,conn)

		dates_func=lambda datesX: datetime.strptime(datesX, "%Y-%m-%d %H:%M:%S")
		#Read file cooling
		dates=list(map(dates_func,data['date_time']))

		if len(dates)>0:
			string+="""		>>>SINK: %s
			>>>> ANNOTATION: %s-FLOWH
			>>>> FACTOR    : 1000 [kJ/kg] - [J/kg]
			>>>> DEVIATION : %s   [kJ/kg]
			>>>> DATA\n"""%(source_nickname,name,h_DEV)

			for n in range(len(dates)):
				timex=(dates[n]-ref_date).total_seconds()
				string_x="				%s 	%6.3E\n"%(timex,data['flowing_enthalpy'][n])
				string+=string_x
			string+="			<<<<\n"
		else:
			string+="""		>>>SINK: %s
			>>>> ANNOTATION: %s-FLOWH
			>>>> NO DATA
			<<<<\n"""%(source_nickname,name)

	string+="""		<<<\n"""

	observation_file_h=open('../model/it2/observations_h.dat','w')
	observation_file_h.write(string)
	observation_file_h.close()

def observations_to_it2_DD(db_path,wells,P_DEV):

	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	string="	>>DRAWDOWN:"

	for name in sorted(wells):
		q0="SELECT DISTINCT TVD from drawdown WHERE well='%s'"%name
		c.execute(q0)
		rows=c.fetchall()
		for row in rows:
			q1="SELECT correlative FROM layers WHERE middle=%s"%row[0]
			c.execute(q1)
			rows_corr=c.fetchall()
			if len(rows_corr)>0:
				q2="SELECT blockcorr FROM t2wellblock WHERE well='%s'"%name
				c.execute(q2)
				rows_bkc=c.fetchall()
				for row2 in rows_bkc:
					block=rows_corr[0][0]+row2[0]

				data=pd.read_sql_query("SELECT date_time, pressure FROM drawdown WHERE well='%s' AND TVD=%s ORDER BY date_time;"%(name,row[0]),conn)
				
				dates_func=lambda datesX: datetime.strptime(datesX, "%Y-%m-%d %H:%M:%S")
				#Read file cooling
				dates=list(map(dates_func,data['date_time']))

				if len(dates)>0:
					string+="""
		>>> ELEMENT: %s-P
			>>>> ANNOTATION: %s-DD-%s
			>>>> FACTOR     : 1.0E5 [bar] - [Pa]
			>>>> DEVIATION  : %s [bar]
			>>>> DATA\n"""%(block,name,row[0],P_DEV)

					for n in range(len(dates)):
						timex=(dates[n]-ref_date).total_seconds()
						string_x="				%s 	%6.3E\n"%(timex,data['pressure'][n])
						string+=string_x
	string+="""		<<<\n"""

	observation_file_dd=open('../model/it2/observations_dd.dat','w')
	observation_file_dd.write(string)
	observation_file_dd.close()

def observations_to_it2(db_path,wells,T_DEV,P_DEV,h_DEV,typer):
	if typer=='prod':
		observations_to_it2_PT(db_path,wells,T_DEV,P_DEV)
		observations_to_it2_h(db_path,wells,h_DEV)
		observations_to_it2_DD(db_path,wells,P_DEV)
		filenames = ['../model/it2/observations_PT.dat','../model/it2/observations_h.dat','../model/it2/observations_dd.dat']
		filename='it2_ob_prod'
	elif typer=='natural':
		observations_to_it2_PT(db_path,wells,T_DEV,P_DEV)
		filenames = ['../model/it2/observations_PT.dat']
		filename='it2_ob_nat'

	with open('../model/it2/%s'%filename, 'w') as outfile:
		outfile.write(">OBSERVATION\n")
		for fname in filenames:
			with open(fname) as infile:
				for line in infile:
					outfile.write(line)
		outfile.write("""	<<\n""")
	outfile.close()

T_DEV=5
P_DEV=10
h_DEV=200
typer='natural' # natural, prod
db_path='../input/model.db'
observations_to_it2(db_path,wells,T_DEV,P_DEV,h_DEV,typer)

