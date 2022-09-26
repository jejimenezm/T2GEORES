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
from scipy import stats
from scipy.stats import norm
from iapws import IAPWS97


plt.style.use('T2GEORES')

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

def image_save_all_plots(typePT,input_dictionary,width=3,height=6):
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
	z_ref=input_dictionary['z_ref']

	limit_layer='U'

	fontsizex=4

	fontsize_layer=3

	rows=int(math.ceil(len(wells)/width))

	widths=[1 for n in range(width)]

	#heights=[int(2*(40.0/3)*len(widths)/int(math.ceil(len(wells)/3.0)))+1 for n in range(int(math.ceil(len(wells)/3.0)))]

	heights=[height for n in range(rows)]

	#gs = gridspec.GridSpec(nrows=len(heights), ncols=len(widths), width_ratios=widths, height_ratios=heights,hspace=0.8, wspace=0.7)

	gs = gridspec.GridSpec(nrows=rows, ncols=width,width_ratios=widths, height_ratios=heights,hspace=0.5, wspace=1)

	fig= plt.figure(figsize=(8.5,rows*4), dpi=100,constrained_layout=True)

	fig.suptitle("%s Calculated vs  %s Measured"%(typePT,typePT), fontsize=10)

	conn=sqlite3.connect(db_path)

	c=conn.cursor()

	layers_info=geometry.vertical_layers(input_dictionary)

	layer_bottom={layers_info['name'][n]:layers_info['bottom'][n] for n in range(len(layers_info['name']))}

	layer_middle={layers_info['name'][n]:layers_info['middle'][n] for n in range(len(layers_info['name']))}

	layer_top={layers_info['name'][n]:layers_info['top'][n] for n in range(len(layers_info['name']))}

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
			data_lims=[30,300]
			divisor=1
			label_name='Temperature [$^\circ$C]'

		for i, name in enumerate(wells):

			#Real data
			data_PT_real=pd.read_sql_query("SELECT well, MeasuredDepth, Pressure, Temperature FROM PT WHERE well='%s' ORDER BY MeasuredDepth DESC;"%name,conn)
			data_PT_real.replace(0, np.nan, inplace=True)

			if len(data_PT_real)>0:

				x_T,y_T,z_T,var_T=geometry.MD_to_TVD_one_var_array(name,data_PT_real[data_to_extract].values,data_PT_real['MeasuredDepth'].values)

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

					#ln2T=axT.plot(np.array(data[typePT])/divisor,np.array(TVD_elem)
					zs=[]
					for bz in data['ELEM']:
						zs.append(layer_middle[bz[0]])

					zp=[]
					for bz in data['ELEM']:
						zp.append(layer_top[bz[0]])

					ln2T=axT.plot(np.array(data[typePT])/divisor,zs,linestyle='None',color=formats.plot_conf_color[typePT][0],marker=formats.plot_conf_marker['current'][0],ms=1,label='Calculated')

					axT.set_ylim([layer_bottom[limit_layer],z_ref])
					
					axT.set_xlim(data_lims)

					ax2T = axT.twinx()

					ax2T.set_yticks(zp,minor=True)

					ax2T.set_yticks(zs,minor=False)
					
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

					axT.yaxis.set_label_coords(-0.2,0.5)

					axT.tick_params(axis='both', which='major', labelsize=fontsizex,pad=1)

					plt.draw()
				else:
					print("File does not exist")

			else:
				print("No data for %s"%name)

		plt.subplots_adjust(top=0.9)

		fig.savefig("../output/PT/images/%s_all.png"%typePT) 
	else:
		sys.exit("There is no real data for the parameter selected: %s "%typePT)

def to_paraview(input_dictionary,itime=None, num = None):
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
		if not os.path.isdir(os.path.join(src_directory, file_name)):
			time=file_name.split("_")[2].split(".j")[0]
			full_file_name = os.path.join(src_directory, file_name)
			files_dictionary[time]=full_file_name
	print(files_dictionary)

	if num != None:
		positions = np.linspace(0, len(files_dictionary), num).astype(int)
	else:
		positions = range(len(files_dictionary))

	if itime==None:
		if files_dictionary:
			for ix, t in enumerate(files_dictionary.keys()):

				if ix in positions:
					file_name=src_directory+'/t2_output_%.0f.json'%float(t)
					with open(file_name) as file:
					  	data_time_n=json.load(file)

					print(data_time_n.keys())

					t = "%.1f"%float(t)

					data = {}
					for head in data_time_n[t][block]:
						if head != 'ELEM':
							data[head] = vtk.vtkFloatArray()
							data[head].SetName(head)

					#temperature=vtk.vtkFloatArray()
					#temperature.SetName('temperature')

					#pressure=vtk.vtkFloatArray()
					#pressure.SetName('pressure')

					for block in blocks:
						for head in data_time_n[t][block]:
							if head != 'ELEM':
								data[head].InsertNextValue(float(data_time_n[t][block][head]))
								ugrid.GetCellData().AddArray(data[head])

						#pressure.InsertNextValue(float(data_time_n[t][block]['P'])/1E5)
						#temperature.InsertNextValue(float(data_time_n[t][block]['T']))
						#ugrid.GetCellData().AddArray(pressure)
						#ugrid.GetCellData().AddArray(temperature)

					writer=vtk.vtkXMLUnstructuredGridWriter()
					writer.SetInputData(ugrid)
					writer.SetFileName('../output/vtu/model_%.0f.vtu'%float(t))
					series["files"].append({"name":"model_%.0f.vtu"%float(t),"time":float(t)})
					writer.SetDataModeToAscii()
					writer.Update()

					writer.Write()

			with open("../output/vtu/model_.vtu.series","w") as f:
				json.dump(series,f)
		else:
			sys.exit("There are no json files generated, run t2_to_json from output")		
	else:
		file_name=src_directory+'/t2_output_%.0f.json'%float(itime)
		with open(file_name) as file:
		  	data_time_n=json.load(file)

		print(data_time_n.keys())

		itime = "%.1f"%float(itime)

		data = {}
		for head in data_time_n[itime][block]:
			if head != 'ELEM':
				data[head] = vtk.vtkFloatArray()
				data[head].SetName(head)

		#temperature=vtk.vtkFloatArray()
		#temperature.SetName('temperature')

		#pressure=vtk.vtkFloatArray()
		#pressure.SetName('pressure')

		for block in blocks:
			for head in data_time_n[itime][block]:
				if head != 'ELEM':
					data[head].InsertNextValue(float(data_time_n[itime][block][head]))
					ugrid.GetCellData().AddArray(data[head])

			#pressure.InsertNextValue(float(data_time_n[t][block]['P'])/1E5)
			#temperature.InsertNextValue(float(data_time_n[t][block]['T']))
			#ugrid.GetCellData().AddArray(pressure)
			#ugrid.GetCellData().AddArray(temperature)

		writer=vtk.vtkXMLUnstructuredGridWriter()
		writer.SetInputData(ugrid)
		writer.SetFileName('../output/vtu/model_%.0f.vtu'%float(itime))
		writer.SetDataModeToAscii()
		writer.Update()

		writer.Write()

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

def cross_section_real_data(wells,ngrid,masl,PT,save_img,model_version):
	"""It Generates a vertical cross section for a specified parameter on a defined path.

	Parameters
	----------	   
	ngrid : int
	  Number of element on the horizontal/vertical direction
	wells : dict
	  Wells names
	masl : float
	  Desire depth for cross section
	PT   : string
	  'T' or 'P'
	save_img : bool
	  Selects weather the plot is save as image or not

	Returns
	-------
	image
		vertical_section_{varible_to_plot}.png: on '../output/PT/images/

	Note
	----
	The data comes from the text file. The function is meant to be use at the early stages of the model to check natural state

	"""

	if PT=='T':
		var_label='Temperature [$^\circ$C]'
		levels=[v for v in range(50,350,25)]
	elif PT=='P':
		var_label='Pressure [bar]'
		levels=[v for v in range(0,150,15)]
	else:
		sys.exit("Not listed variable")

	ngridx=ngrid
	ngridy=ngrid

	#Setting up the canvas
	fig= plt.figure(figsize=(12, 12), dpi=300)
	ax=fig.add_subplot(111)
	ax.set_aspect('equal')
	fig.suptitle("%s m.a.s.l."%masl, fontsize=4)
	plt.text(0.05,0.95,'model_version:'+model_version, transform=fig.transFigure, size=12)


	#Extracting the data
	src='../input/PT'
	src_files = os.listdir(src)
	var=[]
	x=[]
	y=[]
	platorm={}
	toremove=['A','B','C','D','ST']
	for well in wells:
		file_name=well+'_MDPT.dat'
		full_file_name=src+'/'+file_name

		if os.path.isfile(full_file_name):
			well=file_name.split('_')[0]
			data=pd.read_csv(full_file_name,sep=',')
			funcT=interpolate.interp1d(data['MD'],data[PT])

			try:
				if not math.isnan(funcT(geometry.TVD_to_MD(well,masl))):
					var.append(funcT(geometry.TVD_to_MD(well,masl)))
					x.append(geometry.MD_to_TVD(well,geometry.TVD_to_MD(well,masl))[0])
					y.append(geometry.MD_to_TVD(well,geometry.TVD_to_MD(well,masl))[1])

					#Getting the plataform's name
					well_i=well
					for i in toremove:
						well_i=well_i.replace(i,'')
					
					#Plotting plataform name
					if well_i not in platorm.keys():
						platorm[well_i]=well_i
						ax.text(x[-1],y[-1],well_i,color='black',alpha=0.75,fontsize=3)
			except ValueError:
				pass


	#Resampling
	xi = np.linspace(min(x), max(x), ngridx)
	yi = np.linspace(min(y), max(y), ngridy)
	
	triangles=mtri.Triangulation(x,y)
	interpolator=mtri.LinearTriInterpolator(triangles,var)
	X,Y=np.meshgrid(xi,yi)
	zi=interpolator(X,Y)

	ax.plot(X, Y, 'k-', lw=0.1, alpha=0.1)
	ax.plot(X.T, Y.T, 'k-', lw=0.1, alpha=0.1)

	#Plotting the colormarp
	c=ax.contourf(xi,yi,zi,cmap="jet",levels=levels)
	cbar=fig.colorbar(c,ax=ax)

	#Plotting triangles
	ax.triplot(triangles,color='0.7',lw=0.25,alpha=0.5)

	#Setting up the colorbar
	cbar.set_label(var_label,fontsize=4)
	cbar.ax.tick_params(labelsize=4)

	#Setting up the axis
	ax.tick_params(axis='both', which='major', labelsize=4,pad=1)
	ax.set_xlabel('East [m]',fontsize = 4)
	ax.set_ylabel('North [m]',fontsize = 4)

	step=500
	ax.set_xlim([min(x)-step,max(x)+step])
	ax.set_ylim([min(y)-step,max(y)+step])

	plt.show()

	if save_img:
		fig.savefig("../input/PT/selection_PT/%s_%s_masl.png"%(PT,masl)) 

#Now well documented

