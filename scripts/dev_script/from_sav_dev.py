import os
import json

def from_sav_to_json():

	if os.path.isfile("../mesh/from_amesh/eleme"):
		elemefile=open("../mesh/from_amesh/eleme","r")
	eleme_dict={}
	for line in elemefile:
		if len(line.split(" "))!=1:
			eleme_dict[line.split(" ")[0].rstrip()]=[float(line.split(" ")[-3].rstrip()),
													float(line.split(" ")[-2].rstrip()),
													float(line.split(" ")[-1].rstrip())]
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

from_sav_to_json()