import os
from model_conf import *
import subprocess
import shutil
import t2_writer as t2w
import t2gener as t2g
from model_conf import input_data,geners

def incon_replace(incon_file,blocks,incon_file_len):
	string=""
	for index, incon_line in enumerate(incon_file):
		if blocks=='even' and index!=0 and index<=incon_file_len-3:
			if index%2==1:
				string+=incon_line[0:5]+'\n'
			else:
				string+=incon_line
		if blocks=='odd' :
			if index%2!=1:
				string+=incon_line
			else:
				string+=incon_line
	return string

def incon_delete():
	final_t2=""
	incon_section=False
	input_fi_file="../model/t2/t2"
	if os.path.isfile(input_fi_file):
		t2_file=open(input_fi_file, "r")
		for t2_line in t2_file:
			if 'INCON' in t2_line:
				incon_section=True
			elif 'ELEME' in t2_line:
				incon_section=False
			if not incon_section:
				final_t2+=t2_line
		t2_file.close()
		t2_file_out=open(input_fi_file, "w")
		t2_file_out.write(final_t2)
		t2_file_out.close()	
	else:
		sys.exit("The file %s or directory do not exist"%input_fi_file)

def incon_to_t2(incon_state='current'):
	"""Introduce el bloque incon al archivo TOUGH2, proviniente del archivo .sav

	Returns
	-------
	file
	  t2: modifica el archivo '../model/t2/t2' e introduce o actualiza el bloque INCON.

	Examples
	--------
	>>> incon_to_t2()
	"""

	#incon_state could be init or current

	if incon_state=='current':
		input_incon="../model/t2/t2.sav1"
		blocks='even'
		incon_file_len=len(open(input_incon).readlines())
	elif incon_state=='init':
		input_incon="../model/t2/sources/INCON"
		blocks='odd'
		incon_file_len=len(open(input_incon).readlines())

	input_fi_file="../model/t2/t2"

	if os.path.isfile(input_fi_file):
		if os.path.isfile(input_incon):
			incon_file=open(input_incon, "r")
			t2_file=open(input_fi_file, "r")
			if 'INCON' not in open(input_fi_file).read():
				final_t2=""
				for t2_line in t2_file:
					if 'ELEME' not in t2_line:
						final_t2+=t2_line
					elif 'ELEME' in t2_line:
						final_t2+='INCON\n'
						final_t2+=incon_replace(incon_file,blocks,incon_file_len)
						final_t2+='\nELEME----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n'
			else:
				final_t2=""
				incon_section=False
				for t2_line in t2_file:
					if 'INCON' in t2_line:
						incon_section=True
					elif 'ELEME' in t2_line:
						incon_section=False
						final_t2+='INCON\n'
						final_t2+=incon_replace(incon_file,blocks,incon_file_len)
						final_t2+='\n'
					if not incon_section:
						final_t2+=t2_line

			incon_file.close()
			t2_file.close()
			t2_file_out=open(input_fi_file, "w")
			t2_file_out.write(final_t2)
			t2_file_out.close()
		else:
			sys.exit("The file %s or directory do not exist"%input_fi_file)
	else:
		sys.exit("The file %s or directory do not exist"%input_fi_file)

