import ckanapi
import os
from xlsxtocsv import xlsxtocsv, rfc4180
from xlsxtocsv import rfc4180
import tempfile
import csv

# _*_ coding: utf-8 _*_

# measurement methods

class PrepareNADUF(object):
    def __init__(self, metadata):
        self.apikey = self.get_apikey()
        #self.remote = 'https://eaw-ckan-dev1.eawag.wroot.emp-eaw.ch'
        self.remote = 'http://localhost:5000'
        self.targetdir = './upload'
        self.staging_dir = './staging'
        self.metadata = metadata
        
        self.connection = self.connect()
        
        
    def connect(self):
        return ckanapi.RemoteCKAN(self.remote, apikey=self.apikey)
        
    def get_apikey(self):
        apikey = os.environ['CKAN_APIKEY']
        return apikey

    def action(self, action):
        metadata = self.prep_meta(action)
        res = self.connection.call_action(action, metadata)
        print(res)
        
    def prep_meta(self, action):
        if action == 'package_delete' or action == 'dataset_purge':
            return {'id': self.metadata.get('id', None) or
                    self.metadata['name']}
        return self.metadata
    
    def extract_xlsx(self, xlsxfile):
        out_dir = tempfile.mkdtemp(dir=self.targetdir)
        xlsxtocsv.main(os.path.join(self.staging_dir, xlsxfile), out_dir)
        return out_dir

    def extract_subtable(self, csvfile, row1, row2, col1, col2):
        res = []
        with open(csvfile, 'rb') as f:
            readr = csv.reader(f, dialect='RFC4180')
            for i in range(0, 30):
                print(readr.next())
                
            
        
        
        

    def apply_trafos(self, trans):
        for t in trans:
            expression = ('self.' + '(self.'.join(t['trans'][::-1]) +
                          '("' + t['source'] + '"' + (len(t['trans']))*')')
            eval(expression)
        
# Maps pathnames of source files to a list of transformation
# functions, a function that returns a dict of resource-metadata,
# and the final filename (to be written below self.targetdir)
# copymap = {'Messmethoden/methods NADUF-english.pdf': {
#     'transform': [],
#     'target': 'methods_chemical_analysis.pdf',
#     }


metadata = {
    'id': 'naduf',
    'name': 'naduf',
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
    'timerange': '2017 TO 2222',
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



P = PrepareNADUF(metadata)
#P.action('package_create')
#P.action('package_update')
#P.action('package_delete')
#P.action('dataset_purge')

transformations = [
    {'source': 'Stationen/Stationszusammenstellung Jan17.xlsx',
     'trans': ['extract_xlsx']}] 
#t = P.extract_xlsx('source')
#res = P.apply_trafos(transformations)   
fi = './upload/tmp7aT3kH/Stationszusammenstellung Jan17_Bemerkungen_Quellen.csv'
res = P.extract_subtable(fi,5,10,0,0)
print res
