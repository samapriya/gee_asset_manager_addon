#! /usr/bin/env python

import argparse
import logging
import os
import ee
import subprocess

from batch_copy import copy
from batch_remover import delete
from batch_uploader import upload
from config import setup_logging
from query import taskquery
from batch_mover import mover
from cleanup import cleanout
from collectionprop import collprop
from taskreport import genreport
from acl_changer import access
from ee_ls import lst
from collsizes import collsize

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

def upload_from_parser(args):
    upload(user=args.user,
           source_path=args.source,
           destination_path=args.dest,
           metadata_path=args.metadata,
           multipart_upload=args.large,
           nodata_value=args.nodata)

def taskquery_from_parser(args):
    taskquery(destination=args.destination)
def mover_from_parser(args):
	mover(assetpath=args.assetpath,destinationpath=args.finalpath)
def copy_from_parser(args):
	copy(initial=args.initial,final=args.final)
def access_from_parser(args):
	access(mode=args.mode,asset=args.asset,user=args.user)
def cleanout_from_parser(args):
    cleanout(args.dirpath)
def tasks():
    tasklist=subprocess.check_output("earthengine task list")
    taskcompleted=tasklist.count("COMPLETED")
    taskready=tasklist.count("READY")
    taskrunning=tasklist.count("RUNNING")
    taskfailed=tasklist.count("FAILED")
    taskcancelled=tasklist.count("CANCELLED")
    print("Completed Tasks:",taskcompleted)
    print("Running Tasks:",taskrunning)
    print("Ready Tasks:",taskready)
    print("Failed Tasks:",taskfailed)
    print("Cancelled Tasks:",taskcancelled)
def tasks_from_parser(args):
    tasks()

def ee_authorization():
    os.system("python ee_auth.py")
def create_from_parser(args):
    typ=str(args.typ)
    ee_path=str(args.path)
    os.system("earthengine create "+typ+" "+ee_path)
    
def ee_user_from_parser(args):
    ee_authorization()
def genreport_from_parser(args):
    genreport(report=args.r)
def collprop_from_parser(args):
    collprop(imcoll=args.coll,prop=args.p)
def collsize_from_parser(args):
    collsize(coll=args.coll)
def lst_from_parser(args):
    lst(location=args.location,typ=args.type,items=args.items,f=args.folder)

def main(args=None):
    setup_logging()
    parser = argparse.ArgumentParser(description='Google Earth Engine Batch Asset Manager with Addons')

    subparsers = parser.add_subparsers()
    parser_ee_user=subparsers.add_parser('ee_user',help='Allows you to associate/change GEE account to system')
    parser_ee_user.set_defaults(func=ee_user_from_parser)

    parser_create = subparsers.add_parser('create',help='Allows the user to create an asset collection or folder in Google Earth Engine')
    parser_create.add_argument('--typ', help='Specify type: collection or folder', required=True)
    parser_create.add_argument('--path', help='This is the path for the earth engine asset to be created full path is needsed eg: users/johndoe/collection', required=True)
    parser_create.set_defaults(func=create_from_parser)

    parser_upload = subparsers.add_parser('upload', help='Batch Asset Uploader.')
    required_named = parser_upload.add_argument_group('Required named arguments.')
    required_named.add_argument('-u', '--user', help='Google account name (gmail address).', required=True)
    required_named.add_argument('--source', help='Path to the directory with images for upload.', required=True)
    required_named.add_argument('--dest', help='Destination. Full path for upload to Google Earth Engine, e.g. users/pinkiepie/myponycollection', required=True)
    optional_named = parser_upload.add_argument_group('Optional named arguments')
    optional_named.add_argument('-m', '--metadata', help='Path to CSV with metadata.')
    optional_named.add_argument('--large', action='store_true', help='(Advanced) Use multipart upload. Might help if upload of large '
                                                                     'files is failing on some systems. Might cause other issues.')
    optional_named.add_argument('--nodata', type=int, help='The value to burn into the raster as NoData (missing data)')
    parser_upload.set_defaults(func=upload_from_parser)

    parser_lst = subparsers.add_parser('lst',help='List assets in a folder/collection or write as text file')
    parser_lst.add_argument('--location', help='This it the location of your folder/collection', required=True)
    parser_lst.add_argument('--type', help='Whether you want the list to be printed or output as text', required=True)
    parser_lst.add_argument('--items', help="Number of items to list")
    parser_lst.add_argument('--folder',help="Folder location for report to be exported")
    parser_lst.set_defaults(func=lst_from_parser)
    
    parser_collsize = subparsers.add_parser('collsize',help='Collects collection size in Human Readable form & Number of assets')
    parser_collsize.add_argument('--coll', help='Earth Engine Collection for which to get size properties', required=True)
    parser_collsize.set_defaults(func=collsize_from_parser)
    
    parser_tasks=subparsers.add_parser('tasks',help='Queries currently running, enqued,failed')
    parser_tasks.set_defaults(func=tasks_from_parser)
    
    parser_taskquery=subparsers.add_parser('taskquery',help='Queries currently running, enqued,failed ingestions and uploaded assets')
    parser_taskquery.add_argument('--destination',help='Full path to asset where you are uploading files')
    parser_taskquery.set_defaults(func=taskquery_from_parser)

    parser_genreport=subparsers.add_parser('report',help='Create a report of all tasks and exports to a CSV file')
    parser_genreport.add_argument('--r',help='Folder Path where the reports will be saved')
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

    parser_access = subparsers.add_parser('access',help='Sets Permissions for Images, Collection or all assets in EE Folder Example: python ee_permissions.py --mode "folder" --asset "users/john/doe" --user "jimmy@doe.com:R"')
    parser_access.add_argument('--mode', help='This lets you select if you want to change permission or folder/collection/image', required=True)
    parser_access.add_argument('--asset', help='This is the path to the earth engine asset whose permission you are changing folder/collection/image', required=True)
    parser_access.add_argument('--user', help="""This is the email address to whom you want to give read or write permission Usage: "john@doe.com:R" or "john@doe.com:W" R/W refers to read or write permission""", required=True, default=False)
    parser_access.set_defaults(func=access_from_parser)

    parser_collprop=subparsers.add_parser('collprop',help='Sets Overall Properties for Image Collection')
    parser_collprop.add_argument('--coll',help='Path of Image Collection')
    parser_collprop.add_argument('--p',help='"system:description=Description"/"system:provider_url=url"/"system:tags=tags"/"system:title=title')
    parser_collprop.set_defaults(func=collprop_from_parser)
    
    parser_cleanout=subparsers.add_parser('cleanout',help='Clear folders with datasets from earlier downloaded')
    parser_cleanout.add_argument('--dirpath',help='Folder you want to delete after all processes have been completed')
    parser_cleanout.set_defaults(func=cleanout_from_parser)
    
    parser_cancel = subparsers.add_parser('cancel', help='Cancel all running tasks')
    parser_cancel.set_defaults(func=cancel_all_running_tasks_from_parser)

    args = parser.parse_args()

    ee.Initialize()
    args.func(args)

if __name__ == '__main__':
    main()
