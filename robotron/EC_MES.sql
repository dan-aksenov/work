Set define off

spoo ./ec_mes.log

drop user ec_mes cascade;
--
-- EC_MES  (User) 
--
CREATE USER EC_MES
  IDENTIFIED BY EC_MES
  ;
  GRANT CONNECT TO EC_MES;
  GRANT RESOURCE TO EC_MES;
  ALTER USER EC_MES DEFAULT ROLE ALL;
  GRANT CREATE JOB TO EC_MES;
  GRANT CREATE SESSION TO EC_MES;
  GRANT CREATE SYNONYM TO EC_MES;
  GRANT UNLIMITED TABLESPACE TO EC_MES;
    GRANT SELECT ON SYS.ALL_TABLES TO EC_MES;
    GRANT SELECT ON SYS.DBA_SCHEDULER_JOBS TO EC_MES;
    GRANT SELECT ON SYS.DBA_USERS TO EC_MES;
    --GRANT READ ON DIRECTORY DIR_TII TO EC_MES;

--grants on required PROM tables
begin
for i in (
select * from dba_OBJECTS where OBJECT_type IN ('TABLE','VIEW') AND regexp_like(owner,'^PROM_[0-9]{2,3}') and OBJECT_name in (
'PROM_ABONENT',
'PROM_CONPOINT',
'PROM_OTDEL',
'PROM_WORK',                                                                    
'PROM_CHARGE',                                                                              
'PROM_DOGOVOR_STATUS_HIST',
'PROM_TU_GROUP_CP',
 'PROM_VEDOMOST',
 'PROM_CONPOINT_HIST',                                                                             
 'PROM_TU_HIST',                                                                              
 'PROM_REESTR',                                                                                  
 'PROM_SUBABONENT_HIST',                                                                 
 'PROM_TU_GROUP',                                                                                     
 'PROM_TU_GROUP_ASSIGN',                                                                   
 'PROM_SUBABONENT',
 'PROM_SCHEMA',
 'PROM_TU',
 'PROM_POK',
 'PROM_PERIOD',
 'PROM_EDEVICE_TU',
 'PROM_SCHETCH',
 'PROM_TU_GROUP_TARIFF',
 'SEQ_PROM_VEDOMOST')
)  
loop
BEGIN
execute immediate 'grant select,insert,delete,update on '||i.OWNER||'.'||i.OBJECT_NAME||' to EC_MES';
EXCEPTION WHEN OTHERS THEN DBMS_OUTPUT.PUT_LINE(SQLERRM);
END;
end loop;
end;
/

begin
for i in (
select * from dba_OBJECTS where OBJECT_type IN ('SEQUENCE') AND regexp_like(owner,'^PROM_[0-9]{2,3}') and OBJECT_name in (
 'SEQ_PROM_VEDOMOST','SEQ_PROM_POK')
)  
loop
BEGIN
execute immediate 'grant select on '||i.OWNER||'.'||i.OBJECT_NAME||' to EC_MES';
EXCEPTION WHEN OTHERS THEN DBMS_OUTPUT.PUT_LINE(SQLERRM);
END;
end loop;
end;
/

grant select on prom_nsi.prom_tp_rasch to EC_MES;                                                              
grant select on prom_nsi.prom_volt_lvl to EC_MES;                                                                      
grant select on prom_nsi.prom_tp_tu to EC_MES;                                                                      
grant select on prom_nsi.prom_schetch_mod to EC_MES;     

--
-- ERR_LOG  (Table) 
--

CREATE TABLE EC_MES.ERR_LOG
(
  DT            DATE,
  PROC_NAME     VARCHAR2(50 BYTE),
  SCHM_NAME     VARCHAR2(50 BYTE),
  ERR_MSG       VARCHAR2(2000 BYTE),
  ACKNOWLEDGED  NUMBER                          DEFAULT 0
)
;


--
-- LOAD_LOG  (Table) 
--
CREATE TABLE EC_MES.LOAD_LOG
(
  DT_START    DATE,
  DT_FINISH   DATE,
  NM_SCHEMA   VARCHAR2(20 BYTE),
  TABLE_NAME  VARCHAR2(200 BYTE),
  ROWS_INS    NUMBER,
  DUBLS_DEL   NUMBER
)
;

--
-- POK_ZONE_DECODE  (Table) 
--

