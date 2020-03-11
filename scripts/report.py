import sys
from model_conf import *
import sqlite3
import t2resfun as t2r
import pandas as pd
import matplotlib.pyplot as plt
import os
import math
import matplotlib.gridspec as gridspec
from scipy.interpolate import griddata
import json


def plot_compare_one(db_path,name):
	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	#Define plot

	fig= plt.figure(figsize=(12, 96), dpi=300)

	axT=fig.add_subplot(121)

	axP=fig.add_subplot(122)

	#Real data
	data_PT_real=pd.read_sql_query("SELECT well, MeasuredDepth, Pressure, Temperature FROM PT WHERE well='%s';"%name,conn)

	x_T,y_T,z_T,var_T=t2r.MD_to_TVD_one_var_array(name,data_PT_real['Temperature'].values,data_PT_real['MeasuredDepth'].values,100)

	ln1T=axT.plot(var_T,z_T,'-r',linewidth=1,label='Measured')

	x_P,y_P,z_P,var_P=t2r.MD_to_TVD_one_var_array(name,data_PT_real['Pressure'].values,data_PT_real['MeasuredDepth'].values,100)

	ln1P=axP.plot(var_P,z_P,'-b',linewidth=1,label='Measured')

	#Model

	in_file="../output/PT/txt/%s_PT.dat"%name

	if os.path.isfile(in_file):

		data=pd.read_csv(in_file)

		blk_num=data['ELEM'].values

		TVD_elem=[0 for n in range(len(blk_num))]
		TVD_elem_top=[0 for n in range(len(blk_num))]

		for n in range(len(blk_num)):
			TVD_elem[n]=float(pd.read_sql_query("SELECT middle FROM layers WHERE correlative='%s';"%data['ELEM'].values[n][0],conn)['middle'])
			TVD_elem_top[n]=float(pd.read_sql_query("SELECT top FROM layers WHERE correlative='%s';"%data['ELEM'].values[n][0],conn)['top'])

		ln2T=axT.plot(data['T'],TVD_elem,'+r',linewidth=1,label='Calculated')

		ln2P=axP.plot(data['P']/1E5,TVD_elem,'+b',linewidth=1,label='Calculated')

		ax2P = axP.twinx()

		layer_corr=[data['ELEM'].values[n][0] for n in range(len(blk_num))]

		fontsizex=4

		fontsize_layer=3

		ax2P.set_yticks(TVD_elem_top,minor=True)

		ax2P.set_yticks(TVD_elem,minor=False)

		ax2P.tick_params(axis='y',which='major',length=0)

		ax2P.yaxis.grid(True, which='minor',linestyle='--', color='grey', alpha=0.1, lw=0.5)

		ax2P.set_yticklabels(layer_corr,fontsize=fontsize_layer)

		ax2P.set_ylim(axP.get_ylim())


		ax2T = axT.twinx()

		ax2T.set_yticks(TVD_elem_top,minor=True)

		ax2T.set_yticks(TVD_elem,minor=False)
		
		ax2T.tick_params(axis='y',which='major',length=0)

		ax2T.set_yticklabels(layer_corr,fontsize=fontsize_layer)

		ax2T.yaxis.grid(True, which='minor',linestyle='--', color='grey', alpha=0.1, lw=0.5)

		ax2T.set_ylim(axT.get_ylim())

		lnsT = ln1T+ln2T

		labsT = [l.get_label() for l in lnsT]

		axT.legend(lnsT, labsT, loc='upper right', fontsize=fontsizex)

		axT.set_xlabel('Temperature [C]',fontsize=fontsizex)

		axT.xaxis.set_label_coords(0.5,1.1)

		axT.xaxis.tick_top()

		axT.set_ylabel('m.a.s.l.',fontsize = fontsizex)

		axT.tick_params(axis='both', which='major', labelsize=fontsizex,pad=1)
		

		lnsP = ln1P+ln2P

		labsP = [l.get_label() for l in lnsP]

		axP.legend(lnsP, labsP, loc='upper right', fontsize=fontsizex)
		
		axP.set_xlabel('Pressure [bar]',fontsize=fontsizex)

		axP.xaxis.set_label_coords(0.5,1.1)

		axP.xaxis.tick_top()

		axP.tick_params(axis='both', which='major', labelsize=fontsizex,pad=1)

		fig.suptitle("%s"%name, fontsize=fontsizex)


		plt.show()

		fig.savefig('../output/PT/images/PT_%s.png'%name) 