def plot_compare_PT_curr_prev(db_path,name,ELEME,layers,inpath="../output/PT/txt",previnpath="../output/PT/txt/prev",show=False):
	"""
	Not documented
	"""
	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	fontsizex=10

	fontsize_layer=8

	#Define plot

	fig= plt.figure(figsize=(10, 12), dpi=300)

	axT=fig.add_subplot(121)

	axP=fig.add_subplot(122)

	col_name=['rocktype','data','R','G','B']
	rocks_colors=pd.read_csv("../mesh/to_steinar/rocks",delim_whitespace=True,names=col_name)
	rocks_colors.set_index('rocktype', inplace=True)

	#Real data
	data_PT_real=pd.read_sql_query("SELECT well, MeasuredDepth, Pressure, Temperature FROM PT WHERE well='%s' ORDER BY MeasuredDepth DESC;"%name,conn)

	if len(data_PT_real)>0:

		x_T,y_T,z_T,var_T=geometry.MD_to_TVD_one_var_array(name,data_PT_real['Temperature'].values,data_PT_real['MeasuredDepth'].values)

		ln1T=axT.plot(var_T,z_T,'-r',linewidth=1,label='Estimated ')

		x_P,y_P,z_P,var_P=geometry.MD_to_TVD_one_var_array(name,data_PT_real['Pressure'].values,data_PT_real['MeasuredDepth'].values)

		ln1P=axP.plot(var_P,z_P,'-b',linewidth=1,label='Estimated ')


	COF_PT_file = "../output/PT/json/COF_PT.json"
	if os.path.isfile(COF_PT_file):
		COF_PT = pd.read_json(COF_PT_file)

		axP_COF = axP.twiny()
		axT_COF = axT.twiny()

		COF_locations = [0, 0.2, 0.4, 0.6, 0.8, 1]

		# Move twinned axis ticks and label from top to bottom
		axT_COF.xaxis.set_ticks_position("top")
		axT_COF.xaxis.set_label_position("top")

		# Offset the twin axis below the host
		axT_COF.spines["top"].set_position(("axes", 1.03))

		# Turn on the frame for the twin axis, but then hide all 
		# but the bottom spine
		axT_COF.set_frame_on(True)
		axT_COF.patch.set_visible(False)

		for sp in axT_COF.spines.values():
		    sp.set_visible(False)
		axT_COF.spines["top"].set_visible(True)

		axT_COF.set_xticks(COF_locations)
		axT_COF.set_xlabel("COF")
		axT_COF.set_xlim([0,1])


		# Move twinned axis ticks and label from top to bottom
		axP_COF.xaxis.set_ticks_position("top")
		axP_COF.xaxis.set_label_position("top")

		# Offset the twin axis below the host
		axP_COF.spines["top"].set_position(("axes", 1.03))

		# Turn on the frame for the twin axis, but then hide all 
		# but the bottom spine
		axP_COF.set_frame_on(True)
		axP_COF.patch.set_visible(False)

		for sp in axP_COF.spines.values():
		    sp.set_visible(False)
		axP_COF.spines["top"].set_visible(True)

		axP_COF.set_xticks(COF_locations)
		axP_COF.set_xlabel("COF")

		axP_COF.set_xlim([0,1])
	else:
		print("No file on %s"%COF_PT_file)

	COF_PT_prev_file = "../output/PT/json/prev/COF_PT.json"
	if os.path.isfile(COF_PT_prev_file):
		COF_PT_prev = pd.read_json(COF_PT_prev_file)
	else:
		print("No file on %s"%COF_PT_prev_file)

	layers_block={layers['name'][n]:layers['middle'][n] for n in range(len(layers['name']))}

	#Model

	in_file="%s/%s_PT.dat"%(inpath,name)

	prev_in_file="%s/%s_PT.dat"%(previnpath,name)

	if os.path.isfile(in_file):

		data=pd.read_csv(in_file)

		if 'T' in data.columns:
			T_colum = 'T'
		elif 'TEMP' in data.columns:
			T_colum = 'TEMP'

		if 'P' in data.columns:
			P_colum = 'P'
		elif 'PRES_VAP' in data.columns:
			P_colum = 'PRES_VAP'


		blk_num=data['ELEM'].values

		TVD_elem=[0 for n in range(len(blk_num))]
		TVD_elem_top=[0 for n in range(len(blk_num))]
		TVD_elem_bottom=[0 for n in range(len(blk_num))]
		for n in range(len(blk_num)):
			TVD_elem[n]=float(pd.read_sql_query("SELECT middle FROM layers WHERE correlative='%s';"%data['ELEM'].values[n][0],conn)['middle'])
			TVD_elem_top[n]=float(pd.read_sql_query("SELECT top FROM layers WHERE correlative='%s';"%data['ELEM'].values[n][0],conn)['top'])
			TVD_elem_bottom[n]=float(pd.read_sql_query("SELECT bottom FROM layers WHERE correlative='%s';"%data['ELEM'].values[n][0],conn)['bottom'])

		if os.path.isfile(COF_PT_file):
			#COF plot
			T_COF=COF_PT[COF_PT['DATASET'].str.endswith("T-%s"%name)]
			P_COF=COF_PT[COF_PT['DATASET'].str.endswith("P-%s"%name)]

			T_COF['ELEME']=None
			T_COF['masl']=None
			for index, row in T_COF.iterrows():
				T_COF.loc[T_COF['DATASET']==row['DATASET'],'ELEME'] = row['DATASET'][0:5]
				T_COF.loc[T_COF['DATASET']==row['DATASET'],'masl'] = layers_block[row['DATASET'][0]]

			P_COF['ELEME']=None
			P_COF['masl']=None
			for index, row in P_COF.iterrows():
				P_COF.loc[P_COF['DATASET']==row['DATASET'],'ELEME'] = row['DATASET'][0:5]
				P_COF.loc[P_COF['DATASET']==row['DATASET'],'masl'] = layers_block[row['DATASET'][0]]

			lnCOFT = axT_COF.plot(T_COF['COF'],T_COF['masl'],'--+k',lw=0.2,ms=2,label = 'Current calculation')

			lnCOFP = axP_COF.plot(P_COF['COF'],P_COF['masl'],'--+',lw=0.2,ms=2, color = 'grey',label = 'Current calculation')

		#Rock types
		layers_block_limits = {layers['name'][n]:[layers['top'][n],layers['bottom'][n]] for n in range(len(layers['name']))}

		#like {'A':[500,400],'B': [400,300]}

		xs=[290,310]
		
		for iy,block in enumerate(blk_num):
			colori=rocks_colors.loc[ELEME[block]['MA1']]
			axT.fill_between(xs,layers_block_limits[block[0]][1],layers_block_limits[block[0]][0],alpha=0.5,color=[(colori['R']/255.0,colori['G']/255.0,colori['B']/255.0)])


		ln2T=axT.plot(data[T_colum],TVD_elem,'+r',linewidth=1,label='Current calculation')

		def tsat(y):
			try:
				val = IAPWS97(P=(y/1E6),x=0).T - 273.15
			except NotImplementedError:
				val = np.nan
			return val

		data['sat'] = data.apply(lambda y: tsat(y[P_colum]), axis = 1)

		ln2Tsat=axT.plot(data['sat'],TVD_elem,'sr',linewidth=1,label='T SAT', ms = 4)

		ln2P=axP.plot(data[P_colum]/1E5,TVD_elem,'+b',linewidth=1,label='Current calculation', ms = 4)

		if 'PSAT' in data.columns:
			ln2PSAT=axP.plot(data['PSAT']/1E5,TVD_elem,'sb',linewidth=1,label='PSAT')
			lgd_PSAT = True
		else:
			lgd_PSAT = False

	if os.path.isfile(prev_in_file):

		data=pd.read_csv(prev_in_file)

		if 'T' in data.columns:
			T_colum = 'T'
		elif 'TEMP' in data.columns:
			T_colum = 'TEMP'

		if 'P' in data.columns:
			P_colum = 'P'
		elif 'PRES_VAP' in data.columns:
			P_colum = 'PRES_VAP'


		blk_num=data['ELEM'].values


		TVD_elem=[0 for n in range(len(blk_num))]
		TVD_elem_top=[0 for n in range(len(blk_num))]

		for n in range(len(blk_num)):
			TVD_elem[n]=float(pd.read_sql_query("SELECT middle FROM layers WHERE correlative='%s';"%data['ELEM'].values[n][0],conn)['middle'])
			TVD_elem_top[n]=float(pd.read_sql_query("SELECT top FROM layers WHERE correlative='%s';"%data['ELEM'].values[n][0],conn)['top'])


		ln3T=axT.plot(data[T_colum],TVD_elem,'.',linewidth=1,label='Previously calculated', color="orangered")

		ln3P=axP.plot(data[P_colum]/1E5,TVD_elem,'.',linewidth=1,label='Previously calculated', color="indigo")


		if os.path.isfile(COF_PT_prev_file):
			#COF plot
			T_COF_prev=COF_PT_prev[COF_PT_prev['DATASET'].str.endswith("T-%s"%name)]
			P_COF_prev=COF_PT_prev[COF_PT_prev['DATASET'].str.endswith("P-%s"%name)]

			T_COF_prev['ELEME'] = None
			T_COF_prev['masl'] = None
			for index, row in T_COF_prev.iterrows():
				T_COF_prev.loc[T_COF_prev['DATASET']==row['DATASET'],'ELEME'] = row['DATASET'][0:5]
				T_COF_prev.loc[T_COF_prev['DATASET']==row['DATASET'],'masl'] = layers_block[row['DATASET'][0]]

			P_COF_prev['ELEME']=None
			P_COF_prev['masl']=None
			for index, row in P_COF_prev.iterrows():
				P_COF_prev.loc[P_COF_prev['DATASET']==row['DATASET'],'ELEME'] = row['DATASET'][0:5]
				P_COF_prev.loc[P_COF_prev['DATASET']==row['DATASET'],'masl'] = layers_block[row['DATASET'][0]]


			lnCOFT_prev=axT_COF.plot(T_COF_prev['COF'],T_COF_prev['masl'],'-+',lw=0.2,ms=2,color = 'teal', label = 'Previously calculated')

			lnCOFP_prev=axP_COF.plot(P_COF_prev['COF'],P_COF_prev['masl'],'-+',lw=0.2,ms=2, color = 'teal',label = 'Previously calculated')

		lnsT = ln2T+ln3T + ln2Tsat

		lnsP = ln2P+ln3P

		if os.path.isfile(COF_PT_file):
			lnsT += lnCOFT
			lnsP += lnCOFP

		if lgd_PSAT:
			lnsP+=ln2PSAT

		if os.path.isfile(COF_PT_prev_file):
			lnsP+=lnCOFP_prev
			lnsT+=lnCOFT_prev

		if len(data_PT_real)>0:
			lnsP+=ln1T
			lnsT+=ln1P

		labsT = [l.get_label() for l in lnsT]

		axT.legend(lnsT, labsT, loc='lower left', fontsize=fontsizex)

		labsP = [l.get_label() for l in lnsP]
	
		axP.legend(lnsP, labsP, loc='lower left', fontsize=fontsizex)

	if len(data_PT_real)>0:
		try:
			axT.set_ylim([sorted(TVD_elem_bottom)[0],sorted(TVD_elem_top)[-1]])
			axP.set_ylim([sorted(TVD_elem_bottom)[0],sorted(TVD_elem_top)[-1]])
		except UnboundLocalError:
			axT.set_ylim([-3000,550])
			axP.set_ylim([-3000,550])
			print(name)

	axT.set_xlim([20,305])
	axP.set_xlim([0,305])

	ax2P = axP.twinx()

	layer_corr=[data['ELEM'].values[n][0] for n in range(len(blk_num))]

	ax2P.set_yticks(TVD_elem_top,minor=True)

	ax2P.set_yticks(TVD_elem,minor=False)

	ax2P.tick_params(axis='y',which='major',length=0)

	ax2P.yaxis.grid(True, which='minor',linestyle='--', color='grey', alpha=0.5, lw=0.5)

	ax2P.set_yticklabels(layer_corr,fontsize=fontsize_layer)

	ax2P.set_ylim(axP.get_ylim())

	ax2T = axT.twinx()

	ax2T.set_yticks(TVD_elem_top,minor=True)

	ax2T.set_yticks(TVD_elem,minor=False)
	
	ax2T.tick_params(axis='y',which='major',length=0)

	ax2T.set_yticklabels(layer_corr,fontsize=fontsize_layer)

	ax2T.yaxis.grid(True, which='minor',linestyle='--', color='grey', alpha=0.5, lw=0.5)

	ax2T.set_ylim(axT.get_ylim())

	axT.set_xlabel('Temperature [C]',fontsize=fontsizex)

	axT.xaxis.set_label_coords(0.5,1.1)

	axT.xaxis.tick_top()

	axT.set_ylabel('m.a.s.l.',fontsize = fontsizex)

	axT.tick_params(axis='both', which='major', labelsize=fontsizex,pad=1)

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

