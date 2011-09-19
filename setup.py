#!/usr/bin/env python

from setuptools import setup
import os


# Shamelessly cribbed from django's setup.py file.
def fullsplit(path, result=None):
	"""
	Split a pathname into components (the opposite of os.path.join) in a
	platform-neutral way.
	"""
	if result is None:
		result = []
	head, tail = os.path.split(path)
	if head == '':
		return [tail] + result
	if head == path:
		return result
	return fullsplit(head, [tail] + result)

# Compile the list of packages available, because distutils doesn't have
# an easy way to do this. Shamelessly cribbed from django's setup.py file.
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)
kiki_dir = 'kiki'

for dirpath, dirnames, filenames in os.walk(kiki_dir):
	# Ignore dirnames that start with '.'
	for i, dirname in enumerate(dirnames):
		if dirname.startswith('.'): del dirnames[i]
	if '__init__.py' in filenames:
		packages.append('.'.join(fullsplit(dirpath)))
	elif filenames:
		data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])


version = __import__('kiki').VERSION

setup(
	name = 'kiki',
	version = '.'.join([str(v) for v in version]),
	url = "http://github.com/melinath/kiki/",
	description = "An app designed to streamline User-based mailing lists for django.",
	long_description = open(os.path.join(root_dir, 'README.rst')).read(),
	maintainer = "Stephen Burrows",
	maintainer_email = "stephen.r.burrows@gmail.com",
	packages = packages,
	data_files = data_files,
	
	classifiers = [
		'Development Status :: Pre-Alpha',
		'Environment :: Web Environment',
		'Framework :: Django',
		'Intended Audience :: Developers',
		'Intended Audience :: System Administrators',
		'License :: OSI Approved :: BSD License',
		'Operating System :: OS Independent',
		'Programming Language :: Python',
		'Topic :: Communications :: Email',
		'Topic :: Communications :: Email :: Mailing List Servers',

	],
	platforms = ['OS Independent'],
	license = 'BSD License',
	
	install_requires = [
		'django>=1.3',
		'django-celery>=2.3.3'
	],
)
