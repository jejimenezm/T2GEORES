import geometry as geomtr
from model_conf import *
import sqlite3
import pandas as pd
from datetime import datetime
import numpy as  np
from scipy import interpolate
from model_conf import input_data

db_path=input_data['db_path']

def observations_to_it2_PT(db_path=db_path,wells=input_data['WELLS'],T_DEV=input_data['IT2']['T_DEV'],P_DEV=input_data['IT2']['P_DEV']):
	"""Genera archivo "../model/it2/observations_PT.dat"

	Parameters
	----------
	db_path : str
	  Direccion de base de datos sqlite, tomado de model_conf
	wells : array
	  Arreglo con nombre de pozos a ser incluidos, tomado de model_conf
	T_DEV  : float
	  Desviacion a considerar para las mediciones de temperatura, normalmente 5.0 [C]
	P_DEV : float
	  Desviacion a considerar para las mediciones de presion, sugerido 10 [bar]

	Returns
	-------
	file
	  observations_PT.dat: Archivo con observaciones de temperatura y presion en tipo 0 de corrida

	Attention
	---------
	La fuente de informacion es la base de datos sqlite

	Examples
	--------
	>>> observations_to_it2_PT(db_path,wells,5,10)
	"""
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
				x_V,y_V,z_V,var_V=geomtr.MD_to_TVD_one_var_array(name,T_md,md,100)
				func_T=interpolate.interp1d(z_V,var_V)

			try:
				if func_T(middle_tvd[tvdn])>0:
					string_T+="""
			>>> ELEMENT : %s
				>>>> ANNOTATION : %s-T-%s
				>>>> DEVIATION  : %s
				>>>> WINDOW     : 0.0 60.0 [SECONDS]
				>>>> DATA
						 0 %s
				<<<<\n"""%(corr_layer[tvdn]+blockcorr,corr_layer[tvdn]+blockcorr,name,T_DEV,func_T(middle_tvd[tvdn]))
			except ValueError:
				pass

			if not np.isnan(np.mean(P_md)) and np.mean(P_md)>0:
				x_V,y_V,z_V,var_V=geomtr.MD_to_TVD_one_var_array(name,P_md,md,100)
				func_P=interpolate.interp1d(z_V,var_V)

				try:
					if func_P(middle_tvd[tvdn])>1.0:
						string_P+="""
			>>> ELEMENT : %s
				>>>> ANNOTATION : %s-P-%s
				>>>> FACTOR     : 1.0E5 [bar] - [Pa]
				>>>> DEVIATION  : %s
				>>>> WINDOW     : 0.0 60.0 [SECONDS]
				>>>> DATA
					    0 %s
				<<<<\n"""%(corr_layer[tvdn]+blockcorr,corr_layer[tvdn]+blockcorr,name,P_DEV,func_P(middle_tvd[tvdn]))
				except ValueError:
					pass

	string_T+="		<<<\n"
	string_P+="		<<<\n"
	string+=string_T
	string+=string_P
	observation_file=open("../model/it2/observations_PT.dat",'w')
	observation_file.write(string)
	observation_file.close()

def observations_to_it2_h(db_path=db_path,wells=input_data['WELLS'],h_DEV=input_data['IT2']['h_DEV']):
	"""Genera archivo "../model/it2/observations_h.dat"

	Parameters
	----------
	db_path : str
	  Direccion de base de datos sqlite, tomado de model_conf
	wells : array
	  Arreglo con nombre de pozos a ser incluidos, tomado de model_conf
	h_DEV :float
	  Desviacion a considerar para las mediciones de entapia, sugerido 200 [kJ/kg]

	Returns
	-------
	file
	  observations_h.dat: Archivo con observaciones de entalpia a lo largo del tiempo

	Attention
	---------
	La fuente de informacion es la base de datos sqlite y referenciados al tiempo 0 (ref_date de model_conf)

	Examples
	--------
	>>> observations_to_it2_h(db_path,wells,200)
	"""
	conn=sqlite3.connect(db_path)
	c=conn.cursor()
	ref_date=input_data['ref_date']

	string="	>>ENTHALPY\n"

	for name in sorted(wells):

		#X and Z is reserved to new well, which do not have a real flow or enthalpy
		q_source="SELECT source_nickname FROM t2wellsource WHERE well='%s'"%name
		c.execute(q_source)
		rows=c.fetchall()
		for row in rows:
			source_nickname=row[0]

		data=pd.read_sql_query("SELECT flowing_enthalpy, date_time,(steam_flow+liquid_flow) as flow FROM mh WHERE well='%s' ORDER BY date_time;"%name,conn)

		dates_func=lambda datesX: datetime.strptime(datesX, "%Y-%m-%d %H:%M:%S")
		#Read file cooling
		dates=list(map(dates_func,data['date_time']))

		if len(dates)>0:
			if (min(dates)-ref_date).total_seconds()<0:
				min_window=0
			else:
				min_window=(min(dates)-ref_date).total_seconds()
			string+="""		>>>SINK: %s
			>>>> ANNOTATION: %s-FLOWH
			>>>> FACTOR    : 1000 [kJ/kg] - [J/kg]
			>>>> DEVIATION : %s   [kJ/kg]
			>>>> WINDOW     : %s %s [SECONDS]
			>>>> DATA\n"""%(source_nickname,name,h_DEV,min_window,(max(dates)-ref_date).total_seconds())

			for n in range(len(dates)):
				timex=(dates[n]-ref_date).total_seconds()
				if data['flowing_enthalpy'][n]>0 and data['flow'][n]>0 :
					string_x="				 %s 	%6.3E\n"%(timex,data['flowing_enthalpy'][n])
					string+=string_x
			string+="			<<<<\n"
	string+="""		<<<\n"""

	observation_file_h=open("../model/it2/observations_h.dat",'w')
	observation_file_h.write(string)
	observation_file_h.close()

