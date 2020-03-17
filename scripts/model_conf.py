import numpy as np
import matplotlib.pyplot as plt
import pyamesh as pya
import datetime

title="Test runs"

mesh_creation=1  #If 1, it will create the mesh

#Outer field, horizontal configuration

Xmin=404000
Xmax=424000

Ymin=302000
Ymax=322000

x_from_boarder=1000
y_from_boarder=1000

x_space=1000
y_space=1000

#Main field, horizontal configuration

x_gap_min=410300
x_gap_max=417500

y_gap_min=307400
y_gap_max=313450

x_gap_space=1000
y_gap_space=1000

radius_criteria=150

#Vertical 

z0_level=600

layers={1:['A', 100],\
		2:['B', 125],\
		3:['C', 125],\
		4:['D', 100],\
		5:['E', 50],\
		6:['F', 50],\
		7:['G', 50],\
		8:['H', 50],\
		9:['I', 200],\
		10:['J', 200],\
		11:['K', 400],\
		12:['L', 400],\
		13:['M', 400],\
		14:['N', 400],\
		15:['O', 100]}

#Switches
plot_layer=0    #If 1, it will plot and generate shapefile from the layer in the variable layer_to_plot
to_steinar=1
to_GIS=0
plot_all_GIS=0
from_leapfrog=False

layer_to_plot=3

plot_names=0    #Names of the blocks
plot_centers=1  #Plot a point in on the center of the block

filepath=''
#filename='../input/well_feedzone.csv'
filename='../input/ubication.csv'
db_path='../input/model.db'

toler=0.1

"""
t2r.mesh_creation_func(filename,filepath,Xmin,Xmax,Ymin,Ymax,\
			toler,layers,layer_to_plot,x_space,y_space,\
			radius_criteria,x_from_boarder,y_from_boarder,\
			x_gap_min,x_gap_max,x_gap_space,y_gap_min,y_gap_max,\
			y_gap_space,plot_names,plot_centers,z0_level,\
			mesh_creation,plot_layer,to_steiner,to_GIS,plot_all_GIS)
"""
#t2r.empty_mesh()

slr=0.4
sgr=0.03
type_dis='corey'

ref_date= datetime.datetime(1975,01,01)

#'CH-1'
wells=['CH-7BIS','AH-7','AH-1','AH-2','AH-34A',\
        'AH-5','AH-6','AH-34B','AH-8','AH-9',\
        'CH-9A','CH-9B','AH-30','AH-31','AH-32',\
        'AH-34','AH-36','AH-4BIS','CH-7',\
        'AH-18','AH-19','CH-8','AH-13','CH-D',\
        'AH-11','AH-16','AH-17','AH-14','AH-15',\
        'AH-35D','AH-35B','AH-35C','AH-35A','AH-16A',\
        'AH-33A','AH-33B','AH-33C','CH-9','AH-27','AH-26',\
        'AH-25','AH-24','AH-23','AH-22','AH-21','AH-20',\
        'AH-29','AH-28']


type_run='natural'

#Define parameters

param=[{'empty':[1]} for i in range(1,6)]

param[0]={1:['NOITE',None,'>2s'],
			2:['KDATA',20,'>2s'],
			3:['MCYC',9999,'>4s'],
			4:['MSEC',None,'>4s'],
			5:['MCYPR',5000,'>4s'],
			6:['MOP1',1,'>1s'],
			7:['MOP2',0,'>1s'],
			8:['MOP3',0,'>1s'],
			9:['MOP4',0,'>1s'],
			10:['MOP5',1,'>1s'],
			11:['MOP6',0,'>1s'],
			12:['MOP7',2,'>1s'],
			13:['MOP8',0,'>1s'],
			14:['MOP9',0,'>1s'],
			15:['MOP10',0,'>1s'],
			16:['MOP11',0,'>1s'],
			17:['MOP12',2,'>1s'],
			18:['MOP13',0,'>1s'],
			19:['MOP14',0,'>1s'],
			20:['MOP15',0,'>1s'],
			21:['MOP16',4,'>1s'],
			22:['MOP17',None,'>1s'],
			23:['MOP18',None,'>1s'],
			24:['MOP19',None,'>1s'],
			25:['MOP20',None,'>1s'],
			26:['MOP21',2,'>1s'],
			27:['MOP22',None,'>1s'],
			28:['MOP23',None,'>1s'],			
			29:['MOP24',None,'>1s'],
			30:['TEXTP',None,'>10.3E'],
			31:['BE',None,'>10.3E']}

param[1]={1:['TSTART',-3.14E14,'>10.3E'],
		2:['TIMAX',None,'>10.3E'],
		3:['DELTEN',3.14E7,'>10.3E'],
		4:['DELTMX',None,'>10.3E'],
		5:['ELST',None,'>5s'],
		6:['X',None,'>5s'],
		7:['GF',9.81,'>10.3E'],
		8:['REDLT',3.5,'>10.3E'],
		9:['SCALE',None,'>10.3E']}

