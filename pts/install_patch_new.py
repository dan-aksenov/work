import utils
import sys
from glob import glob

linux = utils.Deal_with_linux()

# Variables
# host to be used as ansible distributor for war files.
jump_host = "oemcc.fors.ru"

# temporary
patch_num = '0.28.8.1'
sunny_patch = 'Y:\\pts\\' + patch_num

# war files mappings
wars = [
    [ 'pts-integration-' + patch_num + '.war', 'integration.war' ],
    [ 'pts-public-' + patch_num + '.war', 'mobile.war' ],
    [ 'pts-restricted-' + patch_num + '.war', 'pts.war' ],
    [ 'pts-portal-' + patch_num + '.war', 'portal.war' ],
    [ 'pts-jointstorage-' + patch_num + '.war', 'jointstorage.war'  ]
    ]
                                                       
# check database version and apply database patch

# copy war files to asnible jump_host
for war in wars:
    if glob(sunny_patch + '\\' + war[0]) == []:
        print "ERROR: Unable to locate war file for " + war[0] + "!"
        sys.exit()
    war_path = glob( sunny_patch + '\\' + war[0])[0]
    linux.linux_put( jump_host, war_path, '/tmp/webapps/' + war[1] )

# run serial task to update apps one by one from ansible host.
# will restart of servers be serial too&
# ansible run in python
