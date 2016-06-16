DECLARE
   l_days_ago   NUMBER := 1;
   l_issue_id   NUMBER := 100104;
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

   DBMS_OUTPUT.put_line (SQL%ROWCOUNT);

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

      DBMS_OUTPUT.put_line (SQL%ROWCOUNT);
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
                   FROM JIRAACTION
                  WHERE id = i.id)
       WHERE id = i.id;

      DBMS_OUTPUT.put_line (SQL%ROWCOUNT);
   END LOOP;

   --UPDATE WORKLOG
   DBMS_OUTPUT.put_line ('WORKLOG');

   FOR i IN (SELECT ID
               FROM WORKLOG
              WHERE issueid = l_issue_id)
   LOOP
      UPDATE WORKLOG
         SET (created) =
                (SELECT created - l_days_ago created
                   FROM WORKLOG
                  WHERE id = i.id)
       WHERE id = i.id;

      DBMS_OUTPUT.put_line (SQL%ROWCOUNT);
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

      DBMS_OUTPUT.put_line (SQL%ROWCOUNT);
   END LOOP;

   --UPDATE USERASSOCIATION --выбирать по ПК?
   DBMS_OUTPUT.put_line ('USERASSOCIATION');

   FOR i IN (SELECT *
               FROM USERASSOCIATION
              WHERE sink_node_id = l_issue_id)
   LOOP
      UPDATE USERASSOCIATION
         SET (created) =
                (SELECT created - l_days_ago created
                   FROM USERASSOCIATION
                  WHERE SOURCE_NAME = i.source_name and SINK_NODE_ID=i.sink_node_id and SINK_NODE_ENTITY=i.SINK_NODE_ENTITY and ASSOCIATION_TYPE=i.ASSOCIATION_TYPE)
       WHERE SOURCE_NAME = i.source_name and SINK_NODE_ID=i.sink_node_id and SINK_NODE_ENTITY=i.SINK_NODE_ENTITY and ASSOCIATION_TYPE=i.ASSOCIATION_TYPE;

      DBMS_OUTPUT.put_line (SQL%ROWCOUNT);
   END LOOP;

   ROLLBACK;
END;
/