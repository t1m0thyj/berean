"""index.py - indexing dialog class for Berean"""

import cPickle
import os.path
import re

import wx

_ = wx.GetTranslation

def index(app, Bible, version):
    dialog = wx.ProgressDialog(_("Indexing"), _("Please wait, indexing the %s...") % version, 70, style=wx.PD_AUTO_HIDE | wx.PD_ELAPSED_TIME | wx.PD_REMAINING_TIME)
    punctuation = re.compile(r'((?<=^)\W+|\W+(?=$))')
    index = {}
    for b in range(1, len(Bible)):
        for c in range(1, len(Bible[b])):
            for v in range(1, len(Bible[b][c])):
                verse = Bible[b][c][v]
                if "<div" in verse:
                    verse = verse[:verse.index("<div")]
                words = []
                for word in verse.split():
                    word = punctuation.sub(r'', word)
                    if word not in words:
                        if word not in index:
                            index[word] = []
                        index[word].append("".join([chr(int(i) + 32) for i in (b, c, v)]))
                        words.append(word)
        dialog.Update(b)
    for word in index:
        index[word] = "".join(index[word])
    dialog.Update(68)
    fileobj = open(os.path.join(app.userdatadir, "indexes", "%s.idx" % version), 'wb')
    cPickle.dump(index, fileobj, -1)
    fileobj.close()
    dialog.Destroy()
    return index
