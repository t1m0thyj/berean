import cPickle
import os
import shutil
import subprocess
import sys

sys.path.insert(0, "..\\..")
from settings import VERSION_NAMES

diff_tool = "C:\\Program Files (x86)\\WinMerge\\WinMergeU.exe"
os.mkdir("versions")
for version in VERSION_NAMES:
    with open("..\\%s.bbl" % version, 'rb') as fileobj:
        Bible = list(cPickle.load(fileobj))
    Bible[0] = unicode(Bible[0].strip())
    for b in range(1, len(Bible)):
        Bible[b] = list(Bible[b])
        if Bible[b] and Bible[b][0]:
            Bible[b][0] = unicode(Bible[b][0].strip())
        for c in range(1, len(Bible[b])):
            Bible[b][c] = list(Bible[b][c])
            if Bible[b][c][0]:
                if b == 19:
                    Bible[b][c][0] = unicode(Bible[b][c][0].strip())
                else:
                    Bible[b][c][0] = None
            if Bible[b][c] != [None]:
                for v in range(1, len(Bible[b][c])):
                    Bible[b][c][v] = unicode(Bible[b][c][v].strip())
            Bible[b][c] = tuple(Bible[b][c])
        Bible[b] = tuple(Bible[b])
    Bible = tuple(Bible)
    with open("versions\\%s-tmp.bbl" % version, 'wb') as fileobj:
        cPickle.dump(Bible, fileobj, -1)
    with open("versions\\%s-tmp.bbl" % version, 'rb') as fileobj, \
            open("versions\\%s.bbl" % version, 'wb') as fileobj2:
        cPickle.dump(cPickle.load(fileobj), fileobj2, -1)
    os.remove("versions\\%s-tmp.bbl" % version)
subprocess.call([diff_tool, "..", "versions"])
shutil.rmtree("versions")
