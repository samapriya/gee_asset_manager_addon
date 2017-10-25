from __future__ import print_function
import ee,json,csv,subprocess
ee.Initialize()
def ee_report(output):
    with open(output,"wb") as csvfile:
        writer=csv.DictWriter(csvfile,fieldnames=["type", "path","No of Assets","size","unit","owner","readers","writers"], delimiter=',')
        writer.writeheader()
    a=subprocess.check_output("earthengine ls",shell=True)
    b=subprocess.check_output("earthengine ls "+a+" -l -r",shell=True)
    try:
        for item in b.split('\n'):
            a=item.replace("[","").replace("]","").split()
            header=a[0]
            tail=a[1]
            if header=="ImageCollection":
                collc=ee.ImageCollection(tail)
                own=json.dumps(json.loads(subprocess.check_output('earthengine acl get '+tail,shell=True)), ensure_ascii=False)
                #print(own)
                o=str(own).split('"owners": [')[1].split("]")[0].replace('"','')
                r=str(own).split('"readers": [')[1].split("]")[0].replace('"','')
                w=str(own).split('"writers": [')[1].split("]")[0].replace('"','')
                print("Processing Image Collection "+str(tail))
                ast=collc.size().getInfo()
                size=collc.reduceColumns(ee.Reducer.sum(), ['system:asset_size']).get('sum').getInfo()
                sz=float(size)/1000000
                unit="MB"
                with open(output,"a") as csvfile:
                    writer=csv.writer(csvfile,delimiter=',',lineterminator='\n')
                    writer.writerow([header,tail,ast,format(sz,'.2f'),unit,o,r,w])
                csvfile.close()
            elif header=="Image":
                collc=ee.Image(tail)
                own=json.dumps(json.loads(subprocess.check_output('earthengine acl get '+tail,shell=True)), ensure_ascii=False)
                o=str(own).split('"owners": [')[1].split("]")[0].replace('"','')
                r=str(own).split('"readers": [')[1].split("]")[0].replace('"','')
                w=str(own).split('"writers": [')[1].split("]")[0].replace('"','')
                print("Processing Image "+str(tail))
                size=collc.get('system:asset_size').getInfo()
                ast="1"
                sz=float(size)/1000000
                unit="MB"
                with open(output,"a") as csvfile:
                    writer=csv.writer(csvfile,delimiter=',',lineterminator='\n')
                    writer.writerow([header,tail,ast,format(sz,'.2f'),unit,o,r,w])
                csvfile.close()
            elif header=="Table":
                collc=ee.FeatureCollection(tail)
                own=json.dumps(json.loads(subprocess.check_output('earthengine acl get '+tail,shell=True)), ensure_ascii=False)
                o=str(own).split('"owners": [')[1].split("]")[0].replace('"','')
                r=str(own).split('"readers": [')[1].split("]")[0].replace('"','')
                w=str(own).split('"writers": [')[1].split("]")[0].replace('"','')
                #print(o,r,w)
                print("Processing Table "+str(tail))
                ast="1"
                size=collc.get('system:asset_size').getInfo()
                sz=float(size)/1000000
                unit="MB"
                with open(output,"a") as csvfile:
                    writer=csv.writer(csvfile,delimiter=',',lineterminator='\n')
                    writer.writerow([header,tail,ast,format(sz,'.2f'),unit,o,r,w])
                csvfile.close()
            elif header=="Folder": ##Folders are not added to the list but are print
                ast=int(b.count(tail))-1
                print("Folder "+str(tail) +" has "+str(ast)+" assets")
    except Exception:
        return "worked"
if __name__ == '__main__':
    ee_report(None)
