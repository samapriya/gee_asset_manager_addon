import ee
import os


ee.Initialize()

def delprop(collection_path,property):
    header=ee.data.getInfo(collection_path)['type']
    if header=="Image":
        lst=[]
        lst.append(collection_path)
        assets_names=lst
    if header=="ImageCollection":
        assets_list = ee.data.getList(params={'id': collection_path})
        assets_names = [os.path.basename(asset['id']) for asset in assets_list]
    print('Changing permission for total of '+str(len(assets_names))+'.....')
    for count,items in enumerate(assets_names):
        if header=='ImageCollection':
            nullgrid={property:None}
            init=collection_path+'/'+items
            try:
                print("Processing "+str(count+1)+' of '+str(len(assets_names)))
                ee.data.setAssetProperties(init, nullgrid)
            except Exception as e:
                print("Could not run "+str(count+1)+' of '+str(len(assets_names)))
                print(e)
        else:
            init=items
            nullgrid={property:None}
            try:
                print("Processing "+str(count+1)+' of '+str(len(assets_names)))
                ee.data.setAssetProperties(init, nullgrid)
            except Exception as e:
                print("Could not run "+str(count+1)+' of '+str(len(assets_names)))
                print(e)

#delprop(collection_path='users/samapriya/LA_ASSET_EXP/LS_UNMX_OTSU_MEDOID',property='gridded')
#ee.data.setAssetProperties(args.asset_id, properties)
