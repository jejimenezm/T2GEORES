import shapefile
import numpy as  np

geometry_file="Voronoi_Lithology_Grid_geometry.dat"
leapfrog_t2_file="Voronoi_Lithology_Grid.dat"

layer=2

printgrid=False
printgridxy=False
printrock=False
element_name=[]
geo_in={}

first=True

w=shapefile.Writer('mesh_layer_%s'%layer)
w.field('BLOCK_NAME', 'C', size=5)
w.field('ROCKTYPE', 'C', size=5)
w.field('VOLUMEN', 'F', decimal=10)

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
        if not first and xct:
          c = [x,y]
          centroide = (sum(c[0])/len(c[0]),sum(c[1])/len(c[1]))
          geo_in[element_name[-1]]=[xc,yc]
          x.append(x[0])
          y.append(y[0])
          points=[]
          for vk in range(len(x)):
          	points.append([x[vk],y[vk]])
          w.poly([points])
          w.record(element_name[-1],rock,volumen)

          if line.rstrip()=="":
            continue
        first=False
        segments=[]
        segments_names=[]
        x=[]
        y=[] 
        element_name.append(line.rstrip().replace("0","")[:-1]+str(layer))
        
        #From the t2file it reads the rocktype on the specify layer
        xct=False
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
                volumen=linerock.rstrip()[20:30]
                xc=linerock.rstrip()[51:60]
                yc=linerock.rstrip()[60:70]
                xct=True
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

            if printgridxy and xct:
  						if (linexy.rstrip()[0:3].replace(" ",""))==line.rstrip().replace(" ",""):
  							x.append(float(linexy.rstrip()[3:13]))
  							y.append(float(linexy.rstrip()[13:24]))

w.close()