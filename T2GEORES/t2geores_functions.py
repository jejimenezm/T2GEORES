import numpy as np
from iapws import IAPWS97
import geometry as geomtr
from formats import formats_t2,structure
import pandas as pd
import os
from scipy import interpolate
import sys


def patmfromelev(elev):
	"""It fines the atmospheric pressure base on an approximate formula
	
	Parameters
	----------
	elev
	  masl where the pressure is needed

	Returns
	-------
	float
	  Atmospheric pressure in bar

	Examples
	--------
	>>> patmfromelev(750)
	"""

	p_atm=(101325*((288+(-0.0065*elev))/288)**(-9.8/(-0.0065*287)))/100000
	return p_atm

def water_level_projection(MD,P,Tmin):
	"""It projects the water level based on a pressure log

	Parameters
	----------
	MD : array
	  Measure depth array
	P : array
	  Pressure array
	Tmin : float
	  Minimun temperature allowed

	Returns
	-------
	float
	  D2: water leverl projection
	float
	  Pmin: pressure at water level  

	Examples
	--------
	>>> water_level_projection(MD,P,120)
	"""

	#Creation of array with pressure
	P_array=np.linspace(min(P),max(P),4)
	P0=P_array[1]
	P1=P_array[2]

	#Pressure vs MD function
	MDfunc=interpolate.interp1d(P,MD)
	MD0=MDfunc(P0)
	MD1=MDfunc(P1)

	#water_level_assuming saturation temperature at surface
	delta_MD=MD0-MD1
	delta_P=P0-P1
	m=delta_MD/delta_P
	b=MD0-m*P0

	Pmin=IAPWS97(T=(Tmin+273.15),x=0).P*10

	D2=m*Pmin+b

	return D2,Pmin

def initial_conditions(input_dictionary):
	"""Generates the tempearture and pressure initial conditions assuming boiling from top to bottom layer

	Parameters
	----------
	input_dictionary : dictionary
	  Contains the infomation of the layer under the keyword 'LAYER' and 'z_ref'. Also it contains the keyword 'INCONS_PARAM' with the specified initial conditions, i.e.:'INCONS_PARAM':{'To':30,'GRADTZ':0.08,'DEPTH_TO_SURF':100,'DELTAZ':20}

	Returns
	-------
	list
	  T: initial list of temperature
	list
	  P: initial list of pressure
	list
	  depth: range of depth coming from layers
	"""

	layers_info=geomtr.vertical_layers(input_dictionary)
	
	depths=np.arange(min(layers_info['bottom']),max(layers_info['top']),input_dictionary['INCONS_PARAM']['DELTAZ'])

	Pi=1 #[bar]
	To=input_dictionary['INCONS_PARAM']['To']
	depth=0
	T=[]
	P=[]
	for cnt, TVD in enumerate(depths[::-1]):
		if cnt==0:
			z_ref=max(layers_info['top'])+input_dictionary['INCONS_PARAM']['DEPTH_TO_SURF']
		depth=z_ref-TVD
		Ti=input_dictionary['INCONS_PARAM']['GRADTZ']*depth+To
		rho=IAPWS97(T=(Ti+273.15),x=0).rho
		P_colum=rho*input_dictionary['INCONS_PARAM']['DELTAZ']*formats_t2['PARAMETERS']['GF'][0]
		Pi+=P_colum/1E5
		T.append(Ti)
		P.append(Pi)

	return T, P, depths[::-1]

def incons(input_dictionary):
	"""It returns the coordinates X,Y and Z at a desired depth.

	Parameters
	----------
	Parameters
	----------
	input_dictionary : dictionary
	  Contains the infomation of the layer under the keyword 'LAYER' and 'z_ref'. Also it contains the keyword 'INCONS_PARAM' with the specified initial conditions, i.e.:'INCONS_PARAM':{'To':30,'GRADTZ':0.08,'DEPTH_TO_SURF':100,'DELTAZ':20}

	Returns
	-------
	file
	  INCON : on model/t2/sources

	Attention
	---------
	It requires an updated ELEME.json

	Note
	----
	Boiling conditions are assumed

	Examples
	--------
	>>> incons(input_dictionary)
	"""
	input_file='../mesh/ELEME.json'
	T,P,depth=initial_conditions(input_dictionary)
	print(T,P,depth)
	Tfunc=interpolate.interp1d(depth,T)
	Pfunc=interpolate.interp1d(depth,P)
	output_file='../model/t2/sources/INCON'
	string=""
	if os.path.isfile(input_file):
		eleme_df = pd.read_json(input_file).T
		for index, row in eleme_df.iterrows():
			zi=row['Z']
			Ti=Tfunc(zi)
			Pi=Pfunc(zi)*1E5
			string+="%5s%35s\n"%(index,' ')
			string+=" %19.13E %19.13E\n"%(Pi,Ti)
		file=open(output_file,'w')
		file.write(string)
		file.close()
	else:
		sys.exit("The file %s or directory do not exist"%input_file)

def empty_model(structure=structure, current_path='../'):
	"""It erases all the file on the  T2GEORES structure except the input and scripts folders

	Parameters
	----------
	structure : dictionary
	  It is an internal structure dictionary defined on formats.py	
	current_path : str
	  It specifies the top folder of the structure, if the function is executed from scripts current_path is '../'

	Attention
	---------
	It will erase all the output data, mesh and images on the model.


	Examples
	--------
	>>> empty_model(current_path='../')
	"""
	if structure!=None and len(structure):
		for direc in structure:
			empty_model(structure[direc], os.path.join(current_path, direc))
	else:
		for file in os.listdir(current_path):
			if not any(x in current_path for x in ['input','scripts']):
				try:
					os.remove(os.path.join(current_path,file))
				except IsADirectoryError:
					continue

def create_structure(current_path='.',structure=structure):
	"""It creates the necessary structure for T2GEORES to work

	Parameters
	----------
	structure : dictionary
	  It is an internal structure dictionary defined on formats.py	
	current_path : str
	  It specifies the path where the structure will be constructed

	Note
	----
	A good practice is to create a folder for the whole model

	Examples
	--------
	>>> create_structure(current_path='.')
	"""
	if structure!=None and len(structure):
		for direc in structure:
			empty_model(structure[direc], os.path.join(current_path, direc))
	else:
		os.makedirs(current_path)