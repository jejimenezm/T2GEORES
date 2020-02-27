import sys
from model_conf import *
import sqlite3
import t2resfun as t2r
import pandas as pd
import matplotlib.pyplot as plt
import os
import math
import matplotlib.gridspec as gridspec


def plot_compare_one(db_path,name):
	conn=sqlite3.connect(db_path)
	c=conn.cursor()

	#Define plot

	fig= plt.figure(figsize=(12, 96), dpi=300)

	axT=fig.add_subplot(121)

	axP=fig.add_subplot(122)

	#Real data
	data_PT_real=pd.read_sql_query("SELECT well, MeasuredDepth, Pressure, Temperature FROM PT WHERE well='%s';"%name,conn)

	x_T,y_T,z_T,var_T=t2r.MD_to_TVD_one_var_array(name,data_PT_real['Temperature'].values,data_PT_real['MeasuredDepth'].values,100)

	ln1T=axT.plot(var_T,z_T,'-r',linewidth=1,label='Measured')

	x_P,y_P,z_P,var_P=t2r.MD_to_TVD_one_var_array(name,data_PT_real['Pressure'].values,data_PT_real['MeasuredDepth'].values,100)

	ln1P=axP.plot(var_P,z_P,'-b',linewidth=1,label='Measured')

	#Model

	in_file="../output/PT/txt/%s_PT.dat"%name

	if os.path.isfile(in_file):

		data=pd.read_csv(in_file)

		blk_num=data['ELEM'].values

		TVD_elem=[0 for n in range(len(blk_num))]
		TVD_elem_top=[0 for n in range(len(blk_num))]

		for n in range(len(blk_num)):
			TVD_elem[n]=float(pd.read_sql_query("SELECT middle FROM layers WHERE correlative='%s';"%data['ELEM'].values[n][0],conn)['middle'])
			TVD_elem_top[n]=float(pd.read_sql_query("SELECT top FROM layers WHERE correlative='%s';"%data['ELEM'].values[n][0],conn)['top'])

		ln2T=axT.plot(data['T'],TVD_elem,'+r',linewidth=1,label='Calculated')

		ln2P=axP.plot(data['P']/1E5,TVD_elem,'+b',linewidth=1,label='Calculated')

		ax2P = axP.twinx()

		layer_corr=[data['ELEM'].values[n][0] for n in range(len(blk_num))]

		fontsizex=4

		fontsize_layer=3

		ax2P.set_yticks(TVD_elem_top,minor=True)

		ax2P.set_yticks(TVD_elem,minor=False)

		ax2P.tick_params(axis='y',which='major',length=0)

		ax2P.yaxis.grid(True, which='minor',linestyle='--', color='grey', alpha=0.1, lw=0.5)

		ax2P.set_yticklabels(layer_corr,fontsize=fontsize_layer)

		ax2P.set_ylim(axP.get_ylim())


		ax2T = axT.twinx()

		ax2T.set_yticks(TVD_elem_top,minor=True)

		ax2T.set_yticks(TVD_elem,minor=False)
		
		ax2T.tick_params(axis='y',which='major',length=0)

		ax2T.set_yticklabels(layer_corr,fontsize=fontsize_layer)

		ax2T.yaxis.grid(True, which='minor',linestyle='--', color='grey', alpha=0.1, lw=0.5)

		ax2T.set_ylim(axT.get_ylim())

		lnsT = ln1T+ln2T

		labsT = [l.get_label() for l in lnsT]

		axT.legend(lnsT, labsT, loc='upper right', fontsize=fontsizex)

		axT.set_xlabel('Temperature [C]',fontsize=fontsizex)

		axT.xaxis.set_label_coords(0.5,1.1)

		axT.xaxis.tick_top()

		axT.set_ylabel('m.a.s.l.',fontsize = fontsizex)

		axT.tick_params(axis='both', which='major', labelsize=fontsizex,pad=1)
		

		lnsP = ln1P+ln2P

		labsP = [l.get_label() for l in lnsP]

		axP.legend(lnsP, labsP, loc='upper right', fontsize=fontsizex)
		
		axP.set_xlabel('Pressure [bar]',fontsize=fontsizex)

		axP.xaxis.set_label_coords(0.5,1.1)

		axP.xaxis.tick_top()

		axP.tick_params(axis='both', which='major', labelsize=fontsizex,pad=1)

		fig.suptitle("%s"%name, fontsize=fontsizex)


		plt.show()

		fig.savefig('../output/PT/images/PT_%s.png'%name) 

