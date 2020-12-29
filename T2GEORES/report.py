import sys
import sqlite3
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import os
import math
import matplotlib.gridspec as gridspec
from scipy.interpolate import griddata
import json
from matplotlib.backends.backend_pdf import PdfPages
import datetime
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import matplotlib.tri as mtri
import matplotlib.dates as mdates
import subprocess
from scipy import interpolate
from iapws import IAPWS97
import writer as t2w
from formats import formats_t2
import geometry as geomtr
from formats import plot_conf_color,plot_conf_marker

#It is a must to change the way a json is loaded

def plot_compare_one(well,savefig,data_PT_real, no_real_data, data, TVD_elem, TVD_elem_top,axT,axP,PT_real_dictionary,layer_bottom,limit_layer,input_dictionary,label=None,def_colors=True):
	"""Genera una area con dos graficas, en una se muestra la grafica de temperatura real y la temperatura calculada vs la profundidad real, en la otra la presion real y la calculada vs la profundidad real.

	Parameters
	----------
	input_dictionary : dictionary
	  A dictionary containing the reference level under the keyword 'z_ref'
	db_path : str
	  Direccion de base de datos sqlite, tomado de model_conf
	well : str
	  Name of selected well
	savefig : bool
	  If true the plot is saved on ../output/PT/images/logging/
	data_PT_real : str
	  Direccion de archivo de entrada


	Returns
	-------
	image
		PT_{well}.png: archivo con direccion ../output/PT/images/logging


	Note
	----
	La temperatura rel es tomada de la base de datos

	Examples
	--------
	>>> plot_compare_one(db_path,='AH-34',"../output/PT/txt",savefig=True)
	"""

	fontsize_plot=8
	fontsize_layer=6

	z_ref=input_dictionary['z_ref']

	#Define plot

	if not no_real_data:

		#Plotting real data

		ln1T=axT.plot(PT_real_dictionary['var_T'],PT_real_dictionary['z_T'],marker=plot_conf_marker['real'][0],linewidth=1,ms=1,label='Measured')

		ln1P=axP.plot(PT_real_dictionary['var_P'],PT_real_dictionary['z_P'],marker=plot_conf_marker['real'][0],linewidth=1,ms=1,label='Measured')

		lnsT = ln1T

		lnsP = ln1P

	#Plotting the calculated data

	ln2T=axT.plot(data['T'],TVD_elem,linestyle='None',marker=plot_conf_marker['current'][0],label='Calculated %s'%label)

	ln2P=axP.plot(data['P']/1E5,TVD_elem,linestyle='None',marker=plot_conf_marker['current'][0],label='Calculated %s'%label)

	if def_colors:
		color_real_T=plot_conf_color['T'][0]
		color_real_P=plot_conf_color['P'][0]

		ln1T.set_color(color_real_T)
		ln2T.set_color(color_real_T)

		ln1P.set_color(color_real_P)
		ln2P.set_color(color_real_P)

	axT.set_ylim([layer_bottom[limit_layer],z_ref])

	axP.set_ylim([layer_bottom[limit_layer],z_ref])

	#Preparing the layer axis side for pressure

	ax2P = axP.twinx()

	ax2P.set_yticks(TVD_elem_top,minor=True)

	ax2P.set_yticks(TVD_elem,minor=False)

	ax2P.tick_params(axis='y',which='major',length=0)

	ax2P.yaxis.grid(True, which='minor',linestyle='--', color='grey', alpha=0.1, lw=0.5)

	ax2P.set_yticklabels(data['correlative'],fontsize=fontsize_layer)

	ax2P.set_ylim(axP.get_ylim())

	#Preparing the layer axis side for temperature

	ax2T = axT.twinx()

	ax2T.set_yticks(TVD_elem_top,minor=True)

	ax2T.set_yticks(TVD_elem,minor=False)
	
	ax2T.tick_params(axis='y',which='major',length=0)

	ax2T.set_yticklabels(data['correlative'],fontsize=fontsize_layer)

	ax2T.yaxis.grid(True, which='minor',linestyle='--', color='grey', alpha=0.1, lw=0.5)

	ax2T.set_ylim(axT.get_ylim())

	#Preparing the legends on temperature side
	if no_real_data:
		lnsT=ln2T
	else:
		lnsT+=ln2T

	labsT = [l.get_label() for l in lnsT]

	#axT.legend(lnsT, labsT, loc='upper right', fontsize=fontsize_plot)

	axT.legend(loc='upper right',fontsize=fontsize_plot)

	axT.set_xlabel('Temperature [$^\circ$C]',fontsize=fontsize_plot)

	axT.xaxis.set_label_coords(0.5,1.05)

	axT.xaxis.tick_top()

	axT.set_ylabel('m.a.s.l.',fontsize = fontsize_plot)

	axT.tick_params(axis='both', which='major', labelsize=fontsize_plot,pad=1)

	#Preparing the legends on pressure side
	if no_real_data:
		lnsP=ln2P
	else:
		lnsP+=ln2P

	labsP = [l.get_label() for l in lnsP]

	#axP.legend(lnsP, labsP, loc='upper right', fontsize=fontsize_plot)
	
	axP.legend(loc='upper right', fontsize=fontsize_plot)

	axP.set_xlabel('Pressure [bar]',fontsize=fontsize_plot)

	axP.xaxis.set_label_coords(0.5,1.05)

	axP.xaxis.tick_top()

	axP.tick_params(axis='both', which='major', labelsize=fontsize_plot,pad=1)

	#Title for both plots

	#plt.subplots_adjust(top=0.92)

	if savefig:
		fig.savefig('../output/PT/images/logging/PT_%s.png'%well)