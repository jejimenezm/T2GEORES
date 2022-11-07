from T2GEORES import geometry as geomtr
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import numpy as  np
from scipy import interpolate
import locale
locale.setlocale(locale.LC_TIME, 'en_US.utf8')
import matplotlib.pyplot as plt
#plt.style.use('T2GEORES')

def observations_to_it2_PT(input_dictionary):
	"""It generates the observation section for the iTOUGH2 file, coming from formation temperature and pressure

	Parameters
	----------
	input_dictionary : dictionary
	  A dictionary containing the standard deviation allowed for the temperature (in C) and pressure (in bar). The name and path of the database and a list of the wells for calibration. e.g. 'IT2':{'T_DEV':5,'P_DEV':10}

	Returns
	-------
	file
	  observations_PT.dat: on ../model/it2 , assuming the model is run for on a steady state and transient starts on time 0, the observation are stablished at time zero.

	Attention
	---------
	The input data comes from sqlite

	Examples
	--------
	>>> observations_to_it2_PT(input_dictionary)
	"""


	#Preparing input data
	db_path=input_dictionary['db_path']

	source_txt=input_dictionary['source_txt']
	
	t2_ver=float(input_dictionary['VERSION'][0:3])
	ref_date = input_dictionary['ref_date']
	ref_date_f = (ref_date - timedelta(minutes = 30)).strftime("%d-%b-%Y_%H:%M:%S")
	ref_date_f0 = ref_date.strftime("%d-%b-%Y")
	ref_date_fi = (ref_date + timedelta(minutes = 30)).strftime("%d-%b-%Y_%H:%M:%S")

	layers=geomtr.vertical_layers(input_dictionary)


	types=['WELLS','MAKE_UP_WELLS','NOT_PRODUCING_WELL']
	wells=[]
	for scheme in types:
		try:
			for well in input_dictionary[scheme]:
				wells.append(well)
		except KeyError:
				pass

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
	string_T="""	>> TEMPERATURE"""
	string_P="""	>> PRESSURE"""

	T0=input_dictionary['INCONS_PARAM']['To']
	cut_off_T=input_dictionary['INCONS_PARAM']['CUT_OFF_T_TOP']

	P0=input_dictionary['INCONS_PARAM']['Po']
	cut_off_P=input_dictionary['INCONS_PARAM']['CUT_OFF_P_TOP']

	#This blocks creates a linear interpolation on every layer depth with the formation temperature and pressure
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
			

			if corr_layer[tvdn] in [layers['name'][0],layers['name'][-1]]:
				T_DEV = 9.99E3 
				P_DEV = 9.99E3
			else:
				T_DEV = input_dictionary['IT2']['T_DEV']
				P_DEV = input_dictionary['IT2']['P_DEV']

			if not np.isnan(np.mean(T_md)):
				x_V,y_V,z_V,var_V=geomtr.MD_to_TVD_one_var_array(name,T_md,md)
				func_T=interpolate.interp1d(z_V,var_V)

			try:
				if func_T(middle_tvd[tvdn])>0:
					Ti=func_T(middle_tvd[tvdn])
					if corr_layer[tvdn]=='A':
						if Ti>cut_off_T:
							Ti=cut_off_T
						elif Ti<T0:
							Ti=T0

					string_T+="""
		>>> ELEMENT : %s
			>>>> ANNOTATION : %s-T-%s
			>>>> DEVIATION  : %.2f"""%(corr_layer[tvdn]+blockcorr,corr_layer[tvdn]+blockcorr,name,T_DEV)
			
					if t2_ver<7:
						string_T+="""
			>>>> WINDOW     : 0.0 60.0 [SECONDS]
			>>>> DATA
				 0 %.2f
			<<<<\n"""%Ti
					else:
						string_T+="""
			>>>> WINDOW     : %s	%s [DATES]
			>>>> DATA DATES
				 %s	%.2f
			<<<<\n"""%(ref_date_f,ref_date_fi, ref_date_f0, Ti)

			except ValueError:
				pass


			if not np.isnan(np.mean(P_md)) and np.mean(P_md)>0:
				x_V,y_V,z_V,var_V=geomtr.MD_to_TVD_one_var_array(name,P_md,md)
				func_P=interpolate.interp1d(z_V,var_V)

				try:
					if func_P(middle_tvd[tvdn])>0.0:
						Pi=func_P(middle_tvd[tvdn])
						if corr_layer[tvdn]=='A':
							if Pi>cut_off_P:
								Pi=cut_off_P+0.92
							elif Pi<P0:
								Pi=P0+0.92

						string_P+="""
		>>> ELEMENT : %s
			>>>> ANNOTATION : %s-P-%s
			>>>> FACTOR     : 1.0E5 [bar] - [Pa]
			>>>> DEVIATION  : %.2f"""%(corr_layer[tvdn]+blockcorr,corr_layer[tvdn]+blockcorr,name,P_DEV)
						if t2_ver<7:
							string_P+="""
			>>>> WINDOW     : 0.0 60.0 [SECONDS]
			>>>> DATA
				 0 %2.f
			<<<<"""%Pi
						else:
							string_P+="""
			>>>> WINDOW     : %s	%s [DATES]
			>>>> DATA DATES
				 %s	%.2f
			<<<<\n"""%(ref_date_f,ref_date_fi, ref_date_f0, Pi)


				except ValueError:
					pass

	string_T+="		<<<\n"
	string_P+="		<<<\n"
	string+=string_T
	string+=string_P
	observation_file=open("../model/it2/observations_PT.dat",'w')
	observation_file.write(string)
	observation_file.close()