#DELTEN, UP TO 100

if param[1][3][1] is not None:
	if param[1][3][1]<0:
		param[2]={}
		param[2]={1:[1,'>10.3E'],
			  	  2:[10,'>10.3E'],
			      3:[100,'>10.3E'],
			      4:[1000,'>10.3E'],
				  5:[1100,'>10.3E'],
				  6:[1200,'>10.3E'],
				  7:[1300,'>10.3E'],
				  8:[1400,'>10.3E'],
				  9:[1500,'>10.3E']}

param[3]={1:['RE1',1e-3,'>10.3E'],
		2:['RE2',None,'>10.3E'],
		3:['U',None,'>10.3E'],
		4:['WUP',None,'>10.3E'],
		5:['WNR',None,'>10.3E'],
		6:['DFAC',None,'>10.3E']}

if param[0][10][1]==1:
	param[4]={}
	param[4]={1:['P',100E5,'>20.13E'],
			  2:['T',250,'>20.13E'],
			  3:['X',1e5,'>20.13E']}

recap={1:['IRP',3,'>5s'],
		2:['X',None,'>5s'],
		3:['RP1',0.4,'>10.3E'],
		4:['RP2',0.03,'>10.3E'],
		5:['RP3',None,'>10.3E'],
		6:['RP4',None,'>10.3E'],
		7:['RP5',None,'>10.3E'],
		8:['RP6',None,'>10.3E'],
		9:['RP7',None,'>10.3E'],
		10:['ICP',1,'>5s'],
		11:['X',None,'>5s'],
		12:['CP1',1.0E6,'>10.3E'],
		13:['CP2',0.0,'>10.3E'],
		14:['CP3',1.0,'>10.3E'],
		15:['CP4',None,'>10.3E'],
		16:['CP5',None,'>10.3E'],
		17:['CP6',None,'>10.3E'],
		18:['CP7',None,'>10.3E']}

solver={1:['MATSLV',5,'>1d'],
		2:['X',None,'>2s'],
		3:['ZPROCS','Z4','>2s'],
		4:['X',None,'>3s'],
		5:['OPROCS','O4','>2s'],
		6:['RITMAX',0.04,'>10.3E'],
		7:['CLOSUR1',1E-6,'>10.3E'],
		8:['CLOSUR2',None,'>10.3E']}

multi={1:['NK',1,'>5s'],
		2:['NEQ',2,'>5s'],
		3:['NPH',2,'>5s'],
		4:['NB',6,'>5s']}

#Define TIMES

times=[{'empty':[1]} for i in range(1,3)]

times[0]={1:['ITI',100,'>5s'],
		  2:['ITE',100,'>5s'],
		  3:['DELFAF',None,'>10.3E'],
		  4:['TINTER',None,'>10.3E']}

