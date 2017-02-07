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
        pass

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
        print([r['history'] for r in e.toc])
        self.assertTrue(
            all([r['history'][0] == ('init_xlsx', xlsxfile) for r in e.toc]))

    def test_strip_csv(self):
        pass
