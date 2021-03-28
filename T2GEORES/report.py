from T2GEORES import formats as formats
from T2GEORES import geometry as geometry
from T2GEORES import writer as t2w
import sys
import sqlite3
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
import matplotlib.dates as mdates
import subprocess
from scipy import interpolate
import vtk
import numpy as np
from scipy.spatial import ConvexHull

def plot_compare_one(well,savefig, no_real_data, data, TVD_elem, TVD_elem_top,axT,axP,PT_real_dictionary,layer_bottom,limit_layer,input_dictionary,label=None,def_colors=True):
	"""It generates two plots, they compare real downhole temperature and pressure measurements with model output 

	Parameters
	----------
	well : str
	  Selected well
	savefig : bool
	  If true the plot is saved on ../output/PT/images/logging/
	PT_real_dictionary : dictionary
	  Contains real  measurements on temperature, pressure and measure depth
	no_real_data : bool
	  If True, no real measurements are provides
	data : pandas dataframe
	  Contains model output information for each element assigned to a well
	TVD_elem : array
	  Contains the masl data at the middle for each element assigned to a well
	TVD_elem_top : array
	  Contains the masl data at the top  for each element assigned to a well
	axT : matplotlib_axis
	  Framework where temperature data is plotted
	axP : matplotlib_axis
	  Framework where temperature data is plotted
	layer_bottom : array
	  Contains the masl data at the bottom for each element assigned to a well
	limit_layer : str
	  Layer correlative at which plotting stops
	input_dictionary: dictionary
	  Contains the information of the top level of the mesh on under the key 'z_ref'
	label : str
	  Contains the legend of the plotted line
	def_colors : True
	  If True uses the colors defined on formats

	Returns
	-------
	image
		PT_{well}.png: on the path../output/PT/images/logging
	matplotlib_axis
	    axT: contains real and simulated downhole temperature data
	matplotlib_axis
	    axP: contains real and simulated downhole pressure data

	Note
	----
	It is used in combination of the function plot_compare_one_data

	"""

	fontsize_plot=8
	fontsize_layer=6

	z_ref=input_dictionary['z_ref']

	#Define plot

	if not no_real_data:

		#Plotting real data

		ln1T=axT.plot(PT_real_dictionary['var_T'],PT_real_dictionary['z_T'],marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=1,label='Measured')

		ln1P=axP.plot(PT_real_dictionary['var_P'],PT_real_dictionary['z_P'],marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=1,label='Measured')

		lnsT = ln1T

		lnsP = ln1P

	#Plotting the calculated data

	ln2T=axT.plot(data['T'],TVD_elem,linestyle='None',marker=formats.plot_conf_marker['current'][0],label='Calculated %s'%label)

	ln2P=axP.plot(data['P']/1E5,TVD_elem,linestyle='None',marker=formats.plot_conf_marker['current'][0],label='Calculated %s'%label)

	if def_colors:
		color_real_T=formats.plot_conf_color['T'][0]
		color_real_P=formats.plot_conf_color['P'][0]

		ln1T.set_color(color_real_T)
		ln2T.set_color(color_real_T)

		ln1P.set_color(color_real_P)
		ln2P.set_color(color_real_P)

	axT.set_ylim([layer_bottom[limit_layer],z_ref])

	axP.set_ylim([layer_bottom[limit_layer],z_ref])

	#Preparing the layer axis side for pressure

	ax2P = axP.twinx()

	ax2P.set_yticks(TVD_elem_top,minor=True)

	ax2P.set_yticks(TVD_elem,minor=False)

	ax2P.tick_params(axis='y',which='major',length=0)

	ax2P.yaxis.grid(True, which='minor',linestyle='--', color='grey', alpha=0.1, lw=0.5)

	ax2P.set_yticklabels(data['correlative'],fontsize=fontsize_layer)

	ax2P.set_ylim(axP.get_ylim())

	#Preparing the layer axis side for temperature

	ax2T = axT.twinx()

	ax2T.set_yticks(TVD_elem_top,minor=True)

	ax2T.set_yticks(TVD_elem,minor=False)
	
	ax2T.tick_params(axis='y',which='major',length=0)

	ax2T.set_yticklabels(data['correlative'],fontsize=fontsize_layer)

	ax2T.yaxis.grid(True, which='minor',linestyle='--', color='grey', alpha=0.1, lw=0.5)

	ax2T.set_ylim(axT.get_ylim())

	#Preparing the legends on temperature side
	if no_real_data:
		lnsT=ln2T
	else:
		lnsT+=ln2T

	labsT = [l.get_label() for l in lnsT]

	#axT.legend(lnsT, labsT, loc='upper right', fontsize=fontsize_plot)

	axT.legend(loc='upper right',fontsize=fontsize_plot)

	axT.set_xlabel('Temperature [$^\circ$C]',fontsize=fontsize_plot)

	axT.xaxis.set_label_coords(0.5,1.05)

	axT.xaxis.tick_top()

	axT.set_ylabel('m.a.s.l.',fontsize = fontsize_plot)

	axT.tick_params(axis='both', which='major', labelsize=fontsize_plot,pad=1)

	#Preparing the legends on pressure side
	if no_real_data:
		lnsP=ln2P
	else:
		lnsP+=ln2P

	labsP = [l.get_label() for l in lnsP]

	#axP.legend(lnsP, labsP, loc='upper right', fontsize=fontsize_plot)
	
	axP.legend(loc='upper right', fontsize=fontsize_plot)

	axP.set_xlabel('Pressure [bar]',fontsize=fontsize_plot)

	axP.xaxis.set_label_coords(0.5,1.05)

	axP.xaxis.tick_top()

	axP.tick_params(axis='both', which='major', labelsize=fontsize_plot,pad=1)

	#Title for both plots

	#plt.subplots_adjust(top=0.92)

	if savefig:
		fig.savefig('../output/PT/images/logging/PT_%s.png'%well)

