"""printing.py - printer class and save as function for Berean"""

import wx
from wx import html

from info import *

_ = wx.GetTranslation

class Printer(html.HtmlEasyPrinting):
    def __init__(self, frame):
        html.HtmlEasyPrinting.__init__(self, "Berean", frame)
        self._frame = frame

        data = self.GetPageSetupData()
        data.SetMarginTopLeft(wx.Point(15, 15))
        data.SetMarginBottomRight(wx.Point(15, 15))
        self.SetFooter("<div align=center><font size=-1>Page @PAGENUM@</font></div>")

    def GetChapter(self):
        browser = self._frame.GetBrowser()
        text = browser.GetPage(self._frame.reference[0], self._frame.reference[1])
        if self._frame.notebook.GetSelection() < len(self._frame.versions):
            pos = text.index("</b>")
            text = text[:pos] + " (%s)" % browser.version + text[pos:]
        return text

    def SaveAs(self):
        title = "%s %d (%s)" % (BOOK_NAMES[self._frame.reference[0] - 1], self._frame.reference[1], self._frame.notebook.GetPageText(self._frame.notebook.GetSelection()))
        dialog = wx.FileDialog(self._frame, defaultDir=wx.StandardPaths.Get().GetDocumentsDir(), defaultFile="%s.html" % title, wildcard=_("HTML Documents (*.html;*.htm)|*.html;*.htm"), style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            html = open(dialog.GetPath(), 'w')
            html.write(self.GetChapter().replace("<html>", head % title).encode("utf_8"))
            html.close()
        dialog.Destroy()

    def Print(self):
        if wx.VERSION_STRING >= "2.8.11.0":
            self.SetName("%s %d (%s)" % (BOOK_NAMES[self._frame.reference[0] - 1], self._frame.reference[1], self._frame.notebook.GetPageText(self._frame.notebook.GetSelection())))
        self.PrintText(self.GetChapter())

    def Preview(self):
        if wx.VERSION_STRING >= "2.8.11.0":
            self.SetName("%s %d (%s)" % (BOOK_NAMES[self._frame.reference[0] - 1], self._frame.reference[1], self._frame.notebook.GetPageText(self._frame.notebook.GetSelection())))
        self.PreviewText(self.GetChapter())

head = """<html>
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <title>%s</title>
</head>"""
