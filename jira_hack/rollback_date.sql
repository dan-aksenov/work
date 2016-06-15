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

   ROLLBACK;
END;
/