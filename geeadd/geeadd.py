#! /usr/bin/env python

import argparse,clipboard,time
import logging,getpass
import os
import ee
import subprocess
os.chdir(os.path.dirname(os.path.realpath(__file__)))
from ee import oauth
from batch_copy import copy
from batch_remover import delete
from batch_uploader import upload
from config import setup_logging
from batch_mover import mover
from tabup import tabup
from taskrep import genreport
from acl_changer import access
from ee_ls import lst
from assetsizes import assetsize
from ee_report import ee_report
from ee_del_meta import delprop
from zipfiles import zipshape


suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
def humansize(nbytes):
    i = 0
    while nbytes >= 1024 and i < len(suffixes)-1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])

def cancel_all_running_tasks():
    logging.info('Attempting to cancel all running tasks')
    running_tasks = [task for task in ee.data.getTaskList() if task['state'] == 'RUNNING']
    for task in running_tasks:
        ee.data.cancelTask(task['id'])
    logging.info('Cancel all request completed')

def cancel_all_running_tasks_from_parser(args):
    cancel_all_running_tasks()

def delete_collection_from_parser(args):
    delete(args.id)

def zipshape_from_parser(args):
    zipshape(directory=args.input,export=args.output)

def upload_from_parser(args):
    upload(user=args.user,
           source_path=args.source,
           destination_path=args.dest,
           metadata_path=args.metadata,
           multipart_upload=args.large,
           nodata_value=args.nodata,
           bucket_name=args.bucket,
           band_names=args.bands)
def tabup_from_parser(args):
    tabup(user=args.user,
           source_path=args.source,
           destination_path=args.dest)

def _comma_separated_strings(string):
  """Parses an input consisting of comma-separated strings.
     Slightly modified version of: https://pypkg.com/pypi/earthengine-api/f/ee/cli/commands.py
  """
  error_msg = 'Argument should be a comma-separated list of alphanumeric strings (no spaces or other' \
              'special characters): {}'
  values = string.split(',')
  for name in values:
      if not name.isalnum():
          raise argparse.ArgumentTypeError(error_msg.format(string))
  return values

def quota():
    quota=ee.data.getAssetRootQuota(ee.data.getAssetRoots()[0]['id'])
    print('')
    print("Total Quota: "+str(humansize(quota['asset_size']['limit'])))
    print("Used Quota: "+str(humansize(quota['asset_size']['usage'])))

def quota_from_parser(args):
    quota()

def ee_report_from_parser(args):
    ee_report(output=args.outfile)

def mover_from_parser(args):
	mover(collection_path=args.assetpath,final_path=args.finalpath)
def copy_from_parser(args):
	copy(collection_path=args.initial,final_path=args.final)
def access_from_parser(args):
	access(collection_path=args.asset,user=args.user,role=args.role)
def delete_metadata_from_parser(args):
    delprop(collection_path=args.asset,property=args.property)

def tasks():
    statuses=ee.data.getTaskList()
    st=[]
    for status in statuses:
        st.append(status['state'])
    print("Tasks Running: "+str(st.count('RUNNING')))
    print("Tasks Ready: "+str(st.count('READY')))
    print("Tasks Completed: "+str(st.count('COMPLETED')))
    print("Tasks Failed: "+str(st.count('FAILED')))
    print("Tasks Cancelled: "+str(st.count('CANCELLED')))

def tasks_from_parser(args):
    tasks()

def ee_auth_entry():
    auth_url = ee.oauth.get_authorization_url()
    clipboard.copy(auth_url)
    print("Authentication link copied: Go to browser and click paste")
    time.sleep(10)
    print("Enter your GEE API Token")
    password=str(getpass.getpass())
    auth_code=str(password)
    token = ee.oauth.request_token(auth_code)
    ee.oauth.write_token(token)
    print('\nSuccessfully saved authorization token.')
def ee_user_from_parser(args):
    ee_auth_entry()
def create_from_parser(args):
    typ=str(args.typ)
    ee_path=str(args.path)
    os.system("earthengine create "+typ+" "+ee_path)

def genreport_from_parser(args):
    genreport(report=args.r)
def assetsize_from_parser(args):
    assetsize(asset=args.asset)
def lst_from_parser(args):
    lst(location=args.location,typ=args.typ,items=args.items,output=args.output)

