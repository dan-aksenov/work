CREATE OR REPLACE PACKAGE EC_MES.RBT_PKG
   AUTHID CURRENT_USER
AS
   PROCEDURE rbt_blk;

   PROCEDURE rbt_load (P_SCHM IN VARCHAR);

   PROCEDURE rbt_sql (p_filename IN VARCHAR2,p_querytype in varchar2);

   PROCEDURE rbt_load_decode (P_SCHM IN VARCHAR);

--v5 release notes:
--PROM_311 excluded

END RBT_PKG;
/

CREATE OR REPLACE PACKAGE BODY EC_MES.RBT_PKG
AS
   PROCEDURE rbt_blk
   AS
      v_jbname   VARCHAR2 (50);
      v_err      VARCHAR2 (2000);
      --v_cnt      NUMBER;
      v_jb       number;
      v_cnt      NUMBER;
      v_start    DATE;
   /* cursor c1 is
    select count(*) into v_jb from dba_scheduler_jobs where owner = 'EC_MES' and job_name like '%PROM%';*/
   
   -- Версия_2 --
   
   BEGIN
      --clear logs
      DELETE FROM load_log
            WHERE dt_start < SYSDATE - 60;

      DELETE FROM err_log
            WHERE dt < SYSDATE - 60;

      COMMIT;

      FOR i
         IN (SELECT r.nm_schema
               FROM all_users u, prom_nsi.prom_region r
              WHERE     username LIKE 'PROM%'
                    AND u.username = r.nm_schema
                    AND username <> 'PROM_311')
      LOOP
         --ensure that number of simultaneous jobs is not more then 10
         SELECT COUNT (*)
           INTO v_cnt
           FROM all_scheduler_jobs
          WHERE owner = 'EC_MES' AND job_name LIKE 'RBT_BLK%';

         IF v_cnt > 10
         THEN
            DBMS_LOCK.sleep (10);
         END IF;

         BEGIN
            v_jbname := 'EC_MES.RBT_BLK_' || i.nm_schema;
            --dbms_output.put_line (v_jbname);
            DBMS_SCHEDULER.CREATE_JOB (
               job_name              => v_jbname,
               job_type              => 'STORED_PROCEDURE',
               job_action            => 'EC_MES.RBT_PKG.RBT_LOAD',
               number_of_arguments   => 1,
               start_date            => NULL,
               repeat_interval       => NULL,
               end_date              => NULL,
               enabled               => FALSE,
               auto_drop             => TRUE,
               comments              => '');
            DBMS_SCHEDULER.SET_JOB_ARGUMENT_VALUE (
               job_name            => v_jbname,
               argument_position   => 1,
               argument_value      => i.nm_schema);
            DBMS_SCHEDULER.SET_ATTRIBUTE (
               name        => v_jbname,
               attribute   => 'logging_level',
               VALUE       => DBMS_SCHEDULER.LOGGING_OFF);
            DBMS_SCHEDULER.enable (name => v_jbname);
         EXCEPTION
            WHEN OTHERS
            THEN
               --dbms_output.put_line (SQLERRM);
               v_err := SQLERRM;

               INSERT INTO err_log
                    VALUES (SYSDATE,
                            $$PLSQL_UNIT,
                            i.nm_schema,
                            v_err,
                            0);

               COMMIT;
         END;

         BEGIN
            v_jbname := 'EC_MES.RBT_BLK_DECODE_' || i.nm_schema;
            --dbms_output.put_line (v_jbname);
            DBMS_SCHEDULER.CREATE_JOB (
               job_name              => v_jbname,
               job_type              => 'STORED_PROCEDURE',
               job_action            => 'EC_MES.RBT_PKG.RBT_LOAD_DECODE',
               number_of_arguments   => 1,
               start_date            => NULL,
               repeat_interval       => NULL,
               end_date              => NULL,
               enabled               => FALSE,
               auto_drop             => TRUE,
               comments              => '');
            DBMS_SCHEDULER.SET_JOB_ARGUMENT_VALUE (
               job_name            => v_jbname,
               argument_position   => 1,
               argument_value      => i.nm_schema);
            DBMS_SCHEDULER.SET_ATTRIBUTE (
               name        => v_jbname,
               attribute   => 'logging_level',
               VALUE       => DBMS_SCHEDULER.LOGGING_OFF);
            DBMS_SCHEDULER.enable (name => v_jbname);
         EXCEPTION
            WHEN OTHERS
            THEN
               --dbms_output.put_line (SQLERRM);
               v_err := SQLERRM;

               INSERT INTO err_log
                    VALUES (SYSDATE,
                            $$PLSQL_UNIT,
                            i.nm_schema,
                            v_err,0);

               COMMIT;
         END;
      END LOOP;
      
      BEGIN
      --DELETE ASKUE dubles section
       select count(*) into v_jb from all_scheduler_jobs where owner = 'EC_MES' and job_name like '%RBT_BLK%PROM%';
       while v_jb > 0
       loop
       dbms_lock.sleep(5);
       select count(*) into v_jb from all_scheduler_jobs where owner = 'EC_MES' and job_name like '%RBT_BLK%PROM%';
       end loop;
       
       v_start := SYSDATE;
       
       DELETE FROM Q_COUNTERS_TMP
             WHERE KD_ASKUE IN (  SELECT KD_ASKUE
                                    FROM Q_COUNTERS_TMP
                                GROUP BY KD_ASKUE
                                  HAVING COUNT (*) > 1)
                and PR_TRANSIT=1;
       
       v_cnt:= sql%rowcount;
       --dbms_output.put_line ('ASKUE DBLs deleted '||sql%rowcount);
       
       COMMIT;

       INSERT INTO EC_MES.LOAD_LOG
           VALUES (v_start,
                   SYSDATE,
                   'ALL',--v_schm,
                   'ASKUE',
                   NULL,
                   v_cnt);
                   
                   
                   
        
       delete from  Q_COUNTERS_NEW where NM_SCHEMA in (select distinct NM_SCHEMA from Q_COUNTERS_TMP);  -- Добавил условие (Винокуров А.М.)
       insert into Q_COUNTERS_NEW select * from Q_COUNTERS_TMP;
       delete from  Q_COUNTERS_TMP;
       commit;
       
       
      EXCEPTION
            WHEN OTHERS
            THEN
               --dbms_output.put_line (SQLERRM);
               v_err := SQLERRM;

               INSERT INTO err_log
                    VALUES (SYSDATE,
                            $$PLSQL_UNIT,
                            'ALL',
                            v_err,0);

               COMMIT;
      END;
      COMMIT;
   END rbt_blk;

   PROCEDURE RBT_LOAD (P_SCHM IN VARCHAR)
   IS
      v_schm     VARCHAR (20);
      v_nmrows   NUMBER;
      v_dubl     NUMBER;
      v_start    DATE;
      v_err      VARCHAR2 (2000);
      v_sql      CLOB;
      lvl_err    NUMBER;
   BEGIN
      v_schm := P_SCHM;

      --dbms_output.put_line (v_schm);

      --get actual query from sql_store
      lvl_err:=1;
      SELECT sql_query
        INTO v_sql
        FROM SQL_STORE
       WHERE NM_QUERY = 'Q_COUNTERS';
      lvl_err:=2;
      EXECUTE IMMEDIATE 'alter session set current_schema=' || v_schm;
      lvl_err:=3;
      v_start := SYSDATE;
      lvl_err:=4;
      -- "schema hint" added to prevent contention (cursor pin S wait on X)
      EXECUTE IMMEDIATE
            'INSERT INTO EC_MES.Q_COUNTERS_TMP select /*+'
         || v_schm
         || '*/ * from ('
         || v_sql
         || ')';
      lvl_err:=5;
      --dbms_output.put_line ('inserted '||sql%rowcount);
      EXECUTE IMMEDIATE 'alter session set current_schema=EC_MES';
      lvl_err:=6;
      --delete duplicates
      DELETE FROM Q_COUNTERS_TMP
            WHERE ROWID NOT IN (  SELECT MIN (ROWID)
                                    FROM Q_COUNTERS_TMP
                                GROUP BY ID_ABN,
                                         ID_TU,
                                         DT_PERIOD,
                                         KD_ASKUE,
                                         PR_TRANSIT)
                and nm_schema = v_schm;
     
      v_dubl := SQL%ROWCOUNT;
      lvl_err:=7;
      -- askue dubles moved to rbt_blk
      DELETE FROM Q_COUNTERS_TMP
            WHERE KD_ASKUE IN (  SELECT KD_ASKUE
                                   FROM Q_COUNTERS_TMP
                               GROUP BY KD_ASKUE, PR_TRANSIT
                                 HAVING COUNT (*) > 1)
            and nm_schema = v_schm; --dbms_output.put_line ('dubl deleted '||sql%rowcount);
