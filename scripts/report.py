import sys
from model_conf import *
import sqlite3
import t2resfun as t2r
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import os
import math
import matplotlib.gridspec as gridspec
from scipy.interpolate import griddata
import json
from matplotlib.backends.backend_pdf import PdfPages
import datetime
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import matplotlib.tri as mtri

def plot_compare_one(db_path,name,inpath):
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

	in_file="/%s_PT.dat"%(inpath,name)

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

def print_layer_from_json(layer,method,ngridx,ngridy,save,show,print_points,print_eleme_name,variable_to_plot,source,print_mesh):

	variables_to_plot_t2={"P":4,
						   "T":5,
						   "SG":6,
						   "SW":7,
						   "X1":8,
						   "X2":9,
						   "PCAP":10,
						   "DG":11,
						   "DW":12}

	variables_to_plot_sav={"P":3,
	                       "T":4}

	if source=="sav":
		index=variables_to_plot_sav[variable_to_plot]
		file="../output/PT/json/PT_json_from_sav.txt"
	elif source=="t2":
		index=variables_to_plot_t2[variable_to_plot]
		file="../output/PT/json/PT_json.txt"

	if os.path.isfile(file):
		with open(file,"r") as f:
	  		data=json.load(f)
	  	
	  	element_name=[]
		x=[]
		y=[]
		z=[]
		variable=[]

		variable_min=100E8
		variable_max=0

		for elementx in data:
			if variable_max<data[elementx][index]:
				variable_max=data[elementx][index]

			if variable_min>data[elementx][index]:
				variable_min=data[elementx][index]

			if layer==elementx[0]:
				x.append(data[elementx][0])
				y.append(data[elementx][1])
				z.append(data[elementx][2])
				variable.append(data[elementx][index])
				element_name.append(elementx)


		variable_levels=np.linspace(variable_min,variable_max,num=10)

		xi = np.linspace(min(x), max(x), ngridx)
		yi = np.linspace(min(y), max(y), ngridy)

		zi = griddata((x, y), variable, (xi[None,:], yi[:,None]), method=method)

		fig=plt.figure(figsize=(10,8))

		ax1=fig.add_subplot(1,1,1)

		if variable_levels[0]!=variable_levels[-1]:
			ax1.contour(xi,yi,zi,15,linewidths=0.5,colors='k',levels=variable_levels)

			cntr3 = ax1.contourf(xi,yi,zi,15,cmap="jet",levels=variable_levels)
		else:
			ax1.contour(xi,yi,zi,15,linewidths=0.5,colors='k')
			cntr3 = ax1.contourf(xi,yi,zi,15,cmap="jet")

		fig.colorbar(cntr3,ax=ax1)

		if print_points:
			ax1.plot(x,y,'ok',ms=1)

		if print_eleme_name:
			for n in range(len(element_name)):
				ax1.text(x[n],y[n], element_name[n], color='k',fontsize=4)

		if print_mesh:
			mesh_segment=open("../mesh/to_steinar/segmt","r")
			lines_x=[]
			lines_y=[]
			for line in mesh_segment:
				lines_x.append([float(line[0:15]),float(line[30:45])])
				lines_y.append([float(line[15:30]),float(line[45:60])])

			ax1.plot(np.array(lines_x).T,np.array(lines_y).T,'-k',linewidth=1,alpha=0.75)

		ax1.tick_params(axis='both', which='major', labelsize=6,pad=1)
		ax1.set_ylabel('North [m]',fontsize = 8)
		ax1.set_xlabel('East [m]',fontsize=8)
		ax1.set_title("Layer %s"%layer,fontsize=10)

		if save:
			fig.savefig("../output/PT/images/layer_%s_%s.png"%(layer,variable_to_plot)) 
		if show:
			plt.show()
	else:
		print "The PT_json file does not exist, run extract_json_from_t2out  or from_sav_to_json from output.py first"