def observations_to_it2_h(input_dictionary, dates_format = True):
	"""It generates the flowing enthalpy observation section for the iTOUGH2 file

	Parameters
	----------
	input_dictionary : dictionary
	  A dictionary containing the standard deviation allowed for the flowing enthalpy in kJ/kg, a reference date on datetime format and the name and path of the database a list of the wells for calibration. e.g. 'IT2':{'h_DEV':100},

	Returns
	-------
	file
	  observations_h.dat: on ../model/it2 , the time for every observation is calculated by finding the difference  in seconds from a defined reference time

	Attention
	---------
	The input data comes from sqlite

	Examples
	--------
	>>> observations_to_it2_h(input_dictionary)
	"""

	#Preparing input data
	h_DEV=input_dictionary['IT2']['h_DEV']
	db_path=input_dictionary['db_path']
	ref_date=input_dictionary['ref_date']
	source_txt=input_dictionary['source_txt']

	t2_ver=float(input_dictionary['VERSION'][0:3])

	types=['WELLS','MAKE_UP_WELLS','NOT_PRODUCING_WELL']
	wells=[]
	for scheme in types:
		try:
			for well in input_dictionary[scheme]:
				wells.append(well)
		except KeyError:
				pass

	conn=sqlite3.connect(db_path)
	c=conn.cursor()
	
	string="	>> ENTHALPY\n"

	for name in sorted(wells):

		#data=pd.read_sql_query("SELECT type, flowing_enthalpy, date_time,(steam_flow+liquid_flow) as flow FROM mh WHERE well='%s' ORDER BY date_time;"%name,conn)

		data=pd.read_sql_query("SELECT type, flowing_enthalpy, date_time,(steam_flow+liquid_flow) as flow FROM mh WHERE well='%s' and substr(date_time,9,2) IN ('15') ORDER BY date_time;"%name,conn)

		dates_func=lambda datesX: datetime.strptime(datesX, "%Y-%m-%d_%H:%M:%S")

		dates=list(map(dates_func,data['date_time']))

		if len(dates)>0 and data[data.type == 'P'].shape[0]>0:

			if t2_ver>7 and dates_format:
				time_type = '[DATES]'
				max_window = max(dates)
				min_window=min(dates)
				if (min(dates)-ref_date).total_seconds()<0:
					min_window=ref_date
				else:
					min_window = min(dates)
			elif t2_ver<7 or not dates_format: 
				time_type = '[SECONDS]'
				max_window = (max(dates)-ref_date).total_seconds()
				if (min(dates)-ref_date).total_seconds()<0:
					min_window=(min(dates)-ref_date).total_seconds()
				else:
					min_window = 0


			data_s = pd.read_sql_query("SELECT well, blockcorr, source_nickname FROM t2wellsource WHERE flow_type = 'P' AND well = '%s'"%name, conn)

			string += "		>>> SINK: "
			for source in data_s['source_nickname'].tolist():
				string += "%s "%source

			string+="""
			>>>> ANNOTATION: %s-FLOWH
			>>>> FACTOR    : 1000 [kJ/kg] - [J/kg]
			>>>> DEVIATION : %s   [kJ/kg]
			>>>> DATA %s \n"""%(name,h_DEV, time_type)

			for n in range(len(dates)):
				if t2_ver>7 and dates_format:
					timex=dates[n].strftime("%d-%b-%Y_%H:%M:%S")
				elif t2_ver<7 or not dates_format: 
					timex=(dates[n]-ref_date).total_seconds()

				if data['flowing_enthalpy'][n]>0 and data['flow'][n]>0 :
					string_x="				 %s 	%0.2f\n"%(timex  ,data['flowing_enthalpy'][n])
					string+=string_x
			string+="			<<<<\n"
	string+="""		<<<\n"""

	observation_file_h=open("../model/it2/observations_h.dat",'w')
	observation_file_h.write(string)
	observation_file_h.close()