CREATE TABLE EC_MES.POK_ZONE_DECODE
(
  NM_SCHEMA    VARCHAR2(20 BYTE),
  KD_ASKUE     VARCHAR2(200 BYTE),
  KD_POK_ZONE  NUMBER,
  KD_ZONE_TP   NUMBER
)
;


--
-- POK_ZONE_DECODE_TMP  (Table) 
--
CREATE GLOBAL TEMPORARY TABLE EC_MES.POK_ZONE_DECODE_TMP
(
  NM_SCHEMA    VARCHAR2(20 BYTE),
  KD_ASKUE     VARCHAR2(200 BYTE),
  KD_POK_ZONE  NUMBER,
  KD_ZONE_TP   NUMBER
)
ON COMMIT DELETE ROWS
;


--
-- Q_COUNTERS_NEW  (Table) 
--
CREATE TABLE EC_MES.Q_COUNTERS_NEW
(
  NM_SCHEMA          VARCHAR2(10 BYTE),
  DT_PERIOD          DATE,
  NN_ABN             NUMBER,
  DT_WORK            DATE,
  KD_WORK            NUMBER,
  NM_TU              VARCHAR2(100 BYTE),
  PR_TU_POWER        NUMBER(1)                  NOT NULL,
  TU_STATE           VARCHAR2(12 BYTE),
  ID_ABN             NUMBER(9)                  NOT NULL,
  ID_TU              NUMBER                     NOT NULL,
  NN_SCH             VARCHAR2(50 BYTE)          NOT NULL,
  VOLT_LVL           VARCHAR2(20 BYTE),
  NM_TP_TU           VARCHAR2(50 BYTE),
  VL_RAS_KOEFF       NUMBER(9),
  VL_ZNACH           NUMBER(3,1)                NOT NULL,
  VL_LOSS_PRC        NUMBER,
  NM_TP_RASCH        VARCHAR2(30 BYTE),
  KD_VOLT_LVL        NUMBER(3)                  NOT NULL,
  KD_TU_STATUS       NUMBER                     NOT NULL,
  VL_KOEF            NUMBER(1),
  ID_ABN_PRIMARY     NUMBER(9)                  NOT NULL,
  NN_TU_GROUP        NUMBER(5)                  NOT NULL,
  PR_DATACHECK       NUMBER,
  KD_SUBABONENT      NUMBER                     NOT NULL,
  ID_SCHET           NUMBER(9)                  NOT NULL,
  DT_TU_STATUS       DATE                       NOT NULL,
  KD_ASKUE           VARCHAR2(200 BYTE),
  PR_TRANSIT         NUMBER,
  NET_ASKUE          NUMBER,
  PR_KOEF_TRANSFORM  NUMBER
)
;


--
-- Q_COUNTERS_TMP  (Table) 
--
CREATE GLOBAL TEMPORARY TABLE EC_MES.Q_COUNTERS_TMP
(
  NM_SCHEMA          VARCHAR2(10 BYTE),
  DT_PERIOD          DATE,
  NN_ABN             NUMBER,
  DT_WORK            DATE,
  KD_WORK            NUMBER,
  NM_TU              VARCHAR2(100 BYTE),
  PR_TU_POWER        NUMBER(1)                  NOT NULL,
  TU_STATE           VARCHAR2(12 BYTE),
  ID_ABN             NUMBER(9)                  NOT NULL,
  ID_TU              NUMBER                     NOT NULL,
  NN_SCH             VARCHAR2(50 BYTE)          NOT NULL,
  VOLT_LVL           VARCHAR2(20 BYTE),
  NM_TP_TU           VARCHAR2(50 BYTE),
  VL_RAS_KOEFF       NUMBER(9),
  VL_ZNACH           NUMBER(3,1)                NOT NULL,
  VL_LOSS_PRC        NUMBER,
  NM_TP_RASCH        VARCHAR2(30 BYTE),
  KD_VOLT_LVL        NUMBER(3)                  NOT NULL,
  KD_TU_STATUS       NUMBER                     NOT NULL,
  VL_KOEF            NUMBER(1),
  ID_ABN_PRIMARY     NUMBER(9)                  NOT NULL,
  NN_TU_GROUP        NUMBER(5)                  NOT NULL,
  PR_DATACHECK       NUMBER,
  KD_SUBABONENT      NUMBER                     NOT NULL,
  ID_SCHET           NUMBER(9)                  NOT NULL,
  DT_TU_STATUS       DATE                       NOT NULL,
  KD_ASKUE           VARCHAR2(200 BYTE),
  PR_TRANSIT         NUMBER,
  NET_ASKUE          NUMBER,
  PR_KOEF_TRANSFORM  NUMBER
)
ON COMMIT DELETE ROWS
;