def update_gen(type_run=input_data['TYPE_RUN']):
	"""Actualiza el archivo '../model/t2/sources/GENER_SOURCES', escribe los valores 
	actualizados en la base sqlite e introduce el valor bloque de texto en el archivo t2

	Parameters
	----------
	db_path : str
	  Direccion de base de datos sqlite, tomado de model_conf
	geners : dictionary
	  Diccionario que especifica un elemento del bloque GENER con condiciones constantes, es decir, en caso de ser tipo MASS solo admite un valor

	Returns
	-------
	file
	  GENER_SOURCES: archivo de texto en direccion '../model/t2/sources/GENER_SOURCES' contiene la informacion de cada elemento definido como fuente o sumidero en model_conf

	Examples
	--------
	>>> update_gen(db_path,geners)
	"""

	#t2g.write_geners_to_txt_and_sqlite()

	final_t2=""
	incon_section=False
	input_fi_file="../model/t2/t2"
	sources_file='../model/t2/sources/GENER_SOURCES'
	well_sources_file='../model/t2/sources/GENER_PROD'
	makeup_well_sources_file='../model/t2/sources/GENER_MAKEUP'

	if os.path.isfile(input_fi_file):
		if os.path.isfile(sources_file):
			if 'GENER' not in open(input_fi_file).read():
				t2_file=open(input_fi_file, "a")
				t2_file.write('\nGENER----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n')
				
				gener_source_file=open(sources_file, "r")
				for sources in gener_source_file:
					t2_file.write(sources)

				if type_run=='production':
					if os.path.isfile(well_sources_file):
						well_source_file=open(well_sources_file, "r")
						for sources in well_source_file:
							t2_file.write(sources)
						well_source_file.close()
					else:
						print("The file %s or directory do not exist"%well_sources_file)

					if os.path.isfile(makeup_well_sources_file):
						well_makeup_source_file=open(makeup_well_sources_file, "r")
						for sources in well_makeup_source_file:
							t2_file.write(sources)
						well_makeup_source_file.close()
					else:
						print("The file %s or directory do not exist"%well_sources_file)

				t2_file.write('ENDCY----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n')
				t2_file.close()
				gener_source_file.close()

			else:
				t2_string=""
				t2_file=open(input_fi_file, "r")
				for t2_line in t2_file:
					if 'GENER' not in t2_line:
						t2_string+=t2_line
					else:
						t2_string+='GENER----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n'
						gener_source_file=open(sources_file, "r")
						for sources in gener_source_file:
							t2_string+=sources

						if type_run=='production':
							if os.path.isfile(well_sources_file):
								well_source_file=open(well_sources_file, "r")
								for sources in well_source_file:
									t2_string+=sources
								well_source_file.close()
							else:
								print("The file %s or directory do not exist"%well_sources_file)
						t2_string+='\n'
						if os.path.isfile(makeup_well_sources_file):
							well_makeup_source_file=open(makeup_well_sources_file, "r")
							for sources in well_makeup_source_file:
								t2_string+=sources
							well_makeup_source_file.close()
						else:
							print("The file %s or directory do not exist"%well_sources_file)

						break
					
				t2_string+='\nENDCY----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n'
				t2_file.close()

				t2_file_out=open(input_fi_file, "w")
				t2_file_out.write(t2_string)
				t2_file_out.close()	
		else:
			sys.exit("The file %s or directory do not exist"%sources_file)
	else:
		sys.exit("The file %s or directory do not exist"%input_fi_file)
	#subprocess.Popen(["sh","shell\\insert_geners.sh"])
	#subprocess.call(['./shell/insert_geners.sh'])

def update_rock_distribution(include_FOFT,include_SOLVR,include_COFT,include_GOFT,include_RPCAP,include_MULTI,include_START,type_run=input_data['TYPE_RUN']):
	"""Actualiza el archivo '../model/t2/sources/GENER_SOURCES', escribe los valores 
	actualizados en la base sqlite e introduce el valor bloque de texto en el archivo t2

	Parameters
	----------
	db_path : str
	  Direccion de base de datos sqlite, tomado de model_conf
	geners : dictionary
	  Diccionario que especifica un elemento del bloque GENER con condiciones constantes, es decir, en caso de ser tipo MASS solo admite un valor
	param : dictionary
	  Diccionario que contiene los elementos del bloque PARAM definidos en model_conf
	multi : dictionary
	  Diccionario que contiene los elementos del bloque MULTI definidos en model_conf
	solver : dictionary
	  Diccionario que contiene los elementos del bloque SOLVER definidos en model_conf
	recap : dictionary
	  Diccionario que contiene los elementos del bloque RECAP definidos en model_conf
	type_run : str
	  Puede ser natural o production, el primero no introduce el archivo '../model/t2/sources/GENER_PROD' al archivo t2
	recap : str
	  Titulo del modelo, tomado de model_conf

	Returns
	-------
	file
	  t2: archivo de entrada TOUGH2

	Examples
	--------
	>>> update_rock_distribution(db_path,geners,param,multi,solver,recap,'natural',title)
	"""

	"""
	value = input("How many times have you run copy_folder?\n")
	if value==1:
	"""
	t2g.write_geners_to_txt_and_sqlite()
	t2w.CONNE_from_steinar_to_t2()
	t2w.merge_ELEME_and_in_to_t2()
	t2w.t2_input(include_FOFT,include_SOLVR,include_COFT,include_GOFT,include_RPCAP,include_MULTI,include_START)

