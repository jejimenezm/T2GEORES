from scipy.spatial import Delaunay
import numpy as np
import matplotlib.pyplot as plt

def alpha_shape(points, alpha, only_outer=True):
    """
    Compute the alpha shape (concave hull) of a set of points.
    :param points: np.array of shape (n,2) points.
    :param alpha: alpha value.
    :param only_outer: boolean value to specify if we keep only the outer border
    or also inner edges.
    :return: set of (i,j) pairs representing edges of the alpha-shape. (i,j) are
    the indices in the points array.
    """
    assert points.shape[0] > 3, "Need at least four points"

    def add_edge(edges, i, j):
        """
        Add an edge between the i-th and j-th points,
        if not in the list already
        """
        if (i, j) in edges or (j, i) in edges:
            # already added
            assert (j, i) in edges, "Can't go twice over same directed edge right?"
            if only_outer:
                # if both neighboring triangles are in shape, it's not a boundary edge
                edges.remove((j, i))
            return
        edges.add((i, j))

    tri = Delaunay(points)
    edges = set()
    # Loop over triangles:
    # ia, ib, ic = indices of corner points of the triangle
    for ia, ib, ic in tri.vertices:
        pa = points[ia]
        pb = points[ib]
        pc = points[ic]
        # Computing radius of triangle circumcircle
        # www.mathalino.com/reviewer/derivation-of-formulas/derivation-of-formula-for-radius-of-circumcircle
        a = np.sqrt((pa[0] - pb[0]) ** 2 + (pa[1] - pb[1]) ** 2)
        b = np.sqrt((pb[0] - pc[0]) ** 2 + (pb[1] - pc[1]) ** 2)
        c = np.sqrt((pc[0] - pa[0]) ** 2 + (pc[1] - pa[1]) ** 2)
        s = (a + b + c) / 2.0
        area = np.sqrt(s * (s - a) * (s - b) * (s - c))
        circum_r = a * b * c / (4.0 * area)
        if circum_r < alpha:
            add_edge(edges, ia, ib)
            add_edge(edges, ib, ic)
            add_edge(edges, ic, ia)
    return edges

def find_edges_with(i, edge_set):
    i_first = [j for (x,j) in edge_set if x==i]
    i_second = [j for (j,x) in edge_set if x==i]
    return i_first,i_second

def stitch_boundaries(edges):
    edge_set = edges.copy()
    boundary_lst = []
    while len(edge_set) > 0:
        boundary = []
        edge0 = edge_set.pop()
        boundary.append(edge0)
        last_edge = edge0
        while len(edge_set) > 0:
            i,j = last_edge
            j_first, j_second = find_edges_with(j, edge_set)
            if j_first:
                edge_set.remove((j, j_first[0]))
                edge_with_j = (j, j_first[0])
                boundary.append(edge_with_j)
                last_edge = edge_with_j
            elif j_second:
                edge_set.remove((j_second[0], j))
                edge_with_j = (j, j_second[0])  # flip edge rep
                boundary.append(edge_with_j)
                last_edge = edge_with_j

            if edge0[0] == last_edge[1]:
                break

        boundary_lst.append(boundary)
    return boundary_lst

geometry_file="Voronoi_Lithology_Grid_geometry.dat"
leapfrog_t2_file="Voronoi_Lithology_Grid.dat"

printeleme=False
layer_level=3

elements={}

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

minimin_distance=1E50
elementx=''
elementx2=''
for key in elements:
	for key_others in elements:
		delta_x=elements[key][2]-elements[key_others][2]
		delta_y=elements[key][3]-elements[key_others][3]
		r=(delta_x**2+delta_y**2)**0.5
		if r<minimin_distance and r!=0:
			minimin_distance=r
			elementx=key
			elementx2=key_others

alpha=minimin_distance

x_points=[]
y_points=[]
for key in sorted(elements):
	x_points.append(elements[key][1])
	y_points.append(elements[key][2])

points = np.vstack([x_points, y_points]).T

edges = alpha_shape(points, alpha=735, only_outer=True)

plt.figure()
plt.plot(x_points,y_points, '.')
for i, j in edges:
    plt.plot(points[[i, j], 0], points[[i, j], 1])
plt.show()

for n in stitch_boundaries(edges):
	print type(n)
	n=list(reversed(n))
	for nx in range(len(n)):
		plt.plot(points[[n[nx][0],n[nx][1]],0],points[[n[nx][0],n[nx][1]],1])
		plt.text(points[[n[nx][0],n[nx][1]],0][1],points[[n[nx][0],n[nx][1]],1][1],str(nx), color='k',fontsize=8)
plt.show()

"""
for key in sorted(elements):
	eleme_layer=key[3:5]
	string="{:5s}{:5d}{:20.2f}{:20.2f}{:20.2f}{:20.2f}\n".format(key,int(eleme_layer),elements[key][1],elements[key][2],elements[key][3],elements[key][4])
	print string

"""