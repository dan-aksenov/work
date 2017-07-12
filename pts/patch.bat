set stage_dir=d:\pts_patch

rem del %stage_dir%\* /f /s /q

cd /d %stage_dir%
ren pts-integration-*.war integration.war
ren pts-public-*.war portal.war;
ren pts-restricted-*.war pts.war
