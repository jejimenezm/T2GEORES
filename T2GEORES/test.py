P=[[410675,  310406.25],
 [410675,  310593.75],
 [410800,  310656.25],
 [410925,  310593.75],
 [410925,  310406.25],
 [410800,  310343.75]] 
import matplotlib.pyplot as plt


for n in P:
	plt.plot(n[0],n[1],'ok')

plt.show()