def observations_to_it2_DD(input_dictionary,obs_info,include_pres=False,p_res_block=None, include_wells = True, dates_format = True, show_plot = False):
	"""It generates the drawdown observation section for the iTOUGH2 file
	
	Parameters
	----------
	input_dictionary : dictionary
	  A dictionary containing the standard deviation allowed for the flowing enthalpy in kJ/kg, a reference date on datetime format and the name and path of the database a list of the wells for calibration. e.g. 'IT2':{P_DEV':5}
	include_pres : bool
	  If True a special file is read: '../input/drawdown/p_res.csv' which contains the long history of pressure fluctuation.
	p_res_block : str
	  Block name at which monitoring pressure data is recorded
	obs_info : dictionary
	  Includes well name as keyword and an array with [TVD, layer_correlative]
	include_wells : bool
	  If True includes well drawdown include on obs_info, default : True
	dates_format : bool
	  In case SECONDS are prefered on the DATA section, default : True


	Returns
	-------
	file
	  observations_dd.dat: on ../model/it2 , the time for every observation is calculated by finding the difference in seconds from a defined reference time

	Attention
	---------
	The input data comes from sqlite

	Examples
	--------
	>>> observations_to_it2_DD(input_dictionary)
	"""

	#Preparing input data
	h_DEV=input_dictionary['IT2']['h_DEV']
	db_path=input_dictionary['db_path']
	ref_date=input_dictionary['ref_date']
	source_txt=input_dictionary['source_txt']
	P_DEV=2.0 #input_dictionary['IT2']['P_DEV']
	t2_ver=float(input_dictionary['VERSION'][0:3])

	raw_source = False
	
	types=['WELLS','MAKE_UP_WELLS','NOT_PRODUCING_WELL']
	wells=[]
	for scheme in types:
		try:
			for well in input_dictionary[scheme]:
				wells.append(well)
		except KeyError:
				pass

	conn=sqlite3.connect(db_path)
	c=conn.cursor()


	if t2_ver>7 and dates_format:
		time_type = '[DATES]'
	elif t2_ver<7 or not dates_format: 
		time_type = '[SECONDS]'


	string="	>> DRAWDOWN"

	if include_wells:

		for well in sorted(obs_info):

			data_w= pd.DataFrame(columns = ['date_time', 'pressure'])

			corr=pd.read_sql_query("SELECT correlative FROM layers WHERE middle=%s"%obs_info[well][0],conn)

			blockcorr=pd.read_sql_query("SELECT blockcorr FROM t2wellblock WHERE well='%s'"%well,conn)

			block=str(corr.values[0][0])+str(blockcorr.values[0][0])

			data=pd.read_sql_query("SELECT date_time, pressure FROM drawdown WHERE well='%s' AND TVD=%s ORDER BY date_time;"%(well,obs_info[well][0]),conn)

			dates_func=lambda datesX: datetime.strptime(datesX, "%Y-%m-%d %H:%M:%S")
			#Read file cooling
			dates=list(map(dates_func,data['date_time']))


			data_PT=pd.read_sql_query("SELECT MeasuredDepth, Pressure, Temperature from PT WHERE well='%s' ORDER BY MeasuredDepth"%well, conn)

			data_PT.replace(0, np.nan, inplace=True)

			if not np.isnan(np.mean(data_PT['Pressure'])):
				x_V,y_V,z_V,var_V=geomtr.MD_to_TVD_one_var_array(well,data_PT['Pressure'],data_PT['MeasuredDepth'])
				func_P=interpolate.interp1d(z_V,var_V)

				P0 = (func_P(obs_info[well][0])+0.92)*1E5

				data_i = {'pressure':P0, 'date_time': ref_date}
				data_w = data_w.append(data_i, ignore_index = True)

			if len(dates)>0 and any(data['pressure']-P0 < 0):
				string+="""
		>>> ELEMENT: %s
			>>>> ANNOTATION: %s-DD-%s
			>>>> FACTOR     : 1.0E5 [bar] - [Pa]
			>>>> DEVIATION  : %s [bar]
			>>>> DATA %s\n"""%(block,well,obs_info[well][0],P_DEV, time_type)

				for n in range(len(dates)):

					if t2_ver>7 and dates_format:
						timex=dates[n]

					elif t2_ver<7 or not dates_format: 
						timex=(dates[n]-ref_date).total_seconds()

					if data['pressure'][n]*1E5 < P0:

						data_i = {'pressure':data['pressure'][n]*1E5 , 'date_time': timex}
						data_w = data_w.append(data_i, ignore_index = True)


			if len(data_w)>1:

				for index, row in data_w.iterrows():
					string_x="				 %s 	%6.3E\n"%(row['date_time'].strftime("%d-%b-%Y_%H:%M:%S"),row['pressure']-P0)
					string+=string_x

				data_w.drop_duplicates(inplace = True)
				data_w['date_time'] = pd.to_datetime(data_w['date_time'] , format="%d-%b-%Y %H:%M:%S")
				data_w.index = data_w['date_time']
				del data_w['date_time']
				data_resample= data_w.resample('D')

				interpolated = data_resample.interpolate(method='linear')

				if show_plot:
					fig, ax = plt.subplots()
					l1 =ax.plot(interpolated,label=well, lw=0, marker = 'o', ms = 0.5, linestyle = 'None')
					ax.plot(data_w, marker = 'o', color = l1[0].get_color(), lw= 0)
					ax.set_title(well)
					plt.show()

	if include_wells and raw_source:
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
	
	print(string)
	#iTOUGH2 reservoir pressure


	#observation_file_dd=open("../model/it2/observations_dd.dat",'w')
	#observation_file_dd.write(string)
	#observation_file_dd.close()

