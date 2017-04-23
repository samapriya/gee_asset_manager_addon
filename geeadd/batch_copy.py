import sys
import logging
import sys
import ee
import subprocess
import string
import os
import ee

def copy(initial,final):
    for line in subprocess.check_output("earthengine ls "+initial).split('\n'):
        try:
            src= line
            dest=line.replace(initial,final)
            com=(str('earthengine cp ')+str(src)+' '+str(dest))
            process = subprocess.call(com)
        except Exception:
            print(com)
            with open(errorlogcopy.csv,'a') as csvfile:
                writer=csv.writer(csvfile,delimiter=',')
                writer.writerow([com])
                csvfile.close()
        print("Assets Copied")
