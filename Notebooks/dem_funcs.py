#!/usr/bin/env python
# coding: utf-8

# In[3]:


import rasterio
from rasterio.warp import reproject, Resampling, calculate_default_transform
from shapely.ops import nearest_points
from shapely.geometry import Point, LineString, Polygon
import numpy as np


# In[4]:


def reproj_match(infile, match, outfile):
    """Reproject a file to match the shape and projection of existing raster. 
    
    Parameters
    ----------
    infile : (string) path to input file to reproject
    match : (string) path to raster with desired shape and projection 
    outfile : (string) path to output file tif
    """
    # open input
    with rasterio.open(infile) as src:
        src_transform = src.transform
        
        # open input to match
        with rasterio.open(match) as match:
            dst_crs = match.crs
            
            # calculate the output transform matrix
            dst_transform, dst_width, dst_height = calculate_default_transform(
                src.crs,     # input CRS
                dst_crs,     # output CRS
                match.width,   # input width
                match.height,  # input height 
                *match.bounds,  # unpacks input outer boundaries (left, bottom, right, top)
            )

        # set properties for output
        dst_kwargs = src.meta.copy()
        dst_kwargs.update({"crs": dst_crs,
                           "transform": dst_transform,
                           "width": dst_width,
                           "height": dst_height,
                           "nodata": 0})
        print("Coregistered to shape:", dst_height,dst_width,'\n Affine',dst_transform)
        # open output
        with rasterio.open(outfile, "w", **dst_kwargs) as dst:
            # iterate through bands and write using reproject function
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=dst_transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.nearest)
                
def near(centroid,centerline_points):
    #INPUT: point, centerline with interpolted points 
    #OUTPUT
    """Reproject a file to match the shape and projection of existing raster. 
    
    Parameters
    ----------
    infile : (shapely points) points, centerline with interpolted points 
    outfile : (int) value of index where the point is closest to the location of the centerline
    """

    unary_union = centerline_points.unary_union
    nearest = centerline_points['geometry']== nearest_points(centroid,unary_union)[1]
    nearest_np = nearest.to_numpy()
    value = np.where(nearest_np == True)[0][0]

    return value


# In[ ]:




