from setuptools import setup, find_packages

setup(
	# Application name:
	name="multiplexor",

	# Version number (initial):
	version="0.0.3",

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
		],
	},
	
	classifiers=(
		"Programming Language :: Python :: 3.7",
		"Operating System :: OS Independent",
	),
)
