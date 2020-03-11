import matplotlib.pyplot as plt
import matplotlib.tri as tri
import numpy as np
import pandas as pd
from scipy.interpolate import griddata
import json
import os
from model_conf import *

def extract_json_from_t2out():
	elemefile=open("../mesh/from_amesh/eleme","r")

	eleme_dict={}
	for line in elemefile:
		if len(line.split(" "))!=1:
			eleme_dict[line.split(" ")[0].rstrip()]=[float(line.split(" ")[-3].rstrip()),
													float(line.split(" ")[-2].rstrip()),
													float(line.split(" ")[-1].rstrip())]
	elemefile.close()

	last=""
	t2file=open("../model/t2/t2.out","r")
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



def print_layer_from_json(layer,method,ngridx,ngridy,save,show,print_points,print_eleme_name,plot_type):

	if os.path.isfile("../output/PT/json/PT_json.txt"):
		with open("../output/PT/json/PT_json.txt") as f:
	  		data=json.load(f)
	  	element_name=[]
		x=[]
		y=[]
		z=[]
		P=[]
		T=[]

		Tmax=0
		Tmin=1000
		Pmax=0
		Pmin=100E8

		for elementx in data:
			if Tmax<data[elementx][5]:
				Tmax=data[elementx][5]

			if Tmin>data[elementx][5]:
				Tmin=data[elementx][5]

			if Pmax<data[elementx][4]:
				Pmax=data[elementx][4]

			if Pmin>data[elementx][4]:
				Pmin=data[elementx][4]

			if layer==elementx[0]:
				x.append(data[elementx][0])
				y.append(data[elementx][1])
				z.append(data[elementx][2])
				P.append(data[elementx][4])
				T.append(data[elementx][5])
				element_name.append(elementx)


		T_levels=np.linspace(Tmin,Tmax,num=10)

		P_levels=np.linspace(Pmin,Pmax,num=10)

		#ngridx=1000
		#ngridy=1000
		xi = np.linspace(min(x), max(x), ngridx)
		yi = np.linspace(min(y), max(y), ngridy)

		if plot_type=="T":
			zi = griddata((x, y), T, (xi[None,:], yi[:,None]), method=method)
			levels=T_levels
		elif plot_type=="P":
			zi = griddata((x, y), P, (xi[None,:], yi[:,None]), method=method)
			levels=P_levels


		fig=plt.figure(figsize=(10,8))

		ax1=fig.add_subplot(1,1,1)


		#lev=[230,231,232,233,234,235,236,237,238,239,240,241,242,243,244,245,246,247,248,249,250,251,252,253,254,255,256,257]

		ax1.contour(xi,yi,zi,15,linewidths=0.5,colors='k',levels=levels)
		#ax1.contour(xi,yi,zi,15,linewidths=0.5,colors='k')
		cntr3 = ax1.contourf(xi,yi,zi,15,cmap="jet",levels=levels)
		#cntr3 = ax1.contourf(xi,yi,zi,15,cmap="jet",levels=lev)

		fig.colorbar(cntr3,ax=ax1)

		if print_points:
			ax1.plot(x,y,'ok',ms=1)

		if print_eleme_name:
			for n in range(len(element_name)):
				ax1.text(x[n],y[n], element_name[n], color='k',fontsize=4)

		ax1.tick_params(axis='both', which='major', labelsize=6,pad=1)
		ax1.set_ylabel('North [m]',fontsize = 8)
		ax1.set_xlabel('East [m]',fontsize=8)
		ax1.set_title("Layer %s"%layer,fontsize=10)

		if save:
			if plot_type=="T":
				fig.savefig("../output/PT/images/layer_%s_T.png"%layer) 
			elif plot_type=="P":
				fig.savefig("../output/PT/images/layer_%s_P.png"%layer) 
		if show:
			plt.show()
	else:
		print "The PT_json file does not exist, run extract_json_from_t2out first"


def plot_all_layer():
	layer_coor=[]
	for l in layers:
		layer_coor.append(layers[l][0])

	for layer in layer_coor:
		print layer
		print_layer_from_json(layer,'cubic',1000,1000,save=True,show=False,print_points=True,print_eleme_name=True,plot_type="T")


plot_all_layer()