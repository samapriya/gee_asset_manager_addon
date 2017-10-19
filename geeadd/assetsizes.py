import ee,subprocess,csv,os,json

##initialize earth engine
ee.Initialize()

#Create empty list for file size and asset number
s=[]
fsz=[]
def assetsize(asset):
    header=ee.data.getInfo(asset)['type']
    if header=="ImageCollection":
        collc=ee.ImageCollection(asset)
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
    elif header=="Image":
        collc=ee.Image(asset)
        size=collc.get('system:asset_size').getInfo()
        if int(size)>1000000000000:
            sz=float(size)/1000000000000
            print('Total size in TB = '+format(float(sz),'.2f'))
        elif int(size)>1000000000 and int(size)<1000000000000:
            sz=float(size)/1000000000
            print('Total size in GB = '+format(float(sz),'.2f'))
        elif int(size)>1000000 and int(size)<=1000000000:
            sz=float(size)/1000000
            print('Total size in MB = '+format(float(sz),'.2f'))
        else:
            sz=float(size)/1000
            print('Total size in KB = '+format(float(sz),'.2f'))

    elif header=="Table":
        collc=ee.FeatureCollection(asset)
        size=collc.get('system:asset_size').getInfo()
        if int(size)>1000000000000:
            sz=float(size)/1000000000000
            print('Total size in TB = '+format(float(sz),'.2f'))
        elif int(size)>1000000000 and int(size)<1000000000000:
            sz=float(size)/1000000000
            print('Total size in GB = '+format(float(sz),'.2f'))
        elif int(size)>1000000 and int(size)<=1000000000:
            sz=float(size)/1000000
            print('Total size in MB = '+format(float(sz),'.2f'))
        else:
            sz=float(size)/1000
            print('Total size in KB = '+format(float(sz),'.2f'))
    elif header =="Folder":
        b=subprocess.check_output("earthengine ls "+asset+" -l -r")

        try:
            for item in b.split('\n'):
                a=item.replace("[","").replace("]","").split()
                header=a[0]
                tail=a[1]
                if header=="ImageCollection":
                    collc=ee.ImageCollection(tail)
                    size=collc.reduceColumns(ee.Reducer.sum(), ['system:asset_size']).get('sum').getInfo()
                    s.append(size)
                    fsz.append(collc.size().getInfo())
                elif header=="Image":
                    collc=ee.Image(tail)
                    size=collc.get('system:asset_size').getInfo()
                    s.append(size)
                    fsz.append(1)
                elif header=="Table":
                    collc=ee.FeatureCollection(tail)
                    size=collc.get('system:asset_size').getInfo()
                    s.append(size)
                    fsz.append(1)
                if int(sum(s))>1000000000000:
                    sz=float(sum(s))/1000000000000
                    #print('Total size in TB = '+format(float(sz),'.2f'))
                elif int(sum(s))>1000000000 and int(sum(s))<1000000000000:
                    sz=float(sum(s))/1000000000
                    #print('Total size in GB = '+format(float(sz),'.2f'))
                elif int(sum(s))>1000000 and int(sum(s))<=1000000000:
                    sz=float(sum(s))/1000000
                    #print('Total size in MB = '+format(float(sz),'.2f'))
                else:
                    sz=float(sum(s))/1000
                    #print('Total size in KB = '+format(float(sz),'.2f'))
            print(s)

        except Exception:
            print"Completed Folder Summation for "+str(asset)
            print(" ")
            if int(sum(s))>1000000000000:
                print(str(format(float(sz),'.2f'))+" TB")
                print("Total Number of Assets "+str(sum(fsz)))
            elif int(sum(s))>1000000000 and int(sum(s))<1000000000000:
                print(str(format(float(sz),'.2f'))+" GB")
                print("Total Number of Assets "+str(sum(fsz)))
            elif int(sum(s))>1000000 and int(sum(s))<=1000000000:
                print(str(format(float(sz),'.2f'))+" MB")
                print("Total Number of Assets "+str(sum(fsz)))
            else:
                print(str(format(float(sz),'.2f'))+" KB")
                print("Total Number of Assets "+str(sum(fsz)))

if __name__ == '__main__':
    assetsize(None)
