# for args and exit
import sys
# for db connection
from psycopg2 import connect
#from os import os.listdir, os.rename, rmdir, os.path, os.makedirs
# for war file search
from glob import glob
from getopt import getopt
# for ssh connection and ftp transfer.
import paramiko
# for file md5s
import hashlib
# for waiting
from time import sleep
# for coloured output
from termcolor import colored

import subprocess
import shutil
import os
import re
import requests

''' Internal functions ''' 

def usage():
    ''' Usage '''
    
    print 'Usage: -n for patch number(i.e. 2.10.1), -t for skpdi or predprod'

def md5_check( checked_file ):
    ''' *.war file md5 check '''
    
    md5sum = hashlib.md5(open(checked_file,'rb').read()).hexdigest()
    return md5sum

def linux_exec( linux_host, shell_command ):
    ''' Linux remote execution '''
       
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect( hostname = linux_host, username = ssh_user, port = ssh_port, pkey = linux_key )
    except:
        print '\nERROR: unable to execute on Linux machine!'
        sys.exit()
    stdin, stdout, stderr = client.exec_command( shell_command )
    data = stdout.read() + stderr.read()
    client.close()
    return data

def linux_put( linux_host, source_path, dest_path ):
    ''' Copy to remote Linux '''
           
    transport = paramiko.Transport(( linux_host, ssh_port ))
    try:
        transport.connect( username = ssh_user, pkey = linux_key )
    except:
        print '\nERROR: unable to copy to Linux machine!'
        sys.exit()
    sftp = paramiko.SFTPClient.from_transport( transport )
    
    localpath = source_path
    remotepath = dest_path

    sftp.put( localpath, remotepath )
    sftp.close()
    transport.close()

def recreate_dir( dir_name ):
    ''' Recreate Windows directory '''
    
    if os.path.exists( dir_name ):
        shutil.rmtree( dir_name )
    else:
        os.makedirs( dir_name )

