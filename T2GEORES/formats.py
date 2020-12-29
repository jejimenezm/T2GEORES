"""
The file contains several dictionaries which declare the format and default values from most of the parameters
for modeling.

formats_t2: represents the parameters from TOUGH2 base on sections. For instance, 'PARAMETERS' is a dictionary, every data
on it is formatted as following: 'PARAMETER1':[Default value,format,line section].

plot_conf_color: it gives three color for every main output parameter, the first is for real data, second for current output and final for 
previous run.

plot_conf_marker: gives the marker type and alpha value depending on the the of data in case same color is used when plotting.

structure: gives the fix structure of T2GEORES, necessary as workspace.

"""


initial_conditions={'EOS1':[
						    [100E5,'>20.13E',4,'P'],
						    [250,'>20.13E',4,'T'],
						    [1e5,'>20.13E',4,'X']]}

formats_t2={'TITLE':['TOUGH2 INPUT FILE','>80s',1],
			'PARAMETERS':
					  {'NOITE':[None,'>2s',1],
					  	'KDATA':[1,'>2s',1],
					  	'MCYC':[9999,'>4s',1],
					  	'MSEC':[None,'>4s',1],
					  	'MCYPR':[30,'>4s',1],
						'MOP1':[1,'>1s',1],
						'MOP2':[0,'>1s',1],
						'MOP3':[0,'>1s',1],
						'MOP4':[0,'>1s',1],
						'MOP5':[1,'>1s',1],
						'MOP6':[0,'>1s',1],
						'MOP7':[2,'>1s',1],
						'MOP8':[0,'>1s',1],
						'MOP9':[0,'>1s',1],
						'MOP10':[0,'>1s',1],
						'MOP11':[0,'>1s',1],
						'MOP12':[2,'>1s',1],
						'MOP13':[0,'>1s',1],
						'MOP14':[0,'>1s',1],
						'MOP15':[0,'>1s',1],
						'MOP16':[4,'>1s',1],
						'MOP17':[None,'>1s',1],
						'MOP18':[None,'>1s',1],
						'MOP19':[None,'>1s',1],
						'MOP20':[None,'>1s',1],
						'MOP21':[2,'>1s',1],
						'MOP22':[None,'>1s',1],
						'MOP23':[None,'>1s',1],			
						'MOP24':[None,'>1s',1],
						'SPACE':[None,'>10s',1],
						'TEXTP':[None,'>10.3E',1],
						'BE':[None,'>10.3E',1],
						'TSTART':[-3.14E14,'>10.3E',2],
						'TIMAX':[300,'>10.3E',2],
						'DELTEN':[3.14E7,'>10.3E',2],
						'DELTMX':[None,'>10.3E',2],
						'ELST':['AA110','>5s',2],
						'SPACE2':[None,'>5s',2],
						'GF':[9.81,'>10.3E',2],
						'REDLT':[3.5,'>10.3E',2],
						'SCALE':[None,'>10.3E',2],
						'RE1':[1e-3,'>10.3E',3],
						'RE2':[None,'>10.3E',3],
						'U':[None,'>10.3E',3],
						'WUP':[None,'>10.3E',3],
						'WNR':[None,'>10.3E',3],
						'DFAC':[None,'>10.3E',3],
						'P':[100E5,'>20.13E',4,'EOS1'],
						'T':[250,'>20.13E',4,'EOS1'],
						'X':[1e5,'>20.13E',4,'EOS1']
					  },
			'DELTEN_LIST_FORMAT':[None,'>10.3E',2.1],
			'TIMES':{
				'ITI':[None,'>5s',1],
				'ITE':[None,'>5s',1],
				'DELAF':[None,'>10.3E',1],
				'TINTER':[None,'>10.3E',1],
				'TIMES_N':[None,'>10.3E',2]
				},
			'SOLVR':{
					'MATSLV':[None,'>1d',1],
					'SPACE':[None,'>2s',1],
					'ZPROCS':[None,'>2s',1],
					'SPACE2':[None,'>3s',1],
					'OPROCS':[None,'>2s',1],
					'RITMAX':[None,'>10.3E',1],
					'CLOSUR':[None,'>10.3E',1]
					},
			'RPCAP':{
					'IRP':[None,'>5s',1],
					'SPACE':[None,'>5s',1],
					'RP1':[None,'>10.3E',1],
					'RP2':[None,'>10.3E',1],
					'RP3':[None,'>10.3E',1],
					'RP4':[None,'>10.3E',1],
					'RP5':[None,'>10.3E',1],
					'RP6':[None,'>10.3E',1],
					'RP7':[None,'>10.3E',1],
					'ICP':[None,'>5s',2],
					'SPACE2':[None,'>5s',2],
					'ICP1':[None,'>10.3E',2],
					'ICP2':[None,'>10.3E',2],
					'ICP3':[None,'>10.3E',2],
					'ICP4':[None,'>10.3E',2],
					'ICP5':[None,'>10.3E',2],
					'ICP6':[None,'>10.3E',2],
					'ICP7':[None,'>10.3E',2],					
			},
			'MULTI':{
					 'NK':[None,'>5s',1],
					 'NEQ':[None,'>5s',1],
					 'NPH':[None,'>5s',1],
					 'NB':[None,'>5s',1],
					 'NKIN':[None,'>5s',1]
					},
			'GENER':{
					 'BLOCK':[None,'>5s',1],
					 'SL':[None,'>3s',1],
					 'NS':[None,'>2s',1],
					 'NSEQ':[None,'>5s',1],
					 'NADD':[None,'>5s',1],
					 'NADS':[None,'>5s',1],
					 'LTAB':[None,'>5s',1],
					 'SPACE':[None,'>5s',1],
					 'TYPE':[None,'>4s',1],
					 'ITAB':[None,'>1s',1],
					 'GX':[None,'>10.3E',1],
					 'EX':[None,'>10.3E',1],
					 'HG':[None,'>10.3E',1]
					 }
		}


plot_conf_color={'T':['r','teal','crimson'],\
				 'P':['b','lightseagreen','teal'],\
				 'm':['g','goldenrod','royalblue'],
				 'ms':['indianred','darkcyan','slategrey'],
				 'ml':['navy','dodgerblue','peru'],
				 'h':['orangered','indigo','chocolate'],\
				 'SG':['m','gold','purple']}

plot_conf_marker={'real':['.',1],\
				  'current':["+",0.75],\
				  "previous":["^",0.75]}

structure={'calib':{'drawdown_cooling':{'images':None},
					'mh':{'images':None},
					'PT':{'images':{'layer_distribution':None}}
					},
			'input':{'cooling':None,
			         'drawdown':None,
			         'mh':None,
			         'PT':{'GIS':None,
			               'selection_PT':None},
			         'survey':None},
			'mesh':{'from_amesh':None,
			        'from_leapfrog':None,
			        'GIS':None,
			        'images':None,
			        'to_steinar':None},
			'model':{'it2':None,
			          't2':{'prev':None,
			                'sources':None},
			        },
			'output':{
					  'mh':{'images':None,
					        'txt':{'prev':None}
					        },
			          'PT':{'csv':{'prev':None},
			          		'evol':{'prev':None},
			          		'images':{'evol':None,
			          				  'layer':None,
			          				  'logging':None,
			          				  'real_layer':None},
			          		'json':{'prev':None},
			          		'txt':{'prev':None}
			          		}
			        },
			'scripts':None}
