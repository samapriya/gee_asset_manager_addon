import ee,subprocess,os
##initialize earth engine
ee.Initialize()

suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
def humansize(nbytes):
    i = 0
    while nbytes >= 1024 and i < len(suffixes)-1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])
l=[]
def assetsize(asset):
    header=ee.data.getInfo(asset)['type']
    if header=="ImageCollection":
        collc=ee.ImageCollection(asset)
        size=collc.aggregate_array('system:asset_size')
        print('')
        print(str(asset)+" ===> "+str(humansize(sum(size.getInfo()))))
        print('Total number of items in collection: '+str(collc.size().getInfo()))
    elif header=="Image":
        collc=ee.Image(asset)
        print('')
        print(str(asset)+" ===> "+str(humansize(collc.get('system:asset_size').getInfo())))
    elif header=="Table":
        collc=ee.FeatureCollection(asset)
        print('')
        print(str(asset)+" ===> "+str(humansize(collc.get('system:asset_size').getInfo())))
    elif header =="Folder":
        b=subprocess.check_output("earthengine du "+asset+" -s",shell=True)
        num=subprocess.check_output("earthengine ls "+asset,shell=True)
        size=humansize(float(b.strip().split(' ')[0]))
        print('')
        print(str(asset)+" ===> "+str(size))
        print('Total number of items in folder: '+str(len(num.split('\n'))-1))
if __name__ == '__main__':
    assetsize(None)
