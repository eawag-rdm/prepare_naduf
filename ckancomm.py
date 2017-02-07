import ckanapi
import os
import json

# _*_ coding: utf-8 _*_

class CKANComm(object):
    """A very thin wrapper around ckanapi for modifying the state of a
    remote CKAN instance based on information in a metadata-file.
    """
    
    def __init__(self, metafile, remote='http://localhost:5000'):
        self.apikey = self.get_apikey()
        self.remote = remote
        self.connection = self.connect()
        self.metadata = json.load(metafile)

    def connect(self):
        return ckanapi.RemoteCKAN(self.remote, apikey=self.apikey)
        
    def get_apikey(self):
        apikey = os.environ['CKAN_APIKEY']
        return apikey

    def action(self, action):
        metadata = self.prep_meta(action)
        res = self.connection.call_action(action, metadata)
        return(res)
        
    def prep_meta(self, action):
        if action == 'package_delete' or action == 'dataset_purge':
            return {'id': self.metadata.get('id', None) or
                    self.metadata['name']}
        return self.metadata
