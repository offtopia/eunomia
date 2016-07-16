from setuptools import setup

setup(name="eunomia",
	version="0.1.0",
	packages=["eunomia"],
	entry_points={
		"console_scripts": [
			"eunomia = eunomia.__main__:main"
		]
	},
)