def observations_to_it2(input_dictionary,include_pres=False,p_res_block=None):
	"""It generates the section OBSERVATION from iTOUGH2 input file with pressure, temperature, flowing enthalpy and drawdown data.
	
	Parameters
	----------
	input_dictionary : dictionary
	  A dictionary containing:the standard deviation allowed for the temperature (in C), pressure (in bar) and flowing enthalpy (in kJ/kg).
	  The name and path of the database a list of the wells for calibration and finally the type of run ('natural' or 'production') e.g. input_dictionary={'TYPE_RUN':'production','IT2':{'T_DEV':5,'P_DEV':10,'h_DEV':100}}
	include_pres : bool
	  If True a special file is read: '../input/drawdown/p_res.csv' which contains the long history of pressure fluctuation.
	p_res_block : str
	  Block name at which monitoring pressure data is recorded

	Returns
	-------
	file
	  observations_PT.dat: on ../model/it2 , assuming the model is run for on a steady state and transient starts on time 0, the observation are stablished at time zero.
	file
	  observations_h.dat: on ../model/it2 , the time for every observation is calculated by finding the difference  in seconds from a defined reference time
	file
	  observations_dd.dat: on ../model/it2 , the time for every observation is calculated by finding the difference in seconds from a defined reference time
	file
	  it2_ob_prod.dat : it compiles the information during the transient stage. This is when time is higher than zero
	file
	  it2_ob_nat.dat : it compiles the information at time zero.

	Attention
	---------
	The input data comes from sqlite

	Examples
	--------
	>>> observations_to_it2(input_dictionary)
	"""

	type_run=input_dictionary['TYPE_RUN']
	if type_run=='production':
		observations_to_it2_PT(db_path,wells,T_DEV,P_DEV)
		observations_to_it2_h(db_path,wells,h_DEV)
		observations_to_it2_DD(db_path,wells,P_DEV)
		filenames = ["../model/it2/observations_PT.dat","../model/it2/observations_h.dat","../model/it2/observations_dd.dat"]
		filename='it2_ob_prod'
	elif type_run=='natural':
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


