from setuptools import setup

setup(name="stenotype",
	version="0.1.0",
	packages=["stenotype"],
	entry_points={
		"console_scripts": [
			"stenotype = stenotype.__main__:main"
		]
	},
)