def image_save_all_plots(db_path,wells,typePT):
	#Maybe hspace, wspace, and the set_label_coords will always  need to be adjust

	widths=[2,2,2]

	heights=[int(2*(40.0/3)*len(widths)/int(math.ceil(len(wells)/3.0)))+1 for n in range(int(math.ceil(len(wells)/3.0)))]

	gs = gridspec.GridSpec(nrows=len(heights), ncols=len(widths), width_ratios=widths, height_ratios=heights,hspace=0.2, wspace=0.15)

	fig= plt.figure(figsize=(12, 96), dpi=300,constrained_layout=True)

	fig.suptitle("%s Calculated vs  %s Measured"%(typePT,typePT), fontsize=10)

	conn=sqlite3.connect(db_path)

	c=conn.cursor()
		

	cnt=0
	for name in wells:

		#Real data
		data_PT_real=pd.read_sql_query("SELECT well, MeasuredDepth, Pressure, Temperature FROM PT WHERE well='%s';"%name,conn)

		if len(data_PT_real)>0:

			x_T,y_T,z_T,var_T=t2r.MD_to_TVD_one_var_array(name,data_PT_real['Temperature'].values,data_PT_real['MeasuredDepth'].values,100)

			#Define plot

			axT= fig.add_subplot(gs[cnt])
			
			ln1T=axT.plot(var_T,z_T,'-r',linewidth=1,label='Measured')

			#Model

			in_file="../output/PT/txt/%s_PT.dat"%name

			if os.path.isfile(in_file):

				data=pd.read_csv(in_file)

				blk_num=data['ELEM'].values

				TVD_elem=[0 for n in range(len(blk_num))]
				TVD_elem_top=[0 for n in range(len(blk_num))]

				for n in range(len(blk_num)):
					TVD_elem[n]=float(pd.read_sql_query("SELECT middle FROM layers WHERE correlative='%s';"%data['ELEM'].values[n][0],conn)['middle'])
					TVD_elem_top[n]=float(pd.read_sql_query("SELECT top FROM layers WHERE correlative='%s';"%data['ELEM'].values[n][0],conn)['top'])

				ln2T=axT.plot(data[typePT],TVD_elem,'+r',linewidth=1,ms=3,label='Calculated')

				layer_corr=[data['ELEM'].values[n][0] for n in range(len(blk_num))]

				fontsizex=4

				fontsize_layer=3

				ax2T = axT.twinx()

				ax2T.set_yticks(TVD_elem_top,minor=True)

				ax2T.set_yticks(TVD_elem,minor=False)
				
				ax2T.tick_params(axis='y',which='major',length=0)

				ax2T.set_yticklabels(layer_corr,fontsize=fontsize_layer)

				ax2T.yaxis.grid(True, which='minor',linestyle='--', color='grey', alpha=0.1, lw=0.5)

				ax2T.set_ylim(axT.get_ylim())

				lnsT = ln1T+ln2T

				labsT = [l.get_label() for l in lnsT]

				axT.legend(lnsT, labsT, loc='upper right', fontsize=fontsizex)

				if typePT=='P':
					label_name='Pressure [bar]'
				elif typePT=='T':
					label_name='Temperature [C]'

				axT.set_xlabel('%s, %s'%(name,label_name),fontsize=fontsizex+2)

				axT.xaxis.set_label_coords(0.5,1.1)

				axT.yaxis.set_label_coords(-0.07,0.5)

				axT.xaxis.tick_top()

				axT.set_ylabel('m.a.s.l.',fontsize = fontsizex)

				axT.tick_params(axis='both', which='major', labelsize=fontsizex,pad=1)

				plt.draw()

				cnt+=1

	fig.savefig('../output/PT/images/T_all.png') 

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
		print_layer_from_json(layer,'cubic',1000,1000,save=True,show=False,print_points=True,print_eleme_name=True,plot_type="P")


plot_all_layer()

name='AH-34A'
db_path='../input/model.db'
"""
plot_compare_one(db_path,name)
typePT='T'
image_save_all_plots(db_path,wells,typePT) #typePT, could be T or P
"""