--
-- SQL_STORE  (Table) 
--
CREATE TABLE EC_MES.SQL_STORE
(
  NM_QUERY   VARCHAR2(200 BYTE),
  DT_LOAD    DATE,
  SQL_QUERY  CLOB
)
;

--
-- Q_COUNTERS_NEW_IDX2  (Index) 
--
CREATE INDEX EC_MES.Q_COUNTERS_NEW_IDX2 ON EC_MES.Q_COUNTERS_NEW
(KD_ASKUE)
;


--
-- Q_COUNTERS_NEW_IDX3  (Index) 
--
CREATE INDEX EC_MES.Q_COUNTERS_NEW_IDX3 ON EC_MES.Q_COUNTERS_NEW
(NM_SCHEMA)
;


--
-- Q_COUNTERS_NEW_KEY  (Index) 
--
CREATE UNIQUE INDEX EC_MES.Q_COUNTERS_NEW_KEY ON EC_MES.Q_COUNTERS_NEW
(DT_PERIOD, PR_TRANSIT, ID_ABN, ID_TU, KD_ASKUE)
;


--
-- RBT_PKG  (Package) 
--
@package.sql


--CREATE OR REPLACE PACKAGE EC_MES.RBT_PKG
--   AUTHID CURRENT_USER
--AS
--   PROCEDURE rbt_blk;
--
--   PROCEDURE rbt_load (P_SCHM IN VARCHAR);
--
--   PROCEDURE rbt_sql (p_filename IN VARCHAR2,p_querytype in varchar2);
--   
--   PROCEDURE rbt_load_decode (P_SCHM IN VARCHAR);
--END RBT_PKG;
--/
--
----
---- RBT_PKG  (Package Body) 
----
--CREATE OR REPLACE PACKAGE BODY EC_MES.RBT_PKG
--AS
--   PROCEDURE rbt_blk
--   AS
--      v_jbname   VARCHAR2 (50);
--      v_err      VARCHAR2 (2000);
--   BEGIN
--      --clear logs
--      DELETE FROM EC_MES.load_log
--            WHERE dt_start < SYSDATE - 60;
--
--      DELETE FROM EC_MES.err_log
--            WHERE dt < SYSDATE - 60;
--
--      COMMIT;
--
--      FOR i IN (SELECT r.nm_schema
--                  FROM dba_users u, prom_nsi.prom_region r
--                 WHERE username LIKE 'PROM%' AND u.username = r.nm_schema)
--      LOOP
--         BEGIN
--            v_jbname := 'EC_MES.RBT_BLK_' || i.nm_schema;
--            --dbms_output.put_line (v_jbname);
--            DBMS_SCHEDULER.CREATE_JOB (
--               job_name              => v_jbname,
--               job_type              => 'STORED_PROCEDURE',
--               job_action            => 'EC_MES.RBT_PKG.RBT_LOAD',
--               number_of_arguments   => 1,
--               start_date            => NULL,
--               repeat_interval       => NULL,
--               end_date              => NULL,
--               enabled               => FALSE,
--               auto_drop             => TRUE,
--               comments              => '');
--            DBMS_SCHEDULER.SET_JOB_ARGUMENT_VALUE (
--               job_name            => v_jbname,
--               argument_position   => 1,
--               argument_value      => i.nm_schema);
--            DBMS_SCHEDULER.SET_ATTRIBUTE (
--               name        => v_jbname,
--               attribute   => 'logging_level',
--               VALUE       => DBMS_SCHEDULER.LOGGING_OFF);
--            DBMS_SCHEDULER.enable (name => v_jbname);
--                  
--         EXCEPTION
--            WHEN OTHERS
--            THEN
--               dbms_output.put_line (SQLERRM);
--                dbms_output.put_line ( 'Error_Stack...' || DBMS_UTILITY.FORMAT_ERROR_STACK() );
--                dbms_output.put_line ( 'Error_Backtrace...' ||  DBMS_UTILITY.FORMAT_ERROR_BACKTRACE() );
--               v_err := SQLERRM;
--
--               INSERT INTO err_log
--                    VALUES (SYSDATE,
--                            $$PLSQL_UNIT,
--                            i.nm_schema,
--                            v_err);
--
--               COMMIT;
--         END;
--         
--         BEGIN
--            v_jbname := 'EC_MES.RBT_BLK_DECODE_' || i.nm_schema;
--            --dbms_output.put_line (v_jbname);
--            DBMS_SCHEDULER.CREATE_JOB (
--               job_name              => v_jbname,
--               job_type              => 'STORED_PROCEDURE',
--               job_action            => 'EC_MES.RBT_PKG.RBT_LOAD_DECODE',
--               number_of_arguments   => 1,
--               start_date            => NULL,
--               repeat_interval       => NULL,
--               end_date              => NULL,
--               enabled               => FALSE,
--               auto_drop             => TRUE,
--               comments              => '');
--            DBMS_SCHEDULER.SET_JOB_ARGUMENT_VALUE (
--               job_name            => v_jbname,
--               argument_position   => 1,
--               argument_value      => i.nm_schema);
--            DBMS_SCHEDULER.SET_ATTRIBUTE (
--               name        => v_jbname,
--               attribute   => 'logging_level',
--               VALUE       => DBMS_SCHEDULER.LOGGING_OFF);
--            DBMS_SCHEDULER.enable (name => v_jbname);
--         EXCEPTION
--            WHEN OTHERS
--            THEN
--               dbms_output.put_line (SQLERRM);
--                   dbms_output.put_line ( 'Error_Stack...' || DBMS_UTILITY.FORMAT_ERROR_STACK() );
--                dbms_output.put_line ( 'Error_Backtrace...' ||  DBMS_UTILITY.FORMAT_ERROR_BACKTRACE() );
--               v_err := SQLERRM;
--
--               INSERT INTO err_log
--                    VALUES (SYSDATE,
--                            $$PLSQL_UNIT,
--                            i.nm_schema,
--                            v_err);
--
--               COMMIT;
--         END;
--         
--      END LOOP;
--   END rbt_blk;
--
--   PROCEDURE RBT_LOAD (P_SCHM IN VARCHAR)
--   IS
--      v_schm     VARCHAR (20);
--      v_nmrows   NUMBER;
--      v_dubl     NUMBER;
--      v_start    DATE;
--      v_err      VARCHAR2 (2000);
--      v_sql      CLOB;
--   BEGIN
--      v_schm := P_SCHM;
--
--      --dbms_output.put_line (v_schm);
--     
--      --get actual query from sql_store
--      SELECT sql_query
--        INTO v_sql
--        FROM SQL_STORE
--       WHERE NM_QUERY = 'Q_COUNTERS';
--
--      EXECUTE IMMEDIATE 'alter session set current_schema=' || v_schm;
--
--      v_start := SYSDATE;
--
--      -- "schema hint" added to prevent contention (cursor pin S wait on X)
--      EXECUTE IMMEDIATE
--            'INSERT INTO EC_MES.Q_COUNTERS_TMP select /*+'
--         || v_schm
--         || '*/ * from ('
--         || v_sql
--         || ')';
--
--      --dbms_output.put_line ('inserted '||sql%rowcount);
--      EXECUTE IMMEDIATE 'alter session set current_schema=EC_MES';
--
--      --delete duplicates
--      DELETE FROM Q_COUNTERS_TMP
--            WHERE ROWID NOT IN (  SELECT MIN (ROWID)
--                                    FROM Q_COUNTERS_TMP
--                                GROUP BY ID_ABN,
--                                         ID_TU,
--                                         DT_PERIOD,
--                                         KD_ASKUE,
--                                         PR_TRANSIT
--                                         );
--
--      v_dubl := SQL%ROWCOUNT;
--
--      -- delete some trash (which one?)
--      DELETE FROM Q_COUNTERS_TMP
--            WHERE KD_ASKUE IN (  SELECT KD_ASKUE
--                                   FROM Q_COUNTERS_TMP
--                               GROUP BY KD_ASKUE, PR_TRANSIT
--                                 HAVING COUNT (*) > 1); --dbms_output.put_line ('dubl deleted '||sql%rowcount);
--
--      --delete previous data from Q_COUNTERS
--      DELETE FROM Q_COUNTERS_NEW
--            WHERE nm_schema = v_schm;
--
--      --dbms_output.put_line ('previous deleted '||sql%rowcount);
--
--      --insert final data to Q_COUNTERS
--      INSERT INTO Q_COUNTERS_NEW
--         SELECT * FROM Q_COUNTERS_TMP;
--      --dbms_output.put_line ('consolidate inserted '||sql%rowcount);
--      v_nmrows := SQL%ROWCOUNT;
--      --dbms_output.put_line (v_nmrows);
--      COMMIT;
--
--      --logging section
--      INSERT INTO EC_MES.LOAD_LOG
--           VALUES (v_start,
--                   SYSDATE,
--                   v_schm,
--                   'Q_COUNTERS',
--                   v_nmrows,
--                   v_dubl);
--      COMMIT;
--      
--   EXCEPTION
--      WHEN OTHERS
--      THEN
--         dbms_output.put_line (SQLERRM);
--             dbms_output.put_line ( 'Error_Stack...' || DBMS_UTILITY.FORMAT_ERROR_STACK() );
--dbms_output.put_line ( 'Error_Backtrace...' ||  DBMS_UTILITY.FORMAT_ERROR_BACKTRACE() );
--         v_err := SQLERRM;
--
--         INSERT INTO EC_MES.ERR_LOG
--              VALUES (SYSDATE,
--                      $$PLSQL_UNIT,
--                      v_schm,
--                      v_err);
--
--         COMMIT;
--   END RBT_LOAD;
--   
--   PROCEDURE RBT_LOAD_DECODE (P_SCHM IN VARCHAR)
--   IS
--      v_schm     VARCHAR (20);
--      v_tb       VARCHAR2 (50);
--      v_nmrows   NUMBER;
--      v_dubl     NUMBER;
--      v_start    DATE;
--      v_err      VARCHAR2 (2000);
--      v_sql      CLOB;
--   BEGIN
--      v_schm := P_SCHM;
--      --DBMS_OUTPUT.put_line (v_schm);
--
--       SELECT sql_query
--        INTO v_sql
--        FROM SQL_STORE
--       WHERE NM_QUERY = 'POK_ZONE_DECODE';
--
--      EXECUTE IMMEDIATE 'alter session set current_schema=' || v_schm;
--       
--      v_start := SYSDATE;
--
--      EXECUTE IMMEDIATE
--         'INSERT INTO EC_MES.POK_ZONE_DECODE_TMP select /*+'
--         || v_schm
--         || '*/ * from ('
--         || v_sql
--         || ')';
--
--      EXECUTE IMMEDIATE 'alter session set current_schema=EC_MES';
--
--      DELETE FROM POK_ZONE_DECODE
--            WHERE nm_schema = v_schm;
--
--      INSERT INTO POK_ZONE_DECODE SELECT * FROM POK_ZONE_DECODE_TMP;
--
--      v_nmrows := SQL%ROWCOUNT;
--
--      COMMIT;
--
--      INSERT INTO EC_MES.load_log -- добавить имя таблицы ?
--           VALUES (v_start,
--                   SYSDATE,
--                   v_schm,
--                   'POK_ZONE_DECODE',
--                   v_nmrows,
--                   v_dubl);
--
--      COMMIT;
--   EXCEPTION
--      WHEN OTHERS
--      THEN
--         v_err := SQLERRM;
--
--         INSERT INTO EC_MES.err_log
--              VALUES (SYSDATE, -- добавить имя таблицы ?
--                      $$PLSQL_UNIT,
--                      v_schm,
--                      v_err);
--
--         COMMIT;
--   END RBT_LOAD_DECODE;
--
--   PROCEDURE RBT_SQL (p_filename IN VARCHAR2, p_querytype in varchar2)
--   IS
--      l_clob    CLOB;
--      l_bfile   BFILE;
--      l_nmquery varchar2(200);
--   BEGIN
--   l_nmquery := p_querytype;
--     --invalidate previous queries
--        delete from sql_store where NM_QUERY = l_nmquery;
--        commit;
--
--      --insert new query
--      INSERT INTO EC_MES.sql_store (nm_query,dt_load,sql_query)
--           VALUES (l_nmquery,
--                   SYSDATE,
--                   EMPTY_CLOB ())
--        RETURNING sql_query
--             INTO l_clob;
--
--      l_bfile := BFILENAME ('DIR_TII', p_filename);
--      DBMS_LOB.fileopen (l_bfile);
--      DBMS_LOB.loadfromfile (l_clob, l_bfile, DBMS_LOB.getlength (l_bfile));
--      DBMS_LOB.fileclose (l_bfile);
--      COMMIT;
--   EXCEPTION
--      WHEN OTHERS
--      THEN
--         DBMS_OUTPUT.put_line (SQLERRM);
--             dbms_output.put_line ( 'Error_Stack...' || DBMS_UTILITY.FORMAT_ERROR_STACK() );
--
--dbms_output.put_line ( 'Error_Backtrace...' ||  DBMS_UTILITY.FORMAT_ERROR_BACKTRACE() );
--   END rbt_sql;
--END RBT_PKG;
--/



