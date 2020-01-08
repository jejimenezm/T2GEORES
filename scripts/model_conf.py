import numpy as np
import matplotlib.pyplot as plt
import pyamesh as pya
import t2resfun as t2r

mesh_creation=1  #If 1, it will create the mesh

#Outer field, horizontal configuration

Xmin=404000
Xmax=424000

Ymin=302000
Ymax=322000

x_from_boarder=1000
y_from_boarder=1000

x_space=1000
y_space=1000

#Main field, horizontal configuration

x_gap_min=410300
x_gap_max=417500

y_gap_min=307400
y_gap_max=313450

x_gap_space=1000
y_gap_space=1000

radius_criteria=150

#Vertical 

z0_level=600

layers={1:['A', 100],\
		2:['B', 125],\
		3:['C', 125],\
		4:['D', 100],\
		5:['E', 50],\
		6:['F', 50],\
		7:['G', 50],\
		8:['H', 50],\
		9:['I', 200],\
		10:['J', 200],\
		11:['K', 400],\
		12:['L', 400],\
		13:['M', 400],\
		14:['N', 400],\
		15:['O', 100]}

#Switches
plot_layer=0    #If 1, it will plot and generate shapefile from the layer in the variable layer_to_plot
to_steiner=1
to_GIS=0
plot_all_GIS=0

layer_to_plot=3

plot_names=0    #Names of the blocks
plot_centers=1  #Plot a point in on the center of the block

filepath=''
filename='../input/well_feedzone.csv'

toler=0.1

"""
t2r.mesh_creation_func(filename,filepath,Xmin,Xmax,Ymin,Ymax,\
			toler,layers,layer_to_plot,x_space,y_space,\
			radius_criteria,x_from_boarder,y_from_boarder,\
			x_gap_min,x_gap_max,x_gap_space,y_gap_min,y_gap_max,\
			y_gap_space,plot_names,plot_centers,z0_level,\
			mesh_creation,plot_layer,to_steiner,to_GIS,plot_all_GIS)
"""
#t2r.empty_mesh()

slr=0.4
sgr=0.03
type_dis='corey'

#t2r.permeability_plot(type_dis,slr,sgr)

#t2r.plot_vertical_layer_distribution(layers,z0_level)

ref_date=19750101