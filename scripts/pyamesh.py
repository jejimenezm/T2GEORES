import numpy as np
import re as re
import subprocess
import datetime
import matplotlib.pyplot as plt
import shutil
import os
import json
import shapefile
import time
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,
                               AutoMinorLocator)

class py2amesh:
	#Class to assign wells correlative to a specific name of a layer,
	#make sure the input file not have a name line and use de format ID, X, Y
	#The blocks coming from regular mesh are listed as bigger than 100
	def __init__(self,filename,filepath,Xmin,Xmax,Ymin,Ymax,\
		toler,layers,layer_to_plot,x_space,y_space,radius_criteria,\
		x_from_boarder,y_from_boarder,\
		x_gap_min,x_gap_max,x_gap_space,y_gap_min,y_gap_max,y_gap_space,\
		plot_names,plot_centers,z0_level,plot_all_GIS):

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
		x_regular=range(self.Xmin+self.x_from_boarder,self.Xmax+self.x_space-self.x_from_boarder,self.x_space)
		y_regular=range(self.Ymin+self.y_from_boarder,self.Ymax+self.y_space-self.y_from_boarder,self.y_space)

		x_regular_small=range(self.x_gap_min,self.x_gap_max,self.x_gap_space)
		y_regular_small=range(self.y_gap_min,self.y_gap_max,self.y_gap_space)
		self.mesh_array=[]
		for nx in x_regular:
			for ny in y_regular:
				if ((nx<self.x_gap_min) or (nx>self.x_gap_max)) or ((ny<self.y_gap_min) or (ny>self.y_gap_max)):
					self.mesh_array.append([nx,ny])

		for nxx in x_regular_small:
			cnt=0
			for nyy in y_regular_small:
				if [nxx,nyy] not in self.mesh_array:
					if cnt%2==0:
						self.mesh_array.append([nxx,nyy])
					else:
						self.mesh_array.append([nxx+self.x_gap_space/2,nyy])
					cnt+=1

		return np.array(self.mesh_array)

	def radius_select(self,x0,y0,xr,yr):
		r=((x0-xr)**2+(y0-yr)**2)**0.5
		if r<self.radius_criteria:
			boolean=1
		else:
			boolean=0
		return boolean

	def data(self):
		self.raw_data=np.loadtxt(self.filepath+self.filename,dtype={'names':('ID','X','Y','TYPE'),'formats':('S7','f4','f4','S4')},delimiter=',')
		self.IDXY={}
		regular_mesh=self.regular_mesh()
		for n in range(len(self.raw_data['ID'])):
			self.IDXY["%s"%(self.raw_data['ID'][n])]=[self.raw_data['X'][n],self.raw_data['Y'][n],self.raw_data['TYPE'][n]]
			to_delete=[]
			
			x0=self.raw_data['X'][n]
			y0=self.raw_data['Y'][n]
			
			for ngrid in range(len(regular_mesh)):
				if abs(x0-regular_mesh[ngrid][0])<self.radius_criteria or abs(y0-regular_mesh[ngrid][1])<self.radius_criteria:
					boolean=self.radius_select(x0,y0,regular_mesh[ngrid][0],regular_mesh[ngrid][1])
					if boolean==1:
						to_delete.append(ngrid)

			regular_mesh=np.delete(regular_mesh, to_delete, 0)

		for n in range(len(regular_mesh)):
			#self.IDXY["RG%s"%(n+100)]=[regular_mesh[n][0],regular_mesh[n][1],'REGUL']
			self.IDXY["RG%s"%(n)]=[regular_mesh[n][0],regular_mesh[n][1],'REGUL']

		return {'raw_data':self.raw_data,'IDXY':self.IDXY}

	def blknumber(self,x,layer_number,repeat,cnt):

		string_ele=self.color_dict[layer_number][0][int(cnt/1000)]

		if repeat==0:
			blockindex=int(re.sub(r'\D','',x))+100
			blocknumber="%s"%blockindex
		elif repeat==1:
			blocknumber=int(x)-int(cnt/1000)*1000

		blockname=string_ele+str(blocknumber)
		self.blockname=blockname
		return blockname

	def well_blk_assign(self):
		self.well_names=[]
		self.blocks_PT={}
		self.well_blocks_names={}
		self.wells_correlative={}
		data_dict=self.data()
		for n in range(self.number_of_layer):
			cnt=110
			layer_num=0

			for x in sorted(self.data()['IDXY']):

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
				
				if data_dict['IDXY'][x][2]=='WELL':
					self.blocks_PT["%s"%(blockname)]=[x,\
				                      str(data_dict['IDXY'][x][0]),\
				                      str(data_dict['IDXY'][x][1]),\
				                      data_dict['IDXY'][x][2],\
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

		welldict=self.well_blk_assign()['well_blocks_names']

		Xarray=np.array([self.Xmin,self.Xmax])
		Yarray=np.array([self.Ymin,self.Ymax])

		limit_grid=np.meshgrid(Xarray, Yarray)

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
		for n in Xarray:
			if n==Xarray[0]:
				for i in Yarray:
					string_bound="%10s%10s\n"%(n,i)
					file.write(string_bound)
			else:
				for i in Yarray[::-1]:
					string_bound="%10s%10s\n"%(n,i)
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
							
							if self.plot_names==1:
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

							if self.plot_centers==1:
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
		if os.path.isfile('../mesh/from_amesh/segmt'):
			shutil.copyfile('../mesh/from_amesh/segmt', '../mesh/to_steinar/segmt')
			ele_file_st=open('../mesh/to_steinar/eleme','w')  
			ele_file=open('../mesh/from_amesh/eleme','r')  
			data_eleme=ele_file.readlines()
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
			in_file_st.write(" %6.2d %6.2d\n"%(self.Xmin,self.Ymin))
			in_file_st.write(" %6.2d %6.2d\n"%(self.Xmin,self.Ymax))
			in_file_st.write(" %6.2d %6.2d\n"%(self.Xmax,self.Ymax))
			in_file_st.write(" %6.2d %6.2d\n\n"%(self.Xmax,self.Ymin))
			in_file_st.write("locat\n")

			cnt=0

			for ny in data_in:
				if cnt>0 and cnt<(len(data_in)-10):
					read1=ny[0:6]
					read2=ny[9:11]
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

		if os.path.isfile('../mesh/from_amesh/segmt') and os.path.isfile('../mesh/to_steinar/eleme'):
			if self.plot_all_GIS==1:
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
				data=np.genfromtxt('../mesh/to_steinar/segmt', dtype="f8,f8,f8,f8,i8,S5,S5", names=['X1','Y1','X2','Y2','index','elem1','elem2'],delimiter=[15,15,15,15,5,5,5])

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
