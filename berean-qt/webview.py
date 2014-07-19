"""webview.py - webview class"""

import pickle
import os.path

from PyQt5.QtWebKitWidgets import QWebView

from config import *


class ChapterWebView(QWebView):
    def __init__(self, mainwindow, version):
        super(ChapterWebView, self).__init__()
        self._mainwindow = mainwindow
        filename = os.path.join(mainwindow._app.cwd, "versions",
            "%s.bbl" % version)
        with open(filename, 'rb') as Bible:
            self.Bible = pickle.load(Bible)
        self.setHtml(self.get_html(*mainwindow.reference))

    def get_html(self, book, chapter, verse=-1):
        if self.Bible[book]:
            header = "<font size=\"+2\"><b>%s %d</b></font>" % \
                (BOOK_NAMES[book - 1], chapter)
            if self.Bible[book][chapter][0]:
                header += "<br /><i>%s</i>" % self.Bible[book][chapter][0]. \
                    replace("]", "<i>").replace("[", "</i>")
            verses = []
            for i in range(1, len(self.Bible[book][chapter])):
                if not len(self.Bible[book][chapter][i]):
                    continue
                text = "<font size=\"-1\">%d&nbsp;</font>%s" % (i,
                    self.Bible[book][chapter][i].replace("[", "<i>").
                    replace("]", "</i>"))
                if i == verse:
                    text = "<b>%s</b>" % text
                verses.append("<a name=\"%d\">%s</a>" % (i, text))
            if chapter == BOOK_LENGTHS[book - 1] and self.Bible[book][0]:
                verses[-1] += "<hr /><div align=\"center\"><i>%s</i></div>" % \
                    self.Bible[book][0].replace("]", "<i>"). \
                    replace("[", "</i>")
        else:
            header = ""
            verses = [_("<font color=\"gray\">%s %d is not in this version."
                "</font>") % (BOOK_NAMES[book - 1], chapter)]
        return "<html><body><font size=\"%d\"><div align=center>%s</div>%s" \
            "</font></body></html>" % \
            (self._mainwindow.zoom, header, "<br />".join(verses))
