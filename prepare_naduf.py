import ckanapi
import os
# _*_ coding: utf-8 _*_



# measurement methods

class PrepareNADUF(object):
    def __init__(self, staging_dir, metadata):
        self.apikey = self.get_apikey()
        self.remote = 'https://eaw-ckan-dev1.eawag.wroot.emp-eaw.ch'
        #self.remote = 'http://localhost:5000'
        self.targetdir = './upload'
        self.metadata = self.prep_meta(metadata)
        
        self.connection = self.connect()
        
        
    def connect(self):
        return ckanapi.RemoteCKAN(self.remote, apikey=self.apikey)
        

    def get_apikey(self):
        apikey = os.environ['CKAN_APIKEY']
        return apikey

    def package_create(self):
        res = self.connection.call_action('package_create', self.metadata)
        print(res)

    def package_update(self):
        res = self.connection.call_action('package_patch', self.metadata)

        # res = self.connection.call_action('group_patch', self.group)
        print(res)

    def prep_meta(self, metadata):
        return metadata
        
    
    copydict = {'staging': 'Messmethoden/methods NADUF-english.pdf',
            'target': 'methods_chemical_analysis.pdf'}


metadata = {
    'id': 'naduf',
    'title': 'NADUF – National long-term surveillance of Swiss rivers',
    'notes': '''The "National Long-term Surveillance of Swiss Rivers" (NADUF)
program was initiated in 1972 as a cooperative project between three
institutes: the [Federal Office for the Environment
(BAFU)](https://www.bafu.admin.ch/index.html?lang=en), the Swiss
Federal Institute of Aquatic Science and Technology (EAWAG) and since
2003 the [Swiss Federal Institute for Forest, Snow and Landscape
Research (WSL)](http://www.wsl.ch/index_EN).

With the NADUF program, the chemical-physical state of Swiss rivers as
well as intermediate-term and long-term changes in concentration are
observed. Furthermore, it provides data for scientific studies on
biological, chemical and physical processes in river water. The NADUF
network serves as a basic data and sampling facility to evaluate the
effectiveness of water protection measures and for various scientific
projects.''',
    'keywords': ['none'],
    'variables': ['none'],
    'generic-terms': ['none'],
    'systems': ['none'],
    'taxa': None,
    'substances': None,
    'timerange': '*',
    'spatial': '{}',
    'geographic_name': None,
    'owner_org': 'water-resources-and-drinking-water',
    'private': False,
    'status': 'incomplete',
    'author': ['Ursula Schönenberger <ursula.schoenenberger@eawag.ch>',
               'Stephan Hug <stephan.hug@eawag.ch>'],
    'maintainer': 'Ursula Schönenberger <ursula.schoenenberger@eawag.ch>',
    'usage_contact': 'Ursula Schönenberger <ursula.schoenenberger@eawag.ch>',
    'open_data': ['open_data', 'doi_wanted', 'long_term_archive'],
    'groups': [{'name': 'naduf-national-long-term-surveillance-of-swiss-rivers'}],
    
}


staging_dir = './staging'
P = PrepareNADUF(staging_dir, metadata)
#P.package_create()
P.package_update()
