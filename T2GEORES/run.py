from T2GEORES import writer as writer
from T2GEORES import gener as t2g
import os
import subprocess
import shutil

def incon_replace(incon_file,blocks,incon_file_len):
	"""It rewrite the incon file without the porosity, depending if it comes from .sav file or INCON generated with T2GEORES

	Parameters
	----------
	incon_file : str
	  incon file to be rearange
	blocks: str
	  Declares if the file has the block information on even or odd lines
	incon_file_len: int
	  Length of incon file

	Returns
	-------
	str
	  string: formatted string with incon data
	  
	Attention
	---------
	The function is called by incon_to_t2()

	"""
	string=""
	for index, incon_line in enumerate(incon_file):
		if '+++' in incon_line:
			minus = 3
		else: 
			minus = 2
		if blocks=='even' and index!=0 and index<=incon_file_len-minus:
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
	"""It reads the TOUGH2 file assuming it is on ../model/t2/ and erases the INCON section

	Returns
	-------
	file
	  t2: file without INCON information
	  
	Attention
	---------
	There is no need of input argument

	Examples
	--------
	>>> incon_delete()
	"""
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

def incon_to_t2(input_dictionary, file_name = None):
	"""Adds the INCON block to the TOUGH2 input file

	Parameters
	----------
	input_dictionary : dictionary
	  Dictionary contanining the information of the source of incon with keyword 'incon_state' can take the value of 'current' or 'init'.

	Returns
	-------
	file
	  t2: modified file on  ../model/t2/t2 

	Examples
	--------
	>>> incon_to_t2(input_dictionary)
	"""

	incon_state=input_dictionary['incon_state']

	if incon_state=='current':
		input_incon="../model/t2/%s"%file_name
		blocks='even'
		incon_file_len=len(open(input_incon).readlines())
	elif incon_state=='init':
		input_incon="../model/t2/sources/INCON"
		blocks='odd'
		incon_file_len=len(open(input_incon).readlines())
	elif incon_state=='steinar':
		input_incon="../model/t2/sources/STE_INCON"
		blocks='odd'
		incon_file_len=len(open(input_incon).readlines())
	elif incon_state=='init_mod':
		input_incon="../model/t2/sources/INCON_MOD"
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

def update_gen(input_dictionary):
	"""It updates the file the TOUGH2 input file based on the previous updates of all files on ../model/t2/sources/GENER_*

	Parameters
	----------
	input_dictionary : dictionary
	  Dictionary contaning the type of desire run 'production' or 'natural' written on the keyword 'TYPE_RUN'

	Returns
	-------
	file
	  t2: file with the modified version of GENER

	Note
	----
	Some print sentences are expected depending on the availability of certain files

	Examples
	--------
	>>> update_gen(input_dictionary)
	"""

	type_run=input_dictionary['TYPE_RUN']

	final_t2=""
	incon_section=False
	input_fi_file="../model/t2/t2"
	sources_file='../model/t2/sources/GENER_SOURCES'
	well_sources_file='../model/t2/sources/GENER_PROD'
	makeup_well_sources_file='../model/t2/sources/GENER_MAKEUP'
	t2_ver=float(input_dictionary['VERSION'][0:3])

	if os.path.isfile(input_fi_file):
		if os.path.isfile(sources_file):
			if 'GENER' not in open(input_fi_file).read():

				t2_string=""
				t2_file=open(input_fi_file, "r")
				for t2_line in t2_file:
					if 'ENDCY' not in t2_line:
						t2_string+=t2_line
					else:
						pass

				if t2_ver<7:
					t2_string+='GENER----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n'
				else:
					t2_string+='GENER D--1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n'

				
				gener_source_file=open(sources_file, "r")
				for sources in gener_source_file:
					t2_string+=sources
				gener_source_file.close()
			
				if type_run=='production':
					if os.path.isfile(well_sources_file):
						well_source_file=open(well_sources_file, "r")
						for sources in well_source_file:
							t2_string+=sources
						well_source_file.close()

					else:
						print("The file %s or directory do not exist"%well_sources_file)

					if os.path.isfile(makeup_well_sources_file):
						well_makeup_source_file=open(makeup_well_sources_file, "r")
						for sources in well_makeup_source_file:
							t2_string+=sources
						well_makeup_source_file.close()
					else:
						print("The file %s or directory do not exist"%well_sources_file)

				t2_string+='\n'
				t2_string+='ENDCY----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n'
				t2_file.close()
				

				t2_file_out=open(input_fi_file, "w")
				t2_file_out.write(t2_string)
				t2_file_out.close()	

			else:
				t2_string=""
				t2_file=open(input_fi_file, "r")
				for t2_line in t2_file:
					if 'GENER' not in t2_line:
						t2_string+=t2_line
					else:

						if t2_ver<7:
							t2_string+='GENER----1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n'
						else:
							t2_string+='GENER D--1----*----2----*----3----*----4----*----5----*----6----*----7----*----8\n'

							t2_string+="AA110DUM00                   3     MASS                      10.e5\n"
							t2_string+="           -infinity       0.0\n"
							t2_string+="%s       0.0\n"%(format(input_dictionary['ref_date'].strftime("%Y-%m-%d_00:00:00"),'>20s'))
							t2_string+="            infinity       0.0\n"

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

