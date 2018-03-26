# for args and exit
import sys
# for ssh connection and ftp transfer.
import paramiko
# for file md5s
import hashlib

# for skype notification
from skpy import Skype

import subprocess
import shutil
import os

class Deal_with_linux:
    def __init__(self):
        self.linux_key_path = 'C:\Users\daniil.aksenov\Documents\ssh\id_rsa.key'
        if os.path.isfile( self.linux_key_path ) != True:
            print "ERROR: Linux ssh key " + self.linux_key_path + " not found!"
            sys.exit()

        # Prepare key for paramiko.
        self.linux_key = paramiko.RSAKey.from_private_key_file( self.linux_key_path )
        # SSH user
        self.ssh_user = 'ansible'
        # SSH port
        self.ssh_port = 22

    def linux_exec(self, linux_host, shell_command ):
        ''' Linux remote execution '''
       
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect( hostname = linux_host, username = self.ssh_user, port = self.ssh_port, pkey = self.linux_key )
        except:
            print '\nERROR: unable to execute on Linux machine!'
            sys.exit()
        stdin, stdout, stderr = client.exec_command( shell_command )
        data = stdout.read() + stderr.read()
        client.close()
        return data

    def linux_put(self, linux_host, source_path, dest_path ):
        ''' Copy to remote Linux '''
           
        transport = paramiko.Transport(( linux_host, self.ssh_port ))
        try:
            transport.connect( username = self.ssh_user, pkey = self.linux_key )
        except:
            print '\nERROR: unable to copy to Linux machine!'
            sys.exit()
        sftp = paramiko.SFTPClient.from_transport( transport )
    
        localpath = source_path
        remotepath = dest_path

        sftp.put( localpath, remotepath )
        sftp.close()
        transport.close()
'''
class Interact_with_Skype:
from skpy import Skype
sk = Skype(username, password) # connect to Skype

sk.user # you
sk.contacts # your contacts
sk.chats # your conversations

ch = sk.chats.create(["joe.4", "daisy.5"]) # new group conversation
ch = sk.contacts["joe.4"].chat # 1-to-1 conversation

ch.sendMsg(content) # plain-text message
ch.sendFile(open("song.mp3", "rb"), "song.mp3") # file upload
ch.sendContact(sk.contacts["daisy.5"]) # contact sharing

ch.getMsgs() # retrieve recent messages
'''

def md5_check( checked_file ):
    ''' *.war file md5 check '''
    
    md5sum = hashlib.md5(open(checked_file,'rb').read()).hexdigest()
    return md5sum

def recreate_dir( dir_name ):
    ''' Recreate Windows directory '''
    
    if os.path.exists( dir_name ):
        shutil.rmtree( dir_name )
    else:
        os.makedirs( dir_name )