def observations_delta_it2_filtered(input_dictionary,obs_info):
	"""It generates the drawdown observation section for the iTOUGH2 file
	
	Parameters
	----------
	input_dictionary : dictionary
	  A dictionary containing the standard deviation allowed for the flowing enthalpy in kJ/kg, a reference date on datetime format and the name and path of the database a list of the wells for calibration. e.g. 'IT2':{P_DEV':5}
	include_pres : bool
	  If True a special file is read: '../input/drawdown/p_res.csv' which contains the long history of pressure fluctuation.
	p_res_block : str
	  Block name at which monitoring pressure data is recorded

	Returns
	-------
	file
	  observations_dd.dat: on ../model/it2 , the time for every observation is calculated by finding the difference in seconds from a defined reference time

	Attention
	---------
	The input data comes from sqlite

	Examples
	--------
	>>> observations_to_it2_DD(input_dictionary)
	"""

	#Preparing input data
	db_path=input_dictionary['db_path']
	ref_date=input_dictionary['ref_date']
	source_txt=input_dictionary['source_txt']

	T_DEV=input_dictionary['IT2']['T_DEV']
	P_DEV=input_dictionary['IT2']['P_DEV']

	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	string="	>>DELTA (PRESSURE)"

	for name in sorted(obs_info):


		corr=pd.read_sql_query("SELECT correlative FROM layers WHERE middle=%s"%obs_info[name][0],conn)

		blockcorr=pd.read_sql_query("SELECT blockcorr FROM t2wellblock WHERE well='%s'"%name,conn)

		block=str(corr.values[0][0])+str(blockcorr.values[0][0])

		data=pd.read_sql_query("SELECT date_time, pressure FROM drawdown WHERE well='%s' AND TVD=%s ORDER BY date_time;"%(name,obs_info[name][0]),conn)

		dates_func=lambda datesX: datetime.strptime(datesX, "%Y-%m-%d %H:%M:%S")
		#Read file cooling
		dates=list(map(dates_func,data['date_time']))


		data_PT=pd.read_sql_query("SELECT MeasuredDepth, Pressure, Temperature from PT WHERE well='%s' ORDER BY MeasuredDepth"%name, conn)

		data_PT.replace(0, np.nan, inplace=True)

		if not np.isnan(np.mean(data_PT['Pressure'])):
			x_V,y_V,z_V,var_V=geomtr.MD_to_TVD_one_var_array(name,data_PT['Pressure'],data_PT['MeasuredDepth'])
			func_P=interpolate.interp1d(z_V,var_V)

			P0 = (func_P(obs_info[name][0])+0.92)*1E5


		if len(dates)>0:
			string+="""
		>>> ELEMENT: %s
			>>>> ANNOTATION: %s-DD-%s
			>>>> REFERENCE P: %.1f
			>>>> SHIFT : 	  -%.1f
			>>>> FACTOR     : 1.0E5 [bar] - [Pa]
			>>>> DEVIATION  : %s [bar]
			>>>> DATA\n"""%(block,name,obs_info[name][0],P0,P0,P_DEV)

			for n in range(len(dates)):
				timex=(dates[n]-ref_date).total_seconds()
				if timex>0 and data['pressure'][n]*1E5 < P0:
					string_x="				 %s 	%6.3E\n"%(timex,data['pressure'][n])
					string+=string_x
			string+="""			<<<<\n"""

	observation_file_dd=open("../model/it2/delta_dd.dat",'w')
	observation_file_dd.write(string)
	observation_file_dd.close()

def it2_weighted_h(input_dictionary):


	types=['WELLS','MAKE_UP_WELLS','NOT_PRODUCING_WELL']
	wells_m=[]
	for scheme in types:
		try:
			for well in input_dictionary[scheme]:
				wells_m.append(well)
		except KeyError:
				pass

	string_h = """	>> ENTHALPY\n"""
	string_r = """	>> GENERATION\n"""

	db_path=input_dictionary['db_path']
	conn=sqlite3.connect(db_path)

	data = pd.read_sql_query("SELECT well, blockcorr, source_nickname FROM t2wellsource WHERE flow_type = 'P'", conn)

	string_h += "		>>> SINK: "
	for source in data['source_nickname'].tolist():
		string_h += "%s "%source
	string_h += "\n"
	string_h += "			>>>> ANNOTATION: PROD_FLOWH\n"
	string_h += "			>>>> NO DATA\n"
	string_h += "			<<<< \n"


	string_r += "		>>> SINK: "
	for source in data['source_nickname'].tolist():
		string_r += "%s "%source
	string_r += "\n"
	string_r += "			>>>> ANNOTATION: PROD_FLOWR\n"
	string_r += "			>>>> NO DATA\n"
	string_r += "			<<<< \n"


	wells = data['well'].unique().tolist()

	for well in wells:
		if well in wells_m:
			sources_i = data.loc[data['well'] == well, 'source_nickname'].tolist()
			
			if len(sources_i) > 1:
				string_h += "		>>> SINK: "
				for source in sources_i:
					string_h += "%s "%source
				string_h += "\n"
				string_h += "			>>>> ANNOTATION: %s-FLOWHW\n"%well
				string_h += "			>>>> NO DATA\n"
				string_h += "			<<<< \n"


				string_r += "		>>> SINK: "
				for source in sources_i:
					string_r += "%s "%source
				string_r += "\n"
				string_r += "			>>>> ANNOTATION: %s-FLOWHR\n"%well
				string_r += "			>>>> NO DATA\n"
				string_r += "			<<<< \n"

	string_r += "		<<< \n"

	string_r += '\n'+string_h

	weighted_file_h=open("../model/it2/weighted_file_hr.dat",'w')
	weighted_file_h.write(string_r)
	weighted_file_h.close()

