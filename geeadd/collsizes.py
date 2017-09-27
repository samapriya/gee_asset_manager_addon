import ee
import subprocess
import csv
import os

##initialize earth engine
ee.Initialize()

def collsize(coll):
    collc=ee.ImageCollection(coll)
    size=collc.reduceColumns(ee.Reducer.sum(), ['system:asset_size']).get('sum').getInfo()
    if int(size)>1000000000000:
        sz=float(size)/1000000000000
        print('Total size in TB = '+format(float(sz),'.2f'))
        print('Total Number of Assets in Collection = '+str(collc.size().getInfo()))
    elif int(size)>1000000000 and int(size)<1000000000000:
        sz=float(size)/1000000000
        print('Total size in GB = '+format(float(sz),'.2f'))
        print('Total Number of Assets in Collection = '+str(collc.size().getInfo()))
    elif int(size)>1000000 and int(size)<=1000000000:
        sz=float(size)/1000000
        print('Total size in MB = '+format(float(sz),'.2f'))
        print('Total Number of Assets in Collection = '+str(collc.size().getInfo()))
    else:
        sz=float(size)/1000
        print('Total size in KB = '+format(float(sz),'.2f'))
        print('Total Number of Assets in Collection = '+str(collc.size().getInfo()))
