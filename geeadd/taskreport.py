import ee
import subprocess
import csv
from datetime import datetime
import time
import datetime
import re
ee.Initialize()
def genreport(report):
    with open(report+'./Tasks_failed.csv','wb') as failed:
        writer=csv.DictWriter(failed,fieldnames=["Task ID","Task Type", "Start Date","Start Time","End Date","End Time","Task Description", "Error Message","Source Script", "Output State"],delimiter=',')
        writer.writeheader()
    with open(report+'./Tasks_completed.csv','wb') as completed:
        writer=csv.DictWriter(completed,fieldnames=["Task ID","Task Type", "Start Date","Start Time","End Date","End Time","Task Description", "Output Url", "Output State"],delimiter=',')
        writer.writeheader()
    with open(report+'./Tasks_canceled.csv','wb') as canceled:
        writer=csv.DictWriter(canceled,fieldnames=["Task ID","Task Type", "Start Date","Start Time","End Date","End Time","Task Description", "Source Script", "Output State"],delimiter=',')
        writer.writeheader()
    try:
        for line in subprocess.check_output("earthengine task list",shell=True).split('\n'):
            tsk=line.split(' ')[0]
            ur=ee.data.getTaskStatus(tsk)
            error=str(ur).split('state')[1].split(',')[0].strip("': u'.")
            mode = error
            if mode == 'FAILED':
                        tsktype=str(ur).split('task_type')[1].split(',')[0].strip("': u'.")
                        tskdesc=str(ur).split("'description'")[1].split(',')[0].strip("': u'.")
                        outurl=str(ur).split('source_url')[1].split(',')[0].strip("': u'.")
                        strttime=str(ur).split('start_timestamp_ms')[1].split(',')[0].strip("': u'.L")
                        endtime=str(ur).split('update_timestamp_ms')[1].split(',')[0].strip("': u'.L")
                        errmsg=str(ur).split('error_message')[1].split(',')[0].strip("': u'.")
                        state=str(ur).split('state')[1].split(',')[0].strip("': u'.")
                        tskid=str(ur).split("'id'")[1].split(',')[0].strip("': u'.'}]")
                        v=int(strttime)/1000
                        w=int(endtime)/1000
                        start=datetime.datetime.fromtimestamp(v).strftime('%Y-%m-%d %H:%M:%S.%f')
                        startdate=start.split(' ')[0]
                        starttime=start.split(' ')[1].split('.')[0]
                        end=datetime.datetime.fromtimestamp(w).strftime('%Y-%m-%d %H:%M:%S.%f')
                        enddate=end.split(' ')[0]
                        endtime=end.split(' ')[1].split('.')[0]
                        print(tsktype.title())
                        print(tskdesc)
                        print(outurl)
                        print(start)
                        print(end)
                        print(errmsg)
                        print(tskid)
                        print(state)
                        with open(report+'./Tasks_failed.csv','a') as failed:
                            writer=csv.writer(failed,delimiter=',',lineterminator='\n')
                            writer.writerow([tskid,tsktype,startdate,starttime,enddate,endtime,tskdesc,errmsg,outurl,state])
            elif mode == 'CANCELED':
                    tsktype=str(ur).split('task_type')[1].split(',')[0].strip("': u'.")
                    tskdesc=str(ur).split("'description'")[1].split(':')[1].split(',')[0].strip("': u'.")
                    outurl=str(ur).split('source_url')[1].split(',')[0].strip("[': u'.]")
                    strttime=str(ur).split('start_timestamp_ms')[1].split(',')[0].strip("': u'.L")
                    endtime=str(ur).split('update_timestamp_ms')[1].split(',')[0].strip("': u'.L")
                    state=str(ur).split('state')[1].split(',')[0].strip("': u'.")
                    tskid=str(ur).split("'id'")[1].split(',')[0].strip("': u'.'}]")
                    v=int(strttime)/1000
                    w=int(endtime)/1000
                    start=datetime.datetime.fromtimestamp(v).strftime('%Y-%m-%d %H:%M:%S.%f')
                    startdate=start.split(' ')[0]
                    starttime=start.split(' ')[1].split('.')[0]
                    end=datetime.datetime.fromtimestamp(w).strftime('%Y-%m-%d %H:%M:%S.%f')
                    enddate=end.split(' ')[0]
                    endtime=end.split(' ')[1].split('.')[0]
                    print(tsktype.title())
                    print(tskdesc)
                    print(outurl)
                    print(start)
                    print(end)
                    print(tskid)
                    print(state)
                    with open(report+'./Tasks_canceled.csv','a') as canceled:
                        writer=csv.writer(canceled,delimiter=',',lineterminator='\n')
                        writer.writerow([tskid,tsktype,startdate,starttime,enddate,endtime,tskdesc,outurl,state])
            elif mode == 'COMPLETED':
                    tsktype=str(ur).split('task_type')[1].split(',')[0].strip("': u'.")
                    tskdesc=str(ur).split("'description'")[1].split(':')[1].split(',')[0].strip("': u'.")
                    outurl=str(ur).split('output_url')[1].split(',')[0].strip("[': u'.]")
                    strttime=str(ur).split('start_timestamp_ms')[1].split(',')[0].strip("': u'.L")
                    endtime=str(ur).split('update_timestamp_ms')[1].split(',')[0].strip("': u'.L")
                    state=str(ur).split('state')[1].split(',')[0].strip("': u'.")
                    tskid=str(ur).split("'id'")[1].split(',')[0].strip("': u'.'}]")
                    v=int(strttime)/1000
                    w=int(endtime)/1000
                    start=datetime.datetime.fromtimestamp(v).strftime('%Y-%m-%d %H:%M:%S.%f')
                    startdate=start.split(' ')[0]
                    starttime=start.split(' ')[1].split('.')[0]
                    end=datetime.datetime.fromtimestamp(w).strftime('%Y-%m-%d %H:%M:%S.%f')
                    enddate=end.split(' ')[0]
                    endtime=end.split(' ')[1].split('.')[0]
                    print(tsktype.title())
                    print(tskdesc)
                    print(outurl)
                    print(start)
                    print(end)
                    print(tskid)
                    print(state)
                    with open(report+'./Tasks_completed.csv','a') as completed:
                        writer=csv.writer(completed,delimiter=',',lineterminator='\n')
                        writer.writerow([tskid,tsktype,startdate,starttime,enddate,endtime,tskdesc,outurl,state])
            completed.close()
            failed.close()
            canceled.close()
    except Exception:
        with open(report+'./Errorlog.csv','wb') as csvfile:
            writer=csv.writer(csvfile,delimiter=',')
            writer.writerow([tskid])
            csvfile.close()
