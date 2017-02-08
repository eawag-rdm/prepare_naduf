import os
from csvtrans import CSVFiles

try:
    import unittest2 as unittest
except ImportError:
    import unittest

class TestCSVFiles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home = os.path.dirname(__file__)
        cls.testfiles = os.path.join(cls.home, 'files')

    @classmethod
    def fullpath(cls, fn):
        return os.path.join(cls.testfiles, fn)
    
    def test_init(self):
        e = CSVFiles()
        one = CSVFiles(os.path.join(self.testfiles, 'valid.csv'))
        multi = CSVFiles([
            os.path.join(self.testfiles,'valid.csv'),
            open(os.path.join(self.testfiles, 'valid.csv'), 'rb')
        ])


        self.assertEqual(e.toc, [])
        self.assertEqual(one.toc[0]['name'], 'valid.csv')
        self.assertEqual(one.toc[0]['fobject'].read(7), 'Kuerzel')
        self.assertEqual(one.toc[0]['history'],
                         [('init', os.path.join(self.testfiles, 'valid.csv'))])
        self.assertEqual(multi.toc[0]['name'], one.toc[0]['name'])
        self.assertEqual(multi.toc[0]['history'], one.toc[0]['history'])
        self.assertEqual(multi.toc[0]['fobject'].read(7), 'Kuerzel')
        self.assertEqual(multi.toc[1]['name'], one.toc[0]['name'])
        self.assertNotEqual(multi.toc[1]['history'], one.toc[0]['history'])
        self.assertEqual(multi.toc[1]['fobject'].read(7), 'Kuerzel')
        
    def test_add(self):
        one = CSVFiles(self.fullpath('valid.csv'))
        toc0 = one.toc
        one.addcsvlist([self.fullpath('valid_holes.csv'),
                        open(self.fullpath('valid_holes_stripped.csv'))
                        ])
        toc1 = one.toc
        self.assertEqual(len(one.toc), 3)
        self.assertTrue(one.toc[2]['fobject'].readline().endswith('EAWAG\r\n'))
        self.assertEqual(one.toc[0], toc0[0])

    def test_init_xlsx(self):
        e = CSVFiles()
        xlsxfile = (os.path.join(self.testfiles,'validxlsx.xlsx'))
        e.init_xlsx(xlsxfile)
        sheetnames = ['Allgemeine_Daten', 'Bemerkungen_Quellen',
                      'Klassifikation_AS_CH','Klassifikation_AS_EU']
        #print(e.toc)
        try:
            self.assertItemsEqual(
                ['validxlsx_' + sn + '.csv' for sn in sheetnames],
                [r['name'] for r in e.toc])
        except AttributeError:
            self.assertCountEqual(
                ['validxlsx_' + sn + '.csv' for sn in sheetnames],
                [r['name'] for r in e.toc])
        self.assertTrue(
            all([r['history'][0] == ('init_xlsx', ' '.join([xlsxfile, str(None)]))
                 for r in e.toc]))

    def test_strip_csv(self):
         e = CSVFiles(self.fullpath('valid_holes.csv'))
         print('e\n')
         print(e.toc)
         e1 = e.strip_csv(killemptyrows=False)
         self.assertEqual(
             open(self.fullpath('valid_holes_stripped.csv'), 'rb').read(),
             e1.toc[0]['fobject'].read())
         print "e1:"
         print(e1.toc)
         e2 = e1.strip_csv()
         print("e2")
         print(e2.toc)
         fob1 = e2.toc[0]['fobject']
         newfoc = e.strip_csv().toc[0]['fobject']
         e2.addcsvlist(newfoc)
         #     e.strip_csv().toc[0]['fobject']
         # )
         # print("e2\n")
         # print(e2.toc)
         #self.assertEqual(fob1, e2.toc[0]['fobject'])
         # self.assertEqual(e2.toc[0]['fobject'].read(), e2.toc[1]['fobject'].read())
         # e2.resetfiles()
         # print(e2.toc[1]['fobject'].read())
         # self.assertEqual(
         #     open(self.fullpath('valid_holes_stripped_killempty.csv'), 'rb').read(),
         #     e2.toc[0]['fobject'].read())
         
                     
