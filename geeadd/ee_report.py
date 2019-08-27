from __future__ import print_function
__copyright__ = """

    Copyright 2019 Samapriya Roy

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

"""
__license__ = "Apache 2.0"

import ee,json,csv,subprocess
ee.Initialize()

suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
def humansize(nbytes):
    i = 0
    while nbytes >= 1024 and i < len(suffixes)-1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])

def object_sz(object):
    sz=humansize(object.get('system:asset_size').getInfo())
    return sz

def collect_sz(object):
    sz=humansize(object.reduceColumns(ee.Reducer.sum(), ['system:asset_size']).get('sum').getInfo())
    return sz

def recprocess(header,location,output):
    try:
        if header=="ImageCollection":
            collc=ee.ImageCollection(location)
            own=ee.data.getAssetAcl(location)
            o=",".join(own['owners'])
            r=",".join(own['readers'])
            w=",".join(own['writers'])
            print("Processing Image Collection "+str(location))
            ast=collc.size().getInfo()
            sz=collect_sz(collc)
            with open(output,"a") as csvfile:
                writer=csv.writer(csvfile,delimiter=',',lineterminator='\n')
                writer.writerow([header,location,ast,sz,o,r,w])
            csvfile.close()
        elif header=="Image":
            collc=ee.Image(location)
            own=ee.data.getAssetAcl(location)
            o=",".join(own['owners'])
            r=",".join(own['readers'])
            w=",".join(own['writers'])
            print("Processing Image "+str(location))
            ast="1"
            sz=object_sz(collc)
            print("Processing Image "+str(location))
            with open(output,"a") as csvfile:
                writer=csv.writer(csvfile,delimiter=',',lineterminator='\n')
                writer.writerow([header,location,ast,sz,o,r,w])
            csvfile.close()
        elif header=="Table":
            collc=ee.FeatureCollection(location)
            own=ee.data.getAssetAcl(location)
            o=",".join(own['owners'])
            r=",".join(own['readers'])
            w=",".join(own['writers'])
            print("Processing Table "+str(location))
            ast="1"
            sz=object_sz(collc)
            with open(output,"a") as csvfile:
                writer=csv.writer(csvfile,delimiter=',',lineterminator='\n')
                writer.writerow([header,location,ast,sz,o,r,w])
            csvfile.close()
    except Exception as e:
        print(e)


def ee_report(output):
    with open(output,"wb") as csvfile:
        writer=csv.DictWriter(csvfile,fieldnames=["type", "path","No of Assets","size","owner","readers","writers"], delimiter=',')
        writer.writeheader()
    location=ee.data.getAssetRoots()[0]['id']
    assets_list = ee.data.getList(params={'id': location})
    for things in assets_list:
        header=things['type']
        tail=things['id']
        try:
            if header=="ImageCollection":
                recprocess(header,collc,output)
            elif header=="Image":
                recprocess(header,collc,output)
            elif header=="Table":
                recprocess(header,collc,output)
            elif header=="Folder": ##Folders are not added to the list but are print
                flist = ee.data.getList(params={'id': tail})
                print("Folder: "+str(tail) +" has "+str(len(flist))+' items')
                for things in flist:
                    header=things['type']
                    tail=things['id']
                    try:
                        if header=="ImageCollection":
                            recprocess(header,tail,output)
                        elif header=="Image":
                            recprocess(header,tail,output)
                        elif header=="Table":
                            recprocess(header,tail,output)
                    except Exception as e:
                        pass
        except Exception as e:
            pass
if __name__ == '__main__':
    ee_report(None)
