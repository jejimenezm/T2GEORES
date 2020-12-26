from datetime import datetime, timedelta
import numpy as np


input_data={'ref_date':datetime(1975,1,1,0,0,0),
			'z_ref':600,
			'db_path':'../input/model_month.db',
			'LAYERS':{1:['A',100],
					2:['B', 100],
					3:['C', 125],
					4:['D', 60],
					5:['E',30],
					6:['F',65],
					7:['G',40],
					8:['H',65],
					9:['I',30],
					10:['J',100],
					11:['K',50],
					12:['L',250],
					13:['M',200],
					14:['N',400],
					15:['O',400],
					16:['P',200],
					17:['Q',200],
					18:['R', 100]},
			'TITLE':'Test output TOUGH2',
			'TYPE_RUN':'production',
			'PARAMETERS':
					  {'NOITE':1,
					  	'KDATA':2,
					  	'MCYC':100,
					  	'MCYPR':30,
						'P':100,
						'T':350,
						'X':0.1,
						'DELTEN':-1,
						'DELTEN_LIST':[10,30,50,1000,10000,10000]
					  },
			'TIMES':{'TIMES_N':np.arange(datetime(1985,7,1), datetime(2015,7,1), timedelta(days=120)).astype(datetime)},
			'SOLVR':{
					'MATSLV':5,
					'ZPROCS':'Z4',
					'OPROCS':'O4',
					'RITMAX':0.04,
					'CLOSUR':1E-6,
					},
			'INCONS_PARAM':{
							'To':30,
							'GRADTZ':0.08,
							'DEPTH_TO_SURF':100,
							'DELTAZ':20
							},
			'RPCAP':{
					'IRP':3,
					'RP1':0.4,
					'RP2':0.03,
					'ICP':1,
					'ICP1':1.0E6,
					'ICP2':0.0,
					'ICP3':1.0,
			},
			'MULTI':{
					 'NK':1,
					 'NEQ':2,
					 'NPH':2,
					 'NB':6
			},
			'IT2':{
				'T_DEV':5,
				'P_DEV':10,
				'h_DEV':200,
			},
			'WELLS':['AH-1',
					'AH-2',
					'AH-3',
					'AH-4',
					'AH-4BIS',
					'AH-5',
					'AH-6',
					'AH-7',
					'AH-8',
					'AH-9',
					'AH-11',
					'AH-12',
					'AH-13',
					'AH-14',
					'AH-15',
					'AH-16',
					'AH-16A',
					'AH-17',
					'AH-18',
					'AH-19',
					'AH-20',
					'AH-21',
					'AH-22',
					'AH-23',
					'AH-24',
					'AH-25',
					'AH-26',
					'AH-27',
					'AH-28',
					'AH-29',
					'AH-30',
					'AH-31',
					'AH-32',
					'AH-33A',
					'AH-33B',
					'AH-33C',
					'AH-34',
					'AH-34A',
					'AH-34B',
					'AH-35A',
					'AH-35B',
					'AH-35C',
					'AH-35D',
					'AH-36',
					'CH-1',
					'CH-10',
					'CH-7',
					'CH-7BIS',
					'CH-8',
					'CH-9',
					'CH-9A',
					'CH-9B',
					'CH-A'],
			'MAKE_UP_WELLS':[
					'ZAH-37A',
					'ZAH-37B',
					'ZAH-38A',
					'ZAH-38B',
					'ZAH-38C',
					'ZAH-39A',
					'ZAH-39B',
					'ZAH-39C',
					'XCH-9C',
					'XCH-D1',
					'XCH-D2',
					'XCH-12A',
					'XCH-12B',
					'XCH-8A',
					'XCH-8B',
					],
			'NOT_PRODUCING_WELL':['CH-D'],
		}
#'XAH-2R'

