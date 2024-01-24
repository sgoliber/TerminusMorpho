#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from terminus import termpicks_trace
import shapely
import numpy as np
import pandas as pd
import geopandas as gpd


# In[ ]:


def glac_vectors(glacierID,terminus_data,terminus_centerline,terminus_sidelines, start_date='1984-12-31', end_date='2022-12-31',glacierid_column='GlacierID',date_column='Date'):
    
    #If the data is not a dataframe, open it adn replace the variable with the data
    if not isinstance(terminus_data, gpd.GeoDataFrame):
        terminus_data = gpd.read_file(terminus_data)
    if not isinstance(terminus_centerline, gpd.GeoDataFrame):
        terminus_centerline = gpd.read_file(terminus_centerline)
    if not isinstance(terminus_sidelines, gpd.GeoDataFrame):
        terminus_sidelines = gpd.read_file(terminus_sidelines)
    
    #set up the terminus data
    glac = terminus_data[terminus_data[glacierid_column] == glacierID]
    
    glac = glac[glac[date_column]>start_date]
    glac = glac[glac[date_column]<end_date]
    glac=glac.sort_values(by=['Date'])
    
    glac['Datetime'] = pd.to_datetime(glac[date_column])
    
    #set up the other layers
    sideline=terminus_sidelines[terminus_sidelines[glacierid_column]==glacierID]
    center = terminus_centerline[terminus_centerline[glacierid_column]==glacierID]
    
    return glac, center, sideline


# In[ ]:


def verts(df):
    
    n_vertices=[] ###

    for i, row in df.iterrows():
        # It's better to check if multigeometry
        multi = row.geometry.type.startswith("Multi")

        if multi:
            n = 0
            # iterate over all parts of multigeometry
            for part in row.geometry:
                n += len(part.coords)
        else:
            n = len(row.geometry.coords)
        n_vertices.append(n) ###
    return n_vertices


# In[ ]:


def split_line_by_point(line, point, tolerance: float=1.0e-12):
    return shapely.ops.split(shapely.ops.snap(line, point, tolerance), point)

def sinosity(line, points,distance_delta=1000):
    
    distances = np.arange(0, line.length, distance_delta)
    points = shapely.geometry.MultiPoint([line.interpolate(distance) for distance in distances] + [line.boundary[1]])
    result = split_line_by_point(line,points,1)
    
    indv_sinuosity = []
    for piece in result:
            downval = piece.boundary[0].distance(piece.boundary[1])
            channel = piece.length
            indv_sinuosity.append(channel/downval)
            
    #sdf = gpd.GeoDataFrame(geometry=[i for i in result])
    #sdf['Sinuo'] = indv_sinuosity
    
    mean_sinuosity = (sum(indv_sinuosity)/len(indv_sinuosity))
    
    return points, mean_sinuosity


# In[ ]:


def cut_polygon_by_line(polygon, line):
    merged = shapely.ops.linemerge([polygon.boundary, line])
    borders = shapely.ops.unary_union(merged)
    polygons = shapely.ops.polygonize(borders)
    return list(polygons)

def convexhull(line, points, sideline):
    
    point_array = np.array([[p.x,p.y] for p in points])
    end_points = shapely.geometry.LineString([line.boundary[0], line.boundary[1]])
    
    #convex hull
    polygon = line.convex_hull
    clipped=cut_polygon_by_line(polygon, line)
    
    #Define side
    poly = shapely.geometry.Polygon([*list(sideline.geometry.values[0].coords), *list(end_points.coords)])
    if poly.is_valid == False:
        poly = shapely.geometry.Polygon([*list(sideline.geometry.values[0].coords), *list(end_points.coords)[::-1]])
        
    convex_hulls = []
    for segment in clipped:
        r = segment.contains(line.centroid)
        if r == True:
            ch = segment.convex_hull.centroid
            if poly.contains(ch) == True:
                convex_hulls.append((segment.area)/1000000)
            else:
                convex_hulls.append((segment.area*-1)/1000000)
    hull_area = (sum(convex_hulls))
    
    clippeddf = pd.DataFrame({'geometry':clipped})
    clippedgdf = gpd.GeoDataFrame(df, geometry = 'geometry')
    
    return hull_area, clippedgdf

