import os
import shutil
def cleanout(dirpath):
    shutil.rmtree(dirpath)
    os.mkdir(dirpath)
    print("Directory Cleaned")
