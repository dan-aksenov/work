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
    
    print "Usage: -d database name, -h database host, -x directory to save xmls, -? display this message"
    print "Example: smev_get_xml.py -d smev -h 172.19.1.127 -x d:/tmp/smev_xml/"
    

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
   
    if not os.path.exists( result_xml_dir ):
            os.makedirs( result_xml_dir )

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

    try:   
        opts, args = getopt( sys.argv[1:], 'd:h:x:?:' )
    except:
        usage()
        sys.exit()

    for opt, arg in opts:
        if opt in ( '-d' ):
            db_name = arg
        elif opt in ( '-h' ):
            db_host = arg
        elif opt in ( '-x' ):
            result_xml_dir = arg
        elif opt in ( '-?' ):
            usage()
        else:
            usage()
            sys.exit()
    
    ''' ���������� ����������� '''
    try:
        db_name
    except:
        db_name = 'smev'

    try:
        db_host
    except:
        db_host = '172.19.1.127'
        
    try:
        result_xml_dir
    except:
       result_xml_dir = 'd:\\tmp\\smev_xml\\'
      
    ''' ����������. �����.'''

    main()