def plot_compare_one_data(well,input_dictionary,inpath="../output/PT/txt"):
	"""Compiles real and output for temperature and pressure data 

	Parameters
	----------	  
	well : str
	  Selected well
	input_dictionary : dictionary
	  Dictionary contaning the path and name of database on keyword 'db_path'
	inpath : str
	  Constains path for input files. Default value is "../output/PT/txt"

	Returns
	-------
	PT_real_dictionary : dictionary
	  Contains real  measurements on temperature, pressure and measure depth
	no_real_data : bool
	  If True, no real measurements are provides
	data : pandas dataframe
	  Contains model output information for each element assigned to a well
	TVD_elem : array
	  Contains the masl data at the middle for each element assigned to a well
	TVD_elem_top : array
	  Contains the masl data at the top  for each element assigned to a well
	layer_bottom : array
	  Contains the masl data at the bottom for each element assigned to a well

	Note
	----
	The real data is taken from the the sqlite database

	"""

	conn=sqlite3.connect(input_dictionary['db_path'])
	c=conn.cursor()

	PT_real_dictionary={}

	try:

		#Plotting real data
		data_PT_real=pd.read_sql_query("SELECT well, MeasuredDepth, Pressure, Temperature FROM PT WHERE well='%s';"%well,conn)

		x_T,y_T,z_T,var_T=geometry.MD_to_TVD_one_var_array(well,data_PT_real['Temperature'].values,data_PT_real['MeasuredDepth'].values,100)

		x_P,y_P,z_P,var_P=geometry.MD_to_TVD_one_var_array(well,data_PT_real['Pressure'].values,data_PT_real['MeasuredDepth'].values,100)

		PT_real_dictionary['x_T']=x_T
		PT_real_dictionary['y_T']=y_T
		PT_real_dictionary['z_T']=z_T
		PT_real_dictionary['var_T']=var_T

		PT_real_dictionary['x_P']=x_P
		PT_real_dictionary['y_P']=y_P
		PT_real_dictionary['z_P']=z_P
		PT_real_dictionary['var_P']=var_P

		no_real_data=False

	except ValueError:

		data_PT_real=None

		no_real_data=True

		print("No real data for %s"%well)

	#Preparing the input file from the t2 results

	in_file="%s/%s_PT.dat"%(inpath,well)

	if os.path.isfile(in_file):

		data=pd.read_csv(in_file)

		data[['correlative']]=data.ELEM.apply(lambda x: pd.Series(str(x)[0]))

		data.sort_values(by='correlative' , inplace=True)

		#Retrieving the layers information from model_conf

		layers_info=geometry.vertical_layers(input_dictionary)

		TVD_elem=layers_info['middle']

		TVD_elem_top=layers_info['top']

		layer_bottom={layers_info['name'][n]:layers_info['bottom'][n] for n in range(len(layers_info['name']))}

		conn.close()

		return data_PT_real, no_real_data, data, TVD_elem, TVD_elem_top, PT_real_dictionary, layer_bottom

	else:
		sys.exit("The file %s or directory do not exist"%in_file)