def observations_to_it2_POWER(input_dictionary, dates_format = True):

	t2_ver=float(input_dictionary['VERSION'][0:3])

	if t2_ver>7 and dates_format:
		time_type = '[DATES]'
	elif t2_ver<7 or not dates_format: 
		time_type = '[SECONDS]'


	gen_data = pd.read_csv("../input/generation_data.csv",delimiter=',')

	gen_data = gen_data.sort_values(by ='fecha' )

	gen_data['fecha'] = pd.to_datetime(gen_data['fecha'] , format="%Y%m%d")

	PW_DEV_res = 3.0

	string = "  >> POWER"

	string+="""
	>>> SINK: 
		>>>> ANNOTATION: UNIT1&2
		>>>> FACTOR : 2.1 [MW] - [kg/s]
		>>>> REAL   : 12.0E5 [Pa]
		>>>> DEVIATION  : %s
		>>>> DATA %s\n"""%( PW_DEV_res, time_type)

	gen_data_u12 = gen_data.loc[ ((gen_data.unidad == 'u1') | (gen_data.unidad == 'u2')) & (gen_data.generation > 0), ['generation','fecha','unidad']]

	gen_data_u12 = gen_data_u12.groupby(['fecha']).sum()
	gen_data_u12['fecha'] = gen_data_u12.index
	gen_data_u12 = gen_data_u12.reset_index(drop=True)

	for n, row in gen_data_u12.iterrows():
		if n%10 == 0:
			if t2_ver>7 and dates_format:
				timex=row['fecha'].strftime("%d-%b-%Y_%H:%M:%S")
			elif t2_ver<7 or not dates_format: 
				timex=(row['fecha'] - ref_date).total_seconds()

			string_x="				 %s 	%6.3E\n"%(timex,row['generation'])

			string+=string_x
	string+="""			<<<<\n"""


	string+="""
	>>> SINK: 
		>>>> ANNOTATION: UNIT3
	    >>>> FACTOR : 2.4 [MW] - [kg/s]
	    >>>> REAL   : 9.0E5 [Pa]
	    >>>> DEVIATION  : %s
		>>>> DATA %s\n"""%( PW_DEV_res, time_type)

	gen_data_u3 = gen_data.loc[ (gen_data.unidad == 'u3') & (gen_data.generation > 0), ['generation','fecha','unidad']]
	gen_data_u3 = gen_data_u3.reset_index(drop=True)

	for n, row in gen_data_u3.iterrows():
		if n%10 == 0:
			if t2_ver>7 and dates_format:
				timex=row['fecha'].strftime("%d-%b-%Y_%H:%M:%S")
			elif t2_ver<7 or not dates_format: 
				timex=(row['fecha'] - ref_date).total_seconds()

			string_x="				 %s 	%6.3E\n"%(timex,row['generation'])

			string+=string_x
	string+="""			<<<<\n"""

	string+="""		<<<\n"""

	observation_file_power=open("../model/it2/observations_power.dat",'w')
	observation_file_power.write(string)
	observation_file_power.close()