def copy_folder(src,dest):
	"""Funcion generada para copiar todo el contenido de una carpeta en otra

	Parameters
	----------
	src : str
	  Direccion de folder fuente
	dest : str
	  Direccion de folder destino


	Examples
	--------
	>>> copy_folder('../model/t2','../model/t2/prev')
	"""
	src_files = os.listdir(src)
	for file_name in src_files:
		full_file_name = os.path.join(src, file_name)
		if os.path.isfile(full_file_name):
			try:
				shutil.copy(full_file_name, dest)
			except shutil.Error:
				print("%s and %s didnt change"%(full_file_name,dest))

def create_prev():
	"""Genera una copia de carpetas con resultados de corrida para posterior comparacion

	Note
	----
	Las carpetas a copiar son: 
	'../model/t2'
	'../output/PT/images'
	'../output/PT/json'
	'../output/PT/txt'
	'../output/PT/evol'
	'../output/mh'
	Todas son copiadas a un subfolder llamado prev

	Examples
	--------
	>>> create_prev()
	"""

	#Copy t2 output
	src='../model/t2'
	dest= '../model/t2/prev'
	copy_folder(src,dest)

	#Copy prev images output
	src='../output/PT/images'
	dest='../output/PT/images/prev'
	copy_folder(src,dest)

	#Copy prev json output
	src='../output/PT/json'
	dest='../output/PT/json/prev'
	copy_folder(src,dest)

	#Copy prev txt output
	src='../output/PT/txt'
	dest='../output/PT/txt/prev'
	copy_folder(src,dest)

	#Copy prev txt output
	src='../output/PT/evol'
	dest='../output/PT/evol/prev'
	copy_folder(src,dest)

	#Copy prev txt output
	src='../output/mh/txt'
	dest='../output/mh/txt/prev'
	copy_folder(src,dest)

def run(EOS=1):
	current=os.path.abspath(os.getcwd())
	t2_input_file='%s/model/t2/t2'%current.replace('/scripts','')
	it2_input_file='%s/model/t2/fit2'%current.replace('/scripts','')
	shutil.copyfile(t2_input_file, current+'/t2')
	shutil.copyfile(it2_input_file, current+'/fit2')

	subprocess.run(["itough2", 'fit2','t2',str(EOS)])

	target_dir = current.replace('/scripts','/model/t2')
	file_names = os.listdir(current)

	for file_name in file_names:
		if 't2.' in file_name or 'fit2' in file_name:
			try:
				shutil.move(os.path.join(current, file_name),os.path.join(target_dir, file_name) )
			except shutil.Error:
				print("File already exist %s"%file_name)

#Sostenibilidad Ahuachapan

#incon_from_st_to_t2()

#update_gen(db_path,geners)

#incon_to_t2()

#update_gen(db_path,geners)

#create_prev()

#incon_to_t2()
#incon_delete()
#update_gen()
#update_rock_distribution(include_FOFT=True,include_SOLVR=True,include_COFT=True,include_GOFT=True,include_RPCAP=True,include_MULTI=True,include_START=True)

#run()