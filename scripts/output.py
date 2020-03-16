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
import json
import matplotlib.dates as mdates

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

def extract_json_from_t2out():
	if os.path.isfile("../mesh/to_steinar/in"):
		elemefile=open("../mesh/to_steinar/in","r")
	else:
		return "Theres is not in file on mesh/to_steinar"

	eleme_dict={}
	for line in elemefile:
		if len(line.split())==6:
			
			eleme_dict[line.split()[0].rstrip()]=[float(line.split()[2].rstrip()),
													float(line.split()[3].rstrip()),
													float(line.split()[4].rstrip())]
	elemefile.close()

	last=""
	if os.path.isfile("../model/t2/t2.out"):
		t2file=open("../model/t2/t2.out","r")
	else:
		return "Theres is not t2.out file on t2/t2.out"

	cnt=0
	t2string=[]
	for linet2 in t2file:
		cnt+=1
		t2string.append(linet2.rstrip())
		if "OUTPUT DATA AFTER" in linet2.rstrip():
			last=linet2.rstrip().split(",")
			line=cnt
	t2file.close()

	high_iteration=[int(s) for s in last[0].split() if s.isdigit()]

	for elementx in eleme_dict:
		cnt2=0
		for lineout in t2string[line+cnt2:-1]:
			if " @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"==lineout:
				cnt2+=1
			elif cnt2>2:
				break
			elif elementx in lineout:
				lineselect=lineout.split("  ")
				if len(lineselect)==13:
					eleme_dict[elementx].extend([float(lineselect[2]),float(lineselect[3]),float(lineselect[4]),
												 float(lineselect[5]),float(lineselect[6]),float(lineselect[7]),
												 float(lineselect[8]),float(lineselect[9]),float(lineselect[11]),float(lineselect[12])])
				else:
					eleme_dict[elementx].extend([float(lineselect[1]),float(lineselect[2]),float(lineselect[3]),
								 float(lineselect[4]),float(lineselect[5]),float(lineselect[6]),
								 float(lineselect[7]),float(lineselect[8]),float(lineselect[10]),float(lineselect[11])])
				break


	with open("../output/PT/json/PT_json.txt",'w') as json_file:
	  json.dump(eleme_dict, json_file,sort_keys=True, indent=1)

def from_sav_to_json():

	if os.path.isfile("../mesh/to_steinar/in"):
		elemefile=open("../mesh/to_steinar/in","r")
	else:
		return "Theres is not in file on mesh/to_steinar"

	eleme_dict={}
	for line in elemefile:
		if len(line.split())==6:
			
			eleme_dict[line.split()[0].rstrip()]=[float(line.split()[2].rstrip()),
													float(line.split()[3].rstrip()),
													float(line.split()[4].rstrip())]
	elemefile.close()

	#Creates a string from .sav file
	savfile=open("../model/t2/t2.sav1","r")
	savstring=[]
	for linesav in savfile:
		savstring.append(linesav.rstrip())
	savfile.close()


	line_cnt=0
	for element in sorted(eleme_dict):
		t2file=open("../model/t2/t2.sav1","r")
		for line in t2file:
			if element in line.rstrip():
				line_cnt+=2
				lineselect=savstring[line_cnt].split(" ")
				eleme_dict[element].extend([float(lineselect[1]),float(lineselect[2])])
		t2file.close()

	with open("../output/PT/json/PT_json_from_sav.txt",'w') as json_file:
	  json.dump(eleme_dict, json_file,sort_keys=True, indent=1)

def PTjson_to_sqlite(source):
	conn=sqlite3.connect(db_path)
	c=conn.cursor()
	if source=="t2":
		if os.path.isfile("../output/PT/json/PT_json.txt"):
			with open("../output/PT/json/PT_json.txt") as f:
		  		data=json.load(f)

		  	for element in sorted(data):
		  		try:
			  		q="INSERT INTO t2PTout(blockcorr,x,y,z,'index',P,T,SG,SW,X1,X2,PCAP,DG,DW) \
			  		VALUES ('%s',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"%(element,data[element][0],\
			  			data[element][1],data[element][2],data[element][3],data[element][4],\
			  			data[element][5],data[element][6],data[element][7],data[element][8],
			  			data[element][9],data[element][10],data[element][11],data[element][12])
					c.execute(q)
					
				except sqlite3.IntegrityError:

					q="UPDATE t2PTout SET \
					 x=%s, \
					 y=%s, \
					 z=%s, \
					 'index'=%s, \
					 P=%s, \
					 T=%s, \
					 SG=%s, \
					 SW=%s, \
					 X1=%s, \
					 X2=%s, \
					 PCAP=%s, \
					 DG=%s, \
					 DW=%s \
					 WHERE blockcorr='%s'"%(data[element][0],\
			  			data[element][1],data[element][2],data[element][3],data[element][4],\
			  			data[element][5],data[element][6],data[element][7],data[element][8],
			  			data[element][9],data[element][10],data[element][11],data[element][12],element,)
					c.execute(q)
				conn.commit()

	elif source=="sav":
		if os.path.isfile("../output/PT/json/PT_json_from_sav.txt"):
			with open("../output/PT/json/PT_json_from_sav.txt") as f:
		  		data=json.load(f)

		  	for element in sorted(data):
		  		try:
			  		q="INSERT INTO t2PTout(blockcorr,x,y,z,P,T) \
			  		VALUES ('%s',%s,%s,%s,%s,%s)"%(element,data[element][0],\
			  			data[element][1],data[element][2],data[element][3],data[element][4])
					c.execute(q)
					
				except sqlite3.IntegrityError:
					q="UPDATE t2PTout SET \
					 x=%s, \
					 y=%s, \
					 z=%s, \
					 P=%s, \
					 T=%s \
					 WHERE blockcorr='%s'"%(data[element][0],\
			  			data[element][1],data[element][2],data[element][3],data[element][4],element)
					c.execute(q)
				conn.commit()

	conn.close()

def write_PT_of_wells_from_t2output_in_time(db_path):

	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	data_layer=pd.read_sql_query("SELECT correlative FROM layers ORDER BY middle;",conn)

	for name in sorted(wells):
		data_block=pd.read_sql_query("SELECT blockcorr FROM t2wellblock  WHERE well='%s' ORDER BY blockcorr;"%name,conn)
		string=""
		if len(data_block)>0:
			for n in sorted(data_layer['correlative'].values):
				string+="%s\n"%(n+data_block['blockcorr'].values[0])

		subprocess.call(['./shell/blocks_evol_times.sh',string,name])

	conn.close()

"""
write_PT_from_t2output(db_path)
extract_json_from_t2out()
from_sav_to_json()
"""

write_PT_of_wells_from_t2output_in_time(db_path)
#PTjson_to_sqlite(source="t2")#source="sav",t2