/*    
      --delete previous data from Q_COUNTERS
      DELETE FROM Q_COUNTERS_NEW
            WHERE nm_schema = v_schm;

      --dbms_output.put_line ('previous deleted '||sql%rowcount);

      --insert final data to Q_COUNTERS
      INSERT INTO Q_COUNTERS_NEW
         SELECT * FROM Q_COUNTERS_TMP;
*/
      --dbms_output.put_line ('consolidate inserted '||sql%rowcount);
      v_nmrows := SQL%ROWCOUNT;
      --dbms_output.put_line (v_nmrows);
      COMMIT;
      lvl_err:=9;
      --logging section
      INSERT INTO EC_MES.LOAD_LOG
           VALUES (v_start,
                   SYSDATE,
                   v_schm,
                   'Q_COUNTERS',
                   v_nmrows,
                   v_dubl);

      COMMIT;
   EXCEPTION
      WHEN OTHERS
      THEN
         --dbms_output.put_line (SQLERRM);
         v_err := SQLERRM;

         INSERT INTO EC_MES.ERR_LOG
              VALUES (SYSDATE,
                      $$PLSQL_UNIT,
                      v_schm,
                      lvl_err||' '||v_err,0);

         COMMIT;
   END RBT_LOAD;

   PROCEDURE RBT_LOAD_DECODE (P_SCHM IN VARCHAR)
   IS
      v_schm     VARCHAR (20);
      v_tb       VARCHAR2 (50);
      v_nmrows   NUMBER;
      v_dubl     NUMBER;
      v_start    DATE;
      v_err      VARCHAR2 (2000);
      v_sql      CLOB;
   BEGIN
      v_schm := P_SCHM;

      --DBMS_OUTPUT.put_line (v_schm);

      SELECT sql_query
        INTO v_sql
        FROM SQL_STORE
       WHERE NM_QUERY = 'POK_ZONE_DECODE';

      EXECUTE IMMEDIATE 'alter session set current_schema=' || v_schm;

      v_start := SYSDATE;

      EXECUTE IMMEDIATE
            'INSERT INTO EC_MES.POK_ZONE_DECODE_TMP select /*+'
         || v_schm
         || '*/ * from ('
         || v_sql
         || ')';

      EXECUTE IMMEDIATE 'alter session set current_schema=EC_MES';

      DELETE FROM POK_ZONE_DECODE
            WHERE nm_schema = v_schm;

      INSERT INTO POK_ZONE_DECODE
         SELECT * FROM POK_ZONE_DECODE_TMP;

      v_nmrows := SQL%ROWCOUNT;

      COMMIT;

      INSERT INTO EC_MES.load_log                    -- добавить имя таблицы ?
           VALUES (v_start,
                   SYSDATE,
                   v_schm,
                   'POK_ZONE_DECODE',
                   v_nmrows,
                   v_dubl);

      COMMIT;
   EXCEPTION
      WHEN OTHERS
      THEN
         v_err := SQLERRM;

         INSERT INTO EC_MES.err_log
              VALUES (SYSDATE,                       -- добавить имя таблицы ?
                      $$PLSQL_UNIT,
                      v_schm,
                      v_err,0);

         COMMIT;
   END RBT_LOAD_DECODE;

   PROCEDURE RBT_SQL (p_filename IN VARCHAR2, p_querytype IN VARCHAR2)
   IS
      l_clob      CLOB;
      l_bfile     BFILE;
      l_nmquery   VARCHAR2 (200);
   BEGIN
      l_nmquery := p_querytype;

      --invalidate previous queries
      DELETE FROM sql_store
            WHERE NM_QUERY = l_nmquery;

      COMMIT;

      --insert new query
      INSERT INTO EC_MES.sql_store (nm_query, dt_load, sql_query)
           VALUES (l_nmquery, SYSDATE, EMPTY_CLOB ())
        RETURNING sql_query
             INTO l_clob;

      l_bfile := BFILENAME ('DIR_TII', p_filename);
      DBMS_LOB.fileopen (l_bfile);
      DBMS_LOB.loadfromfile (l_clob, l_bfile, DBMS_LOB.getlength (l_bfile));
      DBMS_LOB.fileclose (l_bfile);
      COMMIT;
   EXCEPTION
      WHEN OTHERS
      THEN
         DBMS_OUTPUT.put_line (SQLERRM);
   END rbt_sql;
END RBT_PKG;
/