def main(args=None):
    setup_logging()
    parser = argparse.ArgumentParser(description='Google Earth Engine Batch Asset Manager with Addons')
    parser.add_argument('-s', '--service-account', help='Google Earth Engine service account.', required=False)
    parser.add_argument('-k', '--private-key', help='Google Earth Engine private key file.', required=False)

    subparsers = parser.add_subparsers()
    parser_ee_user=subparsers.add_parser('ee_user',help='Allows you to associate/change GEE account to system')
    parser_ee_user.set_defaults(func=ee_user_from_parser)

    parser_quota = subparsers.add_parser('quota', help='Print Earth Engine total quota and used quota')
    parser_quota.set_defaults(func=quota_from_parser)

    parser_create = subparsers.add_parser('create',help='Allows the user to create an asset collection or folder in Google Earth Engine')
    parser_create.add_argument('--typ', help='Specify type: collection or folder', required=True)
    parser_create.add_argument('--path', help='This is the path for the earth engine asset to be created full path is needsed eg: users/johndoe/collection', required=True)
    parser_create.set_defaults(func=create_from_parser)

    parser_zipshape = subparsers.add_parser('zipshape', help='Zips all shapefiles and subsidary files into individual zip files')
    required_named = parser_zipshape.add_argument_group('Required named arguments.')
    required_named.add_argument('--input', help='Path to the input directory with all shape files', required=True)
    required_named.add_argument('--output', help='Destination folder Full path where shp, shx, prj and dbf files if present in input will be zipped and stored', required=True)
    parser_zipshape.set_defaults(func=zipshape_from_parser)

    parser_upload = subparsers.add_parser('upload', help='Batch Asset Uploader upload images to collection')
    required_named = parser_upload.add_argument_group('Required named arguments.')
    required_named.add_argument('--source', help='Path to the directory with images for upload.', required=True)
    required_named.add_argument('--dest', help='Destination. Full path for upload to Google Earth Engine, e.g. users/pinkiepie/myponycollection', required=True)
    optional_named = parser_upload.add_argument_group('Optional named arguments')
    optional_named.add_argument('-m', '--metadata', help='Path to CSV with metadata.')
    optional_named.add_argument('--large', action='store_true', help='(Advanced) Use multipart upload. Might help if upload of large '
                                                                     'files is failing on some systems. Might cause other issues.')
    optional_named.add_argument('--nodata', type=int, help='The value to burn into the raster as NoData (missing data)')
    optional_named.add_argument('--bands', type=_comma_separated_strings, help='Comma-separated list of names to use for the image bands. Spaces'
                                                                               'or other special characters are not allowed.')

    required_named.add_argument('-u', '--user', help='Google account name (gmail address).')
    optional_named.add_argument('-b', '--bucket', help='Google Cloud Storage bucket name.')

    parser_upload.set_defaults(func=upload_from_parser)

    parser_tabup = subparsers.add_parser('tabup', help='Batch Table Uploader upload the shapefiles you zipped earlier.')
    required_named = parser_tabup.add_argument_group('Required named arguments.')
    required_named.add_argument('--source', help='Path to the directory with zipped folder for upload.', required=True)
    required_named.add_argument('--dest', help='Destination. Full path for upload to Google Earth Engine, e.g. users/pinkiepie/myponycollection', required=True)
    required_named.add_argument('-u', '--user', help='Google account name (gmail address).')
    parser_tabup.set_defaults(func=tabup_from_parser)

    parser_lst = subparsers.add_parser('lst',help='List assets in a folder/collection or write as text file')
    required_named = parser_lst.add_argument_group('Required named arguments.')
    required_named.add_argument('--location', help='This it the location of your folder/collection', required=True)
    required_named.add_argument('--typ', help='Whether you want the list to be printed or output as text[print/report]', required=True)
    optional_named = parser_lst.add_argument_group('Optional named arguments')
    optional_named.add_argument('--items', help="Number of items to list")
    optional_named.add_argument('--output',help="Folder location for report to be exported")
    parser_lst.set_defaults(func=lst_from_parser)

    parser_ee_report = subparsers.add_parser('ee_report',help='Prints a detailed report of all Earth Engine Assets includes Asset Type, Path,Number of Assets,size(MB),unit,owner,readers,writers')
    parser_ee_report.add_argument('--outfile', help='This it the location of your report csv file ', required=True)
    parser_ee_report.set_defaults(func=ee_report_from_parser)

    parser_assetsize = subparsers.add_parser('assetsize',help='Prints collection size in Human Readable form & Number of assets')
    parser_assetsize.add_argument('--asset', help='Earth Engine Asset for which to get size properties', required=True)
    parser_assetsize.set_defaults(func=assetsize_from_parser)

    parser_tasks=subparsers.add_parser('tasks',help='Queries current task status [completed,running,ready,failed,cancelled]')
    parser_tasks.set_defaults(func=tasks_from_parser)

    parser_genreport=subparsers.add_parser('taskreport',help='Create a report of all tasks and exports to a CSV file')
    parser_genreport.add_argument('--r',help='Path to csv report file')
    parser_genreport.set_defaults(func=genreport_from_parser)


    parser_delete = subparsers.add_parser('delete', help='Deletes collection and all items inside. Supports Unix-like wildcards.')
    parser_delete.add_argument('id', help='Full path to asset for deletion. Recursively removes all folders, collections and images.')
    parser_delete.set_defaults(func=delete_collection_from_parser)

    parser_mover=subparsers.add_parser('mover',help='Moves all assets from one collection to another')
    parser_mover.add_argument('--assetpath',help='Existing path of assets')
    parser_mover.add_argument('--finalpath',help='New path for assets')
    parser_mover.set_defaults(func=mover_from_parser)

    parser_copy=subparsers.add_parser('copy',help='Copies all assets from one collection to another: Including copying from other users if you have read permission to their assets')
    parser_copy.add_argument('--initial',help='Existing path of assets')
    parser_copy.add_argument('--final',help='New path for assets')
    parser_copy.set_defaults(func=copy_from_parser)

    parser_access = subparsers.add_parser('access',help='Sets Permissions for items in folder')
    parser_access.add_argument('--asset', help='This is the path to the earth engine asset whose permission you are changing folder/collection/image', required=True)
    parser_access.add_argument('--user', help='Full email address of the user, try using "AllUsers" to make it public', required=True, default=False)
    parser_access.add_argument('--role', help='Choose between reader, writer or delete', required=True)
    parser_access.set_defaults(func=access_from_parser)

    parser_delete_metadata = subparsers.add_parser('delete_metadata',help='Use with caution: delete any metadata from collection or image')
    parser_delete_metadata.add_argument('--asset', help='This is the path to the earth engine asset whose permission you are changing collection/image', required=True)
    parser_delete_metadata.add_argument('--property', help='Metadata name that you want to delete', required=True, default=False)
    parser_delete_metadata.set_defaults(func=delete_metadata_from_parser)

    parser_cancel = subparsers.add_parser('cancel', help='Cancel all running tasks')
    parser_cancel.set_defaults(func=cancel_all_running_tasks_from_parser)

    args = parser.parse_args()

    #ee.Initialize()
    args.func(args)

if __name__ == '__main__':
    main()
