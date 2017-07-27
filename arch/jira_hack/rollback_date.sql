CREATE OR REPLACE PROCEDURE JIRA_ROLLBACK_DATES (p_days    IN NUMBER,
                                                 p_issue   IN NUMBER)
AS
   l_days_ago   NUMBER := p_days;
   l_issue_id   NUMBER := p_issue;
BEGIN
   --UPDATE JIRAISSUE
   DBMS_OUTPUT.put_line ('JIRAISSUE');

   UPDATE JIRAISSUE
      SET (created, updated) =
             (SELECT created - l_days_ago created,
                     updated - l_days_ago updated
                FROM JIRAISSUE
               WHERE id = l_issue_id)
    WHERE id = l_issue_id;

   DBMS_OUTPUT.put_line (SQL%ROWCOUNT || ' rows updated.');

   --UPDATE JIRAACTION
   DBMS_OUTPUT.put_line ('JIRAACTION');

   FOR i IN (SELECT id
               FROM jiraaction
              WHERE issueid = l_issue_id)
   LOOP
      UPDATE JIRAACTION
         SET (created, updated) =
                (SELECT created - l_days_ago created,
                        updated - l_days_ago updated
                   FROM JIRAACTION
                  WHERE id = i.id)
       WHERE id = i.id;

      DBMS_OUTPUT.put_line (SQL%ROWCOUNT || ' rows updated.');
   END LOOP;

   --update CHANGEGROUP
   DBMS_OUTPUT.put_line ('CHANGEGROUP');

   FOR i IN (SELECT ID
               FROM CHANGEGROUP
              WHERE issueid = l_issue_id)
   LOOP
      UPDATE CHANGEGROUP
         SET (created) =
                (SELECT created - l_days_ago created
                   FROM CHANGEGROUP
                  WHERE id = i.id)
       WHERE id = i.id;

      DBMS_OUTPUT.put_line (SQL%ROWCOUNT || ' rows updated.');
   END LOOP;

   --UPDATE WORKLOG
   DBMS_OUTPUT.put_line ('WORKLOG');

   FOR i IN (SELECT ID
               FROM WORKLOG
              WHERE issueid = l_issue_id)
   LOOP
      UPDATE WORKLOG
         SET (created, startdate, updated) =
                (SELECT created - l_days_ago creatdate,
                        startdate - l_days_ago startdate,
                        updated - l_days_ago updated
                   FROM WORKLOG
                  WHERE id = i.id)
       WHERE id = i.id;

      DBMS_OUTPUT.put_line (SQL%ROWCOUNT || ' rows updated.');
   END LOOP;

   --UPDATE FILEATTACHMENT
   DBMS_OUTPUT.put_line ('FILEATTACHMENT');

   FOR i IN (SELECT ID
               FROM FILEATTACHMENT
              WHERE issueid = l_issue_id)
   LOOP
      UPDATE FILEATTACHMENT
         SET (created) =
                (SELECT created - l_days_ago created
                   FROM FILEATTACHMENT
                  WHERE id = i.id)
       WHERE id = i.id;

      DBMS_OUTPUT.put_line (SQL%ROWCOUNT || ' rows updated.');
   END LOOP;

   --UPDATE USERASSOCIATION
   DBMS_OUTPUT.put_line ('USERASSOCIATION');

   FOR i IN (SELECT *
               FROM USERASSOCIATION
              WHERE sink_node_id = l_issue_id)
   LOOP
      UPDATE USERASSOCIATION
         SET (created) =
                (SELECT created - l_days_ago created
                   FROM USERASSOCIATION
                  WHERE     SOURCE_NAME = i.source_name
                        AND SINK_NODE_ID = i.sink_node_id
                        AND SINK_NODE_ENTITY = i.SINK_NODE_ENTITY
                        AND ASSOCIATION_TYPE = i.ASSOCIATION_TYPE)
       WHERE     SOURCE_NAME = i.source_name
             AND SINK_NODE_ID = i.sink_node_id
             AND SINK_NODE_ENTITY = i.SINK_NODE_ENTITY
             AND ASSOCIATION_TYPE = i.ASSOCIATION_TYPE;

      DBMS_OUTPUT.put_line (SQL%ROWCOUNT || ' rows updated.');
   END LOOP;

   --UPDATE OS_CURRENTSTEP
   DBMS_OUTPUT.put_line ('OS_CURRENTSTEP');

   FOR i IN (SELECT id
               FROM OS_CURRENTSTEP
              WHERE entry_id IN (SELECT workflow_id
                                   FROM jiraissue
                                  WHERE id = l_issue_id))
   LOOP
      UPDATE OS_CURRENTSTEP
         SET (start_date) =
                (SELECT start_date - l_days_ago created
                   FROM OS_CURRENTSTEP
                  WHERE id = i.id)
       WHERE id = i.id;

      DBMS_OUTPUT.put_line (SQL%ROWCOUNT || ' rows updated.');
   END LOOP;

   --UPDATE OS_HISTORYSTEP
   DBMS_OUTPUT.put_line ('OS_HISTORYSTEP');

   FOR i IN (SELECT id
               FROM OS_HISTORYSTEP
              WHERE entry_id IN (SELECT workflow_id
                                   FROM jiraissue
                                  WHERE id = l_issue_id))
   LOOP
      UPDATE OS_HISTORYSTEP
         SET (start_date, finish_date) =
                (SELECT start_date - l_days_ago start_date,
                        finish_date - l_days_ago finish_date
                   FROM OS_HISTORYSTEP
                  WHERE id = i.id)
       WHERE id = i.id;

      DBMS_OUTPUT.put_line (SQL%ROWCOUNT || ' rows updated.');
   END LOOP;

   COMMIT;
--rollback;
END;
/