def observation_pres(input_dictionary,use_formation=False):

	string = ""

	pres_data = pd.read_csv("../input/field_data.csv",delimiter=',')

	pres_data = pres_data.sort_values(by ='fecha')

	pres_data = pres_data.loc[pres_data['prs1'] > 0,['prs1','fecha']]

	dates_func_res=lambda datesX: datetime.strptime(str(datesX), "%Y%m%d")

	dates_res=list(map(dates_func_res,pres_data['fecha']))

	pres_data['dates'] = dates_res

	P_DEV_res = 1.0

	time_type = 'DATES'


	monitoring_wells = {'TR-4':{'dates':[
								   [datetime(1992,2,1,0,0,0),datetime(2010,7,21,0,0,0)],
								   [datetime(2018,10,25,0,0,0),datetime(2019,12,31,0,0,0)]
								   ],
							'feedzone':'NA746'},
					 'TR-3':{'dates':[
							 		  [datetime(2013,3,22,0,0,0),datetime(2016,2,7,0,0,0)],
							         ],
							 'feedzone':'LD367'
							 },
					 'TR-12A':{
					 		'dates': [
							 		  [datetime(2010,7,21,0,0,0),datetime(2013,3,21,0,0,0)],
							 		 ],
							 'feedzone':'OA135'},
					 'TR-4A':{
					 		'dates':[
							 			[datetime(2020,1,1,0,0,0),datetime(2022,2,15,0,0,0)],
							 		],
							 'feedzone':'NA170'},
			}

	fig, ax = plt.subplots(figsize=(10,4))

	for well in monitoring_wells:
		for i, interval in  enumerate(monitoring_wells[well]['dates']):
			string+="""
			>>> ELEMENT: %s
				>>>> ANNOTATION: RES-%s
				>>>> FACTOR     : 1.0E5 [bar] - [Pa]
				>>>> DEVIATION  : %.2f [bar]
				>>>> DATA %s\n"""%(monitoring_wells[well]['feedzone'], well+'-'+str(i+1),P_DEV_res, time_type)


			df = pres_data[(pres_data['dates'] > interval[0]) & (pres_data['dates'] < interval[1])]

			df.reset_index(inplace = True)


			if use_formation:
				p_ref = pres_data['prs1'].iat[0]
				string_x="         		 	 01-Feb-1992_00:00:00   0.000E+00\n"
				string+=string_x

			else:

				p_ref = df['prs1'].iat[0]

			print(well,p_ref)
			dfx = df[df.reset_index().index % 10 == 0]

			ax.plot(dfx['dates'], dfx['prs1']-p_ref, label = well+'-'+str(i+1), linestyle = 'None', marker = 'o', ms = 1)

			for index, row in df.iterrows():
				if index == 0:
					string_x="					 %s 	%6.3E\n"%(row['dates'].strftime("%d-%b-%Y_%H:%M:%S"),row['prs1']-p_ref)
					string+=string_x
				elif index > 0 and index%10==0 and row['prs1'] >0:
					string_x="					 %s 	%6.3E\n"%(row['dates'].strftime("%d-%b-%Y_%H:%M:%S"),row['prs1']-p_ref)
					string+=string_x
		string+="""				<<<<\n"""

	ax.set_ylabel('Pressure [bar]')
	plt.legend(loc = 'lower left')
	ax.set_ylim([-40,1])
	plt.show()

	string+="""			<<<<\n"""
	
	observation_pres=open("../model/it2/observation_pres.dat",'w')
	observation_pres.write(string)
	observation_pres.close()

def observations_to_it2_whp(input_dictionary, dates_format = True):
	"""It generates the wellhead pressure observation section for the iTOUGH2 file

	Parameters
	----------
	input_dictionary : dictionary
	  A dictionary containing the standard deviation allowed for the flowing enthalpy in kJ/kg, a reference date on datetime format and the name and path of the database a list of the wells for calibration. e.g. 'IT2':{'h_DEV':100},

	Returns
	-------
	file
	  observations_whp.dat: on ../model/it2 , the time for every observation is calculated by finding the difference  in seconds from a defined reference time

	Attention
	---------
	The input data comes from sqlite

	Examples
	--------
	>>> observations_to_it2_whp(input_dictionary)
	"""

	#Preparing input data
	WHP_DEV=input_dictionary['IT2']['WHP_DEV']
	db_path=input_dictionary['db_path']
	ref_date=input_dictionary['ref_date']
	source_txt=input_dictionary['source_txt']

	t2_ver=float(input_dictionary['VERSION'][0:3])


	types=['WELLS','MAKE_UP_WELLS','NOT_PRODUCING_WELL']
	wells=[]
	for scheme in types:
		try:
			for well in input_dictionary[scheme]:
				wells.append(well)
		except KeyError:
				pass

	conn=sqlite3.connect(db_path)
	c=conn.cursor()
	
	string="	>> WELLHEAD PRESSURE\n"

	for name in sorted(wells):

		data=pd.read_sql_query("SELECT type, flowing_enthalpy, date_time,(steam_flow+liquid_flow) as flow, well_head_pressure FROM mh WHERE well='%s' and substr(date_time,9,2) IN ('15') ORDER BY date_time;"%name,conn)

		dates_func=lambda datesX: datetime.strptime(str(datesX), "%Y-%m-%d_%H:%M:%S")

		dates = list(map(dates_func,data['date_time']))

		data['dates'] = dates

		if t2_ver>7 and dates_format:
			time_type = '[DATES]'
		elif t2_ver<7 or not dates_format: 
			time_type = '[SECONDS]'

		if len(dates)>0 and data[data.type == 'P'].shape[0]>0:

			data_s = pd.read_sql_query("SELECT well, blockcorr, source_nickname FROM t2wellsource WHERE flow_type = 'P' AND well = '%s'"%name, conn)

			string += "		>>> SINK: "
			for source in data_s['source_nickname'].tolist():
				string += "%s "%source

			string+="""
			>>>> ANNOTATION: %s-WHP
			>>>> FACTOR    : 1E5 [bar] - [Pa]
			>>>> DEVIATION : %s   [bar]
			>>>> DATA %s \n"""%(name,WHP_DEV, time_type)

			for n in range(len(dates)):
				if t2_ver>7 and dates_format:
					timex=dates[n].strftime("%d-%b-%Y_%H:%M:%S")
				elif t2_ver<7 or not dates_format: 
					timex=(dates[n]-ref_date).total_seconds()

				if data['flowing_enthalpy'][n]>0 and data['flow'][n]>0 :
					string_x="				 %s 	%0.2f\n"%(timex,data['well_head_pressure'][n])
					string+=string_x
			string+="			<<<<\n"

	string+="""		<<<\n"""

	observation_file_whp=open("../model/it2/observations_WHP.dat",'w')
	observation_file_whp.write(string)
	observation_file_whp.close()