def update_rock_distribution(input_dictionary):
	"""It updates the file the TOUGH2 input file based on the new rock distribution

	Parameters
	----------
	input_dictionary : dictionary
	  Dictionary contaning the information where the rock distribution comes from

	Returns
	-------
	file
	  t2: file with the modified version of ELEME and CONNE

	Examples
	--------
	>>> update_rock_distribution(input_dictionary)
	"""

	writer.CONNE_from_steinar_to_t2()
	writer.merge_ELEME_and_in_to_t2()

	t2_string=""
	input_fi_file="../model/t2/t2"

	if os.path.isfile(input_fi_file):
		t2_file=open(input_fi_file, "r")
		ELEME_line=1E50
		add_gener=False
		add_ELEME=False
		for i,t2_line in enumerate(t2_file):
			if 'ELEME' not in t2_line and ELEME_line>i:
				t2_string+=t2_line

			if 'ELEME' in t2_line:
				add_ELEME=True
				ELEME_line=0

			if 'GENER D' in t2_line:
				add_gener=True

			if add_gener:
				t2_string+=t2_line

			if add_ELEME:
				t2_string+=writer.ELEME_adder(input_dictionary)
				t2_string+=writer.CONNE_adder(input_dictionary)
				add_ELEME=False

		t2_file.close()
		t2_file_out=open(input_fi_file, "w")
		t2_file_out.write(t2_string)
		t2_file_out.close()
	else:
		sys.exit("The file %s or directory do not exist"%input_fi_file)

def copy_folder(src,dest):
	"""It copies all the files on a folder to another folder

	Parameters
	----------
	src : str
	  Source directory
	dest : str
	  Output directory

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
	"""It creates a copy of several folder for further comparisson

	Note
	----
	The folders to copy are: 
	'../model/t2'
	'../output/PT/images'
	'../output/PT/json'
	'../output/PT/txt'
	'../output/PT/evol'
	'../output/mh'
	All of them contains a subfolder prev where the data is stored

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

def run(input_dictionary):
	"""It runs the TOUGH2 input file

	Parameters
	----------
	input_dictionary : dictionary
	  A dictionary with the EOS used on the model

	Returns
	-------
	files
	  various: containing the output from modelling 
	"""

	EOS=input_dictionary['EOS']
	version=input_dictionary['VERSION']
	current=os.path.abspath(os.getcwd())
	t2_input_file='%s/model/t2/t2'%current.replace('/scripts','')
	it2_input_file='%s/model/t2/fit2'%current.replace('/scripts','')
	shutil.copyfile(t2_input_file, current+'/t2')
	shutil.copyfile(it2_input_file, current+'/fit2')

	if not input_dictionary['IT2_alias']:
		subprocess.run(["itough2",'-v',version,'fit2','t2',str(EOS)])
	else:
		subprocess.run([input_dictionary['IT2_alias'],'fit2','t2',str(EOS)])

	target_dir = current.replace('/scripts','/model/t2')
	file_names = os.listdir(current)

	for file_name in file_names:
		if 't2.' in file_name or 'fit2' in file_name:
			try:
				shutil.move(os.path.join(current, file_name),os.path.join(target_dir, file_name) )
			except shutil.Error:
				print("File already exist %s"%file_name)

def rock_update(input_dictionary):
	"""
	It updates the rock type on the TOUGH2 file
	Parameters
	----------
	input_dictionary : dictionary
		TOUGH2 file name
	"""

	t2_string = ""
	input_fi_file = "../model/t2/%s"%input_dictionary['TOUGH2_file']
	if os.path.isfile(input_fi_file):
		t2_file=open(input_fi_file, "r")
		ELEME_line = 1E50
		add_param = False
		add_rocks = False
		for i,t2_line in enumerate(t2_file):

			if 'ROCKS' not in t2_line and ELEME_line>i:
				t2_string+=t2_line

			if 'ROCKS' in t2_line:
				add_rocks=True
				ELEME_line=0

			if 'PARAM' in t2_line or 'START' in t2_line:
				add_param = True

			if add_param:
				t2_string += t2_line

			if add_rocks:
				t2_string += writer.ROCKS_writer(input_dictionary)
				add_rocks = False

		t2_file.close()
		t2_file_out = open(input_fi_file, "w")
		t2_file_out.write(t2_string)
		t2_file_out.close()
	else:
		sys.exit("The file %s or directory do not exist"%input_fi_file)