def image_save_all_plots(typePT,input_dictionary,width=4,height=4.5):
	"""It plots all the wells defined on input_dictionay and compare real data with model output
	
	Parameters
	----------	  
	db_path : str
	  Direccion de base de datos sqlite, tomado de model_conf
	input_dictionary : dictionary
	 Dictionary contaning the path and name of database on keyword 'db_path', list of wells under the keywords 'WELLS', 'MAKE_UP_WELLS' and 'NOT_PRODUCING_WELL'. Lastly, it contains the information of the top level of the mesh on under the key 'z_ref'
	typePT : str
	  'T' for temperature or 'P' for pressure
	height : float
	  Defines the ratio height/width
	width  : float
	  By dividing the number of wells defines the number of rows on the chart


	Returns
	-------
	image
		{typePT}_all.png: on path ../output/PT/images/logging/

	Note
	----
	The real data is taken from the the sqlite database. Depending on the number of wells defined the default values for width and height migth be changed

	Examples
	--------
	>>> image_save_all_plots(typePT='T',input_dictionary)
	"""

	wells=[]

	for key in ['WELLS','MAKE_UP_WELLS','NOT_PRODUCING_WELL']:
		try:
			for well in input_dictionary[key]:
				wells.append(well)
		except KeyError:
			pass

	db_path=input_dictionary['db_path']

	limit_layer='M'

	fontsizex=4

	fontsize_layer=3

	rows=int(math.ceil(len(wells)/width))

	widths=[1 for n in range(width)]

	#heights=[int(2*(40.0/3)*len(widths)/int(math.ceil(len(wells)/3.0)))+1 for n in range(int(math.ceil(len(wells)/3.0)))]

	heights=[height for n in range(rows)]

	#gs = gridspec.GridSpec(nrows=len(heights), ncols=len(widths), width_ratios=widths, height_ratios=heights,hspace=0.8, wspace=0.7)

	gs = gridspec.GridSpec(nrows=rows, ncols=4,width_ratios=widths, height_ratios=heights,hspace=0.5, wspace=0.25)

	fig= plt.figure(figsize=(8.5,rows*3), dpi=100)

	fig.suptitle("%s Calculated vs  %s Measured"%(typePT,typePT), fontsize=10)

	conn=sqlite3.connect(db_path)

	c=conn.cursor()

	layers_info=geometry.vertical_layers()

	layer_bottom={layers_info['name'][n]:layers_info['bottom'][n] for n in range(len(layers_info['name']))}

	TVD_elem=layers_info['middle']

	TVD_elem_top=layers_info['top']

	ymin=float(pd.read_sql_query("SELECT bottom FROM layers WHERE correlative='%s';"%limit_layer,conn)['bottom'])

	if typePT in ['P','T']:
		if typePT=='P':
			data_to_extract='Pressure'
			label_name='Pressure [bar]'
			data_lims=[0,150]
			divisor=1E5
		elif typePT=='T':
			data_to_extract='Temperature'
			data_lims=[50,260]
			divisor=1
			label_name='Temperature [$^\circ$C]'

		for i, name in enumerate(wells):

			#Real data
			data_PT_real=pd.read_sql_query("SELECT well, MeasuredDepth, Pressure, Temperature FROM PT WHERE well='%s';"%name,conn)

			if len(data_PT_real)>0:

				x_T,y_T,z_T,var_T=geometry.MD_to_TVD_one_var_array(name,data_PT_real[data_to_extract].values,data_PT_real['MeasuredDepth'].values,100)

				#Define plot

				axT= fig.add_subplot(gs[i])
				
				ln1T=axT.plot(var_T,z_T,color=formats.plot_conf_color[typePT][0],marker=formats.plot_conf_marker['real'][0],linewidth=1,ms=0.5,label='Measured')

				#Model

				in_file="../output/PT/txt/%s_PT.dat"%name

				if os.path.isfile(in_file):

					data=pd.read_csv(in_file)

					blk_num=data['ELEM'].values

					data[['correlative']]=data.ELEM.apply(lambda x: pd.Series(str(x)[0]))

					data.sort_values(by='correlative' , inplace=True)

					ln2T=axT.plot(np.array(data[typePT])/divisor,np.array(TVD_elem),linestyle='None',color=formats.plot_conf_color[typePT][0],marker=formats.plot_conf_marker['current'][0],ms=1,label='Calculated')

					axT.set_ylim([layer_bottom[limit_layer],z_ref])
					
					axT.set_xlim(data_lims)

					ax2T = axT.twinx()

					ax2T.set_yticks(TVD_elem_top,minor=True)

					ax2T.set_yticks(TVD_elem,minor=False)
					
					ax2T.tick_params(axis='y',which='major',length=0)

					ax2T.set_yticklabels(data['correlative'],fontsize=fontsize_layer)

					ax2T.yaxis.grid(True, which='minor',linestyle='--', color='grey', alpha=0.1, lw=0.5)

					ax2T.set_ylim(axT.get_ylim())

					lnsT = ln1T+ln2T

					labsT = [l.get_label() for l in lnsT]

					axT.legend(lnsT, labsT, loc='lower left', fontsize=fontsizex)

					axT.set_xlabel('%s\n %s'%(name,label_name),fontsize=fontsizex+2)

					axT.xaxis.set_label_coords(0.5,1.3)

					axT.yaxis.set_label_coords(-0.07,0.5)

					axT.xaxis.tick_top()

					axT.set_ylabel('m.a.s.l.',fontsize = fontsizex)

					axT.tick_params(axis='both', which='major', labelsize=fontsizex,pad=1)

					plt.draw()

		plt.subplots_adjust(top=0.9)

		fig.savefig("../report/images/PT/%s_all.png"%typePT) 
	else:
		sys.exit("There is no real data for the parameter selected: %s "%typePT)

