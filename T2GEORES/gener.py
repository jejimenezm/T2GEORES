#import t2resfun as t2r
from model_conf import *
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
from model_conf import input_data
import t2_writer as t2w
from formats import formats_t2
import geometry as geomtr
import matplotlib.pyplot as plt

def write_t2_format_gener(var_array,time_array,var_type,var_enthalpy,type_flow,input_dictionary):
	"""Genera bloque de tiempos, flujos y entalpia para cada pozo

	Parameters
	----------
	var_array : array
	  Arreglo que contiene los flujos de pozo
	time_array : array
	  Arreglo que contiene una lista de fechas en formato datetime
	ref_date   :date
	  Fecha de referencia, utilizada para calcular delta de tiempo
	var_type	:str
	  Indica el tipo de pozo 'P' o 'R'
	var_enthalpy :array
	  Arreglo que contiene las entalpias para el caso de los pozos reinyectores
	type_flow :str
	  Tipo de flujo a proyectar: invariable, constant o shutdown

	Returns
	-------
	str
	  string_P: Cadena de texto que contiene la entrada TOUGH2 para un pozo productor
	str
	  string_R : Cadena de texto que contiene la entrada TOUGH2 para un pozo reinyector
	int
	  cnt_P : Numero de elementos (tiempos o flujos) contenidos en la cada string_P de pozo productor
	int
	  cnt_R : Numero de elementos (tiempos, flujos o entalpias) contenidos en la cada string_P de pozo productor
	  
	Other Parameters
	----------------
	float
		extra_time : parametro interno, tiempo en segundos, utilizado cuando el tipo de flujo es 'shutdown'

	Attention
	---------
	La longitud de var_array, time_array y var_enthalpy deben ser iguales

	Note
	----
	Para todos los casos se incorpora un flujo cero para un tiempo -1E50 y en tiempo minimo 
	Para el tipo flujo 'constant': reproduce el ultimo flujo  en un tiempo 1E50
	Para el tipo flujo 'invariable': traduce al formato TOUGH2 los arreglos sin hacer cambios
	Para el tipo flujo 'shutdown': reproduce el ultimo flujo  por un tiempo extra_time y luego igual a cero el flujo

	Examples
	--------
	>>> write_t2_format_gener(data['flow'],dates,ref_date,'P',data['flowing_enthalpy'],'constant')
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
	time_zero=0
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

def write_gener_from_sqlite(type_flow,forecast,wells,input_dictionary=input_data,make_up=False):
	"""Genera el bloque GENER para todos los pozos

	Parameters
	----------
	db_path : str
	  Direccion de base de datos sqlite, tomado de model_conf
	wells : array
	  Arreglo con nombre de pozos a ser incluidos en la etapa de produccion
	type_flow :str
	  Tipo de flujo a proyectar: invariable, constant o shutdown
	forecast : bool
	   Se introducen los flujo de pozos nuevos al GENER


	Returns
	-------
	file
	  GENER_PROD: archivo de texto en direccion '../model/t2/sources/GENER_PROD' contiene toda la informacion GENER de cada  pozo
	  
	Other Parameters
	----------------
	int
		source_corr_num : los correlativos de fuentes seran generados de la siguiente forma 'SRC'+source_corr_num

	Attention
	---------
		De existir otras fuentes definidas en el archivo model_conf con el prefijo SRC deben ingresarse primero  a la base de datos 
		sqlite ejecutando la funcion write_geners_to_txt_and_sqlite, de ser asi el correlativo de fuentes sera enumerado con el valor mas alto
		de SRCXX


	Examples
	--------
	>>> write_gener_from_sqlite(db_path,wells,type_flow,'constant')
	"""

	db_path=input_dictionary['db_path']

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

			P,R, LTAB_P, LTAB_R= write_t2_format_gener(data['m_total'].values*porcentage[feedn],dates,data['type'],data['flowing_enthalpy']*1E3,type_flow,input_dictionary=input_dictionary)

			if type_flow=="invariable":
				condition=1
			elif type_flow=="constant":
				condition=2
			elif type_flow=="shutdown":
				condition=4

			r_check=False
			
			if LTAB_R>condition:
				if forecast :
					gener+="%s%s                %4d     MASSi\n"%(source_block,source_corr,LTAB_R)
					gener+=R
					try:
						q="INSERT INTO t2wellsource(well,blockcorr,source_nickname) VALUES ('%s','%s','%s')"%(name,source_block,source_corr)
						print(q)
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

				else:
					gener+="%s%s                %4d     MASSi\n"%(source_block,source_corr,LTAB_R)
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

				if  forecast :
					gener+="%s%s                %4d     MASS\n"%(source_block,source_corr,LTAB_P)
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

				else:
					gener+="%s%s                %4d     MASS\n"%(source_block,source_corr,LTAB_P)
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

def def_gener_selector(section,key,geners):
	try:
		value=geners[section][key]
		def_value=False
	except KeyError:
		value=formats_t2['GENER'][key][0]
		def_value=True
	return value,def_value

def write_geners_to_txt_and_sqlite(db_path=input_data['db_path'],geners=geners):
	"""Genera GENER para cada source

	Parameters
	----------
	db_path : str
	   Direccion de base de datos sqlite, tomado de model_conf
	geners : dicionary
	  Diccionario definido en model_conf con todos los parametros para un sumidero o fuente

	Returns
	-------
	file
	  GENER_SOURCES: archivo de texto en direccion '../model/t2/sources/GENER_SOURCES' contiene la informacion de cada elemento definido como fuente o sumidero en model_conf
	  
	Attention
	---------
		El archivo GENER_SOURCES es reemplazado cuando se ejecuta esta funcion y las fuentes o sumideros actualizados en la base de datos.
		Elimina los elementos que ya no estan definidos en model_conf

	Examples
	--------
	>>> write_geners_to_txt_and_sqlite(db_path,geners)
	"""

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
	#string+="\n"

	file=open('../model/t2/sources/GENER_SOURCES','w')
	file.write(string)
	file.close()

	#As the sources defined on model_conf are the only allowed any other source not incluaded on the geners dictionary will be erased
	list_geners_string=''.join(["'%s',"%str(i) for i in list_geners])
	query="DELETE FROM t2wellsource WHERE source_nickname NOT IN (%s) AND  source_nickname LIKE'GEN*' "%(list_geners_string[0:-1])
	c.execute(query)
	conn.commit()

	conn.close()

def create_well_flow(flow_times,include_gener=True,input_dictionary=input_data):
  """Crea un archivo mh para cada los pozos en flow_times, los cuales a su vez deben haber sido definidos en alguna de las secciones 'WELLS','MAKE_UP_WELLS' o 'NOT_PRODUCING_WELL' de input_data
  
  Parameters
  ----------
  flow_times : dicionary
    Diccionario contiene: nombre de pozo, tiempos (En meses), flujos vapor, flujo agua, entalpia,  presion y tipo de pozo.
  include_gener: bool
  	True convierte en formato T2 a gener y lo adiciona al final del archivo GENER_PROD
  
  Returns
  -------
  str
    string: imprime en pantalla el bloque de texto
  file
 	En la ubicacion ../input/mh/
    
  Attention
  ---------
  El dictionario debe ser ingresado manualmente y el 
  
  Examples
  --------
  Ejemplo de diccionario de entrada:
  >>> flow_times={'CHI-3A':[[0,300],
  >>> [10,10],
  >>> [45,45],
  >>> [1100,1100],
  >>> [6.9,6.9],
  >>> 'P']}
  
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
  	write_gener_from_sqlite(type_flow='constant',forecast=True,wells=flow_times.keys(),make_up=True,input_dictionary=input_dictionary)

