# -*- coding: utf-8 -*-
# Для чтения русских комментов.

# for args and exit
import sys
# for db connection
from psycopg2 import connect
from getopt import getopt

import subprocess
import shutil
import os

''' Внутренние функции. ''' 

def usage():
    '''Функция "Инструкция по пременению" '''
    
    print 'Usage: stuff...'


def postgres_exec( sql_query ):
    ''' Выполенение произвольного sql в базе '''
    
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
    
''' Внутренние функции. Конец. '''
    
def main():
   
    '''
    Поиск и отбор xml.
    '''
    xmls = postgres_exec ( "select t.status, t.operation, t.send_date, t.error, t.message_id, t.original_message_id, t.content,t.sent_response from EXCHANGE_ENDPOINT_LOG t where endpoint_code = 'TEST_SMEV_SUPPLIER' and status in ('ACK_OK','RECEIVED','SENT') order by t.send_date" )
    
    #для каждого из найденных xml - записать в файл с именем вида status_original_message_id.xml

    for i in range(0, len(xmls)):
        # make filename
        out_file = xmls[i][0] + "_"  + xmls[i][5] + ".xml"
        f = open(result_xml_dir + out_file, 'w')
        # Тут нужна обработка null для седьмой позиции
        f.write(xmls[i][6] + '\n' + str(xmls[i][7]))
        f.close()
    
if __name__ == "__main__":
    ''' Переменные. '''
    '''try:    
        opts, args = getopt( sys.argv[1:], 'n:t:h:' )
    except:
        usage()
        sys.exit()

    # Назначение переменных n - patch_num, t - target.
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

    # Имя БД.
    db_name = 'smev'
    # Сервер БД.
    db_host = '172.19.1.127'
    # Директория для временного хранения файлов установки
    result_xml_dir = 'd:\\tmp\\smev_xml\\'
    ''' Переменные. Конец.'''

    main()