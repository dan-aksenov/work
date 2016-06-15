DECLARE
   l_days_ago   NUMBER := 1;
   l_issue_id   NUMBER := 100104;
BEGIN
   --UPDATE JIRAISSUE
   UPDATE JIRAISSUE
      SET (created, updated) =
             (SELECT created - l_days_ago created,
                     updated - l_days_ago updated
                FROM JIRAISSUE
               WHERE id = l_issue_id)
    WHERE id = l_issue_id;

   DBMS_OUTPUT.put_line (SQL%ROWCOUNT);

   --UPDATE JIRAACTION
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

   COMMIT;
END;
/