def plot_makeup_wells(flow_times):

	# Plotting
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
	xlims=[datetime(2025,1,1),datetime(2031,1,1)]
	ax.set_xlim(xlims)
	plt.yticks(y_positions, well_tick)
	plt.show()
	fig.savefig('try.png')

#Sostenibilidad Ahuachapan
#write_gener_from_sqlite(db_path,wells,type_flow='constant',forecast=False)
#write_geners_to_txt_and_sqlite(db_path,geners)

#Escenario 1
flow_times_1={'ZAH-38A':[[datetime(2028,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [7.5,7.5],
			           [50,50],
			           [1100,1100],
			           [7,7],
			           'P'],
				'ZAH-38B':[[datetime(2028,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
				           [7.5,7.5],
				           [50,50],
				           [1100,1100],
				           [7,7],
				           'P'],
				'ZAH-38C':[[datetime(2028,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
				           [7.5,7.5],
				           [50,50],
				           [1100,1100],
				           [7,7],
				           'P'],
				'ZAH-39A':[[datetime(2029,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
				           [7.5,7.5],
				           [60,60],
				           [1100,1100],
				           [7,7],
				           'P'],
				'ZAH-39B':[[datetime(2029,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
				           [7.5,7.5],
				           [60,60],
				           [1100,1100],
				           [7,7],
				           'P'],
				'XAH-2R':[[datetime(2022,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
				           [0,0],
				           [40,40],
				           [250,250],
				           [2,2],
				           'R'],
				'XCH-9C':[[datetime(2022,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
				           [0,0],
				           [102.3,102.3],
				           [410,410],
				           [2,2],
				           'R'],
				'XCH-12A':[[datetime(2029,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
				           [0,0],
				           [60,60],
				           [675,675],
				           [2,2],
				           'R'],
				'XCH-12B':[[datetime(2029,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
				           [0,0],
				           [60,60],
				           [675,675],
				           [2,2],
				           'R'],
				'XCH-8A':[[datetime(2028,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
				           [0,0],
				           [60,60],
				           [675,675],
				           [2,2],
				           'R'],
				'XCH-8B':[[datetime(2028,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
				           [0,0],
				           [60,60],
				           [675,675],
				           [2,2],
				           'R'],
			}



#Escenario_2
flow_times_2={'ZAH-37A':[[datetime(2024,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [7.5,7.5],
			           [60,60],
			           [1100,1100],
			           [7,7],
			           'P'],
			'ZAH-37B':[[datetime(2027,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [7.5,7.5],
			           [60,60],
			           [1100,1100],
			           [7,7],
			           'P'],
			'ZAH-38A':[[datetime(2028,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [7.5,7.5],
			           [50,50],
			           [1100,1100],
			           [7,7],
			           'P'],
			'ZAH-38B':[[datetime(2028,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [7.5,7.5],
			           [50,50],
			           [1100,1100],
			           [7,7],
			           'P'],
			'ZAH-38C':[[datetime(2028,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [7.5,7.5],
			           [50,50],
			           [1100,1100],
			           [7,7],
			           'P'],
			'ZAH-39A':[[datetime(2029,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [7.5,7.5],
			           [60,60],
			           [1100,1100],
			           [7,7],
			           'P'],
			'ZAH-39B':[[datetime(2029,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [7.5,7.5],
			           [60,60],
			           [1100,1100],
			           [7,7],
			           'P'],
			'ZAH-39C':[[datetime(2029,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [7.5,7.5],
			           [60,60],
			           [1100,1100],
			           [7,7],
			           'P'],
			'XAH-2R':[[datetime(2022,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [0,0],
			           [40,40],
			           [250,250],
			           [2,2],
			           'R'],
			'XCH-9C':[[datetime(2022,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [0,0],
			           [87.225,87.225],
			           [410,410],
			           [2,2],
			           'R'],
			'CH-D':[[datetime(2022,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [0,0],
			           [60,60],
			           [675,675],
			           [2,2],
			           'R'],
			'XCH-D2':[[datetime(2025,1,1,0,0,0),datetime(2080,6,1,0,0,0)],
			           [0,0],
			           [60,60],
			           [675,675],
			           [2,2],
			           'R'],
			'XCH-12A':[[datetime(2029,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [0,0],
			           [60,60],
			           [675,675],
			           [2,2],
			           'R'],
			'XCH-12B':[[datetime(2029,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [0,0],
			           [60,60],
			           [675,675],
			           [2,2],
			           'R'],
			'XCH-8A':[[datetime(2028,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [0,0],
			           [60,60],
			           [675,675],
			           [2,2],
			           'R'],
			'XCH-8B':[[datetime(2028,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [0,0],
			           [60,60],
			           [675,675],
			           [2,2],
			           'R'],
			}

#Escenario_3
flow_times_3={'ZAH-37A':[[datetime(2024,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [7.5,7.5],
			           [60,60],
			           [1100,1100],
			           [7,7],
			           'P'],
			'ZAH-37B':[[datetime(2027,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [7.5,7.5],
			           [60,60],
			           [1100,1100],
			           [7,7],
			           'P'],
			'ZAH-38A':[[datetime(2028,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [7.5,7.5],
			           [50,50],
			           [1100,1100],
			           [7,7],
			           'P'],
			'ZAH-38B':[[datetime(2028,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [7.5,7.5],
			           [50,50],
			           [1100,1100],
			           [7,7],
			           'P'],
			'ZAH-38C':[[datetime(2028,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [7.5,7.5],
			           [50,50],
			           [1100,1100],
			           [7,7],
			           'P'],
			'ZAH-39A':[[datetime(2029,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [7.5,7.5],
			           [60,60],
			           [1100,1100],
			           [7,7],
			           'P'],
			'ZAH-39B':[[datetime(2029,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [7.5,7.5],
			           [60,60],
			           [1100,1100],
			           [7,7],
			           'P'],
			'ZAH-39C':[[datetime(2029,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [7.5,7.5],
			           [60,60],
			           [1100,1100],
			           [7,7],
			           'P'],
			'XAH-2R':[[datetime(2022,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [0,0],
			           [40,40],
			           [250,250],
			           [2,2],
			           'R'],
			'XCH-9C':[[datetime(2022,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [0,0],
			           [102.225,102.225],
			           [410,410],
			           [2,2],
			           'R'],
			'CH-D':[[datetime(2024,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [0,0],
			           [60,60],
			           [675,675],
			           [2,2],
			           'R'],
			'XCH-D1':[[datetime(2027,1,1,0,0,0),datetime(2080,6,1,0,0,0)],
			           [0,0],
			           [60,60],
			           [675,675],
			           [2,2],
			           'R'],
			'XCH-D2':[[datetime(2027,1,1,0,0,0),datetime(2080,6,1,0,0,0)],
			           [0,0],
			           [60,60],
			           [675,675],
			           [2,2],
			           'R'],
			'XCH-12A':[[datetime(2029,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [0,0],
			           [60,60],
			           [675,675],
			           [2,2],
			           'R'],
			'XCH-12B':[[datetime(2029,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [0,0],
			           [60,60],
			           [675,675],
			           [2,2],
			           'R'],
			'XCH-8A':[[datetime(2027,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [0,0],
			           [60,60],
			           [675,675],
			           [2,2],
			           'R'],
			'XCH-8B':[[datetime(2028,1,1,0,0,0),datetime(2029,1,1,0,0,0),datetime(2080,1,1,0,0,0)],
			           [0,0,0],
			           [30,60,60],
			           [675,675,675],
			           [2,2,2],
			           'R'],
			}

#Expansion

#create_constant_scenario(db_path,flow_times_3)

#write_gener_from_sqlite(db_path,wells,type_flow='constant',forecast=True)

#write_geners_to_txt_and_sqlite(db_path=input_data['db_path'],geners=geners)

#write_gener_from_sqlite(type_flow='constant',forecast=True,db_path=input_data['db_path'],wells=input_data['WELLS'])

#create_well_flow(flow_times_1,include_gener=True)

#write_geners_to_txt_and_sqlite()