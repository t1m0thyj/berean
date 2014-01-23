"""html.py - HTML classes and functions for Berean"""

import cPickle
import os.path

import wx
import wx.lib.dragscroller
from wx import html

from info import *

_ = wx.GetTranslation


def save_as(frame):
    browser = frame.get_htmlwindow()
    title = "%s %d (%s)" % (BOOK_NAMES[frame.reference[0] - 1],
        frame.reference[1], frame.notebook.GetPageText(
        frame.notebook.GetSelection()))
    filename = wx.FileSelector(default_filename="%s.html" % title,
        wildcard=_("HTML Documents (*.html;*.htm)|*.html;*.htm"),
        flags=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT, parent=frame)
    if len(filename):
        html = open(filename, 'w')
        html.write(browser.get_html(frame.reference[0], frame.reference[1]). \
            encode("utf_8"))
        html.close()


class Printer(html.HtmlEasyPrinting):
    def __init__(self, frame):
        super(Printer, self).__init__("Berean", frame)
        self._frame = frame
        data = self.GetPageSetupData()
        data.SetMarginTopLeft(wx.Point(15, 15))
        data.SetMarginBottomRight(wx.Point(15, 15))
        self.SetFooter(_("<div align=center><font size=\"-1\">Page @PAGENUM@</font></div>"))

    def get_chapter(self):
        browser = self._frame.get_htmlwindow()
        text = browser.get_html(self._frame.reference[0],
            self._frame.reference[1])
        if self._frame.notebook.GetSelection() < len(self._frame.versions):
            pos = text.index("</b>")
            text = text[:pos] + " (%s)" % browser.version + text[pos:]
        return text

    def print_chapter(self):
        if wx.VERSION_STRING >= "2.8.11.0":
            self.SetName("%s %d (%s)" % (BOOK_NAMES[self._frame.reference[0] - 1], self._frame.reference[1], self._frame.notebook.GetPageText(self._frame.notebook.GetSelection())))
        self.PrintText(self.get_chapter())

    def preview_chapter(self):
        if wx.VERSION_STRING >= "2.8.11.0":
            self.SetName("%s %d (%s)" % (BOOK_NAMES[self._frame.reference[0] - 1], self._frame.reference[1], self._frame.notebook.GetPageText(self._frame.notebook.GetSelection())))
        self.PreviewText(self.get_chapter())


class BaseHtmlWindow(html.HtmlWindow):
    def __init__(self, parent):
        super(BaseHtmlWindow, self).__init__(parent)
        self.SetAcceleratorTable(wx.AcceleratorTable([(wx.ACCEL_CTRL,
            ord("A"), wx.ID_SELECTALL)]))
        self.Bind(wx.EVT_MENU, lambda event: self.SelectAll(),
            id=wx.ID_SELECTALL)
        self.dragscroller = wx.lib.dragscroller.DragScroller(self)
        self.Bind(wx.EVT_MIDDLE_DOWN, self.OnMiddleDown)
        self.Bind(wx.EVT_MIDDLE_UP, self.OnMiddleUp)

    def OnMiddleDown(self, event):
        self.dragscroller.Start(event.GetPosition())

    def OnMiddleUp(self, event):
        self.dragscroller.Stop()


class BaseChapterWindow(BaseHtmlWindow):
    def __init__(self, parent, frame):
        super(BaseChapterWindow, self).__init__(parent)
        self._frame = frame
        self.current_verse = -1
        if wx.VERSION_STRING >= "2.9.0.0":
            self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        else:
            self.Bind(wx.EVT_RIGHT_UP, self.OnContextMenu)

    def load_chapter(self, book, chapter, verse=-1):
        self.SetPage(self.get_html(book, chapter, verse))
        if verse > 1 and self.HasAnchor(str(verse)):
            wx.CallAfter(self.ScrollToAnchor, str(verse))
            self.current_verse = -1

    def OnContextMenu(self, event):
        menu = wx.Menu()
        selection = self.SelectionToText()
        menu.Append(wx.ID_COPY, _("&Copy\tCtrl+C"))
        menu.Enable(wx.ID_COPY, len(selection))
        menu.Append(wx.ID_SELECTALL, _("Select &All\tCtrl+A"))
        menu.AppendSeparator()
        search_item = menu.Append(-1, _("&Search for Selected Text"))
        self.Bind(wx.EVT_MENU, self.OnFindText, search_item)
        menu.Enable(search_item.GetId(), len(selection))
        menu.AppendSeparator()
        menu.Append(wx.ID_PRINT, _("&Print...\tCtrl+P"))
        menu.Append(wx.ID_PREVIEW, _("P&rint Preview...\tCtrl+Alt+P"))
        self.PopupMenu(menu)

    def OnFindText(self, event):
        if not self._frame.aui.GetPane("search_pane").IsShown():
            self._frame.ShowSearchPane()
        self._frame.search.text.SetValue(self.SelectionToText().strip().lstrip("1234567890 "))
        self._frame.search.OnSearch(None)


class ChapterWindow(BaseChapterWindow):
    def __init__(self, parent, version):
        super(ChapterWindow, self).__init__(parent, parent.GetParent())
        filename = os.path.join(self._frame._app.cwd, "versions",
            "%s.bbl" % version)
        if not os.path.isfile(filename):
            filename = os.path.join(self._frame._app.userdatadir, "versions",
                "%s.bbl" % version)
        try:
            fileobj = open(filename, 'rb')
            try:
                self.Bible = cPickle.load(fileobj)
            finally:
                fileobj.close()
            self.description, self.flag_name = self.Bible[0]
        except Exception, exc_value:
            wx.MessageBox(_("Could not load %s.\n\nError: %s") % (version,
                exc_value), _("Error"), wx.ICON_WARNING | wx.OK)
        self.version = version

    def get_html(self, book, chapter, verse=-1):
        if self.Bible[book][chapter] != (None,):
            header = ["<div align=center>",
                "<font size=\"+1\"><b>%s %d</b></font>" % (self.Bible[book][0],
                chapter), "</div>", ""]
            if self.Bible[book][chapter][0]:
                header[1] += "<br />"
                header.insert(2, self.Bible[book][chapter][0].replace("[",
                    "<i>").replace("]", "</i>"))
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
        else:
            header = []
            verses = [
                _("<font color=gray>%s %d is not in this version.</font>") %
                (BOOK_NAMES[book - 1], chapter)]
        title = "%s %d (%s)" % (BOOK_NAMES[book - 1], chapter, self.version)
        return HTML % (title, self._frame.zoom_level, "\n  ".join(header) +
            "<br />\n  ".join(verses))


HTML = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <title>%s</title>
</head>
<body>
  <font size=\"%d\">
  %s
  </font>
</body>
</html>"""