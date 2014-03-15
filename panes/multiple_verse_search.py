"""multiple_verse_search.py - multiple verse search pane class"""

import wx
from wx import aui, html

from config import *
from html import BaseHtmlWindow
from refalize import refalize2

_ = wx.GetTranslation


class MultipleVerseSearch(wx.Panel):
    def __init__(self, parent):
        super(MultipleVerseSearch, self).__init__(parent, -1)
        self._parent = parent
        self.html = ""
        self.last_version = -1

        self.toolbar = aui.AuiToolBar(self, -1, (-1, -1), (-1, -1),
            aui.AUI_TB_DEFAULT_STYLE | aui.AUI_TB_OVERFLOW | \
            aui.AUI_TB_HORZ_TEXT)
        self.toolbar.AddLabel(-1, _("Version:"))
        self.version = wx.Choice(self.toolbar, -1, choices=parent.version_list)
        tab = parent.notebook.GetSelection()
        if tab < len(parent.version_list):
            self.version.SetSelection(tab)
        else:
            self.version.SetSelection(0)
        self.toolbar.AddControl(self.version)
        self.toolbar.AddSeparator()
        search_item = self.toolbar.AddTool(-1, _("Search"),
            parent.get_bitmap("search"), _("Search (Ctrl+Enter)"))
        self.Bind(wx.EVT_MENU, self.OnSearch, search_item)
        self.toolbar.AddTool(wx.ID_PRINT, _("Print"),
            parent.get_bitmap("print"), _("Print Search Results"))
        self.toolbar.EnableTool(wx.ID_PRINT, False)
        self.Bind(wx.EVT_MENU, self.OnPrint, id=wx.ID_PRINT)
        ##self.toolbar.AddTool(wx.ID_COPY, _("Copy"), parent.get_bitmap("copy"),
        ##    _("Copy with Formatting"))
        ##self.toolbar.EnableTool(wx.ID_COPY, False)
        self.toolbar.Realize()
        self.splitter_window = wx.SplitterWindow(self, -1)
        self.verse_list = wx.TextCtrl(self.splitter_window, -1,
            parent._app.config.Read("Search/LastMultipleVerseSearch"),
            style=wx.TE_MULTILINE)
        self.verse_list.SetAcceleratorTable(wx.AcceleratorTable([
            (wx.ACCEL_CTRL, wx.WXK_RETURN, search_item.GetId())]))
        self.results = BaseHtmlWindow(self.splitter_window, parent)
        self.results.Bind(html.EVT_HTML_LINK_CLICKED, self.OnHtmlLinkClicked)
        if wx.VERSION_STRING >= "2.9.0.0":
            self.results.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        else:   # wxHtmlWindow doesn't generate EVT_CONTEXT_MENU in 2.8
            self.results.Bind(wx.EVT_RIGHT_UP, self.OnContextMenu)
        self.splitter_window.SplitHorizontally(self.verse_list, self.results,
            60)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.toolbar, 0)
        sizer.Add(self.splitter_window, 1, wx.ALL | wx.EXPAND, 0)
        self.SetSizer(sizer)

    def OnSearch(self, event):
        try:
            version = self.version.GetSelection()
            Bible = self._parent.get_htmlwindow(version).Bible
            data = refalize2(self.verse_list.GetValue(), Bible)
            version_abbrev = self.version.GetStringSelection()
            results = []
            for start, stop in data:
                b1, c1, v1 = start
                b2, c2, v2 = stop
                try:
                    if start == stop:
                        if len(Bible[b1][c1][v1]):
                            results.append("<p><a href=\"%d.%d.%d\">%s %d:%d (%s)</a><br />%s</p>" % (b1, c1, v1, BOOK_NAMES[b1 - 1], c1, v1, version_abbrev, Bible[b1][c1][v1]))
                        else:
                            results.append(_("<p><font color=\"gray\">%s %d:%d is not in the %s.</font></p>") % (BOOK_NAMES[b1 - 1], c1, v1, version_abbrev))
                    else:
                        result = []
                        for b in range(b1, b2 + 1):
                            for c in range(1, len(Bible[b])):
                                for v in range(0, len(Bible[b][c])):
                                    if start <= (b, c, v) <= stop:
                                        if c == 1 and not v:
                                            result.append("<hr /><a href=\"%d.%d.-1\">%s %d</a>" % (b, c, BOOK_NAMES[b - 1], c))
                                        elif not v:
                                            result.append("<p><a href=\"%d.%d.-1\">%s %d</a></p>" % (b, c, BOOK_NAMES[b - 1], c))
                                        elif len(Bible[b][c][v]):
                                            result.append("<font size=\"-1\"><a href=\"%d.%d.%d\">%d</a>&nbsp;</font>%s" % (b, c, v, v, Bible[b][c][v]))
                                        else:
                                            result.append("")
                        if not len(result):
                            raise AssertionError
                except:
                    wx.MessageBox(_("%s %d:%d is not a valid reference.") % (BOOK_NAMES[b1 - 1], c1, v1), "Berean", wx.ICON_EXCLAMATION | wx.OK)
                    return
                if start != stop:
                    if b1 == b2 and c1 == c2:
                        results.append("<p><a href=\"%d.%d.%d\">%s %d:%d-%d (%s)</a><br />%s</p>" % (b1, c1, v1, BOOK_NAMES[b1 - 1], c1, v1, v2, version_abbrev, " ".join(result)))
                    elif b1 == b2:
                        results.append("<p><a href=\"%d.%d.%d\">%s %d:%d-%d:%d (%s)</a><br />%s</p>" % (b1, c1, v1, BOOK_NAMES[b1 - 1], c1, v1, c2, v2, version_abbrev, " ".join(result)))
                    else:
                        results.append("<p><a href=\"%d.%d.%d\">%s %d:%d - %s %d:%d (%s)</a><br />%s</p>" % (b1, c1, v1, BOOK_NAMES[b1 - 1], c1, v1, BOOK_NAMES[b2 - 1], c2, v2, version_abbrev, " ".join(result)))
            self.html = "<html><body><font size=\"%d\">%s</font></body></html>" % (self._parent.zoom_level, "".join(results))
            self.results.SetPage(self.html)
            self.toolbar.EnableTool(wx.ID_PRINT, True)
            ##self.toolbar.EnableTool(wx.ID_COPY, True)
            self.toolbar.Refresh(False)
            self.last_version = version
            wx.CallAfter(self.results.SetFocus)
        except:
            wx.MessageBox(_("One or more of the references you have entered are not valid."), "Berean", wx.ICON_EXCLAMATION | wx.OK)

    def OnPrint(self, event):
        if wx.VERSION_STRING >= "2.8.11.0" and wx.VERSION_STRING != "2.9.0.0":
            self._parent.printing.SetName(_("Search Results"))
        if event.GetId() == wx.ID_PRINT:
            self._parent.printing.PrintText(self.html)
        else:
            self._parent.printing.PreviewText(self.html)

    def OnHtmlLinkClicked(self, event):
        if self._parent.notebook.GetSelection() != self.last_version:
            self._parent.notebook.SetSelection(self.last_version)
        self._parent.load_chapter(*map(int,
            event.GetLinkInfo().GetHref().split(".")))

    def OnContextMenu(self, event):
        if not len(self.html):
            return
        menu = wx.Menu()
        if len(self.results.SelectionToText()):
            menu.Append(wx.ID_COPY, _("&Copy\tCtrl+C"))
        menu.Append(wx.ID_SELECTALL, _("Select &All\tCtrl+A"))
        menu.AppendSeparator()
        print_item = menu.Append(wx.ID_PRINT, _("&Print...\tCtrl+P"))
        self.Bind(wx.EVT_MENU, self.OnPrint, print_item)
        preview_item = menu.Append(wx.ID_PREVIEW,
            _("P&rint Preview...\tCtrl+Alt+P"))
        self.Bind(wx.EVT_MENU, self.OnPrint, preview_item)
        self.results.PopupMenu(menu)
