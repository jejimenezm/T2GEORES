import numpy as np
import re as re
import subprocess
import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import shutil
import os
import itertools
import json
import shapefile
import pylab as plb
import math
import sys
from scipy.spatial import ConvexHull
from model_conf import input_data, mesh_setup,geners
import pandas as pd
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,
                               AutoMinorLocator)
import pyvista as pv
import vtk
import  geometry as geometry

class py2amesh:
	"""Genera malla a partir de posiciones de pozos y malla regular

	Las principales caracteristicas de este clase son:

	-Genera una malla regular cuadrada o rectangular segun se necesite en toda la extension especificada.

	-En el interior (campo cercano) genera una malla en forma hexagonal delimitada por una extension cuadrada/rectangular o por un poligo definido a traves de un shapefile.

	-Permite la introduccion de lineas a lo largo de la malla, los cuales pueden representar fallas o limites.

	-La malla es generada por amesh

	-La nomenclatura es la siguiente: se utiliza el alfabeto para definir el nivel de la capa [A-Z], se utiliza como correlativo el alfabeto seguido por tres numeros, estos no deben contener dos ceros consecutivos o en el centro, por lo que el primero elemento sera AA110 y al llegar a AA199 saltara a AA210.

	-Los pozos definidos en el parametro <i>filename</i> son los primeros de la lista

	-Genera archivos de entrada para Steinar (RockEditor)

	-Permite almacenar una malla en formato shapefile

	-Permite graficar una capa seleccionada a traves de matplotlib (Para capas con muchos elementos se recomienda extrer formato shapefile)

	-Se generan dos archivos en formato json, conteniendo el bloque correlativo de cada pozo y otro con todos los bloques e informacion espacial de cada pozo.

	Parameters
	----------
	filename : str
		Nombre de archivo con ubicaciones de pozos (zonas de alimentacion)
	filepath : str
		Direccion donde se encuentran los archivos de entrada en general "../input"
	Xmin  : float
		Posicion X minima de malla
	Xmax : float
		Posicion X maxima de malla
	Ymin : float
		Posicion Y minima de malla
	Ymax : float
		Posicion Y maxima de malla
	toler : float
		Parametro Amesh para creacion de malla
	layers : dictionary
		Nombre y espesor de capas
	layer_to_plot : int
		En caso de graficar una capa utilizando matplotlib define la capa que se graficara
	x_space : float
		Distanciamiento horizontal de elementos en direccion X
	y_space : float
		Distanciamiento horizontal de elementos en direccion Y
	radius_criteria: float
		Distancia minima entre pozos y elementos de malla regular
	x_from_boarder: float
		Distancia horizontal donde se situara el primer elemento desde el borde
	y_from_boarder: float
		Distancia vertical donde se situara el primer elemento desde el borde
	x_gap_min: float
		Posicion X minima de malla de campo cercano
	x_gap_max: float
		Posicion X maxima de malla de campo cercano
	x_gap_space: float
		Distanciamiento horizontal de elementos en direccion X en campo cercano
	y_gap_min: float
		Posicion Y minima de malla de campo cercano
	y_gap_max: float
		Posicion Y maxima de malla de campo cercano
	y_gap_space: float
		Distanciamiento vertical de elementos en direccion X en campo cercano
	plot_names: bool
		En caso de generar grafico utiliznado matplotlib activa la representacion de los nombres de los bloques [0,1]
	plot_centers: bool
		En caso de generar grafico utiliznado matplotlib activa la representacion centros de los bloques con un punto [0,1]
	z0_level: float
		Nivel de referencia para capas
	mesh_creation: bool
		Ejecuta creacion de malla
	plot_layer: bool
		Genera grafico de capa seleccionada
	to_steinar: bool
		Genera archivos de entrada para RockEditor steinar
	to_GIS: bool
		Genera un archivo shapefile de la capa seleccionada
	plot_all_GIS: bool
		Genera un archivo shapefile para todas las capas
	from_leapfrog: bool
		lee archivos leapfrong ../mesh/from_leapfrog/LF_geometry.dat y ../mesh/from_leapfrog/LF_t2.dat, sin embargo se pierde la simbologia usada en leapfrog y no te utiliza la malla regular ni los pozos. Solamente se crea la malla utilizando amesh
	line_file: str
		En el caso de querer especificar una linea o curva por la cual se quieran generar elementos, especificar punto xy con las cabezeras: ID, X, Y en formato csv. Donde ID corresponde a un mismo elementos, por lo que para formar una linea se deber tener al menos un ID y dos pares xy
	fault_distance: float
		En caso de definir line_file, se crearan elementos paralelos a una distancia fault_distance a lo largo de los elementos
	with_polygon: bool
		De ser cierto leera un archivo shapefile dentro del cual se construira el campo cercano
	polygon_shape: str
		Archivo que delimita la geometria del campo cercano, este no debe contener concavidades internas.
	set_inac_from_poly: bool
		Establece como elementos inactivos a los que se encuentren afuera del poligono definido fuera del shapefile de entrada
	set_inac_from_inner:bool
		Establece como elementos inactivos a los que se encuentren afuera del poligono del campo cerano

	Returns
	-------
	file
	  eleme: elementos de malla especificados en formato TOUGH2, tanto en el formato AMESH como para lectura de steinar
	file
	  conne : conexiones de elementos de malla especificados en formato TOUGH2, tanto en el formato AMESH como para lectura de steinar
	shapefile
	  mesh_{field}_layer_{layer} : archivo shapefile de una o todas las capas, especialmente util cuando ya se ha definido la distribucion de roca.
	graph
	  En caso de ser especificados
	  
	Attention
	---------
	El ejecutable amesh debe estar en la carpeta scripts o en el directorio


	"""

	def __init__(self,filename,filepath,Xmin,Xmax,Ymin,Ymax,\
		toler,layers,layer_to_plot,x_space,y_space,radius_criteria,\
		x_from_boarder,y_from_boarder,\
		x_gap_min,x_gap_max,x_gap_space,y_gap_min,y_gap_max,y_gap_space,\
		plot_names,plot_centers,z0_level,plot_all_GIS,from_leapfrog,line_file,fault_distance,with_polygon,polygon_shape,set_inac_from_poly,set_inac_from_inner,rotate,angle,inner_mesh_type):
		self.filename=filename
		self.filepath=filepath
		self.layers=layers
		self.number_of_layer=len(layers)
		self.Xmin=Xmin
		self.Xmax=Xmax
		self.Ymin=Ymin
		self.Ymax=Ymax
		self.z0_level=z0_level

		self.layer_to_plot=layer_to_plot

		self.radius_criteria=radius_criteria

		self.x_space=x_space
		self.y_space=y_space

		self.x_from_boarder=x_from_boarder
		self.y_from_boarder=y_from_boarder

		self.z=0
		self.delf_rock="101"  #Layer index
		self.filename_out="in"
		self.toler=toler

		self.x_gap_min=x_gap_min
		self.x_gap_max=x_gap_max
		self.x_gap_space=x_gap_space
		self.y_gap_min=y_gap_min
		self.y_gap_max=y_gap_max
		self.y_gap_space=y_gap_space

		self.plot_names=plot_names
		self.plot_centers=plot_centers
		self.plot_all_GIS=plot_all_GIS
		self.from_leapfrog=from_leapfrog
		self.line_file=line_file
		self.fault_distance=fault_distance

		self.with_polygon=with_polygon
		self.set_inac_from_poly=set_inac_from_poly
		self.set_inac_from_inner=set_inac_from_inner
		self.rotate=rotate
		self.angle=angle
		self.inner_mesh_type=inner_mesh_type

		if self.with_polygon:
			shape = shapefile.Reader(polygon_shape)

			#first feature of the shapefile
			feature = shape.shapeRecords()[0]
			points = feature.shape.__geo_interface__ 
			self.polygon=[]
			for n in points:
				for v in points[n]:
					if n=='coordinates':
						self.polygon.append([v[0],v[1]]) # (GeoJSON format)

		self.color_dict = {1:[['AA','AB','AC','AD','AE','AF','AG'],'ROCK1','red'],\
						   2:[['BA','BB','BC','BD','BE','BF','BG'],'ROCK2','white'],\
						   3:[['CA','CB','CC','CD','CE','CF','CG'],'ROCK3','yellow'],\
						   4:[['DA','DB','DC','DD','DE','DF','DG'],'ROCK4','blue'],\
						   5:[['EA','EB','EC','ED','EE','EF','EG'],'ROCK5','green'],\
						   6:[['FA','FB','FC','FD','FE','FF','FG'],'ROCK6','purple'],\
						   7:[['GA','GB','GC','GD','GE','GF','GG'],'ROCK7','#ff69b4'],\
						   8:[['HA','HB','HC','HD','HE','HF','HG'],'ROCK8','darkorange'],\
						   9:[['IA','IB','IC','ID','IE','IF','IG'],'ROCK9','cyan'],\
						   10:[['JA','JB','JC','JD','JE','JF','JG'],'ROK10','magenta'],\
						   11:[['KA','KB','KC','KD','KE','KF','KG'],'ROK11','#faebd7'],\
						   12:[['LA','LB','LC','LD','LE','LF','LG'],'ROK12','#2e8b57'],\
						   13:[['MA','MB','MC','MD','ME','MF','MG'],'ROK13','#eeefff'],\
						   14:[['NA','NB','NC','ND','NE','NF','NG'],'ROK14','#da70d6'],\
						   15:[['OA','OB','OC','OD','OE','OF','OG'],'ROK15','#ff7f50'],\
						   16:[['PA','PB','PC','PD','PE','PF','PG'],'ROK16','#cd853f'],\
						   17:[['QA','QB','QC','QD','QE','QF','QG'],'ROK17','#bc8f8f'],\
						   18:[['RA','RB','RC','RD','RE','RF','RG'],'ROK18','#5f9ea0'],\
						   19:[['SA','SB','SC','SD','SE','SF','SG'],'ROK19','#daa520']}

		self.rock_dict={}
		prof_cont=0
		for jk in range(1,len(layers)+1):
			if jk==1:
				prof_cont=layers[jk-1]*0.5
				z_real=z0_level-prof_cont
			elif jk>1:
				prof_cont=prof_cont+layers[jk-1]*0.5+layers[jk-2]*0.5
				z_real=z0_level-prof_cont
			self.rock_dict[jk]=[self.color_dict[jk][0][0],self.color_dict[jk][1],\
			self.color_dict[jk][2],self.color_dict[jk][0][0],z_real,self.layers[jk-1]]

	def regular_mesh(self):
		"""Genera malla regular en en toda la extension de la region definida por Xmin,Xmax,Ymin y Ymax
		"""
		x_regular=range(self.Xmin+self.x_from_boarder,self.Xmax+self.x_space-self.x_from_boarder,self.x_space)
		y_regular=range(self.Ymin+self.y_from_boarder,self.Ymax+self.y_space-self.y_from_boarder,self.y_space)

		x_regular_small=range(self.x_gap_min,self.x_gap_max+self.x_gap_space,self.x_gap_space)
		y_regular_small=range(self.y_gap_min,self.y_gap_max+self.y_gap_space,self.y_gap_space)
		self.mesh_array=[]
		for nx in x_regular:
			for ny in y_regular:
				if ((nx<self.x_gap_min) or (nx>self.x_gap_max)) or ((ny<self.y_gap_min) or (ny>self.y_gap_max)):
					self.mesh_array.append([nx,ny])


		#Small polygon area must be here

		for nxx in x_regular_small:
			cnt=0
			for nyy in y_regular_small:
				if [nxx,nyy] not in self.mesh_array:
					if self.inner_mesh_type=='honeycomb':
						if cnt%2==0:
							self.mesh_array.append([nxx,nyy])
						else:
							self.mesh_array.append([nxx+self.x_gap_space/2,nyy])
					elif self.inner_mesh_type=='regular':
						self.mesh_array.append([nxx,nyy])
					cnt+=1

		if self.rotate:
			angle=self.angle
			for pair in range(len(self.mesh_array)):
				x1=self.mesh_array[pair][0]-self.Xmin
				y1=self.mesh_array[pair][1]-self.Ymin
				self.mesh_array[pair][0]=x1*math.cos(math.pi*angle/180)-y1*math.sin(math.pi*angle/180)+self.Xmin
				self.mesh_array[pair][1]=x1*math.sin(math.pi*angle/180)+y1*math.cos(math.pi*angle/180)+self.Ymin

		return np.array(self.mesh_array)

	def check_in_out(self,point,source):
		"""Verifica si un punto de la malla del campo cercano esta dentro o fuera del poligo definido por el shapefile de entrada o del campo cercano
		"""

		boolean=False
		if source=='shapefile':
			polygon=self.polygon
			cnt=0
			for n in range(len(polygon)):
				if n+1!=len(polygon):
					m,b=plb.polyfit([polygon[n][0],polygon[n+1][0]],[polygon[n][1],polygon[n+1][1]],1)
					val_range=[polygon[n][1],polygon[n+1][1]]
				elif n+1==len(polygon):
					m,b=plb.polyfit([polygon[-1][0],polygon[0][0]],[polygon[-1][1],polygon[0][1]],1)
					val_range=[polygon[-1][1],polygon[0][1]]
				
				x=(point[1]-b)/m
				if point[0]<x and min(val_range)<point[1] and point[1]<max(val_range):
					cnt+=1
			if cnt==1:
				boolean=True
		elif source=='inner':
			Xarray_inner=np.array([self.x_gap_min,self.x_gap_max+self.x_gap_space])
			Yarray_inner=np.array([self.y_gap_min,self.y_gap_max+self.y_gap_space])
			if Xarray_inner[0]<point[0] and Xarray_inner[1]>point[0] and Yarray_inner[0]<point[1] and Yarray_inner[1]>point[1]:
				boolean=True
		return boolean

	def reg_pol_mesh(self):
		"""Crea malla regular cuando existe un poligono de entrada
		"""
		x_regular=np.arange(self.Xmin+self.x_from_boarder,self.Xmax+self.x_space-self.x_from_boarder,self.x_space)
		y_regular=np.arange(self.Ymin+self.y_from_boarder,self.Ymax+self.y_space-self.y_from_boarder,self.y_space)

		self.mesh_array=[]
		for nx in x_regular:
			for ny in y_regular:
				self.mesh_array.append([nx,ny])

		if self.rotate:
			angle=self.angle
			for pair in range(len(self.mesh_array)):
				x1=self.mesh_array[pair][0]-self.Xmin
				y1=self.mesh_array[pair][1]-self.Ymin
				self.mesh_array[pair][0]=x1*math.cos(math.pi*angle/180)-y1*math.sin(math.pi*angle/180)+self.Xmin
				self.mesh_array[pair][1]=x1*math.sin(math.pi*angle/180)+y1*math.cos(math.pi*angle/180)+self.Ymin


		x_pol=[]
		y_pol=[]
		for n in range(len(self.polygon)):
			x_pol.append(int(self.polygon[n][0]))
			y_pol.append(int(self.polygon[n][1]))
		x_pol.append(int(self.polygon[0][0]))
		y_pol.append(int(self.polygon[0][1]))


		x_gap_min=min(x_pol)
		x_gap_max=max(x_pol)
	
		y_gap_min=min(y_pol)
		y_gap_max=max(y_pol)

		small_mesh=[]

		x_regular_small=np.arange(x_gap_min,x_gap_max+self.x_gap_space,self.x_gap_space)
		y_regular_small=np.arange(y_gap_min,y_gap_max+self.y_gap_space,self.y_gap_space)

		for nxx in x_regular_small:
			cnt=0
			for nyy in y_regular_small:
				if [nxx,nyy] not in small_mesh:
					if self.inner_mesh_type=='honeycomb':
						if cnt%2==0:
							small_mesh.append([nxx,nyy])
						else:
							small_mesh.append([nxx+self.x_gap_space/2,nyy])
					elif self.inner_mesh_type=='regular':
						small_mesh.append([nxx,nyy])
					cnt+=1

		if self.rotate:
			angle=self.angle
			for pair in range(len(small_mesh)):
				x1=small_mesh[pair][0]-self.x_gap_min
				y1=small_mesh[pair][1]-self.y_gap_min
				small_mesh[pair][0]=x1*math.cos(math.pi*angle/180)-y1*math.sin(math.pi*angle/180)+self.x_gap_min
				small_mesh[pair][1]=x1*math.sin(math.pi*angle/180)+y1*math.cos(math.pi*angle/180)+self.y_gap_min
				
		to_delete=[]
		for v in range(len(self.mesh_array)):
			point=[self.mesh_array[v][0],self.mesh_array[v][1]]
			check=self.check_in_out(point,source='shapefile')
			if check:
				to_delete.append(v)

		self.mesh_array=np.delete(self.mesh_array, to_delete, 0)


		to_delete=[]
		for v in range(len(small_mesh)):
			point=[small_mesh[v][0],small_mesh[v][1]]
			check=self.check_in_out(point,source='shapefile')
			if not check:
				to_delete.append(v)

		small_mesh=np.delete(small_mesh, to_delete, 0)

		mesh_pol=[]
		for vk in range(len(self.mesh_array)):
			mesh_pol.append([self.mesh_array[vk][0],self.mesh_array[vk][1]])

		for vk in range(len(small_mesh)):
			mesh_pol.append([small_mesh[vk][0],small_mesh[vk][1]])

		return np.array(mesh_pol)

	def radius_select(self,x0,y0,xr,yr):
		"""Verifica si dos puntos estan mas cerca que el criterio seleccionado
		"""
		r=((x0-xr)**2+(y0-yr)**2)**0.5
		if r<self.radius_criteria:
			boolean=1
		else:
			boolean=0
		return boolean

	def from_leapfrog_mesh(self):
		"""Extrae puntos mas extremos y la posicion de los elementos de un set de datos provinientes de leapfrog, sin embargo no considera los elementos asociados a la roca ATM 0 
		"""
		geometry_file="../mesh/from_leapfrog/LF_geometry.dat"
		leapfrog_t2_file="../mesh/from_leapfrog/LF_t2.dat"

		#Creates a dictionary using the layers
		printlayer=False
		layer_min=[]
		layers={}
		with open(geometry_file,'r') as f:
		  for line in f.readlines():

		  	if line.rstrip()=='LAYERS':
		  		printlayer=True
		  		continue
		  	elif line.rstrip()=='SURFA' or line.rstrip()=='':
		  		printlayer=False

		  	if printlayer:
		  		layer=line.rstrip()[0:2]
		  		if layer==' 0':
		  			layer_min.append(line.rstrip()[2:13])
		  			layer_middle=line.rstrip()[13:23]
		  			layer_max=line.rstrip()[13:23]
		  			continue
		  		else:
		  			layer_max=layer_min[-1]
		  			layer_min.append(line.rstrip()[2:13])
		  			layer_middle=line.rstrip()[13:23]
		  		layers[int(layer)]=[float(layer_max),float(layer_middle),float(layer_min[-1])]

		max_layer=max(layers.keys())

		xc=[]
		yc=[]
		self.LP_mesh=[]
		printeleme=False
		#Takes the elements at the selected leyer
		with open(leapfrog_t2_file,'r') as f:
		  for line in f.readlines():

		  	if line.rstrip()=='ELEME':
		  		printeleme=True
		  		continue
		  	elif line.rstrip()=='CONNE' or line.rstrip()=='':
		  		printeleme=False

		  	if printeleme and line.rstrip()[0:5]!="ATM 0" and int(line.rstrip()[3:5])==max_layer:
		  		xc=float(line.rstrip()[51:60])
		  		yc=float(line.rstrip()[60:70])
		  		self.LP_mesh.append([xc,yc])


		#Creates a dictionary of the VERTICES

		printvertices=False
		self.x_min=1E20
		self.x_max=0

		self.y_min=1E20
		self.y_max=0
		with open(geometry_file,'r') as f:
		  for line in f.readlines():

		    #It will read between the keywords GRID and CONNECTIONS
		    if line.rstrip()=='VERTICES':
		      printvertices=True
		      continue
		    elif line.rstrip()=='GRID' or line.rstrip()=="":
		      printvertices=False

		    if printvertices:
		     	vertice_x=float(line.rstrip()[4:13])
		     	vertice_y=float(line.rstrip()[13:23])

		     	if vertice_x>self.x_max:
		     		self.x_max=vertice_x

		     	if vertice_y>self.y_max:
		     		self.y_max=vertice_y

		     	if vertice_x<self.x_min:
		     		self.x_min=vertice_x

		     	if vertice_y<self.y_min:
		     		self.y_min=vertice_y

		return self.x_max,self.x_min, self.y_min,self.y_max, self.LP_mesh

	def data(self):
		"""Define los puntos que ingresaran al archivo de entrada para amesh. Adicionalmente, en caso de definir un linea en el archivo de entrada <i><lines_data/i> se procedera a ingresar estos puntos y crear puntos paralelos en ambos extremos de la linea
		"""
		self.raw_data=np.genfromtxt(self.filepath+self.filename,dtype={'names':('ID','MD','X','Y','Z','TYPE'),'formats':('<U7','f4','f4','f4','f4','<U10')},delimiter=',',skip_header=True)
		print(self.raw_data)
		self.IDXY={}

		if not self.from_leapfrog:
			if self.with_polygon:
				regular_mesh=self.reg_pol_mesh()
			else:
				regular_mesh=self.regular_mesh()
		else:
			x,x1,y1,y2,regular_mesh=self.from_leapfrog_mesh()
		
		for n in range(len(self.raw_data['ID'])):
			#Store the data from wells
			self.IDXY["%s"%(str(self.raw_data['ID'][n]))]=[self.raw_data['X'][n],self.raw_data['Y'][n],self.raw_data['TYPE'][n]]
			#self.IDXY["%s"%(str(self.raw_data['ID'][n])).split("'")[1]]=[self.raw_data['X'][n],self.raw_data['Y'][n],self.raw_data['TYPE'][n]]
			to_delete=[]
			
			x0=self.raw_data['X'][n]
			y0=self.raw_data['Y'][n]
			
			#Delete the regular points close to the wells
			for ngrid in range(len(regular_mesh)):
				if abs(x0-regular_mesh[ngrid][0])<self.radius_criteria or abs(y0-regular_mesh[ngrid][1])<self.radius_criteria:
					boolean=self.radius_select(x0,y0,regular_mesh[ngrid][0],regular_mesh[ngrid][1])
					if boolean==1:
						to_delete.append(ngrid)

			regular_mesh=np.delete(regular_mesh, to_delete, 0)

		cnt=0
		if len(self.line_file)>0:
			self.lines_data=np.loadtxt(self.filepath+self.line_file,dtype={'names':('ID','X','Y'),'formats':('S10','f4','f4')},delimiter=',',skiprows=1)
			lines_dict={}
			for v in self.lines_data:
				key=v[0].decode('UTF-8')
				if key not in list(lines_dict.keys()):
					lines_dict[key]=[[float(v[1]),float(v[2])]]
				else:
					lines_dict[key].append([float(v[1]),float(v[2])])

			d=self.fault_distance
			for n in lines_dict:
				x_lines=[]
				y_lines=[]
				for v in lines_dict[n]:
					x_lines.append(v[0])
					y_lines.append(v[1])
				x_lines_np=np.array([])
				y_lines_np=np.array([])

				for nv in range(len(x_lines)):
					if nv+1<len(x_lines):

						x_lines_np_local=np.linspace(x_lines[nv],x_lines[nv+1],num=20)
						y_lines_np_local=np.linspace(y_lines[nv],y_lines[nv+1],num=20)
						
						x_lines_np=np.append(x_lines_np,np.linspace(x_lines[nv],x_lines[nv+1],num=20))
						y_lines_np=np.append(y_lines_np,np.linspace(y_lines[nv],y_lines[nv+1],num=20))

						m,b=plb.polyfit(x_lines_np_local,y_lines_np_local,1)

						p_s=(-1/m)
						c=abs(((d**2)/(1+(p_s)**2))**0.5)

						x_u=[c+x for x in x_lines_np_local]
						x_d=[-c+x for x in x_lines_np_local]

						y_u=[]
						y_d=[]

						for v in range(len(x_u)):
							y_u.append(p_s*x_u[v]+y_lines_np_local[v]-p_s*x_lines_np_local[v])
							y_d.append(p_s*x_d[v]+y_lines_np_local[v]-p_s*x_lines_np_local[v])


						x_lines_np=np.append(x_lines_np,x_u)
						x_lines_np=np.append(x_lines_np,x_d)

						y_lines_np=np.append(y_lines_np,y_u)
						y_lines_np=np.append(y_lines_np,y_d)

				for n2 in range(len(x_lines_np)):

					to_delete=[]

					x0=x_lines_np[n2]
					y0=y_lines_np[n2]
					
					for ngrid in range(len(regular_mesh)):
						if abs(x0-regular_mesh[ngrid][0])<self.radius_criteria or abs(y0-regular_mesh[ngrid][1])<self.radius_criteria:
							boolean=self.radius_select(x0,y0,regular_mesh[ngrid][0],regular_mesh[ngrid][1])
							if boolean==1:
								to_delete.append(ngrid)

					regular_mesh=np.delete(regular_mesh, to_delete, 0)

				for n3 in range(len(x_lines_np)):
					self.IDXY["RG%s"%(n3+cnt)]=[x_lines_np[n3],y_lines_np[n3],'REGUL']
				cnt+=n3

		#Store the data from the regular mesh on IDXY
		for n in range(len(regular_mesh)):
			self.IDXY["RG%s"%(n+cnt)]=[regular_mesh[n][0],regular_mesh[n][1],'REGUL']

		return {'raw_data':self.raw_data,'IDXY':self.IDXY}

	def well_blk_assign(self):
		"""Asigna el nombre a cada bloque, priorizando los pozos, es decir, estos llevan los correlativos mas bajos. Por ultimo almacena dos archivo json para registro de los bloques asignados a los pozos
		"""
		self.well_names=[]
		self.blocks_PT={}
		self.well_blocks_names={}
		self.wells_correlative={}
		data_dict=self.data()


		for n in range(self.number_of_layer):
			cnt=110
			layer_num=0

			for x in data_dict['IDXY']:

				if cnt%100==0:
					blocknumber=cnt+10
					cnt=blocknumber
				else:
					blocknumber=cnt
					
				if cnt%1010==0:
					cnt=110
					blocknumber=cnt
					layer_num+=1

				cnt+=1
				string_ele=self.color_dict[n+1][0][(layer_num)]

				blockname=string_ele+str(blocknumber)

				self.well_names.append(blockname)

				self.well_blocks_names["%s"%(blockname)]=[x,\
				                      data_dict['IDXY'][x][0],\
				                      data_dict['IDXY'][x][1],\
				                      data_dict['IDXY'][x][2],\
				                      n+1,self.rock_dict[n+1][4],\
				                      self.rock_dict[n+1][2],self.rock_dict[n+1][5]]
				#print(data_dict['IDXY'][x][2]!='REGUL')
				#if data_dict['IDXY'][x][2]=='prod' or data_dict['IDXY'][x][2]=='rein':
				if data_dict['IDXY'][x][2]!='REGUL':
					#str(data_dict['IDXY'][x][2]).split("'")[1],\
					self.blocks_PT["%s"%(blockname)]=[x,\
				                      str(data_dict['IDXY'][x][0]),\
				                      str(data_dict['IDXY'][x][1]),\
				                      str(data_dict['IDXY'][x][2]),\
				                      str(n+1),str(self.rock_dict[n+1][4]),\
				                      self.rock_dict[n+1][2],str(self.rock_dict[n+1][5])]
					try:
						self.wells_correlative[x]=["%s"%(blockname[1:])]
					except KeyError:
						pass
		json.dump(self.blocks_PT, open("../mesh/well_dict.txt",'w'),sort_keys=True, indent=4)
		json.dump(self.wells_correlative, open("../mesh/wells_correlative.txt",'w'),sort_keys=True, indent=4)

		return {'well_names':self.well_names, 'well_blocks_names':self.well_blocks_names}

	def input_file_to_amesh(self):
		"""Genera el archivo de entrada para amesh
		"""
		welldict=self.well_blk_assign()['well_blocks_names']
		
		if not self.from_leapfrog:
			Xarray=np.array([self.Xmin,self.Xmax])
			Yarray=np.array([self.Ymin,self.Ymax])
		else:
			xmax,xmin,ymin,ymax,regular_mesh=self.from_leapfrog_mesh()
			Xarray=np.array([xmin,xmax])
			Yarray=np.array([ymin,ymax])

		boundaries=[]
		
		for i, j in itertools.product(Xarray, Yarray):
			boundaries.append([i,j])


		if self.rotate:
			angle=self.angle
			for point_n in range(len(boundaries)):
				x1=boundaries[point_n][0]-self.Xmin
				y1=boundaries[point_n][1]-self.Ymin
				boundaries[point_n][0]=x1*math.cos(math.pi*angle/180)-y1*math.sin(math.pi*angle/180)+self.Xmin
				boundaries[point_n][1]=x1*math.sin(math.pi*angle/180)+y1*math.cos(math.pi*angle/180)+self.Ymin

		boundaries=np.array(boundaries)
		hull = ConvexHull(boundaries)

		file=open(self.filename_out, "w")
		file.write("locat\n")
		for x in sorted(welldict.keys()):
			string="{:5s}{:5d}{:20.2f}{:20.2f}{:20.2f}{:20.2f}\n".format(x,welldict[x][4],\
				                                       welldict[x][1],\
				                                       welldict[x][2],\
				                                       welldict[x][5],\
				                                       welldict[x][7])
			file.write(string)
		file.write("     \n")
		file.write("bound\n")
		for n in range(len(boundaries[hull.vertices,0])):
			string_bound=" %9.3E %9.3E\n"%(boundaries[hull.vertices,0][::-1][n],boundaries[hull.vertices,1][::-1][n])
			file.write(string_bound)

		file.write("     \n")
		file.write("toler")
		file.write("     \n")
		file.write("%10s\n"%self.toler)
		file.write("     ")
		file.close()

		fileread=open(self.filename,'r')
		os.system("amesh\n")
		string_out=fileread.read()
		files2move=['in','conne','eleme','segmt']
		for fn in files2move:
			shutil.move(fn,'../mesh/from_amesh/%s'%fn)

		return string_out

	def plot_voronoi(self):
		"""En caso de ser solicitado, grafica la  malla a partir de los archivo en la carpeta ../mesh/from_amesh
		"""
		welldict=self.well_blk_assign()['well_blocks_names']
		if os.path.isfile('../mesh/from_amesh/segmt'):
			data=np.genfromtxt('../mesh/from_amesh/segmt', dtype="f8,f8,f8,f8,i8,S5,S5", names=['X1','Y1','X2','Y2','index','elem1','elem2'],delimiter=[15,15,15,15,5,5,5])
			
			fig, ax0 = plt.subplots(figsize=(10,10))

			#Set of the principal plot
			ax0.axis([self.Xmin,self.Xmax,self.Ymin,self.Ymax])
			ax0.set_xlabel('East [m]')
			ax0.set_ylabel('North [m]')
			ax0.set_title("Mesh for layer %s"%self.layer_to_plot,y=1.04)
			ax0.set_xticks(range(self.Xmin+self.x_from_boarder,self.Xmax+self.x_space-self.x_from_boarder,self.x_space))
			ax0.set_yticks(range(self.Ymin+self.y_from_boarder,self.Ymax+self.y_space-self.y_from_boarder,self.y_space))
			ax0.xaxis.set_minor_locator(AutoMinorLocator())
			ax0.yaxis.set_minor_locator(AutoMinorLocator())

			#Plot of the Yaxis in the top 
			ax1 = ax0.twinx()
			ax1.set_ylim(ax0.get_ylim())
			ax1.set_yticks(ax0.get_yticks())
			ax1.yaxis.set_minor_locator(AutoMinorLocator())

			#Plot of the Xaxis in the top 
			ax2 = ax0.twiny()
			ax2.set_xticks(ax0.get_xticks())
			ax2.set_xlim(ax0.get_xlim())
			ax2.xaxis.set_minor_locator(AutoMinorLocator())


			for n in np.unique(data['elem1']):
				Xfill=[]
				Yfill=[]
				if n[0:2] in self.color_dict[self.layer_to_plot][0]:
					for j in range(len(data['X1'])):
						cnt=0
						if data['elem1'][j]==n:
							Xfill.append(data['X1'][j])
							Xfill.append(data['X2'][j])
							Yfill.append(data['Y1'][j])
							Yfill.append(data['Y2'][j])
							plt.plot([data['X1'][j],data['X2'][j]],[data['Y1'][j],data['Y2'][j]],'-k')
							
							if self.plot_names:
								if cnt==0:
									if welldict[n][3]=='WELL':
										ax0.text(welldict[n][1],welldict[n][2],\
											      "%s, %s"%(welldict[n][0],n),fontsize=8)
										color_dot='r'
									else:
										ax0.text(welldict[n][1],welldict[n][2],\
											      welldict[n][0],fontsize=8)
										color_dot='b'
								cnt+=1

							if self.plot_centers:
								if welldict[n][3]=='WELL':
									color_dot='r'
								else:
									color_dot='b'
								ax0.plot(welldict[n][1],welldict[n][2],'%so'%color_dot,ms=1) 
								

					ax0.fill(Xfill,Yfill,welldict[n][6],alpha=0.5)
			ax0.grid()
			ax0.grid(which='major', color='#CCCCCC', linestyle='--',alpha=0.5)
			fig.savefig('../mesh/plot_voronoi_'+str(datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')),bbox_inches="tight", pad_inches = 0)
			plot_s=plt.show()
		else:
			plot_s="Excecute input_file_to_amesh() function first"
		return plot_s

	def to_steinar(self):
		"""Convierte los archivos de salida amesh en formato de entrada para Steinar
		"""
		if os.path.isfile('../mesh/from_amesh/segmt'):
			shutil.copyfile('../mesh/from_amesh/segmt', '../mesh/to_steinar/segmt')
			ele_file_st=open('../mesh/to_steinar/eleme','w')  
			ele_file=open('../mesh/from_amesh/eleme','r')  
			data_eleme=ele_file.readlines()
			
			if self.set_inac_from_poly or self.set_inac_from_inner:
				source_file="../mesh/from_amesh/eleme"
				data_eleme=pd.read_csv(source_file,delim_whitespace=True,skiprows=1,header=None,names=['block','rocktype','vol','X','Y','Z'])
				data_eleme.set_index('block')
				ele_file_st.write("eleme\n")

				if self.set_inac_from_inner:
					source='inner'
				if self.set_inac_from_poly:
					source='shapefile'
					
				for index, row in data_eleme.iterrows():
					check=self.check_in_out([row['X'],row['Y']],source=source)
					outside=1
					if not check:
						outside=-1
					ele_file_st.write("%5s%10s%5s%10.3E\n"%(row['block']," ",row['rocktype'],row['vol']*outside))
			else:
				cnt=0
				for a_line in data_eleme:
					if cnt!=0:
						name_rock_vol = a_line[0:30]  
						ele_file_st.write("%s\n"%name_rock_vol)
					else:
						ele_file_st.write("eleme\n")
					cnt+=1
			ele_file_st.close()
			ele_file.close()

			conne_file_st=open('../mesh/to_steinar/conne','w')  
			conne_file=open('../mesh/from_amesh/conne','r')  
			data_conne=conne_file.readlines()
			cnt=0
			for a_line in data_conne:
				if cnt!=0:
					name_conne = a_line[0:11]  
					if '*' in name_conne:
						pass
					elif cnt<=len(data_conne)-2:
						try:
							conne_file_st.write("%s"%name_conne)
							conne_file_st.write("   0    0    0   ")

							nod4=a_line[60:64]

							if len(nod4)==4:
								per=3
							else:
								per=a_line[29:30]

							conne_file_st.write("%s"%per)

							nod1=a_line[30:40].replace('+', '')
							conne_file_st.write(" %9.3E"%(float(nod1)))

							nod2=a_line[40:50].replace('+', '')
							conne_file_st.write(" %9.3E"%(float(nod2)))

							nod3=a_line[50:60].replace('+', '')
							conne_file_st.write(" %9.3E"%(float(nod3)))

							if len(nod4)==4:
								#nod4=-1
								conne_file_st.write("{:9.1f}".format(float(nod4)))
							elif len(nod4)==1:
								conne_file_st.write("      0.0")

							conne_file_st.write(" 0.0000E+00\n")

						except ValueError:
							pass
				else:
					conne_file_st.write("conne\n")
				cnt+=1
			conne_file_st.close()
			conne_file.close()

			in_file_st=open('../mesh/to_steinar/in','w')

			#block_file=open('block_name.csv','w')
			in_file=open('../mesh/from_amesh/in','r')  
			data_in=in_file.readlines()
			in_file_st.write("bound\n")

			if not self.from_leapfrog:
				Xarray=np.array([self.Xmin,self.Xmax])
				Yarray=np.array([self.Ymin,self.Ymax])
			else:
				xmax,xmin,ymin,ymax,regular_mesh=self.from_leapfrog_mesh()
				Xarray=np.array([xmin,xmax])
				Yarray=np.array([ymin,ymax])

			in_file_st.write(" %6.2d %6.2d\n"%(Xarray[0],Yarray[0]))
			in_file_st.write(" %6.2d %6.2d\n"%(Xarray[0],Yarray[1]))
			in_file_st.write(" %6.2d %6.2d\n"%(Xarray[1],Yarray[1]))
			in_file_st.write(" %6.2d %6.2d\n\n"%(Xarray[1],Yarray[0]))
			in_file_st.write("locat\n")

			cnt=0

			for ny in data_in:
				if cnt>0 and cnt<(len(data_in)-10):
					read1=ny[0:6]
					read2=ny[8:11]
					read3=ny[11:31]
					read4=ny[31:52]
					read5=ny[51:72]
					read6=ny[71:92]
					in_file_st.write("%s"%read1)
					in_file_st.write("%4s"%read2)
					in_file_st.write("%23.8E"%float(read3))
					in_file_st.write("%24.8E"%float(read4))
					in_file_st.write("%24.8E"%float(read5))
					in_file_st.write("%24.8E\n"%float(read6))

					#stringx="%.2f,%.2f,%.2f\n"%(float(read3),float(read4),float(read5))
					#block_file.write(stringx)
				cnt+=1

			in_file_st.close()
			in_file.close()
			#block_file.close()
			rock_file_st=open('../mesh/to_steinar/rocks','w')
			rock_file_st.write("rock1    02.6500E+031.0000E-011.0000E-151.0000E-151.0000E-152.1000E+008.5000E+02 160 243 150")
			rock_file_st.close()
		else:
			pass

	def to_GIS(self):
		"""Toma como entrada el archivo segment de ../mesh/from_amesh y eleme de ../mesh/to_stainar y los convierte en shapefile con atributos de roca, nombre y volumen
		"""
		if os.path.isfile('../mesh/from_amesh/segmt') and os.path.isfile('../mesh/to_steinar/eleme'):
			if self.plot_all_GIS:
				max_layer=self.number_of_layer
				min_layer=1
			else:
				max_layer=self.layer_to_plot
				min_layer=self.layer_to_plot

			for ln in range(min_layer,max_layer+1,1):
				w=shapefile.Writer('../mesh/GIS/mesh_cga_layer_%s'%ln)
				w.field('BLOCK_NAME', 'C', size=5)
				w.field('ROCKTYPE', 'C', size=5)
				w.field('VOLUMEN', 'F', decimal=10)
				
				alttype = np.dtype([('X1', '<f8'), ('Y1', '<f8'), ('X2', '<f8'), ('Y2', '<f8'), ('index', '<f8'), ('elem1', 'U5'), ('elem2', 'U5')])
				data = np.genfromtxt('../mesh/to_steinar/segmt', dtype=alttype, delimiter=[15,15,15,15,5,5,5])

				elem_file = open('../mesh/to_steinar/eleme', 'r')
				plain_elemfile=elem_file.read()

				for n in np.unique(data['elem1']):
					if n[0:2] in self.color_dict[ln][0]:
						points=[]
						line = re.findall(r"%s.*$"%n, plain_elemfile,re.MULTILINE)
						rocktype=str(line)[17:22]
						volumen=float(str(line)[22:32])
						for j in range(len(data['X1'])):
							if data['elem1'][j]==n:
								point1=[data['X1'][j],data['Y1'][j]]
								point2=[data['X2'][j],data['Y2'][j]]
								points.append(point1)
								points.append(point2)
						w.poly([points])
						w.record(n,rocktype,volumen)
				w.close()
				elem_file.close()
		else:
			None

def mesh_creation_func(dictionary=mesh_setup,model_conf_dictionary=input_data):
	
	"""Genera malla

	Parameters
	----------
	filename : str
		Nombre de archivo con ubicaciones de pozos (zonas de alimentacion)
	filepath : str
		Direccion donde se encuentran los archivos de entrada en general "../input"
	Xmin  : float
		Posicion X minima de malla
	Xmax : float
		Posicion X maxima de malla
	Ymin : float
		Posicion Y minima de malla
	Ymax : float
		Posicion Y maxima de malla
	toler : float
		Parametro Amesh para creacion de malla
	layers : dictionary
		Nombre y espesor de capas
	layer_to_plot : int
		En caso de graficar una capa utilizando matplotlib define la capa que se graficara
	x_space : float
		Distanciamiento horizontal de elementos en direccion X
	y_space : float
		Distanciamiento horizontal de elementos en direccion Y
	radius_criteria: float
		Distancia minima entre pozos y elementos de malla regular
	x_from_boarder: float
		Distancia horizontal donde se situara el primer elemento desde el borde
	y_from_boarder: float
		Distancia vertical donde se situara el primer elemento desde el borde
	x_gap_min: float
		Posicion X minima de malla de campo cercano
	x_gap_max: float
		Posicion X maxima de malla de campo cercano
	x_gap_space: float
		Distanciamiento horizontal de elementos en direccion X en campo cercano
	y_gap_min: float
		Posicion Y minima de malla de campo cercano
	y_gap_max: float
		Posicion Y maxima de malla de campo cercano
	y_gap_space: float
		Distanciamiento vertical de elementos en direccion X en campo cercano
	plot_names: bool
		En caso de generar grafico utiliznado matplotlib activa la representacion de los nombres de los bloques [0,1]
	plot_centers: bool
		En caso de generar grafico utiliznado matplotlib activa la representacion centros de los bloques con un punto [0,1]
	z0_level: float
		Nivel de referencia para capas
	mesh_creation: bool
		Ejecuta creacion de malla
	plot_layer: bool
		Genera grafico de capa seleccionada
	to_steinar: bool
		Genera archivos de entrada para RockEditor steinar
	to_GIS: bool
		Genera un archivo shapefile de la capa seleccionada
	plot_all_GIS: bool
		Genera un archivo shapefile para todas las capas
	from_leapfrog: bool
		lee archivos leapfrong ../mesh/from_leapfrog/LF_geometry.dat y ../mesh/from_leapfrog/LF_t2.dat, sin embargo se pierde la simbologia usada en leapfrog y no te utiliza la malla regular ni los pozos. Solamente se crea la malla utilizando amesh
	line_file: str
		En el caso de querer especificar una linea o curva por la cual se quieran generar elementos, especificar punto xy con las cabezeras: ID, X, Y en formato csv. Donde ID corresponde a un mismo elementos, por lo que para formar una linea se deber tener al menos un ID y dos pares xy
	fault_distance: float
		En caso de definir line_file, se crearan elementos paralelos a una distancia fault_distance a lo largo de los elementos
	with_polygon: bool
		De ser cierto leera un archivo shapefile dentro del cual se construira el campo cercano
	polygon_shape: str
		Archivo que delimita la geometria del campo cercano, este no debe contener concavidades internas.
	set_inac_from_poly: bool
		Establece como elementos inactivos a los que se encuentren afuera del poligono definido fuera del shapefile de entrada
	set_inac_from_inner:bool
		Establece como elementos inactivos a los que se encuentren afuera del poligono del campo cerano

	Returns
	-------
	file
	  eleme: elementos de malla especificados en formato TOUGH2, tanto en el formato AMESH como para lectura de steinar
	file
	  conne : conexiones de elementos de malla especificados en formato TOUGH2, tanto en el formato AMESH como para lectura de steinar
	shapefile
	  mesh_{field}_layer_{layer} : archivo shapefile de una o todas las capas, especialmente util cuando ya se ha definido la distribucion de roca.
	graph
	  En caso de ser especificados
	  
	Attention
	---------
	El ejecutable amesh debe estar en la carpeta scripts o en el directorio
	"""

	layers_thick=list(map(float,np.array(list(model_conf_dictionary['LAYERS'].values()))[:][:,1]))


	#layers_thick=map(float,np.array(layers.values())[:][:,1]) #Python 2

	blocks=py2amesh(dictionary['filename'],dictionary['filepath'],dictionary['Xmin'],dictionary['Xmax'],dictionary['Ymin'],dictionary['Ymax'],\
			dictionary['toler'],layers_thick,dictionary['layer_to_plot'],dictionary['x_space'],dictionary['y_space'],dictionary['radius_criteria'],dictionary['x_from_boarder'],dictionary['y_from_boarder'],\
			dictionary['x_gap_min'],dictionary['x_gap_max'],dictionary['x_gap_space'],dictionary['y_gap_min'],dictionary['y_gap_max'],dictionary['y_gap_space'],dictionary['plot_names'],dictionary['plot_centers'],\
			input_data['z_ref'],dictionary['plot_all_GIS'],dictionary['from_leapfrog'],dictionary['line_file'],dictionary['fault_distance'],dictionary['with_polygon'],dictionary['polygon_shape'],\
			dictionary['set_inac_from_poly'],dictionary['set_inac_from_inner'],dictionary['rotate'],dictionary['angle'],dictionary['inner_mesh_type'])

	if dictionary['mesh_creation']:

		blocks.input_file_to_amesh()

		if dictionary['plot_layer']:
			blocks.plot_voronoi()
		if dictionary['to_steinar']:
			blocks.to_steinar()
		if dictionary['to_GIS']:
			blocks.to_GIS()

	elif not dictionary['mesh_creation']:
		if dictionary['plot_layer']:
			blocks.plot_voronoi()
		if dictionary['to_steinar']:
			blocks.to_steinar()
		if dictionary['to_GIS']:
			blocks.to_GIS()

	return None

def change_ref_elevation(variation=0):

	in_file_steinar='../mesh/to_steinar/in'
	in_file_amesh='../mesh/from_amesh/in'

	if os.path.isfile(in_file_steinar) and os.path.isfile(in_file_amesh):

		steinar_colums=[(0,5),(5,10),(10,35),(35,60),(60,85),(85,110)]
		steinar_data=pd.read_fwf(in_file_steinar,colspecs=steinar_colums,skiprows=7,header=None,names=['block','level','X','Y','Z','h'])
		steinar_data['Z']=steinar_data['Z'] + variation

		string=""
		with open(in_file_steinar,'r') as f:
			for line in f.readlines():
				string+=line
				if 'locat' in line:
					break

		for index, row in steinar_data.iterrows():
			string+="{:5s}{:5d}{:23.8f}{:24.8f}{:24.8f}{:24.8f}\n".format(row['block'], row['level'],row['X'],row['Y'],row['Z'],row['h'])


		steinar_in_file=open(in_file_steinar,'w')
		steinar_in_file.write(string)
		steinar_in_file.close()


		amesh_colums=[(0,5),(5,10),(10,30),(30,50),(50,70),(70,90)]
		amesh_data=pd.read_fwf(in_file_amesh,colspecs=amesh_colums,skiprows=1,header=None,names=['block','level','X','Y','Z','h'])
		amesh_data.dropna(inplace=True)
		amesh_data['Z']=amesh_data['Z'] + variation

		string="locat\n"

		for index, row in amesh_data.iterrows():
			string+="{:5s}{:5.0f}{:20.3f}{:20.3f}{:20.3f}{:20.3f}\n".format(row['block'], row['level'],row['X'],row['Y'],row['Z'],row['h'])

		with open(in_file_amesh,'r') as f:
			check_in=False
			for line in f.readlines():
				if 'bound' in line:
					check_in=True
					string+='\n'
				
				if check_in:
					string+=line

		amesh_in_file=open(in_file_amesh,'w')
		amesh_in_file.write(string)
		amesh_in_file.close()

def empty_mesh():
	"""Vacia carpetas relacionadas con malla: mesh/to_steinar, mesh/from_amesh y mesh/GIS
	
	Examples
	--------
	>>> empty_mesh()

	"""
	folders=['../mesh/to_steinar','../mesh/from_amesh','../mesh/GIS']
	for folder in folders:
		for file in os.listdir(folder):
			try:
				file_path=os.path.join(folder,file)
				os.remove(file_path)
			except IsADirectoryError:
				pass

def ELEM_to_json():
	"""Combina los archivos eleme e in de la carpeta steinar en un archivo json

	Returns
	-------
	file
	  in: de la carpeta steinar
	  eleme: de la carpeta steinar
	  
	Attention
	---------
	Se utiliza la carpeta steinar ya que es la que provee la inofrmacion del modelo con las rocas modificadas.

	Examples
	--------
	>>> ELEM_to_json()
	"""
	source_file="../mesh/to_steinar/in"
	eleme_file="../mesh/to_steinar/eleme"

	eleme_dict={}
	col_eleme=[(0,6),(15,20),(20,30)]

	if os.path.isfile(source_file) and os.path.isfile(eleme_file):
		data_in=pd.read_csv(source_file,delim_whitespace=True,skiprows=7,header=None,names=['block','li','X','Y','Z','h'])
		data_eleme=pd.read_fwf(eleme_file,colspecs=col_eleme,skiprows=1,header=None,names=['block','rocktype','vol'])

		#data_eleme[['rocktype','vol']] =data_eleme.data.apply(lambda x: pd.Series([str(x)[0:5],str(x)[5:16]]))
		#data_eleme.drop('data', axis=1, inplace=True)

		data_in.set_index('block')
		data_eleme.set_index('block')

		data_eleme=data_eleme.merge(data_in, left_on='block', right_on='block',how='left')
		data_eleme.set_index('block',inplace=True)
		data_eleme.to_json('../mesh/ELEME.json',orient="index",indent=2)

	else:
		sys.exit("The file %s or directory do not exist"%source_file)

def CONNE_to_json():
	"""Genera un archivo json a partir del archivo CONNE en la carpeta to_steinar

	Returns
	-------
	file
	  conne: de la carpeta steinar
	  
	Attention
	---------
	Se utiliza la carpeta steinar ya que es la que provee la inofrmacion del modelo con las rocas modificadas.

	Examples
	--------
	>>> CONNE_to_json()
	"""
	source_file="../mesh/to_steinar/conne"

	conne_dict={}

	if os.path.isfile(source_file):
		with open(source_file) as rock_file:
			for line in rock_file.readlines()[1:]:
				linex=line.split()
				if float(linex[8])<=0:
					conne_dict[linex[0]]=[int(linex[4]),float(linex[5]),float(linex[6]),float(linex[7]),float(linex[8])]
				else:
					conne_dict[linex[0]]=[int(linex[4]),float(linex[5]),float(linex[6]),float(linex[7]),-1*float(linex[8])]

		CONNE_pd=pd.DataFrame.from_dict(conne_dict,orient='index', columns=['ISOT','D1','D2','AREAX', 'BETAX'])
		CONNE_pd.to_json('../mesh/CONNE.json',orient="index",indent=2)

	else:
		sys.exit("The file %s or directory do not exist"%source_file)

def segmnt_to_json():

	eleme_file="../mesh/to_steinar/eleme"
	segmt_file="../mesh/to_steinar/segmt"
	elment_dict={}

	col_eleme=[(0,6),(15,20),(20,30)]
	col_segment=[(0,15),(15,30),(30,45),(45,60),(60,65),(65,70),(70,75)]
	if os.path.isfile(segmt_file) and os.path.isfile(eleme_file):

		segmt_data=pd.read_fwf(segmt_file,colspecs=col_segment,header=None,names=['X1','Y1','X2','Y2','redunt','eleme1','eleme2'])

		eleme_data=pd.read_fwf(eleme_file,colspecs=col_eleme,skiprows=1,header=None,names=['block','rocktype','vol'])

		eleme_data=eleme_data.merge(segmt_data, left_on='block', right_on='eleme1',how='left')

		eleme_data['points'] = eleme_data[['X1','Y1','X2','Y2']].apply(lambda r: tuple(r), axis=1).apply(np.array)

		eleme_data=eleme_data.groupby(['block','rocktype','vol'])['points'].agg(lambda x: list(np.concatenate(x.values))).reset_index()

		eleme_data.set_index('block', inplace=True)

		eleme_data.to_json('../mesh/segmt.json',orient="index",indent=2)

	else:
		sys.exit("Either the file %s or %s do not exist"%(eleme_file,segmt_file))

def plot_voronoi(layer='D',plot_center=False,dictionary=mesh_setup,mark_elements=False,geners=geners,cross_section=None):

	segmt_json_file='../mesh/segmt.json'

	eleme_json_file='../mesh/ELEME.json'

	wells_corr_json_file='../mesh/wells_correlative.txt'


	if cross_section:
		x_points=cross_section['cross_section']['x']
		y_points=cross_section['cross_section']['y']

	if os.path.isfile(segmt_json_file):
		with open(segmt_json_file) as file:
		  	blocks=json.load(file)

		rocktypes={}
		cnt=1
		for block in blocks:
			if blocks[block]['rocktype'] not in rocktypes:
				rocktypes[blocks[block]['rocktype']]=dictionary['colors'][cnt]
				cnt+=1

		if os.path.isfile(eleme_json_file):
			with open(eleme_json_file) as file:
			  	ELEME=json.load(file)


		if mark_elements:
			legend='Legend'
			if os.path.isfile(wells_corr_json_file):
				with open(wells_corr_json_file) as file:
				  	well_corr=json.load(file)
			for gen in geners:
				src=geners[gen]['SL']+str(geners[gen]['NS'])
				corr=gen[1:6]
				well_corr[src]=[corr]
			corr_well = {y[0]:x for x,y in well_corr.items()}
		else:
			legend='ROCKS'

		fig, ax0 = plt.subplots(figsize=(10,10))
		ax0.set_xlabel("East [m]")
		ax0.set_ylabel("North [m]")
		
		if cross_section:
			ax0.plot(x_points,y_points,linestyle='--',color='darkred')
			ax0.text(x_points[0], y_points[0], 'A',color='darkred',horizontalalignment='left')
			ax0.text(x_points[-1], y_points[-1], "A'",color='darkred',horizontalalignment='left')


		#ax0.axis([mesh_setup['Xmin'],mesh_setup['Xmax'],mesh_setup['Ymin'],mesh_setup['Ymax']])
		colors_on_plot=[]
		legends=[]
		for block in blocks:
			if block[0]==layer:
				for i, point in enumerate(blocks[block]['points']):
					if i==0:
						fill_x=[]
						fill_y=[]
						line=[]
					if i!=0 and (i)%4==0:
						plt.plot(line[0],line[1],line[2],line[3],'-k')
						fill_x.extend([line[0],line[2]])
						fill_y.extend([line[1],line[3]])
						line=[]
					if i%4 in [0,1,2,3]:
						line.append(point)

				if plot_center:
					ax0.plot(ELEME[block]['X'],ELEME[block]['Y'],'.k')

				ax0.fill(fill_x,fill_y,facecolor=rocktypes[blocks[block]['rocktype']], edgecolor='black',alpha=0.5)
				
				if mark_elements:
					if 'red' not in  colors_on_plot:
						legend_for_rock = mpatches.Patch(color='red', label='sinks/sources',alpha=0.75)
						colors_on_plot.append('red')
						legends.append(legend_for_rock)
					if any(corr[0] in block for corr in well_corr.values()):
						ax0.fill(fill_x,fill_y,facecolor='red', edgecolor='black',alpha=0.75)
						ax0.annotate(corr_well[block[1:6]],
									xy=(ELEME[block]['X'],ELEME[block]['Y']), xycoords='data',
									xytext=(ELEME[block]['X']+500,ELEME[block]['Y']+500),textcoords='data',fontsize=10,
									arrowprops=dict(arrowstyle="->", color="white",
									shrinkA=5, shrinkB=5,
									patchA=None, patchB=None,
									connectionstyle="bar,angle=180,fraction=-0.2"))

				if rocktypes[blocks[block]['rocktype']] not in colors_on_plot:
					legend_for_rock = mpatches.Patch(color=rocktypes[blocks[block]['rocktype']], label=blocks[block]['rocktype'],alpha=0.5)
					colors_on_plot.append(rocktypes[blocks[block]['rocktype']])
					legends.append(legend_for_rock)

		plt.subplots_adjust(right=0.8)
		plt.legend(handles=legends,title=legend, bbox_to_anchor=(1.01, 1), loc='upper left')
		plt.axis('equal')
		plt.savefig('layer_C.png',dpi=300,transparent=False,bbox_inches='tight')
		plt.show()
	else:
		sys.exit("The file %s does not exist"%(segmt_json_file))

def plot_3D_mesh():

	segmt_file='../mesh/from_amesh/segmt'

	if os.path.isfile(segmt_file):
		with open('../mesh/ELEME.json') as file:
	  		blocks_position=json.load(file)

		elements_count = {blocks:{'count':[],'points':[]} for blocks in blocks_position.keys()}

		layer_dictionary={}
		layers_info=geometry.vertical_layers()
		for i, name in enumerate(layers_info['name']):
			layer_dictionary[name]=[layers_info['top'][i],layers_info['bottom'][i]]


		with open(segmt_file,'r') as segmt_file:
			for i, line in enumerate(segmt_file):
				line_array=line.split()
				len_array=len(line_array)
				if len_array==6:
					elem2=line_array[5][5:12]
				elif len_array==7:
					elem2=line_array[5][5:12]+line_array[6]

				X1=float(line_array[0])
				Y1=float(line_array[1])
				
				X2=float(line_array[2])
				Y2=float(line_array[3])
				direction=line_array[4]
				elem1=line_array[5][0:5]
				Z=layer_dictionary[elem1[0]][0]

				if direction==1:
					elements_count[elem1]['points'].append([X1,Y1,Z])
					elements_count[elem1]['points'].append([X2,Y2,Z])
					elements_count[elem1]['count'].append(i*2)
					elements_count[elem2]['count'].append(i*2+1)
				else:
					elements_count[elem1]['points'].append([X2,Y2,Z])
					elements_count[elem1]['points'].append([X1,Y1,Z])
					if '*' in elem2:
						elements_count[elem1]['count'].append(i*2+1)
						elements_count[elem1]['count'].append(i*2)
					else:
						elements_count[elem2]['count'].append(i*2)
						elements_count[elem1]['count'].append(i*2+1)

		points=[]
		cells=[[] for i in range(len(elements_count))]

		cnt=0
		for n, elem in enumerate(elements_count):
			temp_points=list(set(map(tuple, elements_count[elem]['points'])))
			for point in temp_points:
				points.append(list(point))

				cells[n].append(cnt)
				cnt+=1

				Z2=layer_dictionary[elem[0]][1]
				point2=[point[0],point[1],Z2]
				points.append(point2)

				cells[n].append(cnt)
				cnt+=1

		celltypes = np.empty(len(elements_count), dtype=np.uint8)
		celltypes[:]=vtk.VTK_HEXAHEDRON

		"""
		for i, eleme in enumerate(elements_count):
			celltypes[i]=len(cells[i])*3/2
		"""

		cells_x = []
		for i, cell in enumerate(cells):
			cells_x.extend(cells[i])

		cells_x=np.array(cells_x)
		print(cells_x.ravel())

		grid = pv.UnstructuredGrid(cells_x, celltypes, np.array(points))
		_ = grid.plot(show_edges=True)