import ckanapi
import os
from xlsxtocsv import xlsxtocsv, rfc4180
import tempfile
import csv
import shutil
import subprocess as sp
import io
import glob
import sys
import cStringIO
import json

# _*_ coding: utf-8 _*_


## Curently this requires a script "pda2pdfa" that conevrts PDF to PDF/A-1b
## Here we use:
## gs -dPDFA -dBATCH -dNOPAUSE -sProcessColorModel=DeviceCMYK -sDEVICE=pdfwrite \
## -sPDFACompatibilityPolicy=1 -sOutputFile="$outfile" "$infile"

## Curently this requires a script pdfa_vali" that validates against PDF/A-1b.
## Here we use:
## java -jar $HOME/java/lib/preflight-app-2.0.4.jar "$1"


# measurement methods

class PrepareNADUF(object):
    def __init__(self, basedir):
        self.apikey = self.get_apikey()
        #self.remote = 'https://eaw-ckan-dev1.eawag.wroot.emp-eaw.ch'
        self.remote = 'http://localhost:5000'
        self.targetdir = os.path.join(basedir, 'upload')
        self.srcdir = os.path.join(basedir,'staging')
        self.tmpdir = os.path.join(basedir, 'tmp')
        self.metadata = json.load(open('metadata.json', 'r'))
        rfc4180.RFC4180() # register dialect
        
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

    def check_pdf_A(self, pdffile):
        pdffilepath = os.path.join(self.srcdir, pdffile)
        try:
            res = sp.check_output(['pdfa_vali', pdffilepath])
        except sp.CalledProcessError:
            print('{} is not valid PDF/A-1b. trying to convert ...'
                  .format(pdffile))
            return self.pdf2pdfa(pdffile)
        else:
            return pdffile

    def pdf2pdfa(self, pdffile):
        pdffilepath = os.path.join(self.srcdir, pdffile)
        try:
            res = io.BufferedReader(io.BytesIO(sp.check_output(['pdf2pdfa',
                                                      pdffilepath, '-'])))
        except sp.CalledProcessError as e:
            print('Conversion of {} tp PDF/A failed')
            raise(e)
        else:
            outfile = os.path.basename(pdffile).partition('.pdf')[0] + '_A.pdf'
            outfilepath =  os.path.join(self.tmpdir, outfile)
            with io.open(outfilepath, 'bw') as o:
                o.write(res.read())
            print('converted {} to PDF/A'.format(pdffile, outfile))
            return(outfilepath)
                
    def cpfile(self, source, dest):
        src = os.path.join(self.srcdir, source)
        target = os.path.join(self.targetdir, dest)
        shutil.copyfile(src, target)
        print('Copied {}\n->{}'.format(src, target))
        return target

    def get_files(self, basedir, pattern, relative=False):
        """
        Returns absolute paths (relative=False) or paths relative
        to basedir (relative=True) determined by basedir and pattern.

        pattern is a glob-pattern relative to the one indicated by basedir:
        'tmpdir': self.tmpdir
        'srcdir': self.srcdir
        'targetdir': self.targetdir
        """
        pattern = eval('os.path.join(self.{}, pattern)'.format(basedir))
        fs = glob.glob(pattern)
        if not relative:
            return fs
        else:
            return [os.path.relpath(f, self.srcdir) for f in fs]

    def mktmpdir(self):
        return os.path.relpath(tempfile.mkdtemp(dir=self.tmpdir), self.tmpdir)
    
    def extract_xlsx(self, xlsxfiles, sheets=None, tmpdir=None, strip=False):
        if not type(xlsxfiles) == list:
            xlsxfiles = [xlsxfiles]
        if tmpdir:
            out_dir = os.path.join(self.tmpdir, tmpdir)
        else:
            out_dir = tempfile.mkdtemp(dir=self.tmpdir)
        for xlsxfile in xlsxfiles:
            print('Extracting data from {} ...'.format(xlsxfile))
            xlsxtocsv.main(xlsxfile, out_dir, sheets=sheets)
        return os.path.basename(out_dir)

    def strip_csv(self, csvfiles, killemptyrows=True):
        """Strips leading and trailing whitespace from cells.
        csvfiles is the list of abs. paths to operate on.
        Also removes rows with no data.
        Files are overwritten.
        pattern is a glob - pattern relative to the one indicated by basedir:
        'tmpdir': self.tmpdir
        'srcdir': self.srcdir
        'targetdir': self.targetdir
        """
        if not type(csvfiles) == list:
            csvfiles = [csvfiles]
        for csvf in csvfiles:
            print('{}:\nStripping leading and trailing whitespace from cells'
                  .format(os.path.basename(csvf)))
            ftmp = tempfile.SpooledTemporaryFile(max_size=1048576, mode='w+b')
            tmpwriter = csv.writer(ftmp, dialect='RFC4180')
            with open(csvf, 'rb') as f:
                for i, row in enumerate(csv.reader(f, dialect='RFC4180')):
                    if killemptyrows and all([c == '' for c in row]):
                        print('{}:\nremoved empty line {}\n'
                              .format(os.path.basename(csvf), i))
                        continue
                    tmpwriter.writerow([c.strip() if isinstance(c, basestring)
                                        else c for c in row ])
            ftmp.flush()
            ftmp.seek(0)
            with open(csvf, 'wb') as f:
                shutil.copyfileobj(ftmp, f)

    def crop_csv(self, csvfiles):
        """Strips columns that contain only empty cells."""
        if not type(csvfiles) == list:
            csvfiles = [csvfiles]
        for csvf in csvfiles:
            print('{}:\nremoving empty columns'.format(os.path.basename(csvf)))
            with open(csvf, 'rb') as f:
                table = [row for row in csv.reader(f, dialect='RFC4180')]
            table_inv = zip(*table)
            goodcols = []
            for i, col in enumerate(table_inv):
                if all([c == '' for c in col]):
                    print('removing empty column {}'.format(i))
                    continue
                goodcols.append(i)
            table_inv = [table_inv[i] for i in goodcols]
            table = zip(*table_inv)
            with open(csvf, 'wb') as f:
                csv.writer(f, dialect='RFC4180').writerows(table)
            
    def check_column_compat(self, csvfiles):
        """Checks whether a set of csv files has the same column headings.
        pattern is a glob - pattern relative to the one indicated by basedir:
        tmpdir: self.tmpdir
        srcdir: self.srcdir
        targetdir: self.targetdir
        """
        print('Checking compatibility of headers for {}'.format(pattern))
        checklist = {}
        for fn in csvfiles:
            fbase = os.path.basename(fn)
            with open(fn, 'rb') as f:
                checklist[fbase] = tuple(csv.reader(f, dialect='RFC4180').next())
        headerset = set(checklist.values())
        if len(headerset) > 1:
            print('Incompatibilies detected:')
            incomp = {}
            for header in headerset:
                incfiles = [k for k in checklist if checklist[k] == header]
                incomp.setdefault(header, []).extend(incfiles)
            print(incomp)
            print(len(incomp))
        
    def extract_subtable(self, csvfile, row1=None, row2=None,
                         col1=None, col2=None, totxt=False):
        
        """Extracts a rectangular area from CSV - table.  Coordinate parameter
        with value None are interpreted to yield the maximum possible
        size of the recatangle.

        Indices start with 1.

        If totxt=True, rows will be concatenated and written into a .txt file.
        """
        
        res = []
        row1 = row1 or 1
        col1 = col1 or 1
        if type(csvfile) == list:
            csvfile = csvfile[0]
        with open(csvfile, 'rb') as f:
            readr = csv.reader(f, dialect='RFC4180')
            for c, row in enumerate(readr):
                if c + 1 < row1:
                    continue
                elif (row2 is not None) and (c + 1 > row2):
                    continue   # not breaking just to count lines
                else:
                    if [x for x in row if x]: 
                        res.append(row)
            row2 = row2 or readr.line_num
        res_t = zip(*res)
        col2 = col2 or len(res_t)
        res_t = res_t[col1-1:col2]
        res = zip(*res_t)

        suffix = 'txt' if totxt else 'csv'
        outfile = (os.path.basename(csvfile).partition('.csv')[0]
                   + '_{}_{}_{}_{}.{}'.format(str(row1), str(row2),
                                              str(col1), str(col2), suffix))
        outfilepath =  os.path.join(os.path.dirname(csvfile), outfile)
        with io.open(outfilepath, 'bw') as o:
            if totxt:
                res = [' '.join(l) + '\r\n' for l in res]
                o.writelines(res)
            else:
                wr = csv.writer(o, dialect='RFC4180')
                wr.writerows(res)    
        print('wrote {}'.format(outfile))
        return outfilepath