mesh_setup={'mesh_creation':True ,
			'Xmin':404000,
			'Xmax':424000,
			'Ymin':302000,
			'Ymax':322000,
			'x_from_boarder':1000,
			'y_from_boarder':1000,
			'x_space':2000,
			'y_space':2000,
			'x_gap_min':411300,
			'x_gap_max':418500,
			'y_gap_min':304500,
			'y_gap_max':311250,
			'x_gap_space':250,
			'y_gap_space':250,
			'radius_criteria':150,
			'filename':'../input/well_feedzone_xyz.csv',
			'filepath':'',
			'toler':0.1,
			'layer_to_plot':1,
			'plot_names':False,
			'plot_centers':False,
			'plot_layer':False,
			'to_steinar':True,
			'to_GIS':False,
			'plot_all_GIS':False,
			'from_leapfrog':False,
			'line_file':'',
			'fault_distance':50,
			'with_polygon':True,
			'polygon_shape':"../input/area/polygon.shp",
			"set_inac_from_poly":False,
			'set_inac_from_inner':True,
			'angle':10,
			'rotate':True,
			'colors':{1:'red',\
					  2:'white',\
					  3:'yellow',\
					  4:'blue',\
					  5:'green',\
					  6:'purple',\
					  7:'#ff69b4',\
					  8:'darkorange',\
					  9:'cyan',\
					 10:'magenta',\
					 11:'#faebd7',\
					 12:'#2e8b57',\
					 13:'#eeefff',\
					 14:'#da70d6',\
					 15:'#ff7f50',\
					 16:'#cd853f',\
					 17:'#bc8f8f',\
					 18:'#5f9ea0',\
					 19:'#daa520'}}


geners={'QA797':{'SL':'GEN',
				 'NS':10,
                 'TYPE':'MASS',
                 'GX':37,
                 'EX':1.1E6},
		'QA763':{'SL':'GEN',
				 'NS':11,
                 'TYPE':'MASS',
                 'GX':37,
                 'EX':1.1E6},
		'QA839':{'SL':'GEN',
				 'NS':12,
                 'TYPE':'MASS',
                 'GX':37,
                 'EX':1.1E6},
 		'QA762':{'SL':'GEN',
				 'NS':13,
                 'TYPE':'MASS',
                 'GX':37,
                 'EX':1.1E6},
		'QA796':{'SL':'GEN',
				 'NS':14,
                 'TYPE':'MASS',
                 'GX':37,
                 'EX':1.1E6},
		'QA795':{'SL':'GEN',
				 'NS':15,
                 'TYPE':'MASS',
                 'GX':37,
                 'EX':1.1E6},
		'QA761':{'SL':'GEN',
				 'NS':16,
                 'TYPE':'MASS',
                 'GX':37,
                 'EX':1.1E6},
		'EA833':{'SL':'SRC',
				 'NS':81,
                 'TYPE':'DELV',
                 'GX':5.000E-11,
                 'EX':1.500E+06 ,
                 'HG':1.000E+02},
		'EA866':{'SL':'SRC',
				 'NS':82,
                 'TYPE':'DELV',
                 'GX':5.000E-11,
                 'EX':1.500E+06 ,
                 'HG':1.000E+02},
		'EA897':{'SL':'SRC',
				 'NS':83,
                 'TYPE':'DELV',
                 'GX':5.000E-11,
                 'EX':1.500E+06 ,
                 'HG':1.000E+02},
		'EA865':{'SL':'SRC',
				 'NS':84,
                 'TYPE':'DELV',
                 'GX':5.000E-11,
                 'EX':1.500E+06 ,
                 'HG':1.000E+02},
		'EA896':{'SL':'SRC',
				 'NS':85,
                 'TYPE':'DELV',
                 'GX':5.000E-11,
                 'EX':1.500E+06 ,
                 'HG':1.000E+02},
		'EA831':{'SL':'SRC',
				 'NS':86,
                 'TYPE':'DELV',
                 'GX':5.000E-11,
                 'EX':1.500E+06 ,
                 'HG':1.000E+02},
		'EA864':{'SL':'SRC',
				 'NS':87,
                 'TYPE':'DELV',
                 'GX':5.000E-11,
                 'EX':1.500E+06 ,
                 'HG':1.000E+02},
       }



#to_GIS does just one plot
#to_GIS and plot_all_GIS it plots everything

#try polygon true
#'line_file':'../input/lines.csv',

#maybe is better to take out the function to_GIS from pyamesh and run it alone


#For amesh https://askubuntu.com/questions/454253/how-to-run-32-bit-app-in-ubuntu-64-bit
#the ahuachapan model has another mesh setup