def to_paraview(input_dictionary,itime=None):
	"""
	It generates a vtu file to be read on Paraview for different time output including all the parameters from each block.

	Parameters
	----------
 	input_dictionary: dictionary
	  Contains the information of the layers on the model
	itime: float
	  It defines a time at which a the parameters from the blocks are extracted into json file. Must be on the same units as the TOUGH2 output files (days, seconds, etc.)

	Returns
	-------
	file
	  to_paraview.vtu: on ../mesh
	"""

	segmt_json_file='../mesh/segmt.json'

	if os.path.isfile(segmt_json_file):
		with open(segmt_json_file) as file:
		  	blocks=json.load(file)
	else:
		sys.exit("The file %s or directory do not exist, run segmnt_to_json from regeo_mesh"%segmt_json_file)		

	ugrid=vtk.vtkUnstructuredGrid()
	block_name=vtk.vtkStringArray()
	block_name.SetName('block')

	rocktype=vtk.vtkStringArray()
	rocktype.SetName('rocktype')

	layers_dict=geometry.vertical_layers(input_dictionary)

	layers_name={}

	for j, layer in enumerate(layers_dict['name']):
		layers_name[layer]=[layers_dict['top'][j],layers_dict['bottom'][j]]

	points_vtk=vtk.vtkPoints()

	cnt=0
	for block in blocks:

		faceId=vtk.vtkIdList()
		block_name.InsertNextValue(block)
		rocktype.InsertNextValue(blocks[block]['rocktype'])
		points=[]
		for i, point in enumerate(blocks[block]['points']):
			if i%2==0:
				point_x=point
			elif i%2==1:
				point_y=point

			if i%2==1 and i!=0 and [point_x,point_y] not in points:
				points.append([point_x,point_y])

		points=np.array(points)
		hull = ConvexHull(points)

		dict_points={}
		
		cnt_int=0
		for n in range(len(points[hull.vertices,0])):
			dict_points[n]=[points[hull.vertices,0][::-1][n],points[hull.vertices,1][::-1][n],layers_name[block[0]][0]]
			cnt_int+=1

		for n in range(len(points[hull.vertices,0])):
			dict_points[n+len(points)]=[points[hull.vertices,0][::-1][n],points[hull.vertices,1][::-1][n],layers_name[block[0]][1]]
			cnt_int+=1

		for key in dict_points:
			points_vtk.InsertNextPoint(dict_points[key])

		faceId.InsertNextId(len(points)+2)

		faces=[[] for n in range(len(points)+2)]
		faces[0]=[face+cnt for face in range(len(points))]
		faces[1]=[face+len(points)+cnt for face in range(len(points))]
		
		for nx in range(len(points)):
			if nx+1<len(points):
				faces[nx+2]=[nx+cnt,nx+len(points)+cnt,nx+1+len(points)+cnt,nx+1+cnt]
			else:
				faces[nx+2]=[nx+cnt,nx+len(points)+cnt,nx+cnt+1,cnt]
		
		cnt+=cnt_int
		
		for face in faces:
			faceId.InsertNextId(len(face))
			[faceId.InsertNextId(i) for i in face]

		ugrid.InsertNextCell(vtk.VTK_POLYHEDRON,faceId)
		ugrid.GetCellData().AddArray(block_name)
		ugrid.GetCellData().AddArray(rocktype)

	ugrid.SetPoints(points_vtk)

	series={"file-series-version":"1.0",
			"files":[],
			}

	src_directory='../output/PT/json/evol'
	src_files = os.listdir(src_directory)
	files_dictionary={}
	for file_name in src_files:
		time=file_name.split("_")[2].split(".j")[0]
		full_file_name = os.path.join(src_directory, file_name)
		files_dictionary[time]=full_file_name

	if itime==None:
		if files_dictionary:
			for t in files_dictionary.keys():
				file_name=src_directory+'/t2_output_%s.json'%t
				with open(file_name) as file:
				  	data_time_n=json.load(file)

				temperature=vtk.vtkFloatArray()
				temperature.SetName('temperature')

				pressure=vtk.vtkFloatArray()
				pressure.SetName('pressure')

				for block in blocks:
					pressure.InsertNextValue(float(data_time_n[t][block]['P'])/1E5)
					temperature.InsertNextValue(float(data_time_n[t][block]['T']))
					ugrid.GetCellData().AddArray(pressure)
					ugrid.GetCellData().AddArray(temperature)

				writer=vtk.vtkXMLUnstructuredGridWriter()
				writer.SetInputData(ugrid)
				writer.SetFileName('../output/vtu/model_%s.vtu'%t)
				series["files"].append({"name":"mesh_%s.vtu"%t,"time":float(t)})
				writer.SetDataModeToAscii()
				writer.Update()

				writer.Write()

			with open("../output/vtu/model_.vtu.series","w") as f:
				json.dump(series,f)
		else:
			sys.exit("There are no json files generated, run t2_to_json from output")		
	else:
		if not files_dictionary:
			file_name=src_directory+'/t2_output_%6.5E.json'%itime
			with open(file_name) as file:
			  	data_time_n=json.load(file)

			temperature=vtk.vtkFloatArray()
			temperature.SetName('temperature')

			pressure=vtk.vtkFloatArray()
			pressure.SetName('pressure')

			for block in blocks:
				pressure.InsertNextValue(float(data_time_n[t][block]['P'])/1E5)
				temperature.InsertNextValue(float(data_time_n[t][block]['T']))
				ugrid.GetCellData().AddArray(pressure)
				ugrid.GetCellData().AddArray(temperature)

			writer=vtk.vtkXMLUnstructuredGridWriter()
			writer.SetInputData(ugrid)
			writer.SetFileName('../output/vtu/model_%s.vtu'%t)
			series["files"].append({"name":"mesh_%6.5E.vtu"%itime,"time":float(itime)})
			writer.SetDataModeToAscii()
			writer.Update()

			writer.Write()

			with open("../output/vtu/model_.vtu.series","w") as f:
				json.dump(series,f)

