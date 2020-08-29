import numpy as N
import cartopy

# %%matplotlib inline
import matplotlib.pyplot as plt

ax = plt.axes(projection=cartopy.crs.Orthographic())
ax.coastlines()
plt.show()
