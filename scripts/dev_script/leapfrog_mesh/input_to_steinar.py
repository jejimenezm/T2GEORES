import numpy as np
import matplotlib.pyplot as plt

geometry_file="Voronoi_Lithology_Grid_geometry.dat"
leapfrog_t2_file="Voronoi_Lithology_Grid.dat"

printeleme=False
layer_level=4
elements={}

#Takes the elements at the selected leyer
with open(leapfrog_t2_file,'r') as f:
  for line in f.readlines():

  	if line.rstrip()=='ELEME':
  		printeleme=True
  		continue
  	elif line.rstrip()=='CONNE' or line.rstrip()=='':
  		printeleme=False

	if printeleme and line.rstrip()[0:5]!="ATM 0" and int(line.rstrip()[3:5])==layer_level:
		eleme=line.rstrip()[0:5]
		level=line.rstrip()[3:5]
		rock=line.rstrip()[15:20]
		xc=line.rstrip()[51:60]
		yc=line.rstrip()[60:70]
		zc=line.rstrip()[73:80]
		elements[eleme]=[rock,float(xc),float(yc),float(zc)]

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
		layers[int(layer)]=[layer_max,layer_middle,layer_min[-1]]


#Gives the correct thickness to all block for the elements in contact with the surface
printATM=False
printsurfa=False
with open(leapfrog_t2_file,'r') as f:
	for line in f.readlines():
		if line.rstrip()=='CONNE':
			printATM=True
			continue
		elif line.rstrip()=='ENDCY' or line.rstrip()=='':
			printATM=False

		if printATM and line.rstrip()[5:10]=="ATM 0":

			eleme=line.rstrip()[0:5]

			printsurfa=False
			with open(geometry_file,'r') as f2:
				for line2 in f2.readlines():
					if line2.rstrip()=='SURFA':
						printsurfa=True
						continue
					if printsurfa:
						topname=line2.rstrip()[0:3]
						midtopelevation=line2.rstrip()[5:-1]
						eleme_layer=eleme[3:5]

						if eleme[0:3]==topname:
							h=float(midtopelevation)-float(layers[int(eleme_layer)][2])
							try:
								elements[eleme].append(h)
							except KeyError: 
								pass

#It gives the thickness to all the elevations
for key in elements:
	try:
		if elements[key][4]:
			pass
	except IndexError:
		eleme_layer=key[3:5]
		h=float(layers[int(eleme_layer)][1])-float(layers[int(eleme_layer)][2])
		try:
			elements[key].append(h)
		except KeyError: 
			pass


#Creates a dictionary of the VERTICES

vertices_dictionary={}
printvertices=False
with open(geometry_file,'r') as f:
  for line in f.readlines():

    #It will read between the keywords GRID and CONNECTIONS
    if line.rstrip()=='VERTICES':
      printvertices=True
      continue
    elif line.rstrip()=='GRID' or line.rstrip()=="":
      printvertices=False

    if printvertices:
     	vertice=line.rstrip()[0:3]
     	vertice_x=line.rstrip()[4:13]
     	vertice_y=line.rstrip()[13:23]
     	vertices_dictionary[vertice]=[vertice_x,vertice_y]

#Creates a dictionary of elements without layer with their vertices

printgrid=False
elements_vertices_dict={}
all_vertices_list=[]
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
      	element_name=line.rstrip().replace("0","")[:-1]+str(layer_level)
      	take=False
      	if element_name in elements.keys():
	      	elements_vertices_dict[element_name]=[]
	        take=False
	        segments=[]
	        segments_names=[]
	        x=[]
	        y=[]

      else:
   		take=True

      #If it is not 6 long it will take the vertices and look for the X and Y position
      if take:
		try:
			elements_vertices_dict[element_name].append(line.rstrip())
			if line.rstrip() not in all_vertices_list:
				all_vertices_list.append(line.rstrip())
		except KeyError: 
			pass

vertice_counter={}
not_edges=[]
for key in elements_vertices_dict:
	ver_not_could=False
	for key2 in elements_vertices_dict:
		cnt=0
		for ver  in elements_vertices_dict[key]:
			try:
				if vertice_counter[ver]:
					pass
			except KeyError:
				vertice_counter[ver]=0
			for ver2 in elements_vertices_dict[key2]:
				if ver==ver2 and key!=key2:
					vertice_counter[ver]=1+vertice_counter[ver]

for key in vertice_counter:
	if vertice_counter[key]>2:
		not_edges.append(key)

edges=[]
for n in all_vertices_list:
	if n not in not_edges:
		edges.append(n)

edges_lines={}
cnt=0
for l in edges:
	for l2 in edges:
		couple=[l, l2]
		for key in elements_vertices_dict:
			vertices_list=elements_vertices_dict[key]
			for n in range(len(vertices_list)):
				if n+1==len(vertices_list):
					compare=[vertices_list[n],vertices_list[0]]
				else:
					compare=vertices_list[n:n+2]
				if couple[0]==compare[0] and couple[1]==compare[1]:
					cnt+=1
					edges_lines[cnt]=compare

