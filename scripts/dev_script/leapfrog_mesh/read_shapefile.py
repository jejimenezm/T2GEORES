import shapefile
import os

leapfrog_t2_file="Voronoi_Lithology_Grid.dat"

shapefiles=[]
for root, dirs, files in os.walk("."):
    for filename in files:
    	if ".shp" in filename:
        	shapefiles.append(filename)

element_rock={}
for v in shapefiles:
	shape = shapefile.Reader(v)
	records = shape.records()
	for v in records:
		eleme=" "+v[0].encode("utf-8")
		rock=v[1].encode("utf-8")
		element_rock[eleme]=rock

print element_rock

file=open("t2", "w")
changerock=False

with open(leapfrog_t2_file,'r') as frock:
	for linerock in frock.readlines():
		if linerock.rstrip()=='ELEME':
		  changerock=True
		  file.write(linerock.rstrip()+"\n")
		  continue
		elif linerock.rstrip()=='CONNE' or linerock.rstrip()=="":
		    changerock=False

		if changerock:
			try:
				line0=linerock.rstrip()[0:15]
				element=linerock.rstrip()[0:5]
				print element
				rock=element_rock[element]

				line1=linerock.rstrip()[20:-1]
				file.write(line0+rock+line1+"\n")
			except KeyError:
				file.write(linerock.rstrip()+"\n")
		else:
			file.write(linerock.rstrip()+"\n")

file.close()