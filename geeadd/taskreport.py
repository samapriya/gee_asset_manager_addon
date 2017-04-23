import ee
import ee.mapclient
import subprocess
import csv
from datetime import datetime
import time
import datetime
from BeautifulSoup import BeautifulSoup
ee.Initialize()
def genreport(report,error):
    with open(report,'wb') as csvfile:
                    writer=csv.DictWriter(csvfile,fieldnames=["Task ID","Task Type", "Start Date","Start Time","End Date","End Time","Task Description", "Output Url", "Output State"],delimiter=',')
                    writer.writeheader()
    for line in subprocess.check_output("earthengine task list").split('\n'):
        try:
            tsk=line.split(' ')[0]
            ur=ee.data.getTaskStatus(tsk)
            tsktype=str(ur).split(',')[0].split(':')[1].split('u')[1].strip("'")
            tskdesc=str(ur).split(',')[1].split(':')[1].split('u')[1].strip("'")
            outurl=str(ur).split(',')[2].split('https://')[1].split("'],")[0].strip("']")
            strttime=str(ur).split(',')[4].split(':')[1].split('u')[0].strip("'L ")
            endtime=str(ur).split(',')[3].split(':')[1].split('u')[0].strip("'L ")
            v=int(strttime)/1000
            w=int(endtime)/1000
            start=datetime.datetime.fromtimestamp(v).strftime('%Y-%m-%d %H:%M:%S.%f')
            startdate=start.split(' ')[0]
            starttime=start.split(' ')[1].split('.')[0]
            end=datetime.datetime.fromtimestamp(w).strftime('%Y-%m-%d %H:%M:%S.%f')
            enddate=end.split(' ')[0]
            endtime=end.split(' ')[1].split('.')[0]
            outstate=str(ur).split(',')[5].split(':')[1].split('u')[1].strip("'")
            tskid=str(ur).split(',')[7].split(':')[1].split('u')[1].strip("'}]")
            print(tsktype)
            print(tskdesc)
            print('https://'+outurl)
            print(outstate)
            print(startdate)
            print(starttime)
            print(tskid)
            with open(report,'a') as csvfile:
                writer=csv.writer(csvfile,delimiter=',',lineterminator='\n')
                writer.writerow([tskid,tsktype,startdate,starttime,enddate,endtime,tskdesc,str('https://'+outurl),outstate])
            csvfile.close()
        except Exception:
            with open(error,'a') as csvfile:
                writer=csv.writer(csvfile,delimiter=',')
                writer.writerow([tskid])
            csvfile.close()