connection_dict={}
cnt=0
for key in elements_vertices_dict:
	for key2 in elements_vertices_dict:
		v=0
		for ver in elements_vertices_dict[key]:
			for ver2 in elements_vertices_dict[key2]:
				if ver2==ver and key!=key2:
					if v==0:
						prev_ver=ver
						v+=1
					else:
						connection_dict[cnt]=[ver,prev_ver,key,key2]
						cnt+=1

for l in edges:
	for key in elements_vertices_dict:
		if l in elements_vertices_dict[key]:
			connection_dict[cnt]=[l,key]
			cnt+=1

file=open("to_steinar/segmt", "w")
for nv in connection_dict:
	if len(connection_dict[nv])==4:
		x1=vertices_dictionary[connection_dict[nv][0]][0]
		y1=vertices_dictionary[connection_dict[nv][0]][1]
		x2=vertices_dictionary[connection_dict[nv][1]][0]
		y2=vertices_dictionary[connection_dict[nv][1]][1]
		elementx=connection_dict[nv][2]+connection_dict[nv][3]
		string="%15.3d%15.3d%15.3d%15.3d  %1s %10s\n"%(float(x1),float(y1),float(x2),float(y2),"1",elementx)

	elif len(connection_dict[nv])==2:
		x1=vertices_dictionary[connection_dict[nv][0]][0]
		y1=vertices_dictionary[connection_dict[nv][0]][1]

		x2=elements[connection_dict[nv][1]][1]
		y2=elements[connection_dict[nv][1]][2]
		elementx="%s*%s"%(connection_dict[nv][1],connection_dict[nv][0])
		string="%15.3d%15.3d%15.3d%15.3d  %1s  %10s\n"%(float(x1),float(y1),float(x2),float(y2),"1",elementx)

	file.write(string)
file.close()


lines=[]				
for vx in edges_lines:
	lines.append([vertices_dictionary[edges_lines[vx][0]],vertices_dictionary[edges_lines[vx][1]]])

order_lines=[]
lines_copy=lines
while len(lines_copy)>0:
	drop_line=lines_copy[0]
	order_lines.append(drop_line)
	del lines_copy[0]
	x2=float(drop_line[1][0])
	y2=float(drop_line[1][1])
	for line in lines_copy:
		if x2==float(line[0][0]) and y2==float(line[0][1]):
			lines_copy.remove(line)
			lines_copy.insert(0,line)

order_lines.reverse()	

"""
for nv in range(len(order_lines)):
	x_order=[float(order_lines[nv][0][0]),float(order_lines[nv][1][0])]
	y_order=[float(order_lines[nv][0][1]),float(order_lines[nv][1][1])]

	plt.plot(x_order,y_order,'-ok')
	plt.text(x_order[0],y_order[0],nv,fontsize=14)

plt.show()
"""

file=open("to_steinar/in", "w")

file.write("bound\n")
for n in order_lines:
	string_bound="%6.2d%6.2d\n"%(float(n[0][0]),float(n[0][1]))
	file.write(string_bound)
file.write("\n")
file.write("locat\n")

for key in sorted(elements):
	eleme_layer=key[3:5]
	string="{:5s}{:4d}{:24.8E}{:24.8E}{:24.8E}{:24.8E}\n".format(key,int(eleme_layer),elements[key][1],elements[key][2],elements[key][3],elements[key][4])
	file.write(string)

file.write("     \n")
file.close()

file=open("to_steinar/eleme", "w")
file.write("eleme\n")
printeleme=False
with open(leapfrog_t2_file,'r') as f:
  for line in f.readlines():
  	if line.rstrip()=='ELEME':
  		printeleme=True
  		continue
  	elif line.rstrip()=='CONNE' or line.rstrip()=='':
  		printeleme=False

  	if printeleme:
  		if int(line.rstrip()[4])==layer_level:
  			file.write(line.rstrip()[0:30]+"\n")
file.close()

file=open("to_steinar/conne", "w")
file.write("conne\n")
printconne=False
with open(leapfrog_t2_file,'r') as f:
  for line in f.readlines():
  	if line.rstrip()=='CONNE':
  		printconne=True
  		continue
  	elif line.rstrip()=='ENDCY' or line.rstrip()=='':
  		printconne=False

  	if printconne:
  		if int(line.rstrip()[4])==layer_level and int(line.rstrip()[9])==layer_level:
			a_line=line.rstrip()

			name_conne = line.rstrip()[0:11]
  			file.write("%s"%name_conne)
			file.write("   0    0    0   ")

			per=a_line[29]
			file.write("%s"%per)
			nod1=a_line[30:40].replace('+', '')
			file.write(" %9.3E"%(float(nod1)))

			nod2=a_line[40:50].replace('+', '')
			file.write(" %9.3E"%(float(nod2)))

			nod3=a_line[50:60].replace('+', '')
			file.write(" %9.3E"%(float(nod3)))

			gravity=a_line[61:70]

			file.write("{:9.1f}".format(float(gravity)))

			file.write(" 0.0000E+00\n")
file.close()

file=open("to_steinar/rocktype", "w")
printrocktype=False
with open(leapfrog_t2_file,'r') as f:
  for line in f.readlines():
  	if line.rstrip()=='ROCKS':
  		printrocktype=True
  		continue
  	elif line.rstrip()=='PARAM' or line.rstrip()=='':
  		printrocktype=False
  	if printrocktype:
  		file.write(line.rstrip()+"\n")
file.close()