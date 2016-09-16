# eunomia
A bot that logs legislations and caches them for reviewing.

## Installation
### Download
`git clone https://github.com/osdev-offtopic/eunomia.git && cd eunomia`
### Set up Python virtualenv
Initialize environment:  
`virtualenv --python=python3 env`  

Activate the environment:  
`source env/bin/activate`  
<b>NOTE:</b> The activation only works as long as the shell instance is alive, so you will need to `source env/bin/activate` every time you spawn a new shell.  

Install requirements:  
`pip install -r requirements.txt`

## Running
**Note:** All config options are in `eunomia.ini`. Please read the in-file comments for a description of what each section/option does.  

Make sure you have activated the Python environment (`source env/bin/activate`).  
Run the bot:  
`python eunomia`  

All internal bot output is also appended to eunomia.log.  
Channel logs can be found in `logs/channel/[channel name]/date.log`.  
Proposal logs are located in `logs/proposal/[channel name]/date_time.log`

## Documentation
Documentation is automatically generated from docstrings with Sphinx.  
To generate documentation:
Change to the docs dir:  
`cd docs/`  
Generate the documentation:  
`make html`
Open 'docs/_build/html/index.html' in a browser.
