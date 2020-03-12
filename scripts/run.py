import os
from model_conf import *
import subprocess
import shutil
import t2gener as t2g
import t2resfun as t2r

def incon_to_t2():
	subprocess.call(['./shell/incon_to_t2.sh'])

def update_gen(db_path,geners):
	t2g.write_geners_to_txt_and_sqlite(db_path,geners)
	subprocess.call(['./shell/insert_geners.sh'])

def update_rock_distribution(db_path,geners,param,multi,solver,recap,type_run,title):
	"""
	value = input("How many times have you run copy_folder?\n")
	if value==1:
	"""
	update_gen(db_path,geners)
	t2r.conne_from_steinar_to_t2()
	t2r.merge_eleme_and_in_to_t2()
	t2r.t2_input_creation(param,multi,solver,recap,type_run,title)
	incon_to_t2()

def copy_folder(src,dest):
	src_files = os.listdir(src)
	for file_name in src_files:
	    full_file_name = os.path.join(src, file_name)
	    if os.path.isfile(full_file_name):
	        shutil.copy(full_file_name, dest)

def create_prev():

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

#create_prev()
#update_rock_distribution(db_path,geners,param,multi,solver,recap,type_run,title) 

#update_gen(db_path,geners)
#incon_to_t2()