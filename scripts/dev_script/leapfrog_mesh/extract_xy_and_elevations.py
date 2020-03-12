import numpy as np


geometry_file="Voronoi_Lithology_Grid_geometry.dat"
leapfrog_t2_file="Voronoi_Lithology_Grid.dat"

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
LP_mesh=[]
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
		LP_mesh.append([xc,yc])


#Creates a dictionary of the VERTICES

printvertices=False
x_min=1E20
x_max=0

y_min=1E20
y_max=0
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

     	if vertice_x>x_max:
     		x_max=vertice_x

     	if vertice_y>y_max:
     		y_max=vertice_y

     	if vertice_x<x_min:
     		x_min=vertice_x

     	if vertice_y<y_min:
     		y_min=vertice_y



print x_max,x_min, y_min,y_max, 