import ee
import subprocess
import csv
import os

##initialize earth engine
ee.Initialize()

def lst(location, typ, items=None,output=None):
    if items > 0 and typ =='print':
        b=subprocess.check_output("earthengine ls "+location+" --max_items "+str(items)+" -l -r",shell=True)
        try:
            for item in b.split('\n'):
                a=item.replace("[","").replace("]","").split()
                header=a[0]
                tail=a[1]
                if header=="ImageCollection":
                    collc=ee.ImageCollection(tail)
                    ast=collc.size().getInfo()
                    size=collc.reduceColumns(ee.Reducer.sum(), ['system:asset_size']).get('sum').getInfo()
                    sz=float(size)/1000000
                    print("Image Collection "+str(tail)+" has "+str(ast)+" images a total of "+format(sz,'.2f')+" MB")
                elif header=="Image":
                    collc=ee.Image(tail)
                    size=collc.get('system:asset_size').getInfo()
                    sz=float(size)/1000000
                    print("Image "+str(tail)+" is "+format(sz,'.2f')+" MB")
                elif header=="Table":
                    collc=ee.FeatureCollection(tail)
                    size=collc.get('system:asset_size').getInfo()
                    sz=float(size)/1000000
                    print("Table "+str(tail)+" is "+format(sz,'.2f')+" MB")
                elif header=="Folder": ##Folders are not added to the list but are print
                    ast=int(b.count(tail))-1
                    print("Folder "+str(tail) +" has "+format(sz,'.2f')+" assets")
        except Exception:
            return "worked"
    elif items is None and typ =='print':
        b=subprocess.check_output("earthengine ls "+location+" -l -r",shell=True)
        try:
            for item in b.split('\n'):
                a=item.replace("[","").replace("]","").split()
                header=a[0]
                tail=a[1]
                if header=="ImageCollection":
                    collc=ee.ImageCollection(tail)
                    ast=collc.size().getInfo()
                    size=collc.reduceColumns(ee.Reducer.sum(), ['system:asset_size']).get('sum').getInfo()
                    sz=float(size)/1000000
                    print("Image Collection "+str(tail)+" has "+str(ast)+" images a total of "+format(sz,'.2f')+" MB")
                elif header=="Image":
                    collc=ee.Image(tail)
                    size=collc.get('system:asset_size').getInfo()
                    sz=float(size)/1000000
                    print("Image "+str(tail)+" is "+format(sz,'.2f')+" MB")
                elif header=="Table":
                    collc=ee.FeatureCollection(tail)
                    size=collc.get('system:asset_size').getInfo()
                    sz=float(size)/1000000
                    print("Table "+str(tail)+" is "+format(sz,'.2f')+" MB")
                elif header=="Folder": ##Folders are not added to the list but are print
                    ast=int(b.count(tail))-1
                    print("Folder "+str(tail) +" has "+format(sz,'.2f')+" assets")
        except Exception:
            return "worked"
    elif items is None and typ =='report':
        with open(output,"wb") as csvfile:
            writer=csv.DictWriter(csvfile,fieldnames=["type", "path","No of Assets","size","unit"], delimiter=',')
            writer.writeheader()
            b=subprocess.check_output("earthengine ls "+location+" -l -r")
        try:
            for item in b.split('\n'):
                a=item.replace("[","").replace("]","").split()
                header=a[0]
                tail=a[1]
                if header=="ImageCollection":
                    collc=ee.ImageCollection(tail)
                    print("Processing Image Collection "+str(tail))
                    ast=collc.size().getInfo()
                    size=collc.reduceColumns(ee.Reducer.sum(), ['system:asset_size']).get('sum').getInfo()
                    sz=float(size)/1000000
                    unit="MB"
                    with open(output,"a") as csvfile:
                        writer=csv.writer(csvfile,delimiter=',',lineterminator='\n')
                        writer.writerow([header,tail,ast,format(sz,'.2f'),unit])
                    csvfile.close()
                elif header=="Image":
                    collc=ee.Image(tail)
                    print("Processing Image "+str(tail))
                    size=collc.get('system:asset_size').getInfo()
                    ast="1"
                    sz=float(size)/1000000
                    unit="MB"
                    with open(output,"a") as csvfile:
                        writer=csv.writer(csvfile,delimiter=',',lineterminator='\n')
                        writer.writerow([header,tail,ast,format(sz,'.2f'),unit])
                    csvfile.close()
                elif header=="Table":
                    collc=ee.FeatureCollection(tail)
                    print("Processing Table "+str(tail))
                    ast="1"
                    size=collc.get('system:asset_size').getInfo()
                    sz=float(size)/1000000
                    unit="MB"
                    with open(output,"a") as csvfile:
                        writer=csv.writer(csvfile,delimiter=',',lineterminator='\n')
                        writer.writerow([header,tail,ast,format(sz,'.2f'),unit])
                    csvfile.close()
                elif header=="Folder": ##Folders are not added to the list but are print
                    ast=int(b.count(tail))-1
                    print("Folder "+str(tail) +" has "+str(ast)+" assets")
        except Exception:
            return "worked"
    elif items > 0 and typ =='report':
        with open(output,"wb") as csvfile:
            writer=csv.DictWriter(csvfile,fieldnames=["type", "path","No of Assets","size","unit"], delimiter=',')
            writer.writeheader()
            b=subprocess.check_output("earthengine ls "+location+" --max_items "+str(items)+" -l -r",shell=True)
        try:
            for item in b.split('\n'):
                a=item.replace("[","").replace("]","").split()
                header=a[0]
                tail=a[1]
                if header=="ImageCollection":
                    collc=ee.ImageCollection(tail)
                    print("Processing Image Collection "+str(tail))
                    ast=collc.size().getInfo()
                    size=collc.reduceColumns(ee.Reducer.sum(), ['system:asset_size']).get('sum').getInfo()
                    sz=float(size)/1000000
                    unit="MB"
                    with open(output,"a") as csvfile:
                        writer=csv.writer(csvfile,delimiter=',',lineterminator='\n')
                        writer.writerow([header,tail,ast,format(sz,'.2f'),unit])
                    csvfile.close()
                elif header=="Image":
                    collc=ee.Image(tail)
                    print("Processing Image "+str(tail))
                    size=collc.get('system:asset_size').getInfo()
                    ast="1"
                    sz=float(size)/1000000
                    unit="MB"
                    with open(output,"a") as csvfile:
                        writer=csv.writer(csvfile,delimiter=',',lineterminator='\n')
                        writer.writerow([header,tail,ast,format(sz,'.2f'),unit])
                    csvfile.close()
                elif header=="Table":
                    collc=ee.FeatureCollection(tail)
                    print("Processing Table "+str(tail))
                    ast="1"
                    size=collc.get('system:asset_size').getInfo()
                    sz=float(size)/1000000
                    unit="MB"
                    with open(output,"a") as csvfile:
                        writer=csv.writer(csvfile,delimiter=',',lineterminator='\n')
                        writer.writerow([header,tail,ast,format(sz,'.2f'),unit])
                    csvfile.close()
                elif header=="Folder": ##Folders are not added to the list but are print
                    ast=int(b.count(tail))-1
                    print("Folder "+str(tail) +" has "+str(ast)+" assets")
        except Exception:
            return "worked"
#lst(location="users/samapriya/Belem", typ="report",items=0,output=r"C:\planet_demo\rep.csv")