def vertical_cross_section(method,ngridx,ngridy,variable_to_plot,source,show_wells_3D,print_point,savefig,plots_conf,input_dictionary):
	"""It Generates a vertical cross section for a specified parameter on a defined path.

	Parameters
	----------	   
	ngridx : int
	  Number of element on the horizontal direction
	ngridy : int
	  Number of element on the vertical direction
	show_wells_3D : bool
	  If true the wells are shown on 3D
	print_point : bool
	  If true prints the points where the interpolation has taken place.
	variable_to_plot : str
	  Variable to plot: "P","T","SG","SW","X1","X2","PCAP,""DG" y "DW" for 't2' source; "P" and "T" for 'sav' source
	source: str
	  't2' or 'sav'
	savefig : bool
	  If true the plot is saved
	plots_conf: dictionary
	  With key words 'cross_section' defines the points of a lines for the vertical section. 'variables_level' defines the variable values to plot
	input_dictionary: dictioanary
	  Contains the 'LAYERS' keyword

	Returns
	-------
	image
		vertical_section_{varible_to_plot}.png: on '../output/PT/images/

	Note
	----
	The point should not be defined on a well coordinate.

	Examples
	--------
	>>> plots_conf={'cross_section':{'x':[5000,5000,7500],'y':[3000,7250,7250]},'variable_levels':[25,50,75,100,125,150,170,180,200,220,230,250,260]}
	>>> input_dictionary={'LAYERS':{1:['A',100],2:['B', 100],3:['C', 125]}}
	>>> vertical_cross_section(ngridx=100,ngridy=100,variable_to_plot="T",source="t2",show_wells_3D=True)
	"""
	x_points=plots_conf['cross_section']['x']
	y_points=plots_conf['cross_section']['y']
	variable_levels=plots_conf['variable_levels']

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

	#Creates an irregular grid with the form [[x,y,z],[x1,y1,z1]]
	irregular_grid=np.array([[0,0,0]])
	variable=np.array([])
	for elementx in data:
		if variable_max<data[elementx][variable_to_plot]:
			variable_max=data[elementx][variable_to_plot]

		if variable_min>data[elementx][variable_to_plot]:
			variable_min=data[elementx][variable_to_plot]

		irregular_grid=np.append(irregular_grid,[[data[elementx]['X'],data[elementx]['Y'],data[elementx]['Z']]],axis=0)
		variable=np.append(variable,data[elementx][variable_to_plot])


	irregular_grid=irregular_grid[1:]
	variable=variable[0:]


	#Creates the points a long the lines
	x=np.array([])
	y=np.array([])
	
	for xy in range(len(x_points)):
		if xy < len(x_points)-1:
			xt=np.linspace(x_points[xy],x_points[xy+1]+(x_points[xy+1]-x_points[xy])/ngridx,num=ngridx)
			yt=np.linspace(y_points[xy],y_points[xy+1]+(y_points[xy+1]-y_points[xy])/ngridy,num=ngridy)
			x=np.append(x,xt)
			y=np.append(y,yt)

	#Calculastes the distance of every point along the projection

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

	layers_info=geometry.vertical_layers(input_dictionary)

	zmid=layers_info['middle']

	ztop=layers_info['top']

	zbottom=layers_info['bottom']

	zlabels=layers_info['name']

	#Creates the regular  mesh in 3D along all the layers

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

	#Creates regular mesh on projection

	xi_pr = np.linspace(min(proj_req), max(proj_req), 1000)
	yi_pr = np.linspace(min(z_req_proj), max(z_req_proj), 1000)
	zi_pr = griddata((proj_req, z_req_proj), requested_values[:-len(zmid)], (xi_pr[None,:], yi_pr[:,None]))

	fig = plt.figure()

	#Plot projection
	
	ax = fig.add_subplot(211)


	ax.text(0,1.05, "A",color='black',transform=ax.transAxes)
	ax.text(1,1.05, "A'",color='black',transform=ax.transAxes)
	ax.set_xlabel('distance [m]')
	ax.set_ylabel('masl')

	contourax=ax.contour(xi_pr,yi_pr,zi_pr,15,linewidths=0.5,colors='k',levels=variable_levels)
	cntr = ax.contourf(xi_pr,yi_pr,zi_pr,15,cmap="jet",levels=variable_levels)
	
	if print_point:
		ax.plot(proj_req,z_req_proj,'ok',ms=0.5)
	
	ax.clabel(contourax, inline=1, fontsize=6,fmt='%10.0f',colors="k")

	cbar=fig.colorbar(cntr,ax=ax)
	cbar.set_label('Temperature [$^\circ$C]') #Fix it
	#Scatter 3D

	ax3D = fig.add_subplot(212, projection='3d')

	colorbar_source=ax3D.scatter3D(x_req,y_req,z_req,cmap='jet',c=requested_values)

	ax3D.set_xlabel('East [m]')
	ax3D.set_ylabel('North [m]')
	ax3D.set_zlabel('m.a.s.l.')
	fig.colorbar(colorbar_source, ax=ax3D)
	

	#Projects well on slice
	conn=sqlite3.connect(input_dictionary['db_path'])
	c=conn.cursor()

	for name in sorted(input_dictionary['WELLS']):
		data_position=pd.read_sql_query("SELECT east,north,elevation FROM wells WHERE well='%s';"%name,conn)
		data=pd.read_sql_query("SELECT MeasuredDepth FROM survey WHERE well='%s' ORDER BY MeasuredDepth;"%name,conn)

		x_real=[]
		y_real=[]
		z_real=[]
		well_proj=[]

		for v in range(len(data['MeasuredDepth'])):
			xf,yf,zf=geometry.MD_to_TVD(name,data['MeasuredDepth'][v])
			x_real.append(float(xf))
			y_real.append(float(yf))
			z_real.append(float(zf))
		
		for ny in range(len(y_points)):
			if data_position['north'][0]>y_points[ny]:
				position=ny
				bx=x_points[position+1]-x_points[position]
				by=y_points[position+1]-y_points[position]
				br=(bx**2+by**2)**0.5
		
	
		for n_proj in range(len(x_real)):
			delta_x=x_real[n_proj]-x_points[position]
			delta_y=y_real[n_proj]-y_points[position]
			r=(delta_y**2+delta_x**2)**0.5
			proj_w=((bx*delta_x)+(by*delta_y))/br
			print(n_proj)
			well_proj.append(proj_w)
			if n_proj==0:
				d=(r**2-proj_w**2)**0.5
		if d<200:
			ax.annotate(name,
            xy=(well_proj[0], z_real[0]), 
            xytext=(well_proj[0]+200, z_real[0]), 
            arrowprops=dict(arrowstyle="->",
                            connectionstyle="arc3"),
            )
			ax.plot(well_proj,z_real,'-k',ms=0.5)
		
	conn.close()


	#Plot wells on 3D

	if show_wells_3D:
		conn=sqlite3.connect(input_dictionary['db_path'])
		c=conn.cursor()

		for name in sorted(input_dictionary['WELLS']):
			data_position=pd.read_sql_query("SELECT east,north,elevation FROM wells WHERE well='%s';"%name,conn)
			data=pd.read_sql_query("SELECT MeasuredDepth FROM survey WHERE well='%s' ORDER BY MeasuredDepth;"%name,conn)
			
			ax3D.text(data_position['east'][0], data_position['north'][0], data_position['elevation'][0], \
				      name, color='black',alpha=0.75,fontsize=8)

			x_real=[]
			y_real=[]
			z_real=[]

			for v in range(len(data['MeasuredDepth'])):
				xf,yf,zf=geometry.MD_to_TVD(name,data['MeasuredDepth'][v])
				x_real.append(float(xf))
				y_real.append(float(yf))
				z_real.append(float(zf))
		
			ax3D.plot3D(x_real, y_real, z_real,'-k',alpha=0.75)

		conn.close()
	if savefig:
		fig.savefig('../output/PT/images/vertical_section_%s.png'%variable_to_plot) 

	plt.show()

