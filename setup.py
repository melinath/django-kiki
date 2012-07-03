#!/usr/bin/env python

from setuptools import setup, find_packages
import os

version = __import__('kiki').__version__

setup(
	name='django-kiki',
	version='.'.join([str(v) for v in version]),
	url="http://github.com/melinath/kiki/",
	description="An app designed to streamline User-based mailing lists for django.",
	long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
	maintainer="Stephen Burrows",
	maintainer_email="stephen.r.burrows@gmail.com",
	packages=find_packages(exclude=('example_project',)),
	include_package_data=True,
	
	classifiers=[
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
	platforms=['OS Independent'],
	license='BSD License',
	
	install_requires=[
		'django>=1.3',
		'django-celery>=2.4.6'
	],
	extras_require = {
		'docs': ["sphinx>=1.0"],
	}
)