P = PrepareNADUF('/home/vonwalha/rdm/data/preparation/naduf')
#P.action('package_create')
#P.action('package_update')
#P.action('package_delete')
#P.action('dataset_purge')

## main data
dmain_tmp = P.extract_xlsx(P.get_files('srcdir','Messdaten/Daten 2015.xlsx'))
dmain1_tmp = P.extract_xlsx(P.get_files('srcdir', 'Messdaten/Jahresmittel-2.xlsx'))
P.strip_csv(P.get_files('tmpdir', os.path.join(dmain_tmp, '*.csv')))
P.strip_csv(P.get_files('tmpdir', os.path.join(dmain1_tmp, '*.csv')))
P.crop_csv(P.get_files('tmpdir', os.path.join(dmain_tmp, '*.csv')))
P.crop_csv(P.get_files('tmpdir', os.path.join(dmain1_tmp, '*.csv')))

## station information
dstations_tmp = P.extract_xlsx(
    P.get_files('srcdir','Stationen/Stationszusammenstellung Jan17.xlsx'))

P.strip_csv(P.get_files('tmpdir', os.path.join(dstations_tmp, '*Quellen*.csv')),
            killemptyrows=False)

stations_description_legend = P.extract_subtable(
    P.get_files('tmpdir', os.path.join(dstations_tmp, '*Quellen*.csv')),
    7, 18, 1, 4)
