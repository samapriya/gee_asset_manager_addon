from __future__ import print_function
import ee
import os
ee.Initialize()

def mover(collection_path,final_path):
    assets_list = ee.data.getList(params={'id': collection_path})
    assets_names = [os.path.basename(asset['id']) for asset in assets_list]
    print('Moving a total of '+str(len(assets_names))+'.....')
    for count,items in enumerate(assets_names):
        print ('Moving '+str(count+1)+' of '+str(len(assets_names)), end='\r')
        init=collection_path+'/'+items
        final=final_path+'/'+items
        try:
            ee.data.renameAsset(init, final)
        except Exception as e:
            pass
#batchcopy(collection_path='users/samapriya/bl',final_path='users/samapriya/b2')

