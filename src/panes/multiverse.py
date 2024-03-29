"""multiverse.py - multi-verse retrieval pane class"""

import wx
from wx import aui, html

from constants import BOOK_NAMES
from html2 import HtmlWindowBase
from refalize import refalize2

_ = wx.GetTranslation


class MultiVersePane(wx.SplitterWindow):
    def __init__(self, parent):
        super(MultiVersePane, self).__init__(parent)
        self._parent = parent
        self.html = ""
        self.last_version = -1

        left_panel = wx.Panel(self)
        self.toolbar = aui.AuiToolBar(left_panel, wx.ID_ANY, style=aui.AUI_TB_DEFAULT_STYLE |
                                                                   aui.AUI_TB_PLAIN_BACKGROUND)
        self.toolbar.AddLabel(-1, _("Version:"), width=self.toolbar.GetTextExtent(_("Version:"))[0])
        self.version = wx.Choice(self.toolbar, choices=parent.version_list)
        tab = parent.notebook.GetSelection()
        self.version.SetSelection(int(tab < len(parent.version_list)) and tab)
        self.toolbar.AddControl(self.version)
        self.toolbar.AddSeparator()
        ID_SEARCH = wx.NewId()
        self.toolbar.AddTool(ID_SEARCH, "", parent.get_bitmap("search"),
                             _("Search (Ctrl+Enter)"))
        self.Bind(wx.EVT_MENU, self.OnSearch, id=ID_SEARCH)
        self.toolbar.AddTool(wx.ID_PREVIEW, "", parent.get_bitmap("print"),
                             _("Print Verses"))
        self.toolbar.EnableTool(wx.ID_PREVIEW, False)
        self.Bind(wx.EVT_MENU, self.OnPrint, id=wx.ID_PREVIEW)
        self.toolbar.AddTool(wx.ID_COPY, "", parent.get_bitmap("copy"),
                             _("Copy Verses"))
        self.toolbar.EnableTool(wx.ID_COPY, False)
        self.Bind(wx.EVT_MENU, self.OnCopy, id=wx.ID_COPY)
        self.toolbar.Realize()

        self.verse_list = wx.TextCtrl(left_panel,
                                      value=parent._app.config.Read("MultiVerse/LastVerseList"),
                                      style=wx.TE_MULTILINE)
        self.verse_list.SetAcceleratorTable(wx.AcceleratorTable([
            (wx.ACCEL_CTRL, wx.WXK_RETURN, ID_SEARCH),
            (wx.ACCEL_CTRL, ord("A"), wx.ID_SELECTALL)]))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.toolbar, 0)
        sizer.Add(self.verse_list, 1, wx.ALL | wx.EXPAND, 0)
        left_panel.SetSizer(sizer)

        self.htmlwindow = HtmlWindowBase(self, parent)
        self.htmlwindow.Bind(html.EVT_HTML_LINK_CLICKED, self.OnHtmlLinkClicked)

        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.SetMinimumPaneSize(self.toolbar.GetMinWidth() - self.GetSashSize())
        self.SplitVertically(left_panel, self.htmlwindow,
                             parent._app.config.ReadInt("MultiVerse/SplitterPosition", 0))

    def OnSearch(self, event):
        references, failed = refalize2(self.verse_list.GetValue())
        version = self.version.GetSelection()
        Bible = self._parent.get_htmlwindow(version).Bible
        results = []
        version_name = self.version.GetStringSelection()
        for b, c, v, c2, v2, reference in references:
            try:
                if c2 == -1 and v2 == -1:
                    if Bible[b][c][v]:
                        results.append("<p><a href=\"%d.%d.%d\">%s %d:%d (%s)</a><br>%s</p>" %
                                       (b, c, v, BOOK_NAMES[b - 1], c, v, version_name,
                                        Bible[b][c][v]))
                    else:
                        results.append(_("<p><font color=\"gray\">%s %d:%d is not in the %s."
                                         "</font></p>") % (BOOK_NAMES[b - 1], c, v, version_name))
                else:
                    for c3 in range(c, c2 + 1):
                        v3 = 1 if c3 != c else v
                        v4 = len(Bible[b][c3]) - 1 if c3 != c2 else v2
                        verses = []
                        for v5 in range(v3, v4 + 1):
                            if Bible[b][c3][v5]:
                                verses.append("<font size=\"-1\">%d&nbsp;</font>%s" %
                                              (v5, Bible[b][c3][v5]))
                        if not verses:
                            raise IndexError
                        results.append("<p><a href=\"%d.%d.%d\">%s %d:%d-%d (%s)</a><br>%s</p>" %
                                       (b, c3, v3, BOOK_NAMES[b - 1], c3, v3, v4, version_name,
                                        " ".join(verses)))
            except IndexError:
                failed.append(reference)
        if failed:
            results.insert(0, "<font color=\"red\">The following references are not valid:<br>%s"
                              "</font>" % "<br>".join(failed))
        self.html = "<html><body><font size=\"%d\">%s</font></body></html>" % \
                    (self._parent.zoom_level, "".join(results))
        self.htmlwindow.SetPage(self.html)
        self.toolbar.EnableTool(wx.ID_PREVIEW, True)
        self.toolbar.EnableTool(wx.ID_COPY, True)
        self.toolbar.Refresh(False)
        self.last_version = version
        self.htmlwindow.SetFocus()

    def OnPrint(self, event):
        self._parent.printing.SetName(_("Multi-Verse Retrieval"))
        if event.GetId() == wx.ID_PRINT:
            self._parent.printing.PrintText(self.html)
        else:
            self._parent.printing.PreviewText(self.html)

    def OnCopy(self, event):
        self.htmlwindow.SelectAll()
        data = wx.TextDataObject(self.htmlwindow.SelectionToText())
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(data)
            wx.TheClipboard.Flush()
            wx.TheClipboard.Close()

    def OnHtmlLinkClicked(self, event):
        if (self._parent.notebook.GetSelection() != self.last_version and
                not wx.GetKeyState(wx.WXK_CONTROL)):
            self._parent.notebook.SetSelection(self.last_version)
        self._parent.load_chapter(*[int(i) for i in event.GetLinkInfo().GetHref().split(".")])

    def OnContextMenu(self, event):
        if not self.html:
            return
        menu = wx.Menu()
        if self.htmlwindow.SelectionToText():
            menu.Append(wx.ID_COPY, _("&Copy"))
        menu.Append(wx.ID_SELECTALL, _("Select &All"))
        menu.AppendSeparator()
        print_item = menu.Append(wx.ID_PRINT, _("&Print..."))
        self.Bind(wx.EVT_MENU, self.OnPrint, print_item)
        preview_item = menu.Append(wx.ID_PREVIEW, _("P&rint Preview"))
        self.Bind(wx.EVT_MENU, self.OnPrint, preview_item)
        self.htmlwindow.PopupMenu(menu)
