import os
import subprocess
import sys

languages = sys.argv[1:]
if not languages:
    languages = [path for path in os.listdir(".") if os.path.isdir(path)]
for language in languages:
    po_file = os.path.join(language, "%s.po" % language)
    if not os.path.isfile(po_file):
        continue
    lc_messages = os.path.join(language, "LC_MESSAGES")
    mo_file = os.path.join(lc_messages, "berean.mo")
    if not os.path.isdir(lc_messages):
        os.mkdir(lc_messages)
    elif (os.path.isfile(mo_file) and
            os.path.getmtime(mo_file) >= os.path.getmtime(po_file)):
        continue
    print "Compiling", language
    subprocess.call("%s\\Tools\\i18n\\msgfmt.py -o %s %s" % (sys.prefix,
                                                             mo_file, po_file),
                    shell=True)
