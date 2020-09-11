import numpy as N
import cartopy


def cart2sph(x, y, z):
    hxy = N.hypot(x, y)
    el = N.arctan2(z, hxy)
    az = N.arctan2(y, x)
    return N.degrees(az), N.degrees(el)


# %%matplotlib inline
import matplotlib.pyplot as plt

ortho = cartopy.crs.Orthographic()
ax = plt.axes(projection=ortho)
ax.coastlines()


def points_on_sphere(n_points):
    """A nearly-uniform distribution of points on a sphere"""
    # https://scicomp.stackexchange.com/questions/29959/uniform-dots-distribution-in-a-sphere
    alpha = 4.0 * N.pi / n_points
    d = N.sqrt(alpha)
    m_nu = int(N.round(N.pi / d))
    d_nu = N.pi / m_nu
    d_phi = alpha / d_nu
    points = []
    for m in range(0, m_nu):
        nu = N.pi * (m + 0.5) / m_nu
        m_phi = int(N.round(2 * N.pi * N.sin(nu) / d_phi))
        for n in range(0, m_phi):
            phi = 2 * N.pi * n / m_phi
            xp = N.sin(nu) * N.cos(phi)
            yp = N.sin(nu) * N.sin(phi)
            zp = N.cos(nu)
            points.append(cart2sph(xp, yp, zp))
    return N.array(points)


# % (Nearly) uniform distrbuion of points on a sphere

pt = points_on_sphere(50000)
ax.plot(pt[:, 0], pt[:, 1], "o", markersize=0.2, transform=cartopy.crs.Geodetic())
ax.show()
