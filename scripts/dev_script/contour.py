import matplotlib.pyplot as plt
import matplotlib.tri as tri
import numpy as np
import pandas as pd
from scipy.interpolate import griddata


data = pd.read_csv("data.csv",header=None,dtype= {'a': "float64", 'b': "float64", 'c':"float64" }) 
masl=1

lev=[-5,0,5,10,15,20,25,30,35]

x=[]
y=[]
values=[]
for n in range(len(data)):
	if data[2][n]==masl:
		x.append(data[0][n])
		y.append(data[1][n])
		values.append(data[3][n])


fig, (ax1,ax2,ax3,ax4) = plt.subplots(nrows=4)

ngridx=1000
ngridy=1000
xi = np.linspace(min(x), max(x), ngridx)
yi = np.linspace(min(y), max(y), ngridy)

# -----------------------
# Interpolation on a grid
# -----------------------
# A contour plot of irregularly spaced data coordinates
# via interpolation on a grid.

triang = tri.Triangulation(x, y)
interpolator = tri.LinearTriInterpolator(triang, values)
Xi, Yi = np.meshgrid(xi, yi)
zi = interpolator(Xi, Yi)


ax1.contour(xi, yi, zi, linewidths=0.5, colors='k',levels=lev)
cntr1 = ax1.contourf(xi, yi, zi, cmap="RdBu_r",levels=lev)
fig.colorbar(cntr1, ax=ax1)
ax1.plot(x,y,'ok')

# ----------
# Tricontour
# ----------
# Directly supply the unordered, irregularly spaced coordinates
# to tricontour.

ax2.tricontour(x, y, values, linewidths=0.5, colors='k',extent=[min(x),max(x),min(y),max(y)],\
	extend=['neither'],linestyles='--',levels=lev)
cntr2 = ax2.tricontourf(x, y, values,levels=lev, cmap="jet")
fig.colorbar(cntr2, ax=ax2)
ax2.plot(x,y,'ok')


# ----------
# Griddata
# ----------

#Cubic
zi = griddata((x, y), values, (xi[None,:], yi[:,None]), method='cubic')
ax3.contour(xi,yi,zi,15,linewidths=0.5,colors='k',levels=lev)
cntr3 = ax3.contourf(xi,yi,zi,15,cmap="jet",levels=lev)
fig.colorbar(cntr3,ax=ax3)
ax3.plot(x,y,'ok')


#Cubic

zi = griddata((x, y), values, (xi[None,:], yi[:,None]), method='linear')
ax4.contour(xi,yi,zi,15,linewidths=0.5,colors='k',levels=lev)
cntr4 = ax4.contourf(xi,yi,zi,15,cmap="jet",levels=lev)
fig.colorbar(cntr3,ax=ax4)
ax4.plot(x,y,'ok')

plt.show()