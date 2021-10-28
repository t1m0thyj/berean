import cPickle
import glob
import os
import sys

subdirs = sys.argv[1:] if len(sys.argv) > 1 else ("*",)
for subdir in subdirs:
    for filename in glob.glob("..\\%s\\*.bbl" % subdir):
        print "Optimizing %s" % os.path.basename(filename)[:-4]
        filename2 = "%s-tmp.bbl" % filename[:-4]
        os.rename(filename, filename2)
        with open(filename2, 'rb') as fileobj, \
                open(filename, 'wb') as fileobj2:
            cPickle.dump(cPickle.load(fileobj), fileobj2, -1)
        os.remove(filename2)