def observations_to_it2_DD(db_path=db_path,wells=input_data['WELLS'],P_DEV=input_data['IT2']['P_DEV'],include_pres=False,p_res_block=None):
	"""Genera archivo "../model/it2/observations_dd.dat"

	Parameters
	----------
	db_path : str
	  Direccion de base de datos sqlite, tomado de model_conf
	wells : array
	  Arreglo con nombre de pozos a ser incluidos, tomado de model_conf
	P_DEV : float
	  Desviacion a considerar para las mediciones de presion, sugerido 10 [bar]

	Returns
	-------
	file
	  observations_dd.dat: Archivo con observaciones de caida de presion a lo largo del tiempo

	Attention
	---------
	La fuente de informacion es la base de datos sqlite y referenciados al tiempo 0 (ref_date de model_conf)

	Examples
	--------
	>>> observations_to_it2_DD(db_path,wells,10)
	"""

	conn=sqlite3.connect(db_path)
	c=conn.cursor()
	ref_date=input_data['ref_date']

	string="	>>DRAWDOWN"

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
		>>> ELEMENT: %s
			>>>> ANNOTATION: %s-DD-%s
			>>>> FACTOR     : 1.0E5 [bar] - [Pa]
			>>>> DEVIATION  : %s [bar]
			>>>> DATA\n"""%(block,name,row[0],P_DEV)

					for n in range(len(dates)):
						timex=(dates[n]-ref_date).total_seconds()
						string_x="				 %s 	%6.3E\n"%(timex,data['pressure'][n])
						string+=string_x
					string+="""			<<<<\n"""
	

	#iTOUGH2 de presion de reservorio

	if include_pres:
		pres_data=pd.read_csv("../input/drawdown/p_res.csv",delimiter=';')
		dates_func_res=lambda datesX: datetime.strptime(datesX, "%d/%m/%Y")
		dates_res=list(map(dates_func_res,pres_data['date']))
		string+="""
			>>> ELEMENT: %s
				>>>> ANNOTATION: RES
				>>>> FACTOR     : 1.0E5 [bar] - [Pa]
				>>>> DEVIATION  : %s [bar]
				>>>> DATA\n"""%(p_res_block,P_DEV)
		for n in range(len(dates_res)):
			timex=(dates_res[n]-ref_date).total_seconds()
			string_x="				 %s 	%6.3E\n"%(timex,pres_data['pres'][n])
			string+=string_x
		string+="""			<<<<\n"""
	
	string+="""		<<<\n"""

	observation_file_dd=open("../model/it2/observations_dd.dat",'w')
	observation_file_dd.write(string)
	observation_file_dd.close()

def observations_to_it2(db_path=db_path,wells=input_data['WELLS'],T_DEV=input_data['IT2']['T_DEV'],P_DEV=input_data['IT2']['P_DEV'],h_DEV=input_data['IT2']['h_DEV'],typer=input_data['TYPE_RUN']):
	"""Genera bloque OBSERVATION

	Parameters
	----------
	db_path : str
	  Direccion de base de datos sqlite, tomado de model_conf
	wells : array
	  Arreglo con nombre de pozos a ser incluidos, tomado de model_conf
	T_DEV  : float
	  Desviacion a considerar para las mediciones de temperatura, normalmente 5.0 [C]
	P_DEV : float
	  Desviacion a considerar para las mediciones de presion, sugerido 10 [bar]
	h_DEV :float
	  Desviacion a considerar para las mediciones de entapia, sugerido 200 [kJ/kg]
	typer :str
	  Tipo de corrida:  natural o prod

	Returns
	-------
	file
	  observations_PT.dat: Archivo con observaciones de temperatura y presion en tipo 0 de corrida
	file
	  observations_h.dat : archivo con entalpia de flujo a lo largo del tiempo
	file
	  observations_dd.dat : archivo con variacion de presion en elemento a lo largo del tiempo
	file
	  it2_ob_prod.dat : archivo que recopila observations_PT, observations_h y observations_dd en caso de selccionar corrida tipo 'prod'
	file
	  it2_ob_nat.dat : archivo que recopila observations_PT en caso de selccionar corrida tipo 'natural'


	Attention
	---------
	La fuente de informacion es la base de datos sqlite y referenciados al tiempo 0 (ref_date de model_conf)

	Examples
	--------
	>>> observations_to_it2(db_path,wells,5,10,200,'prod')
	"""
	if typer=='production':
		observations_to_it2_PT(db_path,wells,T_DEV,P_DEV)
		observations_to_it2_h(db_path,wells,h_DEV)
		observations_to_it2_DD(db_path,wells,P_DEV)
		filenames = ["../model/it2/observations_PT.dat","../model/it2/observations_h.dat","../model/it2/observations_dd.dat"]
		filename='it2_ob_prod'
	elif typer=='natural':
		observations_to_it2_PT(db_path,wells,T_DEV,P_DEV)
		filenames = ["../model/it2/observations_PT.dat"]
		filename='it2_ob_nat'
	with open("../model/it2/%s"%filename, 'w') as outfile:
		outfile.write(">OBSERVATION\n")
		for fname in filenames:
			with open(fname) as infile:
				for line in infile:
					outfile.write(line)
		outfile.write("""	<<\n""")
	outfile.close()

#Sostenibilidad Ahuachapan
#observations_to_it2()
#observations_to_it2_h()
#observations_to_it2_DD(include_pres=True,p_res_block='DA128')
#observations_to_it2_PT()