"""
times[1]={1:['TIS1',10,'>10.3E'],
		  2:['TIS1',100,'>10.3E'],
		  3:['TIS1',1000,'>10.3E'],
		  4:['TIS1',10000,'>10.3E'],
		  5:['TIS1',100000,'>10.3E'],
		  6:['TIS1',1000000,'>10.3E'],
		  7:['TIS1',10000000,'>10.3E'],
		  8:['TIS1',20000000,'>10.3E'],
		  9:['TIS1',30000000,'>10.3E'],
		  10:['TIS1',40000000,'>10.3E']}
"""
#Every six months
times[1]={1:['TIS1',15778800,'>10.3E'],
		2:['TIS1',31557600,'>10.3E'],
		3:['TIS1',47336400,'>10.3E'],
		4:['TIS1',63115200,'>10.3E'],
		5:['TIS1',78894000,'>10.3E'],
		6:['TIS1',94672800,'>10.3E'],
		7:['TIS1',110451600,'>10.3E'],
		8:['TIS1',126230400,'>10.3E'],
		9:['TIS1',142009200,'>10.3E'],
		10:['TIS1',157788000,'>10.3E'],
		11:['TIS1',173566800,'>10.3E'],
		12:['TIS1',189345600,'>10.3E'],
		13:['TIS1',205124400,'>10.3E'],
		14:['TIS1',220903200,'>10.3E'],
		15:['TIS1',236682000,'>10.3E'],
		16:['TIS1',252460800,'>10.3E'],
		17:['TIS1',268239600,'>10.3E'],
		18:['TIS1',284018400,'>10.3E'],
		19:['TIS1',299797200,'>10.3E'],
		20:['TIS1',315576000,'>10.3E'],
		21:['TIS1',331354800,'>10.3E'],
		22:['TIS1',347133600,'>10.3E'],
		23:['TIS1',362912400,'>10.3E'],
		24:['TIS1',378691200,'>10.3E'],
		25:['TIS1',394470000,'>10.3E'],
		26:['TIS1',410248800,'>10.3E'],
		27:['TIS1',426027600,'>10.3E'],
		28:['TIS1',441806400,'>10.3E'],
		29:['TIS1',457585200,'>10.3E'],
		30:['TIS1',473364000,'>10.3E'],
		31:['TIS1',489142800,'>10.3E'],
		32:['TIS1',504921600,'>10.3E'],
		33:['TIS1',520700400,'>10.3E'],
		34:['TIS1',536479200,'>10.3E'],
		35:['TIS1',552258000,'>10.3E'],
		36:['TIS1',568036800,'>10.3E'],
		37:['TIS1',583815600,'>10.3E'],
		38:['TIS1',599594400,'>10.3E'],
		39:['TIS1',615373200,'>10.3E'],
		40:['TIS1',631152000,'>10.3E'],
		41:['TIS1',646930800,'>10.3E'],
		42:['TIS1',662709600,'>10.3E'],
		43:['TIS1',678488400,'>10.3E'],
		44:['TIS1',694267200,'>10.3E'],
		45:['TIS1',710046000,'>10.3E'],
		46:['TIS1',725824800,'>10.3E'],
		47:['TIS1',741603600,'>10.3E'],
		48:['TIS1',757382400,'>10.3E'],
		49:['TIS1',773161200,'>10.3E'],
		50:['TIS1',788940000,'>10.3E'],
		51:['TIS1',804718800,'>10.3E'],
		52:['TIS1',820497600,'>10.3E'],
		53:['TIS1',836276400,'>10.3E'],
		54:['TIS1',852055200,'>10.3E'],
		55:['TIS1',867834000,'>10.3E'],
		56:['TIS1',883612800,'>10.3E'],
		57:['TIS1',899391600,'>10.3E'],
		58:['TIS1',915170400,'>10.3E'],
		59:['TIS1',930949200,'>10.3E'],
		60:['TIS1',946728000,'>10.3E'],
		61:['TIS1',962506800,'>10.3E'],
		62:['TIS1',978285600,'>10.3E'],
		63:['TIS1',994064400,'>10.3E'],
		64:['TIS1',1009843200,'>10.3E'],
		65:['TIS1',1025622000,'>10.3E'],
		66:['TIS1',1041400800,'>10.3E'],
		67:['TIS1',1057179600,'>10.3E'],
		68:['TIS1',1072958400,'>10.3E'],
		69:['TIS1',1088737200,'>10.3E'],
		70:['TIS1',1104516000,'>10.3E'],
		71:['TIS1',1120294800,'>10.3E'],
		72:['TIS1',1136073600,'>10.3E'],
		73:['TIS1',1151852400,'>10.3E'],
		74:['TIS1',1167631200,'>10.3E'],
		75:['TIS1',1183410000,'>10.3E'],
		76:['TIS1',1199188800,'>10.3E'],
		77:['TIS1',1214967600,'>10.3E'],
		78:['TIS1',1230746400,'>10.3E'],
		79:['TIS1',1246525200,'>10.3E'],
		80:['TIS1',1262304000,'>10.3E'],
		81:['TIS1',1278082800,'>10.3E'],
		82:['TIS1',1293861600,'>10.3E'],
		83:['TIS1',1309640400,'>10.3E'],
		84:['TIS1',1325419200,'>10.3E'],
		85:['TIS1',1341198000,'>10.3E'],
		86:['TIS1',1356976800,'>10.3E'],
		87:['TIS1',1372755600,'>10.3E'],
		88:['TIS1',1388534400,'>10.3E'],
		89:['TIS1',1404313200,'>10.3E'],
		90:['TIS1',1420092000,'>10.3E'],
		91:['TIS1',1435870800,'>10.3E'],
		92:['TIS1',1451649600,'>10.3E'],
		93:['TIS1',1467428400,'>10.3E'],
		94:['TIS1',1483207200,'>10.3E'],
		95:['TIS1',1498986000,'>10.3E'],
		96:['TIS1',1514764800,'>10.3E'],
		97:['TIS1',1530543600,'>10.3E'],
		98:['TIS1',1546322400,'>10.3E'],
		99:['TIS1',1562101200,'>10.3E'],
		100:['TIS1',1577880000,'>10.3E']}

#Define sources

geners=[{'empty':[1]} for i in range(1,50)]

geners[1]={1:['block','NA452','>5s'],
		2:['SL','GEN','>3s'],
		3:['NS',10,'>2s'],
		4:['NSEQ',None,'>5s'],
		5:['NADD',None,'>5s'],
		6:['NADS',None,'>5s'],
		7:['LTAB',None,'>5s'],
		8:['X',None,'>5s'],
		9:['TYPE','MASS','>4s'],
		10:['ITAB',None,'>1s'],
		11:['GX',0.01,'>10.3E'],
		12:['EX',1000E3,'>10.3E'],
		13:['HG',None,'>10.3E']}
