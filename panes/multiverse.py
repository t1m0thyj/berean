"""multiverse.py - multi-verse retrieval pane class"""

import wx
from wx import aui, html

from config import *
from html import BaseHtmlWindow
from refalize import refalize2

_ = wx.GetTranslation


class MultiVersePane(wx.Panel):
    def __init__(self, parent):
        super(MultiVersePane, self).__init__(parent, -1)
        self._parent = parent
        self.html = ""
        self.last_version = -1

        self.toolbar = aui.AuiToolBar(self, -1, (-1, -1), (-1, -1),
            aui.AUI_TB_DEFAULT_STYLE | aui.AUI_TB_OVERFLOW | \
            aui.AUI_TB_HORZ_TEXT)
        self.toolbar.AddLabel(-1, _("Version:"))
        self.version = wx.Choice(self.toolbar, -1, choices=parent.version_list)
        tab = parent.notebook.GetSelection()
        self.version.SetSelection(int(tab < len(parent.version_list)) and tab)
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
            parent._app.config.Read("Search/LastMultiVerseRetrieval"),
            style=wx.TE_MULTILINE)
        self.verse_list.SetAcceleratorTable(wx.AcceleratorTable([
            (wx.ACCEL_CTRL, wx.WXK_RETURN, search_item.GetId())]))
        self.results = BaseHtmlWindow(self.splitter_window, parent)
        self.results.Bind(html.EVT_HTML_LINK_CLICKED, self.OnHtmlLinkClicked)
        if wx.VERSION_STRING >= "2.9.0.0":
            self.results.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        else:  # wxHtmlWindow doesn't generate EVT_CONTEXT_MENU in 2.8
            self.results.Bind(wx.EVT_RIGHT_UP, self.OnContextMenu)
        self.splitter_window.SplitHorizontally(self.verse_list, self.results,
            60)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.toolbar, 0)
        sizer.Add(self.splitter_window, 1, wx.ALL | wx.EXPAND, 0)
        self.SetSizer(sizer)

    def OnSearch(self, event):
        references, failed = refalize2(self.verse_list.GetValue())
        version = self.version.GetSelection()
        Bible = self._parent.get_htmlwindow(version).Bible
        version_abbrev = self.version.GetStringSelection()
        results = []
        for b, c, v, c2, v2, reference in references:
            try:
                if c2 == -1 and v2 == -1:
                    if len(Bible[b][c][v]):
                        results.append("<p><a href=\"%d.%d.%d\">%s %d:%d " \
                            "(%s)</a><br />%s</p>" % (b, c, v,
                            BOOK_NAMES[b - 1], c, v, version_abbrev,
                            Bible[b][c][v]))
                    else:
                        results.append(_("<p><font color=\"gray\">%s %d:%d " \
                            "is not in the %s.</font></p>") %
                            (BOOK_NAMES[b - 1], c, v, version_abbrev))
                else:
                    for c3 in range(c, c2 + 1):
                        v3, v4 = 1, len(Bible[b][c3]) - 1
                        if c3 == c:
                            v3 = v
                        if c3 == c2:
                            v4 = v2
                        verses = []
                        for v5 in range(v3, v4 + 1):
                            if len(Bible[b][c3][v5]):
                                verses.append("<font size=\"-1\"><a href=\"" \
                                    "%d.%d.%d\">%d</a>&nbsp;</font>%s" % (b,
                                    c3, v5, v5, Bible[b][c3][v5]))
                        if not len(verses):
                            raise IndexError
                        results.append("<p><a href=\"%d.%d.%d\">%s %d:%d-%d " \
                            "(%s)</a><br />%s</p>" % (b, c3, v3,
                            BOOK_NAMES[b - 1], c3, v3, v4, version_abbrev,
                            " ".join(verses)))
            except IndexError:
                failed.append(reference)
        if len(failed):
            results.insert(0, "<font color=\"red\">Some of the references " \
                "are not valid:<br />&nbsp;%s</font>" %
                "<br />&nbsp;".join(failed))
        self.html = "<html><body><font size=\"%d\">%s</font></body>" \
            "</html>" % (self._parent.zoom_level, "".join(results))
        self.results.SetPage(self.html)
        self.toolbar.EnableTool(wx.ID_PRINT, True)
        ##self.toolbar.EnableTool(wx.ID_COPY, True)
        self.toolbar.Refresh(False)
        self.last_version = version
        wx.CallAfter(self.results.SetFocus)

    def OnPrint(self, event):
        if wx.VERSION_STRING >= "2.8.11.0" and wx.VERSION_STRING != "2.9.0.0":
            self._parent.printing.SetName(_("Multi-Verse Retrieval"))
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
            menu.Append(wx.ID_COPY, _("&Copy"))
        menu.Append(wx.ID_SELECTALL, _("Select &All"))
        menu.AppendSeparator()
        print_item = menu.Append(wx.ID_PRINT, _("&Print..."))
        self.Bind(wx.EVT_MENU, self.OnPrint, print_item)
        preview_item = menu.Append(wx.ID_PREVIEW, _("P&rint Preview..."))
        self.Bind(wx.EVT_MENU, self.OnPrint, preview_item)
        self.results.PopupMenu(menu)
