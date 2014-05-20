"""html.py - HTML classes"""

import cPickle
import os.path

import wx
import wx.lib.dragscroller
from wx import html

from config import *

_ = wx.GetTranslation


class HelpSystem(html.HtmlHelpController):
    def __init__(self, frame):
        super(HelpSystem, self).__init__(parentWindow=frame)
        self._frame = frame
        self.SetTempDir(os.path.join(frame._app.userdatadir, ""))
        self.SetTitleFormat("%s")
        self.UseConfig(frame._app.config, "Help")
        filename = os.path.join(frame._app.cwd, "locale",
            frame._app.locale.GetCanonicalName(), "help", "header.hhp")
        if not os.path.isfile(filename):
            filename = os.path.join(frame._app.cwd, "locale", "en_US", "help",
                "header.hhp")
        self.AddBook(filename)

    def show_frame(self):
        frame = self.GetFrame()
        if not frame:
            self.DisplayContents()
            self.GetHelpWindow().Bind(html.EVT_HTML_LINK_CLICKED,
                self.OnHtmlLinkClicked)
        else:
            frame.Raise()

    def OnHtmlLinkClicked(self, event):
        link = event.GetLinkInfo().GetHref()
        if link.startswith("http:") or link.startswith("mailto:"):
            wx.LaunchDefaultBrowser(link)
        else:
            event.Skip()


class PrintingSystem(html.HtmlEasyPrinting):
    def __init__(self, frame):
        super(PrintingSystem, self).__init__("Berean", frame)
        self._frame = frame
        data = self.GetPageSetupData()
        data.SetMarginTopLeft(wx.Point(15, 15))
        data.SetMarginBottomRight(wx.Point(15, 15))
        self.SetFooter(_("<div align=\"center\"><font size=\"-1\">Page " \
            "@PAGENUM@</font></div>"))
        self.SetStandardFonts(**frame.default_font)

    def get_chapter_text(self):
        text = self._frame.get_htmlwindow().get_html(
            *self._frame.reference[:2])
        tab = self._frame.notebook.GetSelection()
        if tab < len(self._frame.version_list):
            text = text.replace("</b>",
                " (%s)</b>" % self._frame.notebook.GetPageText(tab), 1)
        return text

    def print_(self):
        if wx.VERSION_STRING >= "2.8.11" and wx.VERSION_STRING != "2.9.0.0":
            self.SetName(self._frame.GetTitle()[9:])
        self.PrintText(self.get_chapter_text())

    def preview(self):
        if wx.VERSION_STRING >= "2.8.11" and wx.VERSION_STRING != "2.9.0.0":
            self.SetName(self._frame.GetTitle()[9:])
        self.PreviewText(self.get_chapter_text())


class BaseHtmlWindow(html.HtmlWindow):
    def __init__(self, parent, frame):
        super(BaseHtmlWindow, self).__init__(parent)
        self.SetAcceleratorTable(wx.AcceleratorTable([(wx.ACCEL_CTRL, ord("A"),
            wx.ID_SELECTALL)]))
        self.SetStandardFonts(**frame.default_font)
        self.Bind(wx.EVT_MENU, self.OnSelectAll, id=wx.ID_SELECTALL)
        self.dragscroller = wx.lib.dragscroller.DragScroller(self)
        self.Bind(wx.EVT_MIDDLE_DOWN, self.OnMiddleDown)
        self.Bind(wx.EVT_MIDDLE_UP, self.OnMiddleUp)

    def OnSelectAll(self, event):
        self.SelectAll()

    def OnMiddleDown(self, event):
        if not self.HasCapture():  # Skip event if context menu is shown
            self.dragscroller.Start(event.GetPosition())

    def OnMiddleUp(self, event):
        self.dragscroller.Stop()


class BaseChapterWindow(BaseHtmlWindow):
    def __init__(self, parent, frame):
        super(BaseChapterWindow, self).__init__(parent, frame)
        self._frame = frame
        self.current_verse = -1
        self.reference = None
        if wx.VERSION_STRING >= "2.9":
            self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        else:  # wxHtmlWindow doesn't generate EVT_CONTEXT_MENU in 2.8
            self.Bind(wx.EVT_RIGHT_UP, self.OnContextMenu)

    def load_chapter(self, book, chapter, verse=-1):
        self.SetPage(self.get_html(book, chapter, verse))
        if verse > 1 and self.HasAnchor(str(verse)):
            self.current_verse = -1
            wx.CallAfter(self.ScrollToAnchor, str(verse))
        self.reference = (book, chapter, verse)

    def OnContextMenu(self, event):
        menu = wx.Menu()
        selected = len(self.SelectionToText()) > 0
        if selected:
            menu.Append(wx.ID_COPY, _("&Copy"))
        menu.Append(wx.ID_SELECTALL, _("Select &All"))
        menu.AppendSeparator()
        search_item = menu.Append(wx.ID_ANY, _("&Search for Selected Text"))
        self.Bind(wx.EVT_MENU, self.OnSearch, search_item)
        menu.Enable(search_item.GetId(), selected)
        menu.AppendSeparator()
        menu.Append(wx.ID_PRINT, _("&Print..."))
        menu.Append(wx.ID_PREVIEW, _("P&rint Preview..."))
        self.PopupMenu(menu)

    def OnSearch(self, event):
        if not self._frame.aui.GetPane("search_pane").IsShown():
            self._frame.show_search_pane()
        self._frame.search.text.SetValue(
            self.SelectionToText().strip().lstrip("1234567890 "))
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
            with open(filename, 'rb') as Bible:
                self.Bible = cPickle.load(Bible)
        except Exception as exc_value:
            wx.MessageBox(_("Could not load %s.\n\nError: %s") % (version,
                exc_value), _("Error"), wx.ICON_WARNING | wx.OK)
        else:
            self.description = VERSION_DESCRIPTIONS[version]

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
            verses = [_("<font color=\"gray\">%s %d is not in this version." \
                "</font>") % (BOOK_NAMES[book - 1], chapter)]
        return "<html><body><font size=\"%d\"><div align=center>%s</div>%s" \
            "</font></body></html>" % (self._frame.zoom_level, header,
            "<br />".join(verses))
