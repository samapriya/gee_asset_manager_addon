import argparse
import subprocess
import sys
import os,sys,time,csv,sys
import subprocess
import os
import json
from pprint import pprint
import argparse
import sys
import time
import fnmatch
import logging
import sys
import ee

def taskquery(destination):
    tcom=str("earthengine ls "+destination)
    tasklist=subprocess.check_output("earthengine task list")
    assetlist=subprocess.check_output(tcom)
    taskready=tasklist.count("READY")
    taskrunning=tasklist.count("RUNNING")
    taskfailed=tasklist.count("FAILED")
    totalfiles=assetlist.count(destination)
    print("Running Tasks:",taskrunning)
    print("Ready Tasks:",taskready)
    print("Failed Tasks:",taskfailed)
    print("Assets Uploaded:",totalfiles)
	
    
