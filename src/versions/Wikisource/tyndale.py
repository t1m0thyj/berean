#!/usr/bin/env python
"""tyndale.py - downloads Tyndale from Wikisource and converts it to USFM
Based on wycliffe.py by Chris Little (Sword Project)
https://crosswire.org/svn/sword-tools/trunk/modules/wikisource/wycliffe.py
"""

import urllib, urllib2
import re
import codecs

WSbase = 'Bible_(Tyndale)/'
WSbooks = (
    'Genesis', 'Exodus', 'Leviticus', 'Numbers',
    'Deuteronomy', 'Jonah', 'Matthew', 'Mark',
    'Luke', 'John', 'Acts', 'Romans',
    '1 Corinthians', '2 Corinthians', 'Galatians', 'Ephesians',
    'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians',
    '1 Timothy', '2 Timothy', 'Titus', 'Philemon',
    'Hebrews', 'James', '1 Peter', '2 Peter',
    '1 John', '2 John', '3 John', 'Jude',
    'Revelation'
    )

OSISbook = (
    'Gen', 'Exod', 'Lev', 'Num',
    'Deut', 'Jonah', 'Matt', 'Mark',
    'Luke', 'John', 'Acts', 'Rom',
    '1Cor', '2Cor', 'Gal', 'Eph',
    'Phil', 'Col', '1Thess', '2Thess',
    '1Tim', '2Tim', 'Titus', 'Phlm',
    'Heb', 'Jas', '1Pet', '2Pet',
    '1John', '2John', '3John', 'Jude',
    'Rev'
    )

USFMbook = (
    'GEN', 'EXO', 'LEV', 'NUM',
    'DEU', 'JON', 'MAT', 'MRK',
    'LUK', 'JHN', 'ACT', 'ROM',
    '1CO', '2CO', 'GAL', 'EPH',
    'PHP', 'COL', '1TH', '2TH',
    '1TI', '2TI', 'TIT', 'PHM',
    'HEB', 'JAS', '1PE', '2PE',
    '1JN', '2JN', '3JN', 'JUD',
    'REV'
    );

"""
articleList = ''
for WSbook in WSbooks:
    articleList += WSbase + '/' + WSbook + '\n'

"""

OSISdoc = ''

for i in range(len(WSbooks)):
    print WSbooks[i]
    url = 'http://en.wikisource.org/wiki/Special:Export'
    vals = {'pages':WSbase+WSbooks[i],
            'curonly':1,
            'wpDownload':0}
    vals = urllib.urlencode(vals)
    request = urllib2.Request(url,vals)
    inputDoc = urllib2.urlopen(request).read().decode('utf-8')
    
    inputDoc = re.sub(r'.*<text .+?>(.+?)</text>.*', r'\1', inputDoc, flags=re.DOTALL|re.IGNORECASE)

    inputDoc = re.sub('  +', ' ', inputDoc)

    inputDoc = re.sub(r'{{header.+?}}', '', inputDoc, flags=re.DOTALL|re.IGNORECASE)
    inputDoc = re.sub(r'{{Other versions.+?}}', '', inputDoc, flags=re.DOTALL|re.IGNORECASE)
    inputDoc = re.sub(r'{{biblecontents.+?}}.*', '', inputDoc, flags=re.DOTALL|re.IGNORECASE)
    inputDoc = re.sub(r'\[\[Category.+?\]\]', '', inputDoc, flags=re.DOTALL|re.IGNORECASE)
    inputDoc = re.sub(r'&lt;section .+?&gt;', '', inputDoc, flags=re.DOTALL|re.IGNORECASE)
    inputDoc = re.sub(r'&lt;onlyinclude&gt;{{{.+?\|\s*(.+?)}}}&lt;/onlyinclude&gt;', r'\1', inputDoc, flags=re.DOTALL|re.IGNORECASE)
    inputDoc = re.sub(r'&lt;/?onlyinclude&gt; *', '', inputDoc, flags=re.DOTALL|re.IGNORECASE)

    inputDoc = re.sub(r'==Chapter \d+==', '', inputDoc, flags=re.IGNORECASE)

    inputDoc = re.sub(r'{{chapter\|(\d+)}}\s*', r'\\c \1\n', inputDoc, flags=re.IGNORECASE)
    inputDoc = re.sub(r'{{verse\|chapter=\d+\|verse=(\d+)}}\s*', r'\\v \1 ', inputDoc, flags=re.IGNORECASE)

    inputDoc = re.sub(r'==External links==.+', '', inputDoc, flags=re.DOTALL|re.IGNORECASE)

    inputDoc = re.sub(r'\[Note:(.+?) +\]', r'\\f + \1\\f*', inputDoc, flags=re.DOTALL|re.IGNORECASE)
    inputDoc = re.sub(r'\[(.+?)\]', r'\\it \1\\it*', inputDoc, flags=re.DOTALL|re.IGNORECASE)

    USFMdoc = codecs.open('tyndale_'+str(i+1).zfill(2)+'_'+USFMbook[i]+'.usfm', 'w', 'utf-8')
    
    USFMdoc.write('\id '+USFMbook[i]+'\n')
    USFMdoc.write('\mt1 '+WSbooks[i]+'\n')

    for l in inputDoc.split('\n'):
        l = l.strip()
        if l:
            USFMdoc.write(l)
            USFMdoc.write('\n')