def observations_to_it2_quality(input_dictionary, dates_format = True):
	"""It generates the wellhead steam quality observation section for the iTOUGH2 file

	Parameters
	----------
	input_dictionary : dictionary
	  A dictionary containing the standard deviation allowed for the flowing enthalpy in kJ/kg, a reference date on datetime format and the name and path of the database a list of the wells for calibration. e.g. 'IT2':{'h_DEV':100},

	Returns
	-------
	file
	  observations_whp.dat: on ../model/it2 , the time for every observation is calculated by finding the difference  in seconds from a defined reference time

	Attention
	---------
	The input data comes from sqlite

	Examples
	--------
	>>> observations_to_it2_whp(input_dictionary)
	"""

	#Preparing input data
	Q_DEV=input_dictionary['IT2']['Q_DEV']
	db_path=input_dictionary['db_path']
	ref_date=input_dictionary['ref_date']
	source_txt=input_dictionary['source_txt']

	t2_ver=float(input_dictionary['VERSION'][0:3])


	types=['WELLS','MAKE_UP_WELLS','NOT_PRODUCING_WELL']
	wells=[]
	for scheme in types:
		try:
			for well in input_dictionary[scheme]:
				wells.append(well)
		except KeyError:
				pass

	conn=sqlite3.connect(db_path)
	c=conn.cursor()
	
	string="	>> STEAM QUALITY\n"

	for name in sorted(wells):

		data=pd.read_sql_query("SELECT type, flowing_enthalpy, date_time, steam_flow, liquid_flow, well_head_pressure FROM mh WHERE well='%s' and substr(date_time,9,2) IN ('15') ORDER BY date_time;"%name,conn)

		dates_func=lambda datesX: datetime.strptime(str(datesX), "%Y-%m-%d_%H:%M:%S")

		dates = list(map(dates_func,data['date_time']))

		data['dates'] = dates

		if t2_ver>7 and dates_format:
			time_type = '[DATES]'
		elif t2_ver<7 or not dates_format: 
			time_type = '[SECONDS]'

		if len(dates)>0 and data[data.type == 'P'].shape[0]>0:

			data_s = pd.read_sql_query("SELECT well, blockcorr, source_nickname FROM t2wellsource WHERE flow_type = 'P' AND well = '%s'"%name, conn)

			string += "		>>> SINK: "
			for source in data_s['source_nickname'].tolist():
				string += "%s "%source

			string+="""
			>>>> ANNOTATION: %s-Q
			>>>> FACTOR    : 100.0 [%s] - [-]
			>>>> DEVIATION : %s   [%s]
			>>>> DATA %s \n"""%(name,'%',Q_DEV, '%', time_type)

			for n in range(len(dates)):
				if t2_ver>7 and dates_format:
					timex=dates[n].strftime("%d-%b-%Y_%H:%M:%S")
				elif t2_ver<7 or not dates_format: 
					timex=(dates[n]-ref_date).total_seconds()

				if data['flowing_enthalpy'][n]>0  :
					string_x="				 %s 	%0.2f\n"%(timex,data['steam_flow'][n]*100/(data['steam_flow'][n]+data['liquid_flow'][n]))
					string+=string_x
			string+="			<<<<\n"

	string+="""		<<<\n"""

	observation_file_Q=open("../model/it2/observations_Q.dat",'w')
	observation_file_Q.write(string)
	observation_file_Q.close()