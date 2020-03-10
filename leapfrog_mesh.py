import matplotlib.pyplot as plt
import matplotlib.tri as tri
import numpy as np
import pandas as pd
from scipy.interpolate import griddata
from io import StringIO




geometry_file="Voronoi_Lithology_Grid_geometry.dat"
leapfrog_t2_file="Voronoi_Lithology_Grid.dat"


layer=4

colors={'rt  1':"b",
'rt  2':"g",
'rt  3':"coral",
'rt  4':"c",
'rt  5':"m",
'rt  6':"y",
'rt  7':"royalblue",
'rt  8':"w",
'rt  9':"darkcyan",
'rt 10':"violet",
'rt 11':"gold"}

printgrid=False
printgridxy=False
printrock=False
element_name=[]
geo_in={}

fig, (ax1)= plt.subplots(nrows=1)
first=True
with open(geometry_file,'r') as f:
  for line in f.readlines():

    #It will read between the keywords GRID and CONNECTIONS
    if line.rstrip()=='GRID':
      printgrid=True
      continue
    elif line.rstrip()=='CONNECTIONS':
      printgrid=False

    #If the line is between GRID and CONNECTIONS it will make the following
    if printgrid:
      #If the line is 6 long it means is a block name, but before CONNECTIONS
      #there is a space, it must plot the last element considering there will be a space
      if len(line.rstrip())==6 or line.rstrip()=="":
        take=False
        #After finishing the run for an element x,y and rock still from the previous element, so they can be plot
        if not first:
          c = [x,y]
          centroide = (sum(c[0])/len(c[0]),sum(c[1])/len(c[1]))
          geo_in[element_name[-1]]=[xc,yc]
          x.append(x[0])
          y.append(y[0])
          ax1.plot(x,y,'-ok',ms=1,lw=1)
          ax1.plot(centroide[0],centroide[1],'or',ms=2) #From calculation
          ax1.plot(float(xc),float(yc),'ok',ms=4) #From t2file
          ax1.fill(x,y,colors[rock])

          if line.rstrip()=="":
            continue
        first=False
        segments=[]
        segments_names=[]
        x=[]
        y=[] 
        element_name.append(line.rstrip().replace("0",""))
        
        #From the t2file it reads the rocktype on the specify layer
        with open(leapfrog_t2_file,'r') as frock:
          for linerock in frock.readlines():
            if linerock.rstrip()=='ELEME':
              printrock=True
              continue
            elif linerock.rstrip()=='CONNE' or line.rstrip()=="":
			    		printrock=False

            if printrock:
              if linerock.rstrip()[0:5]==line.rstrip().replace("0","")[:-1]+str(layer):
                rock=linerock.rstrip()[15:20]
                xc=linerock.rstrip()[51:60]
                yc=linerock.rstrip()[60:70]
      else:
   			take=True

      #If it is not 6 long it will take the vertices and look for the X and Y position
      if take:
        segments_names.append(line.rstrip())
        with open(geometry_file,'r') as fxy:
          for linexy in fxy.readlines():
            if linexy.rstrip()=='VERTICES':
              printgridxy=True
              continue
            elif linexy.rstrip()=='GRID' or linexy.rstrip()=="":
              printgridxy=False

            if printgridxy:
  						if (linexy.rstrip()[0:3].replace(" ",""))==line.rstrip().replace(" ",""):
  							x.append(float(linexy.rstrip()[3:13]))
  							y.append(float(linexy.rstrip()[13:24]))






plt.show()