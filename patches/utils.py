# for args and exit and os stuff
import sys
import os
import shutil
# for ssh connection and ftp transfer.
import paramiko
# for file md5s
import hashlib
# for postgresql connection
from psycopg2 import connect


class Bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Deal_with_linux:
    def __init__(self):
        self.linux_key_path = os.getenv('HOME') + '\\.ssh\\id_rsa.key'
        if not os.path.isfile(self.linux_key_path):
            print Bcolors.FAIL + "\nERROR: Linux ssh key not found!" + Bcolors.ENDC
            print "HINT: Make sure \"" + self.linux_key_path + "\" exists."
            sys.exit()

        # Prepare key for paramiko.
        self.linux_key = paramiko.RSAKey.from_private_key_file(self.linux_key_path)
        # SSH user
        self.ssh_user = 'ansible'
        # SSH port
        self.ssh_port = 22

    def linux_exec(self, linux_host, shell_command):
        ''' Linux remote execution '''
       
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(hostname = linux_host, username = self.ssh_user, port = self.ssh_port, pkey = self.linux_key)
        except:
            print Bcolors.FAIL + "\nERROR: unable to execute on Linux machine!" + Bcolors.ENDC
            sys.exit()
        stdin, stdout, stderr = client.exec_command(shell_command)
        data = stdout.read() + stderr.read()
        client.close()
        return data

    def linux_put(self, linux_host, source_path, dest_path):
        ''' Copy to remote Linux '''
           
        transport = paramiko.Transport((linux_host, self.ssh_port))
        try:
            transport.connect(username = self.ssh_user, pkey = self.linux_key)
        except:
            print Bcolors.FAIL + "\nERROR: unable to copy to Linux machine!" + Bcolors.ENDC
            sys.exit()
        sftp = paramiko.SFTPClient.from_transport(transport)
    
        localpath = source_path
        remotepath = dest_path

        sftp.put(localpath, remotepath)
        sftp.close()
        transport.close()

    def linux_get(self, linux_host, source_path, dest_path):
        ''' Copy from remote Linux '''
      
        transport = paramiko.Transport((linux_host, self.ssh_port))
        try:
            transport.connect(username = self.ssh_user, pkey = self.linux_key)
        except:
            print Bcolors.FAIL + "\nERROR: unable to copy to Linux machine!" + Bcolors.ENDC
            sys.exit()
        sftp = paramiko.SFTPClient.from_transport(transport)
 
        localpath = source_path
        remotepath = dest_path

        sftp.get(localpath,remotepath)
        sftp.close()
        transport.close()

def md5_check(checked_file):
    ''' *.war file md5 check '''
    
    md5sum = hashlib.md5(open(checked_file,'rb').read()).hexdigest()
    return md5sum

def recreate_dir(dir_name):
    ''' Recreate Windows directory '''
    
    if os.path.exists(dir_name):
        shutil.rmtree(dir_name)
    else:
        os.makedirs(dir_name)

def postgres_exec(db_host, db_name, sql_query):
    ''' SQL execution '''
    
    # pgpass shoule be used insead of password
    conn_string = 'dbname= ' + db_name + ' user=''postgres'' host=' + db_host
    try:
        conn = connect(conn_string)
    except:
        print Bcolors.FAIL + "\nERROR: unable to connect to the database!" + Bcolors.ENDC
        print "HINT: Is .pgpass present and correct?"
        sys.exit()
    cur = conn.cursor()
    cur.execute(sql_query)
    query_results = []
    # This check needed, because delete doesn't return cursor
    if cur.description != None:
        rows = cur.fetchall()
       # Need list of stings instead of tuples for future manipulation.
        for row in rows:
            query_results.append(row[0])
    rowcnt = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return query_results, rowcnt
