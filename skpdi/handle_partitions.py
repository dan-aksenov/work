#!/bin/python
import sys
import subprocess
from psycopg2 import connect

db_host = 'localhost'
db_name = 'ods_predprod'
# keep at least this many partitions
interval = 3
dump_dir = '/usr/local/pgsql/backup/'
remote_dir = '/mnt/nfs/backup/dump/'

def postgres_exec(db_host, db_name, sql_query):
    ''' SQL execution '''
    conn_string = 'dbname= ' + db_name + ' user=''postgres'' host=' + db_host
    try:
        conn = connect(conn_string)
    except:
        print ("\nERROR: unable to connect to the database!")
        print "HINT: Is .pgpass present and correct?"
        sys.exit(1)
    cur = conn.cursor()
    cur.execute(sql_query)
    query_results = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return query_results

get_partitions_sql = '''
select a.drop_name_suffix, 'pg_dump ''' + db_name + ''' -Fc -Z5 --table="'|| string_agg(a.drop_table_name,'" --table="') ||'" --blobs --file="''' + dump_dir + '''events_'||a.drop_name_suffix||'.dmp" &>''' + dump_dir + '''events_dump_'|| a.drop_name_suffix ||'.log'
from
  (select distinct dt.drop_name_suffix,
                   dt.drop_table_name
   from
     (select chld_ns.nspname||'.'||chld.relname as drop_table_name,
             substring(chld.relname,length(prnt.relname||'_')+1,6)::integer as drop_name_suffix
      from pg_inherits pgi
      join pg_class prnt on pgi.inhparent=prnt.oid
      join pg_namespace prnt_ns on prnt.relnamespace=prnt_ns.oid
      join pg_class chld on pgi.inhrelid=chld.oid
      join pg_namespace chld_ns on chld.relnamespace=chld_ns.oid
      where prnt_ns.nspname = 'event'
        and prnt.relname in('fdc_app_log',
                            'fdc_app_log_entity_field',
                            'fdc_app_log_entity')
        and prnt.relkind='r'
        and chld_ns.nspname = 'event'
        and chld.relkind='r' ) dt
   where drop_name_suffix < to_char(date_trunc('month',current_date) - interval ' '''+ str(interval) + ''' ' month,'yyyymm')::integer ) as a
group by a.drop_name_suffix
'''

def main():
    partitions_to_handle = postgres_exec( db_host, db_name, get_partitions_sql)

    # Check if list is no empty of exit
    if not partitions_to_handle:
        print("No partitions to handle. Exiting.")
        sys.exit(0)
    else:
        # Export partitions. Exit if something goes wrong.
        for partition in partitions_to_handle:
            print( "Dumping " + str(partition[0]) + " partition...")  
            if subprocess.call( [ partition[1] ], shell = True ) != 0:
                print( "Unable to dump partition " + str(partition[0]) + ". Exiting.")
                print( "HINT: Check corresponding logfile.")
                sys.exit(1)
            print( "Done.")
            subprocess.call(["cp "+ dump_dir + "events_"+ str(partition[0]) + ".dmp " + remote_dir], shell = True )
        if subprocess.call( ['psql -U ods '+ db_name + ' -c "select event.srv_handle_partitions()"'], shell = True ) != 0:
            print( "Partition handler failed.")
        
if __name__ == '__main__':
    main()
