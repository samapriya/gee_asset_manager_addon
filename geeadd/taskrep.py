import ee
import datetime
import csv

ee.Initialize()

def genreport(report):
    with open(report,'wb') as failed:
        writer=csv.DictWriter(failed,fieldnames=["Task ID","Task Type", "Task Description","Creation","Start","End","Time to Start","Time to End","Output State"],delimiter=',')
        writer.writeheader()
    status=ee.data.getTaskList()
    for items in status:
        ttype=items['task_type']
        tdesc=items['description']
        tstate=items['state']
        tid=items['id']
        try:
            tcreate=datetime.datetime.fromtimestamp(items['creation_timestamp_ms']/1000).strftime('%c')
            tstart=datetime.datetime.fromtimestamp(items['start_timestamp_ms']/1000).strftime('%c')
            tupdate=datetime.datetime.fromtimestamp(items['update_timestamp_ms']/1000).strftime('%c')
            tdiffstart=items['start_timestamp_ms']/1000-items['creation_timestamp_ms']/1000
            tdiffend=items['update_timestamp_ms']/1000-items['start_timestamp_ms']/1000
            #print(ttype,tdesc,tstate,tid,tcreate,tstart,tupdate,tdiffstart,tdiffend)
            with open(report,'a') as tasks:
                writer=csv.writer(tasks,delimiter=',',lineterminator='\n')
                writer.writerow([tid,ttype,tdesc,str(tcreate),str(tstart),str(tupdate),str(tdiffstart),str(tdiffend),tstate])
        except Exception as e:
            pass
    print('Report exported to '+str(report))
#genreport(report=r'C:\planet_demo\taskrep.csv')