P.strip_csv(stations_description_legend)

stations_description_sources = P.extract_subtable(
    P.get_files('tmpdir', os.path.join(dstations_tmp, '*Quellen.csv')),
    21, 38, 1, 3)
P.strip_csv(stations_description_sources)

stations_description_notes = P.extract_subtable(
    P.get_files('tmpdir', os.path.join(dstations_tmp, '*Quellen.csv')),
    1, 5, 1, 1, totxt=True)
 
#XXX

P.strip_csv(
    P.get_files('tmpdir', os.path.join(dstations_tmp, '*Allgemeine*.csv'))
    + P.get_files('tmpdir', os.path.join(dstations_tmp, '*Klassifikation*.csv')))

P.crop_csv(
    P.get_files('tmpdir', os.path.join(dstations_tmp, '*Allgemeine*.csv'))
    + P.get_files('tmpdir', os.path.join(dstations_tmp, '*Klassifikation*.csv')))


dnotes = P.mktmpdir()

P.extract_xlsx(
    P.get_files('srcdir', 'Hauptfiles (Instrument für mich)/*.xlsx'),
    sheets=['Stoerungen','Logsheet'], tmpdir=dnotes)
    
P.strip_csv(P.get_files('tmpdir', os.path.join(dnotes, '*.csv')))

P.check_column_compat(P.get_files('tmpdir',
                                  os.path.join(dnotes, '*Stoerungen.csv')))
P.check_column_compat(P.get_files('tmpdir',
                                  os.path.join(dnotes, '*Logsheet.csv')))

sys.exit()

## copy files:
ftocopy = [
    (P.check_pdf_A('Messmethoden/methods NADUF-english.pdf'),
     'methods_chemical_analysis.pdf'),
    (P.check_pdf_A('ReadMe.pdf'), 'measurements_notes.pdf'),
    (os.path.join(dmain_tmp, 'Daten 2015_Onelinemessung.csv'),
     'hourly_measurements_1990-1998.csv'),
    (os.path.join(dmain_tmp, 'Daten 2015_Originaldaten.csv'),
     'measurements_raw.csv'),
    (os.path.join(dmain_tmp, 'Daten 2015_14tg_Daten.csv'),
     'measurements_raw.csv'),
    (os.path.join(dmain_tmp, 'Daten 2015_14tg_Daten.csv'),
     'measurements_biweekly.csv'),
    (os.path.join(dmain1_tmp, 'Jahresmittel-2_Sheet1.csv'),
     'measurements_annual.csv'),
    (os.path.join(dstations_tmp,
                  'Stationszusammenstellung Jan17_Allgemeine_Daten.csv'),
     'stations_description.csv'),
    (P.extract_subtable(
        os.path.join(dstations_tmp,
                     'Stationszusammenstellung Jan17_Bemerkungen_Quellen.csv'),
        7, 18, 1, 4),'stations_description_legend.csv'),
    (P.extract_subtable(
        os.path.join(dstations_tmp,
                     'Stationszusammenstellung Jan17_Bemerkungen_Quellen.csv'),
        21, 38, 1, 3),'stations_description_sources.csv'),
    (P.extract_subtable(
        os.path.join(dstations_tmp,
                     'Stationszusammenstellung Jan17_Bemerkungen_Quellen.csv'),
        1, 5, 1, 1, totxt=True),'stations_description_notes.txt'),
    (os.path.join(dstations_tmp,
                  'Stationszusammenstellung Jan17_Klassifikation_AS_CH.csv'),
     'stations_description_arealstats_mapping_CH.csv'),
    (os.path.join(dstations_tmp,
                  'Stationszusammenstellung Jan17_Klassifikation_AS_EU.csv'),
     'stations_description_arealstats_mapping_EU.csv'),
    
]

           
# for f in ftocopy:
#     P.cpfile(f[0], f[1])
           
           # csvfile = '/home/vonwalha/rdm/data/preparation/naduf/upload/stations_description.csv'
           # row1 = 26
           # row2 = None
           # res = P.extract_subtable(csvfile, row1, row2, 3, None)
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

with open('metadata.json', 'w') as f:
    json.dump(metadata, f, indent=4, separators=(',', ':'))

