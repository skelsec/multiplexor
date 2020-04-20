from setuptools import setup, find_packages
import re

VERSIONFILE="multiplexor/_version.py"
verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    verstr = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))

setup(
	# Application name:
	name="multiplexor",

	# Version number (initial):
	version=verstr,

	# Application author details:
	author="Tamas Jos",
	author_email="info@skelsec.com",

	# Packages
	packages=find_packages(),

	# Include additional files into the package
	include_package_data=True,


	# Details
	url="https://github.com/skelsec/multiplexor",

	zip_safe = True,
	#
	# license="LICENSE.txt",
	description="multiplexor",

	# long_description=open("README.txt").read(),
	python_requires='>=3.7',
	install_requires=[
		'websockets',
	],

	entry_points={
		'console_scripts': [
			'multiplexor = multiplexor.__main__:main',
			'mpsocks5 = multiplexor.examples.mpsocks5:main',
		],
	},
	
	classifiers=(
		"Programming Language :: Python :: 3.7",
		"Operating System :: OS Independent",
	),
)
