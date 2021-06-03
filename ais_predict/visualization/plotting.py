import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as ctx
import ais_predict.datasets.bigquery as bq
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
import matplotlib.transforms as transforms

def plot(df: gpd.GeoDataFrame, *args, **kwargs):
    """ Plot geopandas dataframe
    
    This functions is intended as a unified plotting function. A map is by default added as a background.
    """
    ax = df.plot(*args, **kwargs)
    ctx.add_basemap(ax, crs=df.crs)
    return ax




def confidence_ellipse(x, y, P, ax, std=2, facecolor='none', **kwargs):
    """
    Create a plot of the covariance confidence ellipse of *x* and *y*.

    Parameters
    ----------
    x, y : array-like, shape (n, )
        Input data.

    ax : matplotlib.axes.Axes
        The axes object to draw the ellipse into.

    n_std : float
        The number of standard deviations to determine the ellipse's radiuses.

    **kwargs
        Forwarded to `~matplotlib.patches.Ellipse`

    Returns
    -------
    matplotlib.patches.Ellipse
    """
    if x.size != y.size:
        raise ValueError("x and y must be the same size")

    
    pearson = P[:, 0, 1]/np.sqrt(P[:, 0, 0] * P[:, 1, 1])
    # Using a special case to obtain the eigenvalues of this
    # two-dimensionl dataset.
    width = np.sqrt(1 + pearson) * 2
    height = np.sqrt(1 - pearson) * 2

        # Calculating the stdandard deviation of x from
    # the squareroot of the variance and multiplying
    # with the given number of standard deviations.
    scale_x = np.sqrt(P[:, 0, 0]) * std
    mean_x = x

    # calculating the stdandard deviation of y ...
    scale_y = np.sqrt(P[:, 1, 1]) * std
    mean_y = y

    for i in range(P.shape[0]):
        ellipse = Ellipse((0, 0), width=width[i], height=height[i],
                        facecolor=facecolor, **kwargs)

        transf = transforms.Affine2D() \
            .rotate_deg(45) \
            .scale(scale_x[i], scale_y[i]) \
            .translate(mean_x[i], mean_y[i])

        ellipse.set_transform(transf + ax.transData)
        ax.add_patch(ellipse)
    return ax

def limits(*args):
    args = [a.reshape((-1, 2)) for a in args]
    temp = np.concatenate(args)
    min = np.min(temp, axis=0)
    max = np.max(temp, axis=0)
    return tuple(zip(min, max))