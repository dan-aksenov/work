-- find not working metrics
SELECT testname,testmethod, a.cnt was, b.cnt now, a.cnt-b.cnt diff 
  FROM (  SELECT testname,testmethod, COUNT (*) cnt
            FROM LOG.hmlog
           WHERE     --testname = 'GAMMA2_TABLESPACE_ALERT' AND
            eventtime BETWEEN SYSDATE - 30 AND SYSDATE - 29
        GROUP BY testname,testmethod) a
       FULL OUTER JOIN
       (  SELECT testname,testmethod, COUNT (*) cnt
            FROM LOG.hmlog
           WHERE     --testname = 'GAMMA2_TABLESPACE_ALERT' AND
            eventtime BETWEEN SYSDATE - 1 AND SYSDATE - 1 / 24 / 60
        GROUP BY testname,testmethod) b
 using(testname,testmethod)
 --where a.cnt > b.cnt
 order by 5 desc

-- not collected metric time histogram.
select b.dd,a.cnt from(
SELECT TRUNC(eventtime) dd,
  COUNT(*) cnt
FROM log.hmlog where
testname = 'MAIN ASM DSK disk full'
GROUP BY TRUNC(eventtime)) a,
(select to_date('01.01.2015','dd.mm.yyyy') + rownum -1 dd
    from all_objects
    where rownum <= 
to_date('20.02.2016','dd.mm.yyyy')-to_date('01.01.2015','dd.mm.yyyy')+1) b
WHERE 
a.dd(+)=b.dd
--AND eventtime  > sysdate - 100
ORDER BY 1 DESC;

