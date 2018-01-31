# -*- coding: utf-8 -*-
# Для чтения русских комментов.

# for args and exit
import sys
# for db connection
from psycopg2 import connect
from getopt import getopt
# Для поиска сегоднешних файлов
from datetime import datetime, date
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
    Поиск и отбор xml
    '''
    xmls = postgres_exec ( "select t.status, t.operation, t.send_date, t.error, t.message_id, t.original_message_id, t.content,t.sent_response from EXCHANGE_ENDPOINT_LOG t where endpoint_code = 'TEST_SMEV_SUPPLIER' and status in ('ACK_OK','RECEIVED','SENT') order by t.send_date" )
    
    '''
    Каждый найденный xml запивать в файл вида original_message_id_status.xml
    '''
    for i in range(0, len(xmls)):
        # Создаем имя файла
        #print (xmls[i][2].date() == datetime.today().date()) 
        # Директории для разбивки по датам
        dir = ( result_xml_dir + str(xmls[i][2].date()) )
        if not os.path.exists( dir ):
            os.makedirs( dir )
        out_file = ( xmls[i][5] + "_" + xmls[i][0] +  ".xml" )
        f = open( dir + "\\" + out_file, 'w' )
        # Проверка sent_response,
        # если ненулевой то записать и его тоже
        if type ( xmls[i][7] ) == str:
            f.write(xmls[i][6] + '\n' + xmls[i][7])
        # если нулевой - записать только content
        else:
            f.write(xmls[i][6])
        f.close()
    
if __name__ == "__main__":
    ''' Переменные. '''
    
    '''
    # Параметры остались от другого скрпипта - пока не удалаю, может потому нужно будет.
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

    # Имя БД.
    db_name = 'smev'
    # Сервер БД.
    db_host = '172.19.1.127'
    # Директория для временного хранения файлов установки
    result_xml_dir = 'd:\\tmp\\smev_xml\\'
    ''' Переменные. Конец.'''

    main()