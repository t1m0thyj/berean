import cPickle
import sys

sys.path.insert(0, "..\\..")
from settings import BOOK_LENGTHS, CHAPTER_LENGTHS, VERSION_NAMES

fileobj = open("v11n.txt", 'w')
for version in VERSION_NAMES:
    print >> fileobj, version
    with open("..\\%s.bbl" % version, 'rb') as fileobj2:
        Bible = cPickle.load(fileobj2)
    for b in range(1, len(Bible)):
        if Bible[b] == tuple():
            continue
        if len(Bible[b]) != BOOK_LENGTHS[b - 1] + 1:
            print >> fileobj, b
        for c in range(1, len(Bible[b])):
            try:
                if len(Bible[b][c]) != CHAPTER_LENGTHS[b - 1][c - 1] + 1:
                    print >> fileobj, "%d.%d" % (b, c)
            except StandardError:
                print >> fileobj, "*%d.%d" % (b, c)
    print >> fileobj
