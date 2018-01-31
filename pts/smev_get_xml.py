# -*- coding: utf-8 -*-
# ��� ������ ������� ���������.

# for args and exit
import sys
# for db connection
from psycopg2 import connect
from getopt import getopt
# ��� ������ ����������� ������
from datetime import datetime, date
import os

''' ���������� �������. ''' 

def usage():
    '''������� "���������� �� ����������" '''
    
    print 'Usage: stuff...'

def postgres_exec( sql_query ):
    ''' ����������� ������������� sql � ���� '''
    
    conn_string = 'dbname= ' + db_name + ' user=''postgres'' password=''postgres'' host=' + db_host
    try:
        conn = connect( conn_string )
    except:
        print '\nERROR: unable to connect to the database!'
        sys.exit()
    cur = conn.cursor()
    cur.execute( sql_query )
    query_results = cur.fetchall()
    cur.close()
    conn.close()
    return query_results
    
''' ���������� �������. �����. '''
    
def main():
   
    '''
    ����� � ����� xml
    '''
    xmls = postgres_exec ( "select t.status, t.operation, t.send_date, t.error, t.message_id, t.original_message_id, t.content,t.sent_response from EXCHANGE_ENDPOINT_LOG t where endpoint_code = 'TEST_SMEV_SUPPLIER' and status in ('ACK_OK','RECEIVED','SENT') order by t.send_date" )
    
    '''
    ������ ��������� xml �������� � ���� ���� original_message_id_status.xml
    '''
    for i in range(0, len(xmls)):
        # ������� ��� �����
        #print (xmls[i][2].date() == datetime.today().date()) 
        # ���������� ��� �������� �� �����
        dir = ( result_xml_dir + str(xmls[i][2].date()) )
        if not os.path.exists( dir ):
            os.makedirs( dir )
        out_file = ( xmls[i][5] + "_" + xmls[i][0] +  ".xml" )
        f = open( dir + "\\" + out_file, 'w' )
        # �������� sent_response,
        # ���� ��������� �� �������� � ��� ����
        if type ( xmls[i][7] ) == str:
            f.write(xmls[i][6] + '\n' + xmls[i][7])
        # ���� ������� - �������� ������ content
        else:
            f.write(xmls[i][6])
        f.close()
    
if __name__ == "__main__":
    ''' ����������. '''
    
    '''
    # ��������� �������� �� ������� �������� - ���� �� ������, ����� ������ ����� �����.
    try:   
        opts, args = getopt( sys.argv[1:], 'n:t:h:' )
    except:
        usage()
        sys.exit()

    for opt, arg in opts:
        if opt in ( '-n' ):
            patch_num = arg
        elif opt in ( '-t' ):
            target = arg
        elif opt in ( '-h' ):
            usage()
        else:
            usage()
            sys.exit()
   '''

    # ��� ��.
    db_name = 'smev'
    # ������ ��.
    db_host = '172.19.1.127'
    # ���������� ��� ���������� �������� ������ ���������
    result_xml_dir = 'd:\\tmp\\smev_xml\\'
    ''' ����������. �����.'''

    main()