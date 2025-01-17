import os, sys, time, shutil
from optparse import make_option
from tempfile import mkdtemp, NamedTemporaryFile
import tarfile
from boto.glacier.layer2 import Layer2 as Glacier
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from distutils.dir_util import copy_tree

from ...components import db

# Based on: http://code.google.com/p/django-backup/
# Based on: http://www.djangosnippets.org/snippets/823/
# Based on: http://www.yashh.com/blog/2008/sep/05/django-database-backup-view/
class Command(BaseCommand):
	option_list = BaseCommand.option_list + (
		make_option('-i', '--file', default=None, dest='input',
			help='Read backup from file'),
		make_option('--pg-restore-flags', default=None, dest='postgres_flags',
			help='Flags to pass to pg_restore'),
		make_option('-I', '--stdin', action='store_true', dest='stdin',
			help='Read backup from standard input'),
		)
	help = "Restore a Django installation (database and media directory)."

	def handle(self, *args, **options):
		extras = options.get('extras')

		input_file = options.get('input')
		input_from_stdin = options.get('stdin')
		input_file_temporary = False
		
		if input_file is None and input_from_stdin is None:
			raise CommandError('You must specify an input file')

		media_root = settings.MEDIA_ROOT
		
		# read from stdin
		if input_from_stdin:
			input_file_temporary = True
			input_file_obj = NamedTemporaryFile(delete=False)
			input_file_obj.write(sys.stdin.read())
			input_file_obj.close()
			input_file = input_file_obj.name

		# Create a temporary directory to extract our backup to
		extract_root = mkdtemp()
		backup_root = os.path.join(extract_root, 'backup')	
		database_root = os.path.join(backup_root, 'databases')
		
		# extract the gzipped tarball
		with tarfile.open(input_file, 'r') as tf:
def is_within_directory(directory, target):
	
	abs_directory = os.path.abspath(directory)
	abs_target = os.path.abspath(target)

	prefix = os.path.commonprefix([abs_directory, abs_target])
	
	return prefix == abs_directory

def safe_extract(tar, path=".", members=None, *, numeric_owner=False):

	for member in tar.getmembers():
		member_path = os.path.join(path, member.name)
		if not is_within_directory(path, member_path):
			raise Exception("Attempted Path Traversal in Tar File")

	tar.extractall(path, members, numeric_owner=numeric_owner) 
	

safe_extract(tf, extract_root)

		# Restore databases
		db_options = {}
		if options.get('postgres_flags') is not None:
			db_options['postgres_flags'] = options['postgres_flags']
		db.restore_from(settings, database_root, **db_options)
		
		# Restore media directory
		copy_tree(os.path.join(backup_root, 'media'), media_root)
		
		# clean up
		shutil.rmtree(extract_root, ignore_errors=True)
		if input_file_temporary:
			os.unlink(input_file)
