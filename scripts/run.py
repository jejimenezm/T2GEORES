import os
from model_conf import *
import subprocess
import t2gener as t2g

def incon_to_t2():
	subprocess.call(['./shell/incon_to_t2.sh'])

def update_gen(db_path,geners):
	t2g.write_geners_to_txt_and_sqlite(db_path,geners)
	subprocess.call(['./shell/insert_geners.sh'])

db_path='../input/model.db'
update_gen(db_path,geners)
#incon_to_t2()