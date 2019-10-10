from setuptools import setup, find_packages

setup(
	# Application name:
	name="multiplexor",

	# Version number (initial):
	version="0.0.1",

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
	#install_requires=[
	#	'minikerberos>=0.0.10',
	#	'winsspi>=0.0.2',
	#	'six',
	#],
	
	classifiers=(
		"Programming Language :: Python :: 3.7",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
	),
)