def compare_runs_PT(input_dictionary,comment='', compare_wells = True):
	"""It generates a pdf for calibration pourposes, comparing current and previous data set

	Parameters
	----------	   
	input_dictionary : dict
		Contains well names, model version, db path and layers information.

	Returns
	-------
	pdf
		run_{date_time}.pdf: on '../calib/PT/run

	Note
	----
	Some other files such as ELEME.json, OBJ.json and COF_PT.json must be ready.

	"""

	db_path=input_dictionary['db_path']
	model_version=input_dictionary['model_version']
	wells=[]

	for key in ['WELLS','MAKE_UP_WELLS','NOT_PRODUCING_WELL']:
		try:
			for well in input_dictionary[key]:
				wells.append(well)
		except KeyError:
			pass

	pdf_pages=PdfPages('../calib/PT/run_'+str(datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S'))+'.pdf')

	layers=geometry.vertical_layers(input_dictionary)

	eleme_json_file='../mesh/ELEME.json'
	if os.path.isfile(eleme_json_file):
		with open(eleme_json_file) as file:
		  	ELEME=json.load(file)
	else:
		sys.exit("The file %s does not exist"%(eleme_json_file))

	if compare_wells:
		for name in sorted(wells):
			fig = plot_compare_PT_curr_prev(db_path,name,ELEME,layers,"../output/PT/txt","../output/PT/txt/prev",show=False)
			pdf_pages.savefig(fig)


	#Scatter plot

	fig= plt.figure(figsize=(24, 12), dpi=300)
	axT=fig.add_subplot(121)
	axP=fig.add_subplot(122)

	layers_block = {layers['name'][n]:layers['middle'][n] for n in range(len(layers['name']))}

	OBJ_PT_file = "../output/PT/json/it2_PT.json"
	if os.path.isfile(OBJ_PT_file):
		OBJ_PT = pd.read_json(OBJ_PT_file)

		data_T=[]
		data_P=[]

		for name in sorted(wells):
			in_file="%s/%s_PT.dat"%("../output/PT/txt",name)
			data=pd.read_csv(in_file)

			if 'T' in data.columns:
				T_colum = 'T'
			elif 'TEMP' in data.columns:
				T_colum = 'TEMP'

			if 'P' in data.columns:
				P_colum = 'P'
			elif 'PRES_VAP' in data.columns:
				P_colum = 'PRES_VAP'

			for index,row in data.iterrows():
				T_COF = OBJ_PT.loc[OBJ_PT['OBSERVATION']=="%s-T-%s"%(row['ELEM'],name),'MEASURED']
				P_COF = OBJ_PT.loc[OBJ_PT['OBSERVATION']=="%s-P-%s"%(row['ELEM'],name),'MEASURED']
				if len(P_COF)>0 and len(T_COF)>0:
					print(row[T_colum],float(T_COF.values[0]))
					data_T.append([row[T_colum],float(T_COF.values[0])])
					data_P.append([row[P_colum]/1E5,float(P_COF.values[0])/1E5])

		data_T=np.array(data_T)
		resT = stats.linregress(data_T[:,0],data_T[:,1])
		
		data_P=np.array(data_P)
		resP = stats.linregress(data_P[:,0],data_P[:,1])

		axT.plot(data_T[:,0],data_T[:,1],'or',linestyle='None')
		T_s=np.linspace(min(data_T[:,0]),max(data_T[:,0]),10)
		axT.plot(T_s,resT.slope*T_s+resT.intercept,'--k',label='%.2f*P+%.2f'%(resT.slope,resT.intercept))
		axT.set_xlim([50,320])
		axT.set_ylim([50,320])
		axT.set_ylabel('Calculated Temperature [C]')
		axT.set_xlabel('Measured Temperature [C]')
		axT.legend()

		axP.plot(data_P[:,0],data_P[:,1],'ob',linestyle='None')
		P_s=np.linspace(min(data_P[:,0]),max(data_P[:,0]),10)
		axP.plot(P_s,resP.slope*P_s+resP.intercept,'--k',label='%.2f*P+%.2f'%(resP.slope,resP.intercept))
		axP.set_xlim([0,250])
		axP.set_ylim([0,250])
		axP.set_ylabel('Calculated Pressure [bar]')
		axP.set_xlabel('Measured Pressure [bar]')
		axP.legend()

		pdf_pages.savefig()
		plt.close()

		#Histogram

		fig= plt.figure(figsize=(24, 12), dpi=300)
		ax=fig.add_subplot(121)
		ax2=fig.add_subplot(122)
		# An "interface" to matplotlib.axes.Axes.hist() method
		T_diff = (data_T[:,0]-data_T[:,1]) 
		n, bins, patches = ax.hist(x=T_diff, bins = 20, density = True, rwidth=0.85, color = "lightcoral")
		muT, stdT = norm.fit(T_diff)
		T_diff_x = np.linspace(min(T_diff), max(T_diff), 100)
		ax.plot(bins,norm.pdf(bins, muT, stdT),'--r')

		P_diff = (data_P[:,0]-data_P[:,1]) 
		n2, bins2, patches2 = ax2.hist(x=P_diff, bins = 20, density = True, width=0.85, color = "steelblue")
		P_diff_x = np.linspace(min(P_diff), max(P_diff), 100)
		muP, stdP = norm.fit(P_diff)
		ax2.plot(bins2,norm.pdf(bins2, muP, stdP),'--r')

		ax.set_xlabel('Diff [C]')
		ax.set_ylabel('Frequency')
		ax.set_title(r'$\mu = '+'%.2f ,'%muT+r'\sigma$ = '+'%.2f'%stdT)

		ax2.set_xlabel('Diff [bar]')
		ax2.set_ylabel('Frequency')
		ax2.set_title(r'$\mu = '+'%.2f ,'%muP+r'\sigma$ = '+'%.2f'%stdP)
		pdf_pages.savefig()
		plt.close()
	else:
		print("No file on %s"%OBJ_PT_file)

	#Objective function

	OBJ_file = "../output/PT/json/OBJ.json"
	if os.path.isfile(OBJ_file):
		OBJ = pd.read_json(OBJ_file)

		fig = plt.figure(figsize=(12,8))
		fig.clf()

		ax=fig.add_subplot(111)

		ax.plot(OBJ["TIME"],OBJ['OBJ'],'ok',ms=2,linestyle="None")

		labels = []
		for label in OBJ["TIME"].to_list():
			label = label.split('_')
			labels.append(label[0] + '\n' + label[1])

		ax.set_xticklabels(labels)

		ax.set_ylabel('Val')
		ax.set_xlabel('Time')

		ax.tick_params(axis='x', labelrotation=90,labelsize=6)

		pdf_pages.savefig()
		plt.close()

	else:
		print("No file on %s"%OBJ_file)


	if comment!='':
		firstPage = plt.figure(figsize=(10,12))
		firstPage.clf()
		firstPage.text(0.5,0.5,comment+'\n'+'model version: '+str(model_version), transform=firstPage.transFigure, size=10, ha="center")
		pdf_pages.savefig()
		plt.close()

	d = pdf_pages.infodict()
	d['Title'] = 'Calibration Model Plots'
	d['Author'] = 'EJ'
	d['Subject'] = 'BGF'
	d['Keywords'] = 'Model, TOUGH2, iTOUGH2, HÍ'
	d['CreationDate'] = datetime.datetime.today()
	d['ModDate'] = datetime.datetime.today()

	# Write the PDF document to the disk
	pdf_pages.close()

def plot_compare_mh(input_dictionary, well,block,source,save,show, production_dictionary, years = 35, variables = [], plot_feedzones = True):
	"""Genera una grafica donde compara la evolucion de flujo y entalpia para el bloque asignado a la fuente de un pozo en particular

	Parameters
	----------	  
	well : str
	  Nombre de pozo
	block : str
	  Nombre de bloque, en general donde se ubica zona de alimentacion
	source : str
	  Nombre de fuente asociada a pozo
	save : bool
	  Almacaena la grafica generada
	show : bool
	  Almacaena la grafica generada

	Returns
	-------
	image
		{well}_{block}_{source}_evol.png: archivo con direccion ../output/mh/images/

	Note
	----
	El archivo correspondiente en la carpeta  ../output/mh/txt debe existir

	Examples
	--------
	>>> plot_compare_mh('AH-1','DA110','SRC1',save=True,show=False)
	"""

	#Read file, current calculated
	file="../output/mh/txt/%s_%s_%s_evol_mh.dat"%(well,block,source)
	OBJ_file = "../output/PT/json/it2_PT.json"
	OBJ_file_prev = "../output/PT/json/prev/it2_PT.json"

	if os.path.isfile(file):

		fig = plt.figure(figsize=(10,4.5))
		ax = plt.subplot(111)
		ax1 = ax.twinx()

		line_index = 1

		#Section dedicated to wells with more with one feedzone. iT2 computes the weighted enthlapy and the flowrate sum for each timestep define on the iT2 file
		if well in production_dictionary and not plot_feedzones:
			data_t = pd.read_json(OBJ_file)
			data_h = data_t.loc[data_t['OBSERVATION'] == production_dictionary[well][0],['TIME','COMPUTED']]
			data_r = data_t.loc[data_t['OBSERVATION'] == production_dictionary[well][1],['TIME','COMPUTED']]

			times = data_h['TIME']

			dates_h=[]
			for ind in times.index:
				if float(times[ind])>=0:
					try:
						dates_h.append(input_dictionary['ref_date']+datetime.timedelta(seconds=int(times[ind])))
					except OverflowError:
						print(times[ind],"plus",str(times[ind]),"wont be plot")
				else:
					print(times[ind])

			times = data_r['TIME']

			dates_r=[]
			for ind in times.index:
				if float(times[ind])>=0:
					try:
						dates_r.append(input_dictionary['ref_date']+datetime.timedelta(seconds=int(times[ind])))
					except OverflowError:
						print(times[ind],"plus",str(times[ind]),"wont be plot")
				else:
					print(times[ind])

			ax.set_title("Well: %s"%(well) ,fontsize=8)
			ax.set_ylabel('Flow rate [kg/s]',fontsize = 8)
			ax.set_xlabel("Time",fontsize = 8)


			ax.plot(dates_r,np.absolute(data_r['COMPUTED']),color=formats.plot_conf_color['m'][1],\
				linestyle='--',ms=5,label='Computed flow',marker=formats.plot_conf_marker['current'][0],alpha=formats.plot_conf_marker['current'][1])


			ax1.set_ylabel('Enthalpy [kJ/kg]',fontsize = 8)

			ax1.plot(dates_h,np.absolute(data_h['COMPUTED'])/1E3,\
				linestyle='--',color=formats.plot_conf_color['h'][1],ms=5,label='Computed enthalpy',marker=formats.plot_conf_marker['current'][0],alpha=formats.plot_conf_marker['current'][1])

			ax1.set_ylim([500,3000])

			data_t = pd.read_json(OBJ_file_prev)
			data_h = data_t.loc[data_t['OBSERVATION'] == production_dictionary[well][0],['TIME','COMPUTED']]
			data_r = data_t.loc[data_t['OBSERVATION'] == production_dictionary[well][1],['TIME','COMPUTED']]

			times = data_h['TIME']

			dates_h=[]
			for ind in times.index:
				if float(times[ind])>=0:
					try:
						dates_h.append(input_dictionary['ref_date']+datetime.timedelta(seconds=int(times[ind])))
					except OverflowError:
						print(times[ind],"plus",str(times[ind]),"wont be plot")
				else:
					print(times[ind])

			times = data_r['TIME']

			dates_r=[]
			for ind in times.index:
				if float(times[ind])>=0:
					try:
						dates_r.append(input_dictionary['ref_date']+datetime.timedelta(seconds=int(times[ind])))
					except OverflowError:
						print(times[ind],"plus",str(times[ind]),"wont be plot")
				else:
					print(times[ind])

			ax.set_title("Well: %s"%(well) ,fontsize=8)
			ax.set_ylabel('Flow rate [kg/s]',fontsize = 8)
			ax.set_xlabel("Time",fontsize = 8)


			ax.plot(dates_r,np.absolute(data_r['COMPUTED']),color=formats.plot_conf_color['m'][1],\
				linestyle='--',ms=5,label='Computed flow prev',marker=formats.plot_conf_marker['current'][0],alpha=formats.plot_conf_marker['current'][1]-0.25)

			line_index = 2


			ax1 = ax.twinx()
			ax1.set_ylabel('Enthalpy [kJ/kg]',fontsize = 8)
			ax1.set_ylim([500,3000])


			ax1.plot(dates_h,np.absolute(data_h['COMPUTED'])/1E3,\
				linestyle='--',color=formats.plot_conf_color['h'][1],ms=5,label='Computed enthalpy prev',marker=formats.plot_conf_marker['current'][0],alpha=formats.plot_conf_marker['current'][1]-0.25)

		else:
			data=pd.read_csv(file)

			#Setting the time to plot
			
			times=data['TIME']

			dates=[]
			for n in range(len(times)):
				if float(times[n])>0:
					try:
						dates.append(input_dictionary['ref_date']+datetime.timedelta(seconds=int(times[n])))
					except OverflowError:
						print(times[n],"plus",str(times[n]),"wont be plot")

			if len(variables) == 0:

				
				enthalpy=[]
				flow_rate=[]
				WHP=[]

				for n in range(len(times)):
					if float(times[n])>0:
						try:
							#dates.append(input_dictionary['ref_date']+datetime.timedelta(seconds=int(times[n])))

							if 'ENTHALPY' in data.columns:
								H_colum = 'ENTHALPY'
							elif 'ENTH' in data.columns:
								H_colum = 'ENTH'

							if 'GENERATION RATE' in data.columns:
								m_colum = 'GENERATION RATE'
							elif 'GEN' in data.columns:
								m_colum = 'GEN'


							enthalpy.append(data[H_colum][n]/1E3)
							flow_rate.append(data[m_colum][n])
						except OverflowError:
							print(times[n],"plus",str(times[n]),"wont be plot")

		
			#Real data

			ax.set_title("Well: %s, block %s, source %s"%(well,block,source) ,fontsize=8)
			ax.set_ylabel('Flow rate [kg/s]',fontsize = 8)
			ax.set_xlabel("Time",fontsize = 8)

			ax1.set_ylabel('Enthalpy [kJ/kg]',fontsize = 8)
			ax1.set_ylim([500,2700])
			
			if len(variables) == 0:

				ax.plot(dates,np.absolute(flow_rate),color=formats.plot_conf_color['m'][1],\
					linestyle='--',ms=5,label='Calculated flow',marker=formats.plot_conf_marker['current'][0],alpha=formats.plot_conf_marker['current'][1])


				ax1.plot(dates,enthalpy,\
					linestyle='--',color=formats.plot_conf_color['h'][1],ms=5,label='Calculated enthalpy',marker=formats.plot_conf_marker['current'][0],alpha=formats.plot_conf_marker['current'][1])

			else:
				for var in variables:
					ax.plot(dates,data[var].loc[data.TIME>0],\
						linestyle='--',ms=5,marker=formats.plot_conf_marker['current'][0],alpha=formats.plot_conf_marker['current'][1])
				ax.set_ylabel('Flow rate [kg/s] + variable',fontsize = 8)
		

		try:
			data_real=pd.read_csv("../input/mh/%s_mh.dat"%well)
			data_real['date_time'] = pd.to_datetime(data_real['date_time'] , format="%Y-%m-%d_%H:%M:%S")
			data_real=data_real.set_index(['date_time'])
			data_real.index = pd.to_datetime(data_real.index)

			data_real['total_flow']=data_real['steam']+data_real['liquid']

			#Plotting

			#ax=data[['Flujo_total']].plot(figsize=(12,4),legend=False,linestyle="-")

			ax.plot(data_real.index,data_real['steam']+data_real['liquid'],\
				linestyle='-',color=formats.plot_conf_color['m'][0],ms=3,label='Real',marker=formats.plot_conf_marker['real'][0],alpha=formats.plot_conf_marker['current'][1])

			ax1.plot(data_real.index,data_real['enthalpy'],\
				linestyle='None',color=formats.plot_conf_color['h'][0],ms=3,label='Real',marker=formats.plot_conf_marker['real'][0],alpha=formats.plot_conf_marker['current'][1])


			if 'PWH' in variables:
				ax.plot(data_real.index,data_real['WHPabs'],linestyle='None',color=formats.plot_conf_color['P'][0],ms=3,label='Real',marker=formats.plot_conf_marker['real'][0],alpha=formats.plot_conf_marker['current'][1])

			real_data=True
			
		except FileNotFoundError:
			real_data=False
			print("No real data for %s"%well)
			pass

		if len(variables) == 0:

			if real_data:
				plt.legend([ax.get_lines()[0],ax.get_lines()[line_index],ax1.get_lines()[0],ax1.get_lines()[1]],\
				                   ['Computed flow rate ','Measured flow rate ',\
				                    'Computed enthalpy', 'Estimated enthalpy'],loc="lower center", bbox_to_anchor=(0.5, -0.25), ncol=4, fancybox=True, shadow=True)
			else:
				plt.legend([ax.get_lines()[0],ax1.get_lines()[0]],\
				           ['Computed Flow rate ','Estimated enthalpy'], loc="lower center", bbox_to_anchor=(0.5, -0.25), ncol=2,  fancybox=True, shadow=True)

		else:
			if real_data:
				variables_lines =  ax.get_lines()[:-1]

				legends = [ax.get_lines()[len(variables)+1],ax1.get_lines()[0]].extend(variables_lines)
				labeles = ['Measured flow rate', 'Estimated enthalpy'].extend(variables)

				print(legends,labeles)

				plt.legend([legends],[labeles],loc="lower center", bbox_to_anchor=(0.5, -0.25), ncol=4, fancybox=True, shadow=True)
		
		box = ax.get_position()
		ax.set_position([box.x0, box.y0+0.1, box.width, box.height*0.9])

		#Plotting formating
		#xlims=[min(dates)-datetime.timedelta(days=365),max(dates)+datetime.timedelta(days=365)]
		ax.format_xdata = mdates.DateFormatter('%Y%-m-%d %H:%M:%S')


		xlims=[input_dictionary['ref_date']-datetime.timedelta(days=365),input_dictionary['ref_date']+datetime.timedelta(days=years*365.25)]
		#ylims=[0,100]
		#ax1.set_ylim(ylims)

		ax.set_xlim(xlims)
		years = mdates.YearLocator()
		years_fmt = mdates.DateFormatter('%Y')

		ax.xaxis.set_major_formatter(years_fmt)

		#ax.xaxis.set_major_locator(years)
		#fig.autofmt_xdate()

		#Grid style
		ax.yaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
		ax.xaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
		ax.grid(True)

		if save:
			fig.savefig('../output/mh/images/%s_%s_%s_evol.png'%(well,block,source)) 
		if show:
			plt.show()
	else:
		print("There is not a file called %s, try running src_evol from output.py"%file)

def plot_compare_PT(input_dictionary, well,block,save,show):
	"""Genera una grafica donde compara la evolucion de flujo y entalpia para el bloque asignado a la fuente de un pozo en particular

	Parameters
	----------	  
	well : str
	  Nombre de pozo
	block : str
	  Nombre de bloque, en general donde se ubica zona de alimentacion
	source : str
	  Nombre de fuente asociada a pozo
	save : bool
	  Almacaena la grafica generada
	show : bool
	  Almacaena la grafica generada

	Returns
	-------
	image
		{well}_{block}_{source}_evol.png: archivo con direccion ../output/mh/images/

	Note
	----
	El archivo correspondiente en la carpeta  ../output/mh/txt debe existir

	Examples
	--------
	>>> plot_compare_mh('AH-1','DA110','SRC1',save=True,show=False)
	"""

	#Read file, current calculated
	file = "../output/PT/evol/%s_PT_evol.dat"%(well)

	if os.path.isfile(file):
		data=pd.read_csv(file)

		#Setting the time to plot
		
		times = data['TIME'].loc[data['ELEM'] == block]
		times.reset_index(drop=True)
		dates = []
		for time  in times:
			try:
				dates.append(input_dictionary['ref_date']+datetime.timedelta(seconds=int(time)))
			except OverflowError:
				print(time, "wont be plot")

		#Real data

		fig, ax = plt.subplots(figsize=(10,4))

		ax.plot(dates,data['TEMP'].loc[(data['ELEM'] == block) & (data['TIME'] > 0)],color=formats.plot_conf_color['T'][1],\
			linestyle='--',ms=5,label='Temperature',marker=formats.plot_conf_marker['current'][0],alpha=formats.plot_conf_marker['current'][1])

		ax.set_title("Well: %s, block %s "%(well,block) ,fontsize=8)
		ax.set_xlabel("Time",fontsize = 8)
		ax.set_ylabel('Temperature [C]',fontsize = 8)

		ax1 = ax.twinx()

		ax1.plot(dates,data['PRES_VAP'].loc[(data['ELEM'] == block) & (data['TIME']> 0 )]/1E5,\
			linestyle='--',color=formats.plot_conf_color['P'][1],ms=5,label='Calculated enthalpy',marker=formats.plot_conf_marker['current'][0],alpha=formats.plot_conf_marker['current'][1])

		ax1.set_ylabel('Pressure [bar]',fontsize = 8)
		

		plt.legend([ax.get_lines()[0],ax1.get_lines()[0]],\
			           ['Calculated Temperature','Calculated Pressure '],loc="upper right")

		ax.format_xdata = mdates.DateFormatter('%Y%-m-%d %H:%M:%S')

		xlims=[input_dictionary['ref_date']-datetime.timedelta(days=365),input_dictionary['ref_date']+datetime.timedelta(days=35*365.25)]
		#ylims=[0,100]
		#ax1.set_ylim(ylims)

		ax.set_xlim(xlims)
		years = mdates.YearLocator()
		years_fmt = mdates.DateFormatter('%Y')

		ax.xaxis.set_major_formatter(years_fmt)

		#ax.xaxis.set_major_locator(years)
		#fig.autofmt_xdate()

		#Grid style
		ax.yaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
		ax.xaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
		ax.grid(True)

		if save:
			fig.savefig('../output/mh/images/%s_%s_evol.png'%(well,block)) 
		if show:
			plt.show()
	else:
		print("There is not a file called %s, try running src_evol from output.py"%file)

def plot_compare_PT_vertical(input_dictionary, well,block,save,show, years = 35, p_res_block = None, delta = False, var_name = 'P'):
	"""Genera una grafica donde compara la evolucion de flujo y entalpia para el bloque asignado a la fuente de un pozo en particular

	Parameters
	----------	  
	well : str
	  Nombre de pozo
	block : str
	  Nombre de bloque, en general donde se ubica zona de alimentacion
	source : str
	  Nombre de fuente asociada a pozo
	save : bool
	  Almacaena la grafica generada
	show : bool
	  Almacaena la grafica generada

	Returns
	-------
	image
		{well}_{block}_{source}_evol.png: archivo con direccion ../output/mh/images/

	Note
	----
	El archivo correspondiente en la carpeta  ../output/mh/txt debe existir

	Examples
	--------
	>>> plot_compare_mh('AH-1','DA110','SRC1',save=True,show=False)
	"""

	#Read file, current calculated
	file = "../output/PT/evol/%s_PT_evol.dat"%(well)


	layers_info=geometry.vertical_layers(input_dictionary)

	blocks = [name+block[1:] for name in layers_info['name']]

	if os.path.isfile(file):
		data=pd.read_csv(file)

		fig, ax = plt.subplots(figsize=(10,4))

		ax.set_title("Well: %s "%(well) )
		ax.set_xlabel("Time")

		colormap = plt.cm.jet
		colors = [colormap(i) for i in np.linspace(0, 1,len(blocks))]
		ax.set_prop_cycle('color', colors)

		for block_i in blocks:

			#Setting the time to plot
			
			times = data['TIME'].loc[data['ELEM'] == block_i]
			times.reset_index(drop=True)
			dates = []
			for time  in times:
				try:
					dates.append(input_dictionary['ref_date']+datetime.timedelta(seconds=int(time)))
				except OverflowError:
					print(time, "wont be plot")


			if p_res_block != None and block_i == p_res_block:
				linestyle_i = '--'
			else:
				linestyle_i = '-'

			if var_name == 'P':
				var_name = 'PRES_VAP'
				label_y = 'Pressure [bar]'
				divisor = 1E5
			elif var_name == 'T':
				var_name = 'TEMP'
				label_y = 'Temperature [C]'
				divisor = 1
			elif var_name == 'Q':
				var_name = 'SAT_VAP'
				label_y = 'Quality'
				divisor = 0.01


			data_var = data[var_name].loc[(data['ELEM'] == block_i) & (data['TIME']> 0 )]/divisor

			data_var = data_var.reset_index()

			if delta:
				var = 'delta'
				pos = data_var.columns.get_loc(var_name)
				data_var['delta'] =  data_var.iloc[1:, pos] - data_var.iat[0, pos]
				
			else:
				var = var_name

			ax.plot(dates,data_var[var],linestyle=linestyle_i,ms=2,label=block_i,marker=formats.plot_conf_marker['current'][0],alpha=formats.plot_conf_marker['current'][1])

			if p_res_block != None and block_i == p_res_block:
				pres_data=pd.read_csv("../input/field_data.csv",delimiter=',')
				pres_data.replace(0, np.nan, inplace=True)

				pres_data = pres_data[pres_data['prs1'].notna()]

				if delta:
					pos = pres_data.columns.get_loc('prs1')
					pres_data['delta'] =  pres_data.iloc[1:, pos] - pres_data.iat[0, pos]

				pres_data.to_csv('test.csv')

				dates_func_res=lambda datesX: datetime.datetime.strptime(str(datesX), "%Y%m%d")
				dates_res=list(map(dates_func_res,pres_data['fecha']))
				

				if delta:
					ax.plot(dates_res,pres_data['delta'],label = 'p_res',color = 'black',linestyle = 'None' ,ms=0.5,marker='s',alpha=1)
				else:
					ax.plot(dates_res,pres_data['prs1'],label = 'p_res',color = 'black',linestyle = 'None' ,ms=0.5,marker='s',alpha=1)


		ax.set_ylabel(label_y)

		plt.legend(loc="upper right")

		ax.format_xdata = mdates.DateFormatter('%Y%-m-%d %H:%M:%S')

		xlims=[input_dictionary['ref_date']-datetime.timedelta(days=365),input_dictionary['ref_date']+datetime.timedelta(days=years*365.25)]

		ax.set_xlim(xlims)
		years = mdates.YearLocator()
		years_fmt = mdates.DateFormatter('%Y')

		ax.xaxis.set_major_formatter(years_fmt)

		#Grid style
		ax.yaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
		ax.xaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
		ax.grid(True)

		if save:
			fig.savefig('../output/PT/evol/%s_evol_%s.png'%(well,var_name)) 
		if show:
			plt.show()
	else:
		print("There is not a file called %s, try running src_evol from output.py"%file)

def plot_compare_producers(input_dictionary, years = 35):
	"""
	Not documented
	"""
	fig, ax = plt.subplots(figsize=(10,4))

	OBJ_file = "../output/PT/json/it2_PT.json"

	data_t = pd.read_json(OBJ_file)
	data_h = data_t.loc[data_t['OBSERVATION'] == 'PROD_FLOWH',['TIME','COMPUTED']]
	data_r = data_t.loc[data_t['OBSERVATION'] == 'PROD_FLOWR',['TIME','COMPUTED']]

	print(data_t)

	times = data_h['TIME']

	dates=[]
	for ind in times.index:
		if float(times[ind])>=0:
			try:
				dates.append(input_dictionary['ref_date']+datetime.timedelta(seconds=int(times[ind])))
			except OverflowError:
				print(times[ind],"plus",str(times[ind]),"wont be plot")
		else:
			print(times[ind])

	ax.set_title("Production wells" ,fontsize=8)
	ax.set_ylabel('Flow rate [kg/s]',fontsize = 8)
	ax.set_xlabel("Time",fontsize = 8)

	ax.plot(dates,np.absolute(data_r['COMPUTED']),color=formats.plot_conf_color['m'][1],\
		linestyle='--',ms=5,label='Computed flow',marker=formats.plot_conf_marker['current'][0],alpha=formats.plot_conf_marker['current'][1])

	ax1 = ax.twinx()
	ax1.set_ylabel('Enthalpy [kJ/kg]',fontsize = 8)


	ax1.plot(dates,np.absolute(data_h['COMPUTED'])/1E3,\
		linestyle='--',color=formats.plot_conf_color['h'][1],ms=5,label='Computed enthalpy',marker=formats.plot_conf_marker['current'][0],alpha=formats.plot_conf_marker['current'][1])


	"""
	data_real=pd.read_csv("../input/mh/total_prod_mh.csv")
	data_real['date_time'] = pd.to_datetime(data_real['date_time'] , format="%Y-%m-%d")
	data_real=data_real.set_index(['date_time'])
	data_real.index = pd.to_datetime(data_real.index)


	#Plotting

	#ax=data[['Flujo_total']].plot(figsize=(12,4),legend=False,linestyle="-")

	ax.plot(data_real.index,data_real['m'],\
		linestyle='-',color=formats.plot_conf_color['m'][0],ms=3,label='Measured flow',marker=formats.plot_conf_marker['real'][0],alpha=formats.plot_conf_marker['current'][1])
	ax1.plot(data_real.index,data_real['h'],'ob',\
		linestyle='None',color=formats.plot_conf_color['h'][0],ms=3,label='Estimated enthalpy',marker=formats.plot_conf_marker['real'][0],alpha=formats.plot_conf_marker['current'][1])
	"""
	data_real=pd.read_csv("../input/field_data.csv")
	data_real['fecha'] = pd.to_datetime(data_real['fecha'] , format="%Y%m%d")
	data_real=data_real.set_index(['fecha'])
	data_real.index = pd.to_datetime(data_real.index)


	#Plotting

	#ax=data[['Flujo_total']].plot(figsize=(12,4),legend=False,linestyle="-")

	ax.plot(data_real.index,data_real['agua']+data_real['vapor'],\
		linestyle='-',color=formats.plot_conf_color['m'][0],ms=3,label='Measured flow',marker=formats.plot_conf_marker['real'][0],alpha=formats.plot_conf_marker['current'][1])
	ax1.plot(data_real.index,data_real['h'],'ob',\
		linestyle='None',color=formats.plot_conf_color['h'][0],ms=3,label='Estimated enthalpy',marker=formats.plot_conf_marker['real'][0],alpha=formats.plot_conf_marker['current'][1])
	
	plt.legend([ax.get_lines()[0],ax.get_lines()[1],ax1.get_lines()[0],ax1.get_lines()[1]],\
				                   ['Computed Flow rate ','Measured flow rate ',\
				                    'Computed Enthalpy', 'Estimated enthalpy'], loc="lower center", bbox_to_anchor=(0.5, -0.27), ncol=4, fancybox=True, shadow=True)


	box = ax.get_position()
	ax.set_position([box.x0, box.y0+0.1, box.width, box.height*0.9])

	fig.savefig('../output/mh/producer_wells.png') 

	plt.show()

def cross_section(input_dictionary, variable, layer, time, plot_mesh = False):
	"""
	Not documented
	"""

	ngridx = 200
	ngridy = 200

	fontsize_labels = 6


	file_output="../output/PT/json/evol/t2_output_%s.json"%time

	elem_file='../mesh/ELEME.json'

	if os.path.isfile(elem_file):
		 blocks=pd.read_json(elem_file)

	if os.path.isfile(file_output):
		with open(file_output) as file:
		  	data=json.load(file)
		
	data = data['%.1f'%time]

	if variable == 'TEMP':
		divisor = 1
	elif variable == 'PRES_VAP':
		divisor = 1E5
	else:
		divisor = 1

	x = []
	y = []
	d = []
	for eleme in data:
		if eleme[0] == layer:
			x.append(blocks[eleme]['X'])
			y.append(blocks[eleme]['Y'])
			d.append(data[eleme][variable]/divisor)

	xi = np.linspace(min(x), max(x), ngridx)
	yi = np.linspace(min(y), max(y), ngridy)
	zi = griddata((x, y), d, (xi[None,:], yi[:,None]), method='linear')

	fig=plt.figure(figsize=(10,10))
	ax=fig.add_subplot(1,1,1)
	ax.set_aspect('equal')

	lv = np.linspace(min(d),max(d),20)

	c=ax.contour(xi,yi,zi, linewidths = 1, colors = "k", levels = lv)
	ax.clabel(c, inline = True, fontsize = fontsize_labels, fmt = '%4.1f', colors = "k")
	contour = ax.contourf(xi,yi,zi, cmap = "jet", levels = lv)
	cbar=fig.colorbar(contour,ax=ax)
	cbar.set_label("%s"%variable)

	ax.tick_params(axis='both', which='major', labelsize=fontsize_labels,pad=1)
	ax.set_ylabel('North [m]',fontsize =fontsize_labels)
	ax.set_xlabel('East [m]',fontsize=fontsize_labels)
	ax.set_title("Layer %s"%layer,fontsize=fontsize_labels)


	if plot_mesh:
		segmt_json_file='../mesh/segmt.json'

		if os.path.isfile(segmt_json_file):
			with open(segmt_json_file) as file:
			  	blocks_seg=json.load(file)

			for block in blocks_seg:
				if block[0]==layer:
					for i, point in enumerate(blocks_seg[block]['points']):

						if i==0:
							line=[]
						if i!=0 and (i)%4==0:
							ax.plot([line[0],line[2]],[line[1],line[3]],'-k', lw = 0.25)
							line=[]
						if i%4 in [0,1,2,3]:
							line.append(point)

	fig.savefig('../output/PT/images/layer/%s_%s_%s.png'%(layer, variable, time)) 

	plt.show()

def plot_power(input_dictionary, save = True, show= True):
	"""
	Not documented
	"""
	real_data = "../input/generation_data.csv"

	gen_data = pd.read_csv(real_data,delimiter=',')
	gen_data = gen_data.sort_values(by ='fecha' )
	gen_data['fecha'] = pd.to_datetime(gen_data['fecha'] , format="%Y%m%d")

	gen_data_u12 = gen_data.loc[ ((gen_data.unidad == 'u1') | (gen_data.unidad == 'u2')) & (gen_data.generation > 0), ['generation','fecha','unidad']]
	gen_data_u12 = gen_data_u12.groupby(['fecha']).sum()
	gen_data_u12['fecha'] = gen_data_u12.index
	gen_data_u12 = gen_data_u12.reset_index(drop=True)

	gen_data_u3 = gen_data.loc[ (gen_data.unidad == 'u3') & (gen_data.generation > 0), ['generation','fecha','unidad']]
	gen_data_u3 = gen_data_u3.reset_index(drop=True)

	file_12 = "../output/unit_12_power.csv"
	file_3 = "../output/unit_3_power.csv"

	data_12 = pd.read_csv(file_12, delimiter=',')
	data_12['date_time'] = pd.to_datetime(data_12['date_time'] , format="%Y%m%d %H:%M:%S")

	data_3 = pd.read_csv(file_3, delimiter=',')
	data_3['date_time'] = pd.to_datetime(data_3['date_time'] , format="%Y%m%d %H:%M:%S")

	fig12 = plt.figure(figsize=(10,4.5))

	ax12 = plt.subplot(111)
	ax12.set_title("Power Generation, Units 1 and 2" ,fontsize=8)
	ax12.set_ylabel('Generation [MW]',fontsize = 8)
	ax12.set_xlabel("Time",fontsize = 8)

	fig3 = plt.figure(figsize=(10,4.5))

	ax3 = plt.subplot(111)
	ax3.set_title("Power Generation, Units 3" ,fontsize=8)
	ax3.set_ylabel('Generation [MW]',fontsize = 8)
	ax3.set_xlabel("Time",fontsize = 8)

	ax12.plot(data_12['date_time'],data_12['power'],color=formats.plot_conf_color['m'][1],\
		linestyle='--',ms=1,label='Computed power',marker=formats.plot_conf_marker['current'][0],alpha=formats.plot_conf_marker['current'][1])
	ax12.plot(gen_data_u12['fecha'],gen_data_u12['generation'],color='k',\
		linestyle='None',ms=1,label='Real power',marker=formats.plot_conf_marker['current'][0],alpha=formats.plot_conf_marker['current'][1])
	ax12.legend(loc = 'lower right')

	ax3.plot(data_3['date_time'],data_3['power'],color=formats.plot_conf_color['m'][1],\
		linestyle='--',ms=1,label='Computed power',marker=formats.plot_conf_marker['current'][0],alpha=0.5)
	ax3.plot(gen_data_u3['fecha'],gen_data_u3['generation'],color='k',\
		linestyle='None',ms=1,label='Real power',marker=formats.plot_conf_marker['current'][0],alpha=0.5)
	ax3.legend(loc = 'lower right')

	if save:
		fig12.savefig('../output/power_12.png',dpi=300) 
		fig3.savefig('../output/power_3.png', dpi= 300) 

	plt.show()

def plot_power_flowell(input_dictionary, save = True, show= True):
	"""
	Not documented
	"""
	real_data = "../input/generation_data.csv"

	gen_data = pd.read_csv(real_data,delimiter=',')
	gen_data = gen_data.sort_values(by ='fecha' )
	gen_data['fecha'] = pd.to_datetime(gen_data['fecha'] , format="%Y%m%d")

	gen_data_u12 = gen_data.loc[ ((gen_data.unidad == 'u1') | (gen_data.unidad == 'u2')) & (gen_data.generation > 0), ['generation','fecha','unidad']]
	gen_data_u12 = gen_data_u12.groupby(['fecha']).sum()
	gen_data_u12['fecha'] = gen_data_u12.index
	gen_data_u12 = gen_data_u12.reset_index(drop=True)

	gen_data_u3 = gen_data.loc[ (gen_data.unidad == 'u3') & (gen_data.generation > 0), ['generation','fecha','unidad']]
	gen_data_u3 = gen_data_u3.reset_index(drop=True)

	file_12 = "../output/unit_12_power_flowell.csv"
	file_3 = "../output/unit_3_power_flowell.csv"

	data_12 = pd.read_csv(file_12, delimiter=',')
	data_12['date_time'] = pd.to_datetime(data_12['date_time'] , format="%Y%m%d %H:%M:%S")


	data_12=data_12.set_index(['date_time'])
	data_12.index = pd.to_datetime(data_12.index)

	power12 = data_12['power']#	.resample('6M').mean()
	power12 = pd.DataFrame({'date_time':power12.index, 'power':power12.values}) 


	data_3 = pd.read_csv(file_3, delimiter=',')
	data_3['date_time'] = pd.to_datetime(data_3['date_time'] , format="%Y%m%d %H:%M:%S")

	fig12 = plt.figure(figsize=(10,4.5))

	ax12 = plt.subplot(111)
	ax12.set_title("Power Generation, Units 1 and 2, flowell" ,fontsize=8)
	ax12.set_ylabel('Generation [MW]',fontsize = 8)
	ax12.set_xlabel("Time",fontsize = 8)

	fig3 = plt.figure(figsize=(10,4.5))

	ax3 = plt.subplot(111)
	ax3.set_title("Power Generation, Units 3, flowell" ,fontsize=8)
	ax3.set_ylabel('Generation [MW]',fontsize = 8)
	ax3.set_xlabel("Time",fontsize = 8)

	ax12.plot(power12['date_time'],power12['power'],color=formats.plot_conf_color['m'][1],\
		linestyle='--',ms=1,label='Computed power',marker=formats.plot_conf_marker['current'][0],alpha=formats.plot_conf_marker['current'][1])
	ax12.plot(gen_data_u12['fecha'],gen_data_u12['generation'],color='k',\
		linestyle='None',ms=1,label='Real power',marker=formats.plot_conf_marker['current'][0],alpha=formats.plot_conf_marker['current'][1])
	ax12.legend(loc = 'lower right')
	ax12.fill_between([min(gen_data_u12['fecha']),max(power12['date_time'])],59,53,color = 'grey', alpha = 0.5)

	ax3.plot(data_3['date_time'],data_3['power'],color=formats.plot_conf_color['m'][1],\
		linestyle='--',ms=1,label='Computed power',marker=formats.plot_conf_marker['current'][0],alpha=0.5)
	ax3.plot(gen_data_u3['fecha'],gen_data_u3['generation'],color='k',\
		linestyle='None',ms=1,label='Real power',marker=formats.plot_conf_marker['current'][0],alpha=0.5)
	ax3.legend(loc = 'lower right')
	ax3.fill_between([min(gen_data_u3['fecha']),max(data_3['date_time'])],45,42,color = 'grey', alpha = 0.5)

	if save:
		fig12.savefig('../output/power_12_flowell.png',dpi=300) 
		fig3.savefig('../output/power_3_flowell.png', dpi= 300) 

	plt.show()

def plot_power_it2(input_dictionary, save = True, show= True):
	"""
	Not documented
	"""
	#Read file, current calculated
	file="../input/generation_data.csv"
	OBJ_file = "../output/PT/json/it2_PT.json"
	OBJ_file_prev = "../output/PT/json/prev/it2_PT.json"

	if os.path.isfile(file):

		gen_data = pd.read_csv(file,delimiter=',')
		gen_data = gen_data.sort_values(by ='fecha' )
		gen_data['fecha'] = pd.to_datetime(gen_data['fecha'] , format="%Y%m%d")

		gen_data_u12 = gen_data.loc[ ((gen_data.unidad == 'u1') | (gen_data.unidad == 'u2')) & (gen_data.generation > 0), ['generation','fecha','unidad']]
		gen_data_u12 = gen_data_u12.groupby(['fecha']).sum()
		gen_data_u12['fecha'] = gen_data_u12.index
		gen_data_u12 = gen_data_u12.reset_index(drop=True)

		gen_data_u3 = gen_data.loc[ (gen_data.unidad == 'u3') & (gen_data.generation > 0), ['generation','fecha','unidad']]
		gen_data_u3 = gen_data_u3.reset_index(drop=True)


		#Section dedicated to wells with more with one feedzone. iT2 computes the weighted enthlapy and the flowrate sum for each timestep define on the iT2 file
		if os.path.isfile(OBJ_file):
			fig = plt.figure(figsize=(10,4.5))
			ax = plt.subplot(111)

			data_t = pd.read_json(OBJ_file)

			data_12 = data_t.loc[data_t['OBSERVATION'] == 'UNIT1&2',['TIME','COMPUTED']]

			dates_12=[]
			times = data_12['TIME']
			for ind in times.index:
				if float(times[ind])>=0:
					try:
						dates_12.append(input_dictionary['ref_date']+datetime.timedelta(seconds=int(times[ind])))
					except OverflowError:
						print(times[ind],"plus",str(times[ind]),"wont be plot")
				else:
					print(times[ind])

			ax.set_title("Power Generation, Units 1 and 2" ,fontsize=8)
			ax.set_ylabel('Generation [MW]',fontsize = 8)
			ax.set_xlabel("Time",fontsize = 8)


			ax.plot(dates_12,np.absolute(data_12['COMPUTED']),color=formats.plot_conf_color['m'][1],\
				linestyle='--',ms=5,label='Computed power',marker=formats.plot_conf_marker['current'][0],alpha=formats.plot_conf_marker['current'][1])

			ax.plot(gen_data_u12['fecha'],gen_data_u12['generation'],color='k',\
				linestyle='None',ms=1,label='Real power',marker=formats.plot_conf_marker['current'][0],alpha=0.5)

			ax.legend(loc = 'lower right')

			if show:
				plt.show()
			
			if save:
				fig.savefig('../output/power_12.png') 



			fig = plt.figure(figsize=(10,4.5))
			ax = plt.subplot(111)

			data_3 = data_t.loc[data_t['OBSERVATION'] == 'UNIT3',['TIME','COMPUTED']]

			dates_3=[]
			times = data_3['TIME']
			for ind in times.index:
				if float(times[ind])>=0:
					try:
						dates_3.append(input_dictionary['ref_date']+datetime.timedelta(seconds=int(times[ind])))
					except OverflowError:
						print(times[ind],"plus",str(times[ind]),"wont be plot")
				else:
					print(times[ind])

			ax.set_title("Power Generation, Unit 3" ,fontsize=8)
			ax.set_ylabel('Generation [MW]',fontsize = 8)
			ax.set_xlabel("Time",fontsize = 8)


			ax.plot(dates_3,np.absolute(data_3['COMPUTED'])/32,color=formats.plot_conf_color['m'][1],\
				linestyle='--',ms=5,label='Computed power',marker=formats.plot_conf_marker['current'][0],alpha=formats.plot_conf_marker['current'][1])

			ax.plot(gen_data_u3['fecha'],gen_data_u3['generation'],color='k',\
				linestyle='None',ms=1,label='Real power',marker=formats.plot_conf_marker['current'][0],alpha=0.5)

			ax.legend(loc = 'lower right')

			if show:
				plt.show()
			
			if save:
				fig.savefig('../output/power_3.png') 

def plot_compare_mh_filtered(input_dictionary, well):
	"""
	Not documented
	"""
	years = 35

	fig = plt.figure(figsize=(10,4.5))
	ax = plt.subplot(111)
	ax1 = ax.twinx()


	ax.set_title("Well: %s"%(well) ,fontsize=8)
	ax.set_ylabel('Flow rate [kg/s]',fontsize = 8)
	ax.set_xlabel("Time",fontsize = 8)


	data_real=pd.read_csv("../input/mh/%s_mh.dat"%well)
	data_real['date_time'] = pd.to_datetime(data_real['date_time'] , format="%Y-%m-%d_%H:%M:%S")
	data_real=data_real.set_index(['date_time'])
	data_real.index = pd.to_datetime(data_real.index)
	data_real['total_flow']=data_real['steam']+data_real['liquid']

	data_real_filtered=pd.read_csv("../input/mh/filtered/%s_week_avg.csv"%well)
	data_real_filtered['date_time'] = pd.to_datetime(data_real_filtered['date_time'] , format="%Y-%m-%d %H:%M:%S")
	data_real_filtered=data_real_filtered.set_index(['date_time'])
	data_real_filtered.index = pd.to_datetime(data_real_filtered.index)
	data_real_filtered['total_flow']=data_real_filtered['steam']+data_real_filtered['liquid']


	#Plotting

	#ax=data[['Flujo_total']].plot(figsize=(12,4),legend=False,linestyle="-")

	ax.plot(data_real.index,data_real['steam']+data_real['liquid'],'or',\
		linestyle='-',ms=1,label='Real',marker=formats.plot_conf_marker['real'][0],alpha=formats.plot_conf_marker['current'][1])
	ax.plot(data_real_filtered.index,data_real_filtered['steam']+data_real_filtered['liquid'],'og',\
		linestyle='-',ms=2,label='Real',marker=formats.plot_conf_marker['real'][0],alpha=formats.plot_conf_marker['current'][1])

	ax1.plot(data_real.index,data_real['enthalpy'],'ob',\
		linestyle='None',ms=3,label='Real',marker=formats.plot_conf_marker['real'][0],alpha=formats.plot_conf_marker['current'][1])
	ax1.plot(data_real_filtered.index,data_real_filtered['enthalpy'],'ok',\
		linestyle='None',ms=3,label='Real',marker=formats.plot_conf_marker['real'][0],alpha=formats.plot_conf_marker['current'][1])

	box = ax.get_position()
	ax.set_position([box.x0, box.y0+0.1, box.width, box.height*0.9])

	#Plotting formating
	#xlims=[min(dates)-datetime.timedelta(days=365),max(dates)+datetime.timedelta(days=365)]
	ax.format_xdata = mdates.DateFormatter('%Y%-m-%d %H:%M:%S')


	xlims=[input_dictionary['ref_date']-datetime.timedelta(days=365),input_dictionary['ref_date']+datetime.timedelta(days=years*365.25)]
	#ylims=[0,100]
	#ax1.set_ylim(ylims)

	ax.set_xlim(xlims)
	years = mdates.YearLocator()
	years_fmt = mdates.DateFormatter('%Y')

	ax.xaxis.set_major_formatter(years_fmt)

	#ax.xaxis.set_major_locator(years)
	#fig.autofmt_xdate()

	#Grid style
	ax.yaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
	ax.xaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
	ax.grid(True)

	plt.legend([ax.get_lines()[0],ax.get_lines()[1],ax1.get_lines()[0],ax1.get_lines()[1]],\
	                   ['Flow rate ','Filtered flow rate',\
	                    'Enthalpy', 'Filtered enthalpy'],loc="lower center", bbox_to_anchor=(0.5, -0.25), ncol=4, fancybox=True, shadow=True)

	plt.show()

def pres(input_dictionary, incon_init = False):
	"""
	Not documented
	"""
	years = 35
	"""
	wells = {'TR-4':[
					 [datetime.datetime(1992,1,1,0,0,0),datetime.datetime(2001,5,30,0,0,0)],
					 [datetime.datetime(2002,5,22,0,0,0),datetime.datetime(2005,3,28,0,0)],
					 [datetime.datetime(2006,1,1,0,0,0),datetime.datetime(2009,10,20,0,0,0)],
					 [datetime.datetime(2018,9,8,0,0,0),datetime.datetime(2022,2,10,0,0,0)],
					 ],
			 'TR-3':[
					 [datetime.datetime(2009,9,23,0,0,0),datetime.datetime(2010,5,7,0,0,0)],
					 [datetime.datetime(2011,6,27,0,0,0),datetime.datetime(2012,6,18,0,0)],
					 [datetime.datetime(2014,4,10,0,0,0),datetime.datetime(2016,6,7,0,0,0)],
					 ],
			 'TR-12A':[
					 [datetime.datetime(2010,6,30,0,0,0),datetime.datetime(2010,11,30,0,0,0)],
					 [datetime.datetime(2011,5,30,0,0,0),datetime.datetime(2012,4,30,0,0)],
					 [datetime.datetime(2012,11,30,0,0,0),datetime.datetime(2013,3,1,0,0,0)],
					 [datetime.datetime(2014,3,1,0,0,0),datetime.datetime(2015,3,1,0,0,0)],
					 ]
			}
	

	wells = {'TR-4':[
					 [datetime.datetime(2005,1,29,0,0,0),datetime.datetime(2019,8,29,0,0,0)],
					 ],
			 'TR-3':[
					 [datetime.datetime(2006,6,29,0,0,0),datetime.datetime(2018,4,4,0,0,0)],
					 ],
			 'TR-12A':[
					 [datetime.datetime(2004,8,26,0,0,0),datetime.datetime(2015,1,26,0,0,0)],
					 ],
			 'TR-4A':[
					 [datetime.datetime(2019,8,28,0,0,0),datetime.datetime(2022,2,15,0,0,0)],
					 ],
			 'TR-10A':[
					 [datetime.datetime(2000,12,16,0,0,0),datetime.datetime(2009,6,10,0,0,0)],
					 ]
			}
	"""
	wells = {'TR-4':[
					 [datetime.datetime(1992,1,1,0,0,0),datetime.datetime(2010,7,21,0,0,0)],
					 [datetime.datetime(2018,9,8,0,0,0),datetime.datetime(2019,12,31,0,0,0)]
					 ],
			 'TR-3':[
					 [datetime.datetime(2013,3,22,0,0,0),datetime.datetime(2013,12,22,0,0,0)],
					 [datetime.datetime(2014,9,21,0,0,0),datetime.datetime(2015,1,1,0,0,0)],
					 [datetime.datetime(2015,11,1,0,0,0),datetime.datetime(2016,2,7,0,0,0)],
					 ],
			 'TR-12A':[
					 [datetime.datetime(2010,7,21,0,0,0),datetime.datetime(2013,3,21,0,0,0)],
					 ],
			 'TR-4A':[
					 [datetime.datetime(2020,1,1,0,0,0),datetime.datetime(2022,2,15,0,0,0)],
					 ],
			}

	colors_wells = {'TR-4':'red',
					'TR-3':'green',
					'TR-12A':'blue',
					'TR-4A':'orange'}

	wells_feezones = {'TR-4':'NA746',
					'TR-3':'LD367',
					'TR-12A':'OA135',
					'TR-4A':'NA170'}

	model_init = {'TR-4':0.123524648502E8/1E5,
					'TR-3':0.104568567423E8/1E5,
					'TR-12A':0.13246656868E8/1E5,
					'TR-4A':0.124001354238E8/1E5}


	pres_data=pd.read_csv("../input/field_data.csv",delimiter=',')
	pres_data.replace(0, np.nan, inplace=True)
	pres_data = pres_data[pres_data['prs1'].notna()]
	pos = pres_data.columns.get_loc('prs1')
	pres_data['delta'] =  pres_data.iloc[1:, pos] - pres_data.iat[0, pos]

	dates_func_res=lambda datesX: datetime.datetime.strptime(str(datesX), "%Y%m%d")
	dates_res=list(map(dates_func_res,pres_data['fecha']))
	
	fig, ax = plt.subplots(figsize=(10,4))

	init_value = 35
	for i, well in enumerate(wells):
		data = wells[well]

		for n, dates_range in enumerate(data):
			ax.fill_between(dates_range,[-init_value-i,-init_value-i], [-init_value-(i+1),-init_value-(i+1)],color= colors_wells[well], alpha = 0.75)
			if n == 0:
				ax.text(dates_range[0]- datetime.timedelta(days=365),-init_value-i-0.75, well, fontsize = 8)


	for well in wells_feezones:

		file = "../output/PT/evol/%s_PT_evol.dat"%(well)
		data=pd.read_csv(file)

		times = data['TIME'].loc[data['ELEM'] == wells_feezones[well]]
		times.reset_index(drop=True)
		dates = []
		for time  in times:
			try:
				dates.append(input_dictionary['ref_date']+datetime.timedelta(seconds=int(time)))
			except OverflowError:
				print(time, "wont be plot")

		data_var = data['PRES_VAP'].loc[(data['ELEM'] == wells_feezones[well]) & (data['TIME']> 0 )]/1E5

		data_var = data_var.reset_index()

		var = 'delta'
		pos = data_var.columns.get_loc('PRES_VAP')

		if not incon_init:
			data_var['delta'] =  data_var.iloc[1:, pos] - data_var.iat[0, pos]
		else:
			data_var['delta'] =  data_var.iloc[1:, pos] - model_init[well]

		data_var['dates'] = dates

		ax.plot(data_var['dates'],data_var[var],lw = 0.3, linestyle='--',alpha=1,  color = colors_wells[well] )

		for interval in wells[well]:

			df = data_var[(data_var['dates'] > interval[0]) & (data_var['dates'] < interval[1])]

			ax.plot(df['dates'],df[var],linestyle='-',lw = 5, ms=2,marker=formats.plot_conf_marker['current'][0],alpha=0.5, color = colors_wells[well], label = well + ' ' + wells_feezones[well])


	handles, labels = ax.get_legend_handles_labels()
	unique = [(h, l) for i, (h, l) in enumerate(zip(handles, labels)) if l not in labels[:i]]
	ax.legend(*zip(*unique),loc="upper left")

	ax.set_title("Monitoring pressure")
	ax.set_xlabel("Time")
	ax.set_ylabel("Pressure drawdown [bar]")

	#Grid style
	ax.yaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
	ax.xaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
	ax.grid(True)

	ax.plot(dates_res,pres_data['delta'],color = 'black',linestyle = 'None' ,ms=0.5,marker='s',alpha=1, label = 'Monitoring')


	ax.format_xdata = mdates.DateFormatter('%Y%-m-%d %H:%M:%S')

	xlims=[input_dictionary['ref_date']-datetime.timedelta(days=365),input_dictionary['ref_date']+datetime.timedelta(days=years*365.25)]

	ax.set_xlim(xlims)
	years = mdates.YearLocator()
	years_fmt = mdates.DateFormatter('%Y')

	ax.xaxis.set_major_formatter(years_fmt)

	fig.savefig('../output/res_pressure.png',dpi=300) 

	plt.show()

def WB_scatter(input_dictionary, well,block,source):
	"""
	Not documented
	"""
	file="../output/mh/txt/%s_%s_%s_evol_mh.dat"%(well,block,source)

	if os.path.isfile(file):
		data=pd.read_csv(file)

		data=data.loc[(data['TIME']>0) & (data['FWH']>0) ]

		dates=[]
		for t in data['TIME']:
			dates.append(input_dictionary['ref_date']+datetime.timedelta(seconds=int(t)))

		fig1 = plt.figure(figsize=(10,4.5))

		ax = plt.subplot(111)

		ax2 = ax.twinx()
		
		ax.plot(data['PWB']/1E5,data['PWH']/1E5,'og',linestyle = 'None', label = 'PWB vs PWH', ms = 1)
		ax2.plot(data['PWB']/1E5,data['FWH'],'ob',linestyle = 'None', label = 'PWB vs FWH', ms = 1)

		ax.set_ylabel('Pressure [bar]')
		ax.set_xlabel('Pressure [bar]')
		ax2.set_ylabel('Flow rate [kg/s]')

		ax.set_title("%s %s %s"%(well,block,source))

		legends = [ax.get_lines()[0], ax2.get_lines()[0]]
		labels = ['PWH', 'FWH']

		plt.legend(legends, labels, loc="lower center", bbox_to_anchor=(0.75, -0.15), ncol=2, fancybox=True, shadow=True)

		plt.show()


		fig2 = plt.figure(figsize=(10,4.5))

		ax3 = plt.subplot(111)

		ax4 = ax3.twinx()
		
		ax3.plot(data['TWB'],data['TWH'],'or',linestyle = 'None', label = 'PWB vs PWH', ms = 1)
		ax4.plot(data['TWB'],data['FWH'],'om',linestyle = 'None', label = 'PWB vs FWH', ms = 1)

		ax3.set_ylabel('Temperature [C]')
		ax3.set_xlabel('Temperature [C]')
		ax4.set_ylabel('Flow rate [kg/s]')

		ax3.set_title("%s %s %s"%(well,block,source))

		legends = [ax3.get_lines()[0], ax4.get_lines()[0]]
		labels = ['TWH', 'FWH']

		plt.legend(legends, labels, loc="lower center", bbox_to_anchor=(0.75, -0.15), ncol=2, fancybox=True, shadow=True)

		plt.show()

def sources_plots(input_dictionary, well,block,source, variables = []):
	"""
	Not documented
	"""
	file = "../output/mh/txt/%s_%s_%s_evol_mh.dat"%(well,block,source)
	file2 = "../output/PT/evol/%s_PT_evol.dat"%(well)

	if os.path.isfile(file):
		data=pd.read_csv(file)

		data=data.loc[(data['TIME']>0)]

		dates=[]
		for t in data['TIME']:
			dates.append(input_dictionary['ref_date']+datetime.timedelta(seconds=int(t)))

		data['date_time']=dates

		fig = plt.figure(figsize=(10,4.5))

		ax = plt.subplot(111)

		for variable in variables:
		
			if variable == 'PWH':
				divisor = 1E5
				marker = '+'
			elif variable == 'ENTH':
				divisor = 1E3
				marker = 's'
			elif variable == 'EWH':
				divisor = 1E3
				marker = 'o'
			elif variable == 'PWB':
				divisor = 1E5
				marker = '^'
			else:
				divisor = 1
				marker = 'd'

			ax.plot(data['date_time'],data[variable]/divisor,marker=marker,linestyle = 'None', label = variable, ms = 3)

		if os.path.isfile(file2):
			data2 = pd.read_csv(file2)

			data2 = data2.loc[(data2['ELEM'] == block) & (data2['TIME']>0) ]

			dates2 = []
			for t in data2['TIME']:
				dates2.append(input_dictionary['ref_date']+datetime.timedelta(seconds=int(t)))
			data2['date_time']=dates2

			ax.plot(data2['date_time'],data2['PRES_VAP']/1E5,marker='o',linestyle = '-', label = 'PRES_VAP', ms = 1)

		ax.set_ylabel('Variable')
		ax.set_xlabel('Time')

		ax.set_title("%s %s %s"%(well,block,source))

		#legends = [ax.get_lines()[n] for n in range(len(variables))]
		#labels = variables.extend('PRES_VAP')

		plt.legend(loc="lower center", bbox_to_anchor=(0.78, -0.18), ncol=2, fancybox=True, shadow=True)

		fig.savefig('../output/PT/images/evol/%s_%s_%s_evol_plots.png'%(well,block,source)) 

		plt.show()

	else:
		print("%s does not exist"%file)

def mh_indivual(input_dictionary, well,block,source,save,show, production_dictionary, years = 35):
	"""Genera una grafica donde compara la evolucion de flujo y entalpia para el bloque asignado a la fuente de un pozo en particular

	Parameters
	----------	  
	well : str
	  Nombre de pozo
	block : str
	  Nombre de bloque, en general donde se ubica zona de alimentacion
	source : str
	  Nombre de fuente asociada a pozo
	save : bool
	  Almacaena la grafica generada
	show : bool
	  Almacaena la grafica generada

	Returns
	-------
	image
		{well}_{block}_{source}_evol.png: archivo con direccion ../output/mh/images/

	Note
	----
	El archivo correspondiente en la carpeta  ../output/mh/txt debe existir

	Examples
	--------
	>>> plot_compare_mh('AH-1','DA110','SRC1',save=True,show=False)
	"""

	#Read file, current calculated
	file="../output/mh/txt/%s_%s_%s_evol_mh.dat"%(well,block,source)
	OBJ_file = "../output/PT/json/it2_PT.json"
	OBJ_file_prev = "../output/PT/json/prev/it2_PT.json"
	file_real = "../input/mh/%s_mh.dat"%well

	if os.path.isfile(file):

		#fig = plt.figure(figsize=(10,4.5))
		#ax = plt.subplot(111)
		#ax1 = ax.twinx()


		data=pd.read_csv(file)

		#Setting the time to plot
		
		times=data['TIME']

		dates=[]
		for n in range(len(times)):
			if float(times[n])>0:
				try:
					dates.append(input_dictionary['ref_date']+datetime.timedelta(seconds=int(times[n])))
				except OverflowError:
					print(times[n],"plus",str(times[n]),"wont be plot")
				
		enthalpy=[]
		flow_rate=[]
		WHP=[]
		shw=[]

		for n in range(len(times)):
			if float(times[n])>0:
				try:
					if 'ENTHALPY' in data.columns:
						H_colum = 'ENTHALPY'
					elif 'ENTH' in data.columns:
						H_colum = 'ENTH'

					if 'GENERATION RATE' in data.columns:
						m_colum = 'GENERATION RATE'
					elif 'GEN' in data.columns:
						m_colum = 'GEN'

					if 'PWH' in data.columns:
						whp_colum = 'PWH'

					if 'SWH'in data.columns:
						swh_colum = 'SWH'

					enthalpy.append(data[H_colum][n]/1E3)
					flow_rate.append(data[m_colum][n])
					WHP.append(data[whp_colum][n])
					shw.append(data[swh_colum][n])
				except OverflowError:
					print(times[n],"plus",str(times[n]),"wont be plot")



		#ax.set_title("Well: %s, block %s, source %s"%(well,block,source) ,fontsize=8)
		#ax.set_ylabel('Flow rate [kg/s]',fontsize = 8)
		#ax.set_xlabel("Time",fontsize = 8)

		#ax1.set_ylabel('Enthalpy [kJ/kg]',fontsize = 8)
		#ax1.set_ylim([500,2700])
		

		#ax.plot(dates,np.absolute(flow_rate),color=formats.plot_conf_color['m'][1],\
		#	linestyle='--',ms=5,label='Calculated flow',marker=formats.plot_conf_marker['current'][0],alpha=formats.plot_conf_marker['current'][1])

		#ax.plot(dates,np.absolute(WHP)/1E5,color=formats.plot_conf_color['P'][1],\
		#	linestyle='--',ms=5,label='Calculated WHP',marker=formats.plot_conf_marker['current'][0],alpha=formats.plot_conf_marker['current'][1])

		#ax1.plot(dates,enthalpy,\
		#	linestyle='--',color=formats.plot_conf_color['h'][1],ms=5,label='Calculated enthalpy',marker=formats.plot_conf_marker['current'][0],alpha=formats.plot_conf_marker['current'][1])

		fontsize_ylabel = 8

		gs = gridspec.GridSpec(4, 1)
		fig, ax = plt.subplots(figsize=(12,7))

		fig.suptitle('%s %s %s'%(well,block,source))

		#Flow plot
		ax.format_xdata = mdates.DateFormatter('%Y%-m-%d_%H:%M:%S')
		ax=plt.subplot(gs[0,0])
		ln1=ax.plot(dates,np.absolute(flow_rate),color=formats.plot_conf_color['m'][1],linestyle='--',ms=5,label='Calculated flow',marker=formats.plot_conf_marker['current'][0],alpha=formats.plot_conf_marker['current'][1])
		ax.set_ylabel('Flow s[kg/s]',fontsize = fontsize_ylabel)
		ax.legend(loc="upper right")


		#Enthalpy plot
		ax2=plt.subplot(gs[1,0], sharex = ax)
		ax2.plot(dates,enthalpy,linestyle='--',color=formats.plot_conf_color['h'][1],ms=5,label='Calculated enthalpy',marker=formats.plot_conf_marker['current'][0],alpha=formats.plot_conf_marker['current'][1])
		ax2.legend(loc="upper right")
		ax2.set_ylabel('Enthalpy [kJ/kg]',fontsize = fontsize_ylabel)


		#WHPressure plot
		ax3=plt.subplot(gs[3,0], sharex = ax)
		ax3.plot(dates,np.absolute(WHP)/1E5,color=formats.plot_conf_color['P'][1],linestyle='--',ms=5,label='Calculated WHP',marker=formats.plot_conf_marker['current'][0],alpha=formats.plot_conf_marker['current'][1])
		ax3.legend(loc="upper right")
		ax3.set_ylabel('Pressure [bara]',fontsize = fontsize_ylabel)

		#Quality
		ax4=plt.subplot(gs[2,0], sharex = ax)
		ax4.plot(dates,np.absolute(shw),color=formats.plot_conf_color['SG'][1],linestyle='--',ms=5,label='Calculated Quality',marker=formats.plot_conf_marker['current'][0],alpha=formats.plot_conf_marker['current'][1])
		ax4.legend(loc="upper right")
		ax4.set_ylabel('Quality',fontsize = fontsize_ylabel)


		years = mdates.YearLocator()
		years_fmt = mdates.DateFormatter('%Y')

		plt.setp(ax.get_xticklabels(), visible=False)
		plt.setp(ax2.get_xticklabels(), visible=False)
		plt.setp(ax4.get_xticklabels(), visible=False)

		ax.xaxis.set_major_formatter(years_fmt)
		ax2.xaxis.set_major_formatter(years_fmt)
		ax3.xaxis.set_major_formatter(years_fmt)
		ax4.xaxis.set_major_formatter(years_fmt)

		try:
			data_real=pd.read_csv(file_real)
			data_real['date_time'] = pd.to_datetime(data_real['date_time'] , format="%Y-%m-%d_%H:%M:%S")
			data_real=data_real.set_index(['date_time'])
			data_real.index = pd.to_datetime(data_real.index)

			data_real['total_flow']=data_real['steam']+data_real['liquid']

			data_real['quality']= data_real['steam']/(data_real['liquid']+data_real['steam'])

			ln2=ax.plot(data_real.index,data_real['steam']+data_real['liquid'],linestyle='None',color=formats.plot_conf_color['m'][0],ms=3,label='Measured flow rate ',marker=formats.plot_conf_marker['real'][0],alpha=formats.plot_conf_marker['real'][1])

			ax2.plot(data_real.index,data_real['enthalpy'],linestyle='None',color=formats.plot_conf_color['h'][0],ms=3,label='Measured enthalpy',marker=formats.plot_conf_marker['real'][0],alpha=formats.plot_conf_marker['real'][1])

			ax3.plot(data_real.index,data_real['WHPabs'],linestyle='None',color=formats.plot_conf_color['P'][0],ms=3,label='Measured WHP',marker=formats.plot_conf_marker['real'][0],alpha=formats.plot_conf_marker['real'][1])

			ax4.plot(data_real.index,data_real['quality'],linestyle='None',color=formats.plot_conf_color['SG'][0],ms=3,label='Measured Quality',marker=formats.plot_conf_marker['real'][0],alpha=formats.plot_conf_marker['real'][1])



			#ax.plot(data_real.index,data_real['steam']+data_real['liquid'],\
				#linestyle='None',color=formats.plot_conf_color['m'][0],ms=3,label='Measured flow rate ',marker=formats.plot_conf_marker['real'][0],alpha=formats.plot_conf_marker['real'][1])

			#ax1.plot(data_real.index,data_real['enthalpy'],\
				#linestyle='None',color=formats.plot_conf_color['h'][0],ms=3,label='Measured enthalpy',marker=formats.plot_conf_marker['real'][0],alpha=formats.plot_conf_marker['real'][1])

			#ax.plot(data_real.index,data_real['WHPabs'],linestyle='None',color=formats.plot_conf_color['P'][0],ms=3,label='Measured WHP',marker=formats.plot_conf_marker['real'][0],alpha=formats.plot_conf_marker['real'][1])

			real_data=True

		except FileNotFoundError:
			real_data=False
			print("No real data for %s"%well)
			pass

		if save:
			fig.savefig('../output/mh/images/%s_%s_%s_evol_whp.png'%(well,block,source)) 
		if show:
			plt.show()



		"""

		plt.legend([ax.get_lines()[0],ax.get_lines()[2],
			        ax.get_lines()[1],ax.get_lines()[3],
			        ax1.get_lines()[0],ax1.get_lines()[1]],\
				   ['Computed flow rate ','Measured flow rate',\
				    'Computed WHP', 'Measured WHP',
				    'Computed flowing enthalpy', 'Measured flowing enthalpy'],loc="lower center", bbox_to_anchor=(0.5, -0.3), ncol=4, fancybox=True, shadow=True)
		
		box = ax.get_position()
		ax.set_position([box.x0, box.y0+0.1, box.width, box.height*0.9])
		ax.format_xdata = mdates.DateFormatter('%Y%-m-%d %H:%M:%S')
		xlims=[input_dictionary['ref_date']-datetime.timedelta(days=365),input_dictionary['ref_date']+datetime.timedelta(days=years*365.25)]

		ax.set_xlim(xlims)
		years = mdates.YearLocator()
		years_fmt = mdates.DateFormatter('%Y')
		ax.xaxis.set_major_formatter(years_fmt)


		#Grid style
		ax.yaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
		ax.xaxis.grid(True, which='major',linestyle='--', color='grey', alpha=0.6)
		ax.grid(True)
		"""


	else:
		print("There is not a file called %s, try running src_evol from output.py"%file)

def flowell_dates(input_dictionary,d1,d2,well, position = 3, source = None):
	"""
	Not documented
	"""

	db_path=input_dictionary['db_path']
	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	if source == None:
		sources_data = pd.read_sql_query("SELECT well, source_nickname, blockcorr FROM t2wellsource WHERE flow_type = 'P' ",conn)
		source = sources_data.loc[sources_data['well']==well].iloc[0]['source_nickname']
		blockcorr = sources_data.loc[sources_data['well']==well].iloc[0]['blockcorr']
		id_n = blockcorr + source
	else:
		id_n = source

	flowell_file = '../output/flowell.json'

	if os.path.isfile(flowell_file):
		df = pd.read_json(flowell_file, orient = 'split')
		df = df.loc[df['TIME']!=0]

		df['date_time'] = pd.to_datetime(df['TIME'] , format="%Y-%m-%d_%H:%M:%S")



		print(id_n)

		df = df.loc[(df['date_time']>d1) & (df['date_time']<d2) & (df['SOURCE'] == id_n),['date_time','DATA','ITER']]

		df.reset_index(inplace = True)

		positions = {0 : 'DEPTH',
					 1 : 'FLOW',
					 2 : 'VELOCITY',
					 3 : 'PRESSURE',
					 4 : 'ENTHALPY',
					 5 : 'TEMPERATURE',
					 6 : 'QUALITY',
					 7 : 'PROD. IND',
					 8 : 'PRODUCT'}
		"""
		max_iter = 4
		colors = {}
		color_m = cm.get_cmap('viridis', max_iter)
		for i, n in enumerate(np.linspace(0,1,max_iter)):
			colors[i]=color_m(n)
		"""

		colors = {  0 : 'grey',
					1:'orange',
					2:'k',
					3:'b',
					4:'g',
					5:'r',
					6:'m',
					7:'c',
					8:'lime',
					9:'royalblue',
					10:'crimson',
					11:'green',
					12:'olive',
					13:'mediumblue',
					14:'indigo',
					15:'violet',
					16:'orangered',
					17:'dodgerblue',
					18:'darkred',
					19:'navy',
					20:'darkorange',
					21:'teal',
					22:'darkturquoise',
					23:'cadetblue',
					24:'deepskyblue',
					25:'steelblue',
					26:'slateblue',
					27:'blueviolet',
					28:'darkorchid',
					29:'plum',
					30:'hotpink'}

		dates = df['date_time'].unique()

		fig, ax = plt.subplots(figsize=(5,8), dpi=300)

		from matplotlib.lines import Line2D

		clr = [colors[k] for k in colors]
		lines = [Line2D([0], [0], color=c, linewidth=1, linestyle='-') for c in clr]
		labels = colors.keys()

		#ax = fig.add_subplot(111)

		for date in dates:
			ix = df.loc[df['date_time']==date,'ITER'].unique()
			for i in ix:
				for data in df.loc[(df['date_time']==date) & (df['ITER']==i),'DATA']:
					data_n = []
					depths = []
					for point in data:
						data_n.append(point[position]/1E5)
						depths.append(geometry.MD_to_TVD(well,point[0])[2])
					ax.plot(data_n,depths, marker = 'o', ms = 3, label = date, lw = 0.1, color = colors[i], alpha = 1)


		ax.set_ylabel("masl")
		ax.xaxis.set_label_coords(0.5,1.07)
		ax.xaxis.tick_top()
		ax.set_xlabel("%s"%positions[position])

		#Set layers
		layers_info=geometry.vertical_layers(input_dictionary)
		ax2 = ax.twinx()            
		ax2.set_yticks(layers_info['top'], minor=True)
		ax2.yaxis.grid(True, which='minor',linestyle='--', color='grey', alpha=0.6)
		ax2.set_yticks( layers_info['middle'], minor=False)
		ax2.set_yticklabels(layers_info['name'])
		ax2.tick_params(axis='y',which='both',length=0)
		ax2.set_ylabel('Layers')
		ax2.set_ylim(ax.get_ylim())
		

		plt.legend(lines, labels, labelspacing = 0.075)

		fig.suptitle("%s \n from %s to %s"%(well,d1,d2), fontsize=10)
		fig.savefig('../output/flowell/%s'%well,dpi=300)

		plt.tight_layout()

		plt.show()


	else:
		return "Theres is not flowell output file"
	
def multiple_PI(input_dictionary, well, block, well_collection, save, show):
	"""
	It generates a single plot from a well that has been divided into many periods
	"""

	gs = gridspec.GridSpec(4, 1)
	fig, ax = plt.subplots(figsize=(12,7))

	ax.format_xdata = mdates.DateFormatter('%Y%-m-%d_%H:%M:%S')
	ax=plt.subplot(gs[0,0])
	ax2=plt.subplot(gs[1,0], sharex = ax)
	ax3=plt.subplot(gs[3,0], sharex = ax)
	ax4=plt.subplot(gs[2,0], sharex = ax)

	real_data=True
	fontsize_ylabel = 8


	fig.suptitle('%s %s %s'%(well,block,'multiple_PI'))

	ax.set_ylabel('Flow s[kg/s]',fontsize = fontsize_ylabel)
	ax.legend(loc="upper right")

	ax2.legend(loc="upper right")
	ax2.set_ylabel('Enthalpy [kJ/kg]',fontsize = fontsize_ylabel)

	ax3.legend(loc="upper right")
	ax3.set_ylabel('Pressure [bara]',fontsize = fontsize_ylabel)

	ax4.legend(loc="upper right")
	ax4.set_ylabel('Quality',fontsize = fontsize_ylabel)

	years = mdates.YearLocator()
	years_fmt = mdates.DateFormatter('%Y')

	plt.setp(ax.get_xticklabels(), visible=False)
	plt.setp(ax2.get_xticklabels(), visible=False)
	plt.setp(ax4.get_xticklabels(), visible=False)

	ax.xaxis.set_major_formatter(years_fmt)
	ax2.xaxis.set_major_formatter(years_fmt)
	ax3.xaxis.set_major_formatter(years_fmt)
	ax4.xaxis.set_major_formatter(years_fmt)


	for source in well_collection[well]:

		#Read file, current calculated
		file="../output/mh/txt/%s_%s_%s_evol_mh.dat"%(well,block,source)
		file_real = "../input/mh/%s_mh.dat"%well

		if os.path.isfile(file) and os.path.isfile(file_real):

			data=pd.read_csv(file)

			#Setting the time to plot
			
			times=data['TIME']

			dates=[]
			for n in range(len(times)):
				if float(times[n])>0:
					try:
						dates.append(input_dictionary['ref_date']+datetime.timedelta(seconds=int(times[n])))
					except OverflowError:
						print(times[n],"plus",str(times[n]),"wont be plot")
					
			enthalpy=[]
			flow_rate=[]
			WHP=[]
			shw=[]

			for n in range(len(times)):
				if float(times[n])>0:
					try:
						if 'ENTHALPY' in data.columns:
							H_colum = 'ENTHALPY'
						elif 'ENTH' in data.columns:
							H_colum = 'ENTH'

						if 'GENERATION RATE' in data.columns:
							m_colum = 'GENERATION RATE'
						elif 'GEN' in data.columns:
							m_colum = 'GEN'

						if 'PWH' in data.columns:
							whp_colum = 'PWH'

						if 'SWH'in data.columns:
							swh_colum = 'SWH'

						enthalpy.append(data[H_colum][n]/1E3)
						flow_rate.append(data[m_colum][n])
						WHP.append(data[whp_colum][n])
						shw.append(data[swh_colum][n])
					except OverflowError:
						print(times[n],"plus",str(times[n]),"wont be plot")

			try:
				data_real=pd.read_csv(file_real)
				data_real['date_time'] = pd.to_datetime(data_real['date_time'] , format="%Y-%m-%d_%H:%M:%S")
				data_real=data_real.set_index(['date_time'])
				data_real.index = pd.to_datetime(data_real.index)

				data_real['total_flow']=data_real['steam']+data_real['liquid']

				data_real['quality']= data_real['steam']/(data_real['liquid']+data_real['steam'])

				#Flow plot
				ln1=ax.plot(dates,np.absolute(flow_rate),color=formats.plot_conf_color['m'][1],linestyle='--',ms=5,label='Calculated flow',marker=formats.plot_conf_marker['current'][0],alpha=formats.plot_conf_marker['current'][1])
				ln2=ax.plot(data_real.index,data_real['steam']+data_real['liquid'],linestyle='None',color=formats.plot_conf_color['m'][0],ms=3,label='Measured flow rate ',marker=formats.plot_conf_marker['real'][0],alpha=formats.plot_conf_marker['real'][1])

				#Enthalpy plot
				ax2.plot(dates,enthalpy,linestyle='--',color=formats.plot_conf_color['h'][1],ms=5,label='Calculated enthalpy',marker=formats.plot_conf_marker['current'][0],alpha=formats.plot_conf_marker['current'][1])
				ax2.plot(data_real.index,data_real['enthalpy'],linestyle='None',color=formats.plot_conf_color['h'][0],ms=3,label='Measured enthalpy',marker=formats.plot_conf_marker['real'][0],alpha=formats.plot_conf_marker['real'][1])

				#WHPressure plot
				ax3.plot(dates,np.absolute(WHP)/1E5,color=formats.plot_conf_color['P'][1],linestyle='--',ms=5,label='Calculated WHP',marker=formats.plot_conf_marker['current'][0],alpha=formats.plot_conf_marker['current'][1])
				ax3.plot(data_real.index,data_real['WHPabs'],linestyle='None',color=formats.plot_conf_color['P'][0],ms=3,label='Measured WHP',marker=formats.plot_conf_marker['real'][0],alpha=formats.plot_conf_marker['real'][1])

				#Quality
				ax4.plot(dates,np.absolute(shw),color=formats.plot_conf_color['SG'][1],linestyle='--',ms=5,label='Calculated Quality',marker=formats.plot_conf_marker['current'][0],alpha=formats.plot_conf_marker['current'][1])
				ax4.plot(data_real.index,data_real['quality'],linestyle='None',color=formats.plot_conf_color['SG'][0],ms=3,label='Measured Quality',marker=formats.plot_conf_marker['real'][0],alpha=formats.plot_conf_marker['real'][1])
			except FileNotFoundError:
				real_data=False
				print("No real data for %s"%well)
				pass
	if save:
		fig.savefig('../output/mh/images/%s_%s_%s_evol_whp_multi_PI.png'%(well,block,source)) 
	if show:
		plt.show()
