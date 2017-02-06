# Adapted from
# https://github.com/ckan/ckanapi/blob/master/ckanapi/tests/test_remote.py

# _*_ coding: utf-8 _*_

import subprocess
import os
import atexit
import time
from StringIO import StringIO

from ckancomm import CKANComm

try:
    import unittest2 as unittest
except ImportError:
    import unittest
    
try:
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull, 'wb')

try:
    from urllib2 import urlopen, URLError
except ImportError:
    from urllib.request import urlopen, URLError    

TEST_CKAN = 'http://localhost:8901'

class TestRemoteAction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = os.path.join(os.path.dirname(__file__), 'mock/mock_ckan.py')
        _mock_ckan = subprocess.Popen(['python2', script],
                                      stdout=DEVNULL, stderr=DEVNULL)
        
        def kill_child():
            try:
                _mock_ckan.kill()
                _mock_ckan.wait()
            except OSError:
                pass  # alread cleaned up from tearDownClass

        atexit.register(kill_child)
        cls._mock_ckan = _mock_ckan
        while True: # wait for the server to start
            try:
                r = urlopen(TEST_CKAN + '/api/action/site_read')
                if r.getcode() == 200:
                    break
            except URLError as e:
                pass
            time.sleep(0.1)

    def test_package_create(self):
        metafile = StringIO('{"id": "packagename"}')
        com = CKANComm(metafile, remote=TEST_CKAN)
        self.assertEqual(com.action('package_create'), "packagename")

    def test_package_delete(self):
        metafile = StringIO('{"name": "packagename"}')
        com = CKANComm(metafile, remote=TEST_CKAN)
        self.assertEqual(com.action('package_delete'), "packagename")
    

        

