import os
import ee
import subprocess
import sys
from ee import oauth
import re
import getpass
import clipboard
import time
auth_url = ee.oauth.get_authorization_url()
clipboard.copy(auth_url)
print("Authentication link copied: Go to browser and click paste and go")
time.sleep(20)
print("Enter your GEE API Token")
password=str(getpass.getpass())
auth_code=str(password)
token = ee.oauth.request_token(auth_code)
ee.oauth.write_token(token)
print('\nSuccessfully saved authorization token.')

