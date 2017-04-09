#! /usr/bin/env python

import argparse
import logging

import ee

from batch_remover import delete
from batch_uploader import upload
from config import setup_logging
from query import taskquery
from batch_mover import mover
from cleanup import cleanout
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
def ft_from_parser(args):
    input_file=str(args.i)
    output_ft=str(args.o)
    os.system("ogr2ft.py -i "+input_file+" -o "+output_ft)
def taskquery_from_parser(args):
    taskquery(destination=args.destination)
def mover_from_parser(args):
	mover(assetpath=args.assetpath,destinationpath=args.finalpath)
def cleanout_from_parser(args):
    cleanout(args.dirpath)
def main(args=None):
    setup_logging()
    parser = argparse.ArgumentParser(description='Google Earth Engine Batch Asset Manager with Addons')

    subparsers = parser.add_subparsers()
    parser_delete = subparsers.add_parser('delete', help='Deletes collection and all items inside. Supports Unix-like wildcards.')
    parser_delete.add_argument('id', help='Full path to asset for deletion. Recursively removes all folders, collections and images.')
    parser_delete.set_defaults(func=delete_collection_from_parser)

    parser_taskquery=subparsers.add_parser('taskquery',help='Queries currently running, enqued and uploaded assets')
    parser_taskquery.add_argument('--destination',help='Full path to asset where you are uploading files')
    parser_taskquery.set_defaults(func=taskquery_from_parser)
	
    parser_mover=subparsers.add_parser('mover',help='Moves all assets from one folder to other')
    parser_mover.add_argument('--assetpath',help='Existing path of assets')
    parser_mover.add_argument('--finalpath',help='New path for assets')
    parser_mover.set_defaults(func=mover_from_parser)
	
    parser_ft = subparsers.add_parser('convert2ft',help='Uploads a given feature collection to Google Fusion Table.')
    parser_ft.add_argument('--i', help='input feature source (KML, SHP, SpatiLite, etc.)', required=True)
    parser_ft.add_argument('--o', help='output Fusion Table name', required=True)
    parser_ft.add_argument('--add_missing', help='add missing features from the last inserted feature index', action='store_true', required=False, default=False)
    parser_ft.set_defaults(func=ft_from_parser)

    parser_cleanout=subparsers.add_parser('cleanout',help='Clear folders with datasets from earlier downloaded')
    parser_cleanout.add_argument('--dirpath',help='Folder you want to delete after all processes have been completed')
    parser_cleanout.set_defaults(func=cleanout_from_parser)
    
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

    parser_cancel = subparsers.add_parser('cancel', help='Cancel all running tasks')
    parser_cancel.set_defaults(func=cancel_all_running_tasks_from_parser)

    args = parser.parse_args()

    ee.Initialize()
    args.func(args)

if __name__ == '__main__':
    main()