def image_save_all_plots(db_path,wells,typePT):
	#Maybe hspace, wspace, and the set_label_coords will always  need to be adjust

	widths=[2,2,2]

	heights=[int(2*(40.0/3)*len(widths)/int(math.ceil(len(wells)/3.0)))+1 for n in range(int(math.ceil(len(wells)/3.0)))]

	gs = gridspec.GridSpec(nrows=len(heights), ncols=len(widths), width_ratios=widths, height_ratios=heights,hspace=0.2, wspace=0.15)

	fig= plt.figure(figsize=(12, 96), dpi=300,constrained_layout=True)

	fig.suptitle("%s Calculated vs  %s Measured"%(typePT,typePT), fontsize=10)

	conn=sqlite3.connect(db_path)

	c=conn.cursor()
		

	cnt=0
	for name in wells:

		#Real data
		data_PT_real=pd.read_sql_query("SELECT well, MeasuredDepth, Pressure, Temperature FROM PT WHERE well='%s';"%name,conn)

		if len(data_PT_real)>0:

			x_T,y_T,z_T,var_T=t2r.MD_to_TVD_one_var_array(name,data_PT_real['Temperature'].values,data_PT_real['MeasuredDepth'].values,100)

			#Define plot

			axT= fig.add_subplot(gs[cnt])
			
			ln1T=axT.plot(var_T,z_T,'-r',linewidth=1,label='Measured')

			#Model

			in_file="../output/PT/txt/%s_PT.dat"%name

			if os.path.isfile(in_file):

				data=pd.read_csv(in_file)

				blk_num=data['ELEM'].values

				TVD_elem=[0 for n in range(len(blk_num))]
				TVD_elem_top=[0 for n in range(len(blk_num))]

				for n in range(len(blk_num)):
					TVD_elem[n]=float(pd.read_sql_query("SELECT middle FROM layers WHERE correlative='%s';"%data['ELEM'].values[n][0],conn)['middle'])
					TVD_elem_top[n]=float(pd.read_sql_query("SELECT top FROM layers WHERE correlative='%s';"%data['ELEM'].values[n][0],conn)['top'])

				ln2T=axT.plot(data[typePT],TVD_elem,'+r',linewidth=1,ms=3,label='Calculated')

				layer_corr=[data['ELEM'].values[n][0] for n in range(len(blk_num))]

				fontsizex=4

				fontsize_layer=3

				ax2T = axT.twinx()

				ax2T.set_yticks(TVD_elem_top,minor=True)

				ax2T.set_yticks(TVD_elem,minor=False)
				
				ax2T.tick_params(axis='y',which='major',length=0)

				ax2T.set_yticklabels(layer_corr,fontsize=fontsize_layer)

				ax2T.yaxis.grid(True, which='minor',linestyle='--', color='grey', alpha=0.1, lw=0.5)

				ax2T.set_ylim(axT.get_ylim())

				lnsT = ln1T+ln2T

				labsT = [l.get_label() for l in lnsT]

				axT.legend(lnsT, labsT, loc='upper right', fontsize=fontsizex)

				if typePT=='P':
					label_name='Pressure [bar]'
				elif typePT=='T':
					label_name='Temperature [C]'

				axT.set_xlabel('%s, %s'%(name,label_name),fontsize=fontsizex+2)

				axT.xaxis.set_label_coords(0.5,1.1)

				axT.yaxis.set_label_coords(-0.07,0.5)

				axT.xaxis.tick_top()

				axT.set_ylabel('m.a.s.l.',fontsize = fontsizex)

				axT.tick_params(axis='both', which='major', labelsize=fontsizex,pad=1)

				plt.draw()

				cnt+=1

	fig.savefig('../output/PT/images/T_all.png') 


name='AH-34A'
db_path='../input/model.db'

plot_compare_one(db_path,name)
typePT='T'
image_save_all_plots(db_path,wells,typePT) #typePT, could be T or P
