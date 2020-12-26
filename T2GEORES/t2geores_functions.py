import numpy as np
from iapws import IAPWS97
import geometry as geomtr
from model_conf import input_data
from formats import formats_t2,structure
import pandas as pd
import os
from scipy import interpolate
import sys


def patmfromelev(elev):
	"""Encuentra presion atmosferica basada en elevacion

	Returns
	-------

	float
	  Presion atmosferica en bares

	Examples
	--------
	>>> patmfromelev(750)
	"""

	p_atm=(101325*((288+(-0.0065*elev))/288)**(-9.8/(-0.0065*287)))/100000
	return p_atm

def water_level_projection(MD,P,Tmin):
	"""Proyecta el nivel de agua considerando un perfil de presion estatico cualquiera

	Parameters
	----------
	MD : array
	  Arreglo de profundidad medida
	P : array
	  Arreglo de presion
	Tmin : float
	  Temperatura minima de registro de temperatura de referencia

	Returns
	-------
	float
	  D2: profundidad de nivel de agua
	float
	  Pmin: presion en nivel hidrostatico	  

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

def incons(input_dictionary=input_data):
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

def empty_model(structure, current_path):
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

def create_structure(structure, current_path):
    if structure!=None and len(structure):
        for direc in structure:
            empty_model(structure[direc], os.path.join(current_path, direc))
    else:
    	os.makedirs(current_path)

#empty_model(structure,'../')
#create_structure(structure,'.')