def plot_compare_PT_curr_prev(db_path,name,inpath,previnpath,show):

	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	fontsizex=10

	fontsize_layer=8

	#Define plot

	fig= plt.figure(figsize=(8.27, 11.69), dpi=100)

	axT=fig.add_subplot(121)

	axP=fig.add_subplot(122)

	#Real data
	data_PT_real=pd.read_sql_query("SELECT well, MeasuredDepth, Pressure, Temperature FROM PT WHERE well='%s';"%name,conn)


	x_T,y_T,z_T,var_T=t2r.MD_to_TVD_one_var_array(name,data_PT_real['Temperature'].values,data_PT_real['MeasuredDepth'].values,100)

	ln1T=axT.plot(var_T,z_T,'-r',linewidth=1,label='Measured')

	x_P,y_P,z_P,var_P=t2r.MD_to_TVD_one_var_array(name,data_PT_real['Pressure'].values,data_PT_real['MeasuredDepth'].values,100)

	ln1P=axP.plot(var_P,z_P,'-b',linewidth=1,label='Measured')

	#Model

	in_file="%s/%s_PT.dat"%(inpath,name)

	prev_in_file="%s/%s_PT.dat"%(previnpath,name)

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

	if os.path.isfile(prev_in_file):

		data=pd.read_csv(prev_in_file)

		blk_num=data['ELEM'].values

		TVD_elem=[0 for n in range(len(blk_num))]
		TVD_elem_top=[0 for n in range(len(blk_num))]

		for n in range(len(blk_num)):
			TVD_elem[n]=float(pd.read_sql_query("SELECT middle FROM layers WHERE correlative='%s';"%data['ELEM'].values[n][0],conn)['middle'])
			TVD_elem_top[n]=float(pd.read_sql_query("SELECT top FROM layers WHERE correlative='%s';"%data['ELEM'].values[n][0],conn)['top'])

		ln3T=axT.plot(data['T'],TVD_elem,'.',linewidth=1,label='Calculated previous', color="orangered")

		ln3P=axP.plot(data['P']/1E5,TVD_elem,'.',linewidth=1,label='Calculated previous', color="indigo")

		lnsT = ln1T+ln2T+ln3T

		labsT = [l.get_label() for l in lnsT]

		axT.legend(lnsT, labsT, loc='upper right', fontsize=fontsizex)

		axT.set_xlabel('Temperature [C]',fontsize=fontsizex)

		axT.xaxis.set_label_coords(0.5,1.1)

		axT.xaxis.tick_top()

		axT.set_ylabel('m.a.s.l.',fontsize = fontsizex)

		axT.tick_params(axis='both', which='major', labelsize=fontsizex,pad=1)
		

		lnsP = ln1P+ln2P+ln3P

		labsP = [l.get_label() for l in lnsP]

		axP.legend(lnsP, labsP, loc='upper right', fontsize=fontsizex)
		
		axP.set_xlabel('Pressure [bar]',fontsize=fontsizex)

		axP.xaxis.set_label_coords(0.5,1.1)

		axP.xaxis.tick_top()

		axP.tick_params(axis='both', which='major', labelsize=fontsizex,pad=1)

		fig.suptitle("%s"%name, fontsize=fontsizex)
	
	if  os.path.isfile(prev_in_file) and  os.path.isfile(in_file):
		fig.savefig('../calib/PT/images/PT_%s.png'%name) 

	if show:
		plt.show()

	return fig