def plot_evol_well_data(well,layer,parameter,input_dictionary):
	"""It generates the input data for a line type plot data, from model and real , for one parameter along the time from a reference date define on input_dictionary 

	Parameters
	----------	  
	well : str
	  Well name
	layer : str
	  Layer (level) at which the data will be extracted
	parameter : str
	  Variable to plot: "P","T","SG","SW","X1","X2","PCAP,""DG" y "DW"
	input_dictionary: dict
	  Dictionary with the keywords 'ref_date' (datetime type value) and 'db_path' (database path)

	Returns
	-------
	dictionary
		calculated: output data from model
	pandas.dataframe
		data_real: Real data (if exist)
	float
		depth: masl
	string
		header: Parameter keyword
	string
		parameter_label: parameter label
	string
		parameter_unit: Parameter unit

	Note
	----
	it generates the input data for the function plot_evol_well_lines
	"""
	if parameter  not in ["P","T","SG","SW","X(WAT1)","X(WAT2)","PCAP","DG","DW"]:
		print("Cant be printed, the parameter is  not register")
	elif parameter=="P":
		parameter_label="Pressure"
		parameter_unit="bar"
		file="../input/drawdown/%s_DD.dat"%well
		header='pressure'
	elif parameter=="T":
		parameter_label="Temperature"
		parameter_unit="C"
		file="../input/cooling/%s_C.dat"%well
		header='temperature'

	elif parameter=="SW":
		parameter_label="1-Quality"
		parameter_unit=""
	elif parameter=="SG":
		parameter_label="Quality"
		parameter_unit=""
	elif parameter=="DG":
		parameter_label="Density"
		parameter_unit="kg/m3"
	elif parameter=="DW":
		parameter_label="Density"
		parameter_unit="kg/m3"
	else:
		parameter_label=""
		parameter_unit=""

	color_real=formats.plot_conf_color[parameter][0]
	color_calc=formats.plot_conf_color[parameter][1]
	#Read file, calculated
	file="../output/PT/evol/%s_PT_%s_evol.dat"%(well,layer)
	data=pd.read_csv(file)

	times=data['TIME']

	values=data[parameter]

	dates=[]
	values_to_plot=[]
	for n in range(len(times)):
		if float(times[n])>0:
			try:
				dates.append(input_dictionary['ref_date']+datetime.timedelta(days=int(times[n])))
				if parameter!="P":
					values_to_plot.append(values[n])
				else:
					values_to_plot.append(values[n]/1E5)
					
			except OverflowError:
				print(input_dictionary['ref_date'],"plus",str(times[n]),"wont be plot")

	conn=sqlite3.connect(input_dictionary['db_path'])
	c=conn.cursor()

	depth=pd.read_sql_query("SELECT middle FROM layers WHERE correlative='%s';"%layer,conn)

	depth=depth.values[0][0]


	#Read file, real
	
	try:
		check_res=False
		if parameter=="P":
			if well!='AH-25' or layer!='E':
				file="../input/drawdown/%s_DD.dat"%well
			elif well=='AH-25' and layer=='E':
				file="../input/drawdown/p_res.csv"
				check_res=True
		elif parameter=="T":	
			file="../input/cooling/%s_C.dat"%well

		data_real=pd.read_csv(file)
		
	except IOError:
		data_real=None
		print("No real data exist")
		pass


	calculated={'dates':dates,'values':values_to_plot}

	return calculated,data_real,depth,header,parameter_label,parameter_unit

