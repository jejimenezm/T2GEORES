import numpy as np
import pyamesh as pya
import shutil
import os
import matplotlib.pyplot as plt
import csv
from scipy import interpolate
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
import os
import sys
from model_conf import *
import sqlite3
import subprocess

db_path='../input/model.db'

def write_PT_from_t2output(db_path):

	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	data_layer=pd.read_sql_query("SELECT correlative FROM layers ORDER BY middle;",conn)

	for name in sorted(wells):
		data_block=pd.read_sql_query("SELECT blockcorr FROM t2wellblock  WHERE well='%s' ORDER BY blockcorr;"%name,conn)
		string=""
		if len(data_block)>0:
			for n in sorted(data_layer['correlative'].values):
				string+="%s\n"%(n+data_block['blockcorr'].values[0])

		subprocess.call(['./shell/write_PT.sh',string,name])

	conn.close()

write_PT_from_t2output(db_path)