def compare_runs_PT(wells,db_path):

	pdf_pages=PdfPages('../calib/PT/run_'+str(datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S'))+'.pdf')
	for name in sorted(wells):
		print name
		fig=plot_compare_PT_curr_prev(db_path,name,"../output/PT/txt","../output/PT/txt/prev",show=False)
		pdf_pages.savefig(fig)

	d = pdf_pages.infodict()
	d['Title'] = 'CGA Calibration Model Plots'
	d['Author'] = 'O&MReservorios'
	d['Subject'] = 'TEST'
	d['Keywords'] = 'Model, TOUGH2'
	d['CreationDate'] = datetime.datetime.today()
	d['ModDate'] = datetime.datetime.today()

	# Write the PDF document to the disk
	pdf_pages.close()

def plot_all_layer():
	layer_coor=[]
	for l in layers:
		layer_coor.append(layers[l][0])

	for layer in layer_coor:
		print_layer_from_json(layer,'cubic',1000,1000,save=True,show=False,print_points=True,print_eleme_name=False,\
			variable_to_plot="P",source="t2",print_mesh=False)

def vertical_cross_section(method,ngridx,ngridy,variable_to_plot,source,show_wells):

	x_points=[405000,420000,408000]
	y_points=[304000,310000,318000]

	variables_to_plot_t2={"P":4,
						   "T":5,
						   "SG":6,
						   "SW":7,
						   "X1":8,
						   "X2":9,
						   "PCAP":10,
						   "DG":11,
						   "DW":12}

	variables_to_plot_sav={"P":3,
	                       "T":4}

	if source=="sav":
		index=variables_to_plot_sav[variable_to_plot]
		file="../output/PT/json/PT_json_from_sav.txt"
	elif source=="t2":
		index=variables_to_plot_t2[variable_to_plot]
		file="../output/PT/json/PT_json.txt"

	if os.path.isfile(file):
		with open(file,"r") as f:
	  		data=json.load(f)
	  	

	variable_min=100E8
	variable_max=0

	irregular_grid=np.array([[0,0,0]])
	variable=np.array([])
	for elementx in data:
		if variable_max<data[elementx][index]:
			variable_max=data[elementx][index]

		if variable_min>data[elementx][index]:
			variable_min=data[elementx][index]

		irregular_grid=np.append(irregular_grid,[[data[elementx][0],data[elementx][1],data[elementx][2]]],axis=0)
		variable=np.append(variable,data[elementx][index])


	irregular_grid=irregular_grid[1:]

	variable=variable[0:]

	x=np.array([])
	y=np.array([])
	


	for xy in range(len(x_points)):
		if xy < len(x_points)-1:
			xt=np.linspace(x_points[xy],x_points[xy+1]+(x_points[xy+1]-x_points[xy])/ngridx,num=ngridx)
			yt=np.linspace(y_points[xy],y_points[xy+1]+(y_points[xy+1]-y_points[xy])/ngridy,num=ngridy)
			x=np.append(x,xt)
			y=np.append(y,yt)

	projection_req=np.array([0])
	for npr in range(1,len(x)):
		if npr==len(x)-1:
			break
		if npr==1:
			delta_x_pr=(x_points[0]-x[0])**2
			delta_y_pr=(y_points[0]-y[0])**2
			prj_prox=(delta_y_pr+delta_x_pr)**0.5
		else:
			delta_x_pr=(x[npr+1]-x[npr])**2
			delta_y_pr=(y[npr+1]-y[npr])**2
			prj_prox=(delta_y_pr+delta_x_pr)**0.5
		projection_req=np.append(projection_req,prj_prox+projection_req[npr-1])

	ztop,zlabels, zmid,zbottom=t2r.vertical_layer(layers,z0_level)

	xi = np.linspace(min(x), max(x), ngridx)
	yi = np.linspace(min(y), max(y), ngridy)
	zi = np.array(zmid)


	proj_req=np.array([])
	z_req_proj=np.array([])

	for nprj in range(len(projection_req)):
		for nz in range(len(zi)):
			proj_req=np.append(proj_req,projection_req[nprj])
			z_req_proj=np.append(z_req_proj,zi[nz])

	request_points=np.array([[0,0,0]])
	x_req=np.array([])
	y_req=np.array([])
	z_req=np.array([])


	for nx in range(len(x)):
		for nz in range(len(zi)):
			request_points= np.append(request_points,[[x[nx],y[nx],zi[nz]]],axis=0)
			x_req=np.append(x_req,x[nx])
			y_req=np.append(y_req,y[nx])
			z_req=np.append(z_req,zi[nz])

	request_points=request_points[1:]

	requested_values = griddata(irregular_grid, variable, request_points)

	"""
	request_prj_grid=np.array([[0,0]])
	for nx in range(len(proj_req)):
		for nz in range(len(z_req_proj)):
			request_prj_grid= np.append(request_prj_grid,[[proj_req[nx],z_req_proj[nz]]],axis=0)

	request_prj_grid=request_prj_grid[1:]
	"""
	
	xi_pr = np.linspace(min(proj_req), max(proj_req), 1000)
	yi_pr = np.linspace(min(z_req_proj), max(z_req_proj), 1000)
	zi_pr = griddata((proj_req, z_req_proj), requested_values[:-len(zmid)], (xi_pr[None,:], yi_pr[:,None]))

	fig = plt.figure()

	#Plot projection
	
	ax = fig.add_subplot(211)

	ax.contour(xi_pr,yi_pr,zi_pr,15,linewidths=0.5,colors='k')
	cntr = ax.contourf(xi_pr,yi_pr,zi_pr,15,cmap="jet")
	ax.plot(proj_req,z_req_proj,'ok',ms=0.5)

	fig.colorbar(cntr,ax=ax)

	#Scatter 3D

	ax3D = fig.add_subplot(212, projection='3d')

	colorbar_source=ax3D.scatter3D(x_req,y_req,z_req,cmap='jet',c=requested_values)

	ax3D.set_xlabel('East [m]')
	ax3D.set_ylabel('North [m]')
	ax3D.set_zlabel('m.a.s.l.')
	fig.colorbar(colorbar_source, ax=ax3D)

	#Plot wells on 3D

	if show_wells:
		conn=sqlite3.connect(db_path)
		c=conn.cursor()

		for name in sorted(wells):
			data_position=pd.read_sql_query("SELECT east,north,elevation FROM wells WHERE well='%s';"%name,conn)
			data=pd.read_sql_query("SELECT MeasuredDepth FROM survey WHERE well='%s' ORDER BY MeasuredDepth;"%name,conn)
			
			ax3D.text(data_position['east'][0], data_position['north'][0], data_position['elevation'][0], \
				      name, color='black',alpha=0.75,fontsize=8)

			x_real=[]
			y_real=[]
			z_real=[]

			for v in range(len(data['MeasuredDepth'])):
				xf,yf,zf=t2r.MD_to_TVD(name,data['MeasuredDepth'][v])
				x_real.append(float(xf))
				y_real.append(float(yf))
				z_real.append(float(zf))
		
			ax3D.plot3D(x_real, y_real, z_real,'-k',alpha=0.75)

	plt.show()
	
	

vertical_cross_section(method='cubic',ngridx=100,ngridy=100,variable_to_plot="P",source="t2",show_wells=True)



#plot_all_layer()

name='AH-34'
db_path='../input/model.db'
inpath="../output/PT/txt"

#compare_runs_PT(wells,db_path)

#plot_compare_one(db_path,name,inpath)
"""
typePT='T'
image_save_all_plots(db_path,wells,typePT) #typePT, could be T or P
"""