--
-- EC_MES_HOURLY_LOAD  (Scheduler Job) 
--
BEGIN
  SYS.DBMS_SCHEDULER.CREATE_JOB
    (
       job_name        => 'EC_MES.EC_MES_HOURLY_LOAD'
      ,start_date      => TO_TIMESTAMP_TZ('2014/03/07 20:00:00.000000 +04:00','yyyy/mm/dd hh24:mi:ss.ff tzr')
      ,repeat_interval => 'FREQ=HOURLY;INTERVAL=1'
      ,end_date        => NULL
      ,job_class       => 'DEFAULT_JOB_CLASS'
      ,job_type        => 'STORED_PROCEDURE'
      ,job_action      => 'EC_MES.RBT_PKG.RBT_BLK'
      ,comments        => NULL
    );
  SYS.DBMS_SCHEDULER.SET_ATTRIBUTE
    ( name      => 'EC_MES.EC_MES_HOURLY_LOAD'
     ,attribute => 'RESTARTABLE'
     ,value     => FALSE);
  SYS.DBMS_SCHEDULER.SET_ATTRIBUTE
    ( name      => 'EC_MES.EC_MES_HOURLY_LOAD'
     ,attribute => 'LOGGING_LEVEL'
     ,value     => SYS.DBMS_SCHEDULER.LOGGING_FULL);
  SYS.DBMS_SCHEDULER.SET_ATTRIBUTE_NULL
    ( name      => 'EC_MES.EC_MES_HOURLY_LOAD'
     ,attribute => 'MAX_FAILURES');
  SYS.DBMS_SCHEDULER.SET_ATTRIBUTE_NULL
    ( name      => 'EC_MES.EC_MES_HOURLY_LOAD'
     ,attribute => 'MAX_RUNS');
  SYS.DBMS_SCHEDULER.SET_ATTRIBUTE
    ( name      => 'EC_MES.EC_MES_HOURLY_LOAD'
     ,attribute => 'STOP_ON_WINDOW_CLOSE'
     ,value     => FALSE);
  SYS.DBMS_SCHEDULER.SET_ATTRIBUTE
    ( name      => 'EC_MES.EC_MES_HOURLY_LOAD'
     ,attribute => 'JOB_PRIORITY'
     ,value     => 3);
  SYS.DBMS_SCHEDULER.SET_ATTRIBUTE_NULL
    ( name      => 'EC_MES.EC_MES_HOURLY_LOAD'
     ,attribute => 'SCHEDULE_LIMIT');
  SYS.DBMS_SCHEDULER.SET_ATTRIBUTE
    ( name      => 'EC_MES.EC_MES_HOURLY_LOAD'
     ,attribute => 'AUTO_DROP'
     ,value     => FALSE);

  --SYS.DBMS_SCHEDULER.ENABLE
    --(name                  => 'EC_MES.EC_MES_HOURLY_LOAD');
END;
/

-- 
-- Non Foreign Key Constraints for Table Q_COUNTERS_NEW 
-- 
ALTER TABLE EC_MES.Q_COUNTERS_NEW ADD (
  CONSTRAINT Q_COUNTERS_NEW_KEY
  PRIMARY KEY
  (DT_PERIOD, PR_TRANSIT, ID_ABN, ID_TU, KD_ASKUE)
  USING INDEX EC_MES.Q_COUNTERS_NEW_KEY
  ENABLE VALIDATE);


CREATE OR REPLACE SYNONYM EC_MES.Q_COUNTERS FOR EC_MES.Q_COUNTERS_NEW;
  
GRANT DELETE, INSERT, SELECT, UPDATE ON EC_MES.POK_ZONE_DECODE TO PUBLIC;
GRANT DELETE, INSERT, SELECT, UPDATE ON EC_MES.Q_COUNTERS_NEW TO PUBLIC;

exit