def plot_evol_well_lines(calculated,real_data,parameter,depth,header,well,layer,parameter_unit,parameter_label,label,ax,input_dictionary,years=15,color_def=False):
	"""It generates the input data for a line type plot data, from model and real , for one parameter along the time from a reference date define on input_dictionary 

	Parameters
	----------	 
	calculated: dict
		Output data from model
	pandas.dataframe
		data_real: Real data (if exist)
	float
		depth: masl
	header: str
		Parameter keyword
	parameter_label: str
		parameter label
	parameter_unit: str
		parameter_unit: Parameter unit
	well : str
	  Well name
	layer : str
	  Layer (level) at which the data will be extracted
	parameter : str
	  Variable to plot: "P","T","SG","SW","X1","X2","PCAP,""DG" y "DW"
	input_dictionary: dict
	  Dictionary with the keywords 'ref_date' (datetime type value) and 'db_path' (database path)
	years: float
	  Number of years after the ref_date to be plotted on the chart
	color_def: bool
	  If true default colors are use from the formats module

	Returns
	-------
	matplotlib_axis
		ax: contains real and simulated for the selected paramter along the time

	Note
	----
		It is use in combination with the function plot_evol_well_data
	"""
	dates_func=lambda datesX: datetime.datetime.strptime(datesX, "%Y-%m-%d %H:%M:%S")
	
	line,=ax.plot(calculated['dates'],calculated['values'],'-o',linewidth=1,ms=2,label='Calculated %s'%label)
	if color_def:
		color=formats.plot_conf_color[parameter][1]
		line.set_color(color)

	if real_data!=None:
		dates_real=list(map(dates_func,real_data.loc[real_data['TVD']==depth]['datetime'].values))
		ax.plot(dates_real,real_data.loc[real_data['TVD']==depth][header].values,marker=formats.plot_conf_marker['real'][0],linestyle='None',color=formats.plot_conf_color[parameter][0],linewidth=1,ms=3,label='Real %s'%well)

	ax.set_title("Well: %s at %s masl (layer %s)"%(well,depth,layer) ,fontsize=8)
	ax.set_xlabel("Time",fontsize = 8)
	ax.set_ylabel('%s [%s]'%(parameter_label,parameter_unit),fontsize = 8)

	ax.legend(loc="upper right")

	xlims=[input_dictionary['ref_date'],input_dictionary['ref_date']+datetime.timedelta(days=years*365.25)]
	
	ax.format_xdata = mdates.DateFormatter('%Y%-m-%d %H:%M:%S')

	years = mdates.YearLocator()
	years_fmt = mdates.DateFormatter('%Y')

	ax.set_xlim(xlims)
	
	ax.xaxis.set_major_formatter(years_fmt)

	#Grid style
	ax.yaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
	ax.xaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
	ax.grid(True)

