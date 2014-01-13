"""html.py - HTML classes and functions for Berean"""

import cPickle
import os.path

import wx
import wx.lib.dragscroller
from wx import html

from info import *

_ = wx.GetTranslation


class BaseHtmlWindow(html.HtmlWindow):
    def __init__(self, parent):
        super(BaseHtmlWindow, self).__init__(parent)

        self.dragscroller = wx.lib.dragscroller.DragScroller(self)
        self.SetAcceleratorTable(wx.AcceleratorTable([
            (wx.ACCEL_CTRL, ord("A"), wx.ID_SELECTALL)]))

        self.Bind(wx.EVT_MENU, self.OnSelectAll, id=wx.ID_SELECTALL)
        self.Bind(wx.EVT_MIDDLE_DOWN, self.OnMiddleDown)
        self.Bind(wx.EVT_MIDDLE_UP, self.OnMiddleUp)

    def OnSelectAll(self, event):
        self.SelectAll()

    def OnMiddleDown(self, event):
        self.dragscroller.Start(event.GetPosition())

    def OnMiddleUp(self, event):
        self.dragscroller.Stop()


class HtmlWindow(BaseHtmlWindow):
    def __init__(self, parent, frame):
        super(HtmlWindow, self).__init__(parent)
        self._frame = frame

        self.verse = -1

        self.Bind(wx.EVT_RIGHT_UP, self.OnContextMenu)  # EVT_CONTEXT_MENU doesn't work for wxHtmlWindow in 2.8

    def LoadChapter(self, book, chapter, verse=-1):
        self.SetPage(self.GetPage(book, chapter, verse))
        if verse > 1 and self.HasAnchor(str(verse)):
            wx.CallAfter(self.ScrollToAnchor, str(verse))
            self.verse = -1

    def OnContextMenu(self, event):
        menu = wx.Menu()
        selection = self.SelectionToText()
        if len(selection):
            menu.Append(wx.ID_COPY, _("&Copy\tCtrl+C"))
        menu.Append(wx.ID_SELECTALL, _("Select &All\tCtrl+A"))
        menu.AppendSeparator()
        if len(selection):
            ID_FIND_TEXT = wx.NewId()
            menu.Append(ID_FIND_TEXT, _("&Search for Selected Text"))
            self.Bind(wx.EVT_MENU, self.OnFindText, id=ID_FIND_TEXT)
            menu.AppendSeparator()
        menu.Append(wx.ID_PRINT, _("&Print...\tCtrl+P"))
        menu.Append(wx.ID_PREVIEW, _("P&rint Preview...\tCtrl+Alt+P"))
        self.PopupMenu(menu)

    def OnFindText(self, event):
        if not self._frame.aui.GetPane("searchpane").IsShown():
            self._frame.ShowSearchPane()
        self._frame.search.text.SetValue(self.SelectionToText().strip().lstrip("1234567890 "))
        self._frame.search.OnSearch(None)


class ChapterWindow(HtmlWindow):
    def __init__(self, parent, version):
        super(ChapterWindow, self).__init__(parent, parent.GetParent())

        self.version = version

        filename = os.path.join(self._frame._app.cwd, "versions", "%s.bbl" % version)
        if not os.path.isfile(filename):
            filename = os.path.join(self._frame._app.userdatadir, "versions", "%s.bbl" % version)
        try:
            fileobj = open(filename, 'rb')
            try:
                self.Bible = cPickle.load(fileobj)
            finally:
                fileobj.close()
            self.description, self.flag = self.Bible[0]
        except Exception, exc_value:
            wx.MessageBox(_("Could not load %s.\n\nError: %s") % (version,
                exc_value), _("Error"), wx.ICON_WARNING | wx.OK)

    def GetPage(self, book, chapter, verse=-1):
        if self.Bible[book][chapter] != (None,):
            items = [heading % (self.Bible[book][0], chapter)]
            if self.Bible[book][chapter][0]:
                items[0] = subtitle % (items[0][:-6], self.Bible[book][chapter][0].replace("[", "<i>").replace("]", "</i>"))
            for i in range(1, len(self.Bible[book][chapter])):
                if not len(self.Bible[book][chapter][i]):
                    continue
                items.append("<font size=-1>%d&nbsp;</font>%s<a name=\"%d\"></a>" % (i, self.Bible[book][chapter][i].replace("[", "<i>").replace("]", "</i>"), i + 1))
                if i == verse:
                    items[-1] = "<b>%s</b>" % items[-1]
        else:
            items = [_("<font color=gray>%s %d is not in the %s.</font>") % (BOOK_NAMES[book - 1], chapter, self.version)]
        return body % (self._frame.zoom_level, "\n  <br />\n  ".join(items))


class Printer(html.HtmlEasyPrinting):
    def __init__(self, frame):
        super(Printer, self).__init__("Berean", frame)
        self._frame = frame

        data = self.GetPageSetupData()
        data.SetMarginTopLeft(wx.Point(15, 15))
        data.SetMarginBottomRight(wx.Point(15, 15))
        self.SetFooter(_("<div align=center><font size=-1>Page @PAGENUM@</font></div>"))

    def get_chapter(self):
        browser = self._frame.GetBrowser()
        text = browser.GetPage(self._frame.reference[0], self._frame.reference[1])
        if self._frame.notebook.GetSelection() < len(self._frame.versions):
            pos = text.index("</b>")
            text = text[:pos] + " (%s)" % browser.version + text[pos:]
        return text

    def save_as(self):
        title = "%s %d (%s)" % (BOOK_NAMES[self._frame.reference[0] - 1], self._frame.reference[1], self._frame.notebook.GetPageText(self._frame.notebook.GetSelection()))
        dialog = wx.FileDialog(self._frame, defaultDir=wx.StandardPaths.Get().GetDocumentsDir(), defaultFile="%s.html" % title, wildcard=_("HTML Documents (*.html;*.htm)|*.html;*.htm"), style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            html = open(dialog.GetPath(), 'w')
            html.write(self.get_chapter().replace("<html>", head % title).encode("utf_8"))
            html.close()
        dialog.Destroy()

    def print_chapter(self):
        if wx.VERSION_STRING >= "2.8.11.0":
            self.SetName("%s %d (%s)" % (BOOK_NAMES[self._frame.reference[0] - 1], self._frame.reference[1], self._frame.notebook.GetPageText(self._frame.notebook.GetSelection())))
        self.PrintText(self.get_chapter())

    def preview_chapter(self):
        if wx.VERSION_STRING >= "2.8.11.0":
            self.SetName("%s %d (%s)" % (BOOK_NAMES[self._frame.reference[0] - 1], self._frame.reference[1], self._frame.notebook.GetPageText(self._frame.notebook.GetSelection())))
        self.PreviewText(self.get_chapter())


head = """<html>
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <title>%s</title>
</head>"""
body = """<html>
<body>
  <font size=%d>
  %s
  </font>
</body>
</html>
"""
heading = """<div align=center>
  <font size=+1><b>%s %d</b></font>
  </div>"""
subtitle = """%s<br />
  %s
  </div>"""
