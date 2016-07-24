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
Currently bot settings are hardcoded. You can change them by editing eunomia/\_\_main\_\_.py  
Make sure you have activated the Python environment (`source env/bin/activate`).  
Run the bot:  
`python eunomia`  
Remember that the bot only logs to stdout/stderr. I would recommend logging the bot's output to a file, as well as stdout:  
`python eunomia 2>&1 | tee eunomia_log.txt`
