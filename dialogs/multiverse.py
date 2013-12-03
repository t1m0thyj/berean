"""
multiverse.py - multiple verse search dialog for Berean
Copyright (C) 2013 Timothy Johnson <timothysw@objectmail.com>
"""

import re
import wx
from wx.html import EVT_HTML_LINK_CLICKED

import aui
from htmlwin import BaseHtmlWindow
from panes.search import refalize2

_ = wx.GetTranslation

class MultiverseDialog(wx.Dialog):
    def __init__(self, parent, references=None):
        wx.Dialog.__init__(self, parent, -1, _("Multiple Verse Search"), size=(600, 440), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self._parent = parent

        self.html = ""
        self.lastversion = None

        self.toolbar = aui.AuiToolBar(self, -1, agwStyle=aui.AUI_TB_DEFAULT_STYLE | aui.AUI_TB_OVERFLOW | aui.AUI_TB_PLAIN_BACKGROUND | aui.AUI_TB_HORZ_TEXT)
        self.toolbar.AddLabel(-1, _("Version:"), self.toolbar.GetTextExtent(_("Version:"))[0] - 5)
        self.version = wx.Choice(self.toolbar, -1, choices=parent.versions)
        tab = parent.notebook.GetSelection()
        if tab < len(parent.versions):
            self.version.SetSelection(tab)
        else:
            self.version.SetSelection(0)
        self.toolbar.AddControl(self.version)
        self.toolbar.AddSeparator()
        ID_SEARCH = wx.NewId()
        self.toolbar.AddSimpleTool(ID_SEARCH, _("Search"), parent.Bitmap("search"), _("Search (Ctrl+Enter)"))
        self.toolbar.AddSimpleTool(wx.ID_PRINT, _("Print"), parent.Bitmap("print"), _("Print Search Results"))
        self.toolbar.SetToolDropDown(wx.ID_PRINT, True)
        self.toolbar.EnableTool(wx.ID_PRINT, False)
        self.toolbar.AddSimpleTool(wx.ID_COPY, _("Copy"), parent.Bitmap("copy"), _("Copy with Formatting"))
        self.toolbar.EnableTool(wx.ID_COPY, False)
        self.toolbar.Realize()
        self.splitter = wx.SplitterWindow(self, -1)
        if not references:
            references = parent._app.settings["LastVerses"]
        else:
            wx.CallAfter(self.OnSearch, None)
        self.references = wx.TextCtrl(self.splitter, -1, references, style=wx.TE_MULTILINE)
        self.references.SetAcceleratorTable(wx.AcceleratorTable([(wx.ACCEL_CTRL, wx.WXK_RETURN, ID_SEARCH),
                                                                 (wx.ACCEL_CTRL, ord("A"), wx.ID_SELECTALL)]))
        self.results = BaseHtmlWindow(self.splitter)
        self.splitter.SplitHorizontally(self.references, self.results, 60)
        self.close = wx.Button(self, wx.ID_CLOSE)    # Needed because Gnome 3 doesn't have close button on dialogs

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.toolbar, 0, wx.EXPAND)
        sizer.Add(self.splitter, 1, (wx.ALL ^ wx.TOP) | wx.EXPAND, 2)
        sizer.Add(self.close, 0, wx.ALL | wx.ALIGN_RIGHT, 3)
        self.SetSizer(sizer)

        self.Bind(wx.EVT_MENU, self.OnSearch, id=ID_SEARCH)
        for id in (wx.ID_PRINT, wx.ID_PAGE_SETUP, wx.ID_PREVIEW):
            self.Bind(wx.EVT_MENU, self.OnPrintMenu, id=id)
        self.toolbar.Bind(aui.EVT_AUITOOLBAR_TOOL_DROPDOWN, self.OnPrintDropdown, id=wx.ID_PRINT)
        self.results.Bind(EVT_HTML_LINK_CLICKED, self.OnHtmlLinkClicked)
        self.results.Bind(wx.EVT_RIGHT_UP, self.OnContextMenu)    # EVT_CONTEXT_MENU doesn't work for wxHtmlWindow in 2.8
        self.close.Bind(wx.EVT_BUTTON, self.OnClose)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnSearch(self, event):
        try:
            version = self.version.GetStringSelection()
            browser = self._parent.GetBrowser(self._parent.versions.index(version))
            data = refalize2(self.references.GetValue(), browser.Bible)
            results = []
            if self._parent._app.settings["AbbrevSearchResults"]:
                books = self._parent.abbrevs
            else:
                books = self._parent.books
            for start, stop in data:
                b1, c1, v1 = start
                b2, c2, v2 = stop
                try:
                    if start == stop:
                        if len(browser.Bible[b1][c1][v1]):
                            results.append("<p><a href='%d.%d.%d'>%s %d:%d</a><br />%s</p>" % (b1, c1, v1, books[b1 - 1], c1, v1, browser.Bible[b1][c1][v1]))
                        else:
                            results.append(_("<p><font color=gray>%s %d:%d is not in the %s.</font></p>") % (books[b1 - 1], c1, v1, version))
                    else:
                        result = []
                        for b in range(b1, b2 + 1):
                            for c in range(1, len(browser.Bible[b])):
                                for v in range(0, len(browser.Bible[b][c])):
                                    if (b1, c1, v1) <= (b, c, v) <= (b2, c2, v2):
                                        if c == 1 and not v:
                                            result.append("<hr /><a href='%d.%d.-1'>%s %d</a>" % (b, c, books[b - 1], c))
                                        elif not v:
                                            result.append("<p><a href='%d.%d.-1'>%s %d</a></p>" % (b, c, books[b - 1], c))
                                        elif len(browser.Bible[b][c][v]):
                                            result.append("<font size=-1><a href='%d.%d.%d'>%d</a>&nbsp;</font>%s" % (b, c, v, v, browser.Bible[b][c][v]))
                                        else:
                                            result.append("")
                        if not len(result):
                            raise AssertionError
                except:
                    wx.MessageBox(_("%s %d:%d is not a valid reference.\n\nMake sure that it exists (i.e., is not like Mark 17 or Psalms 1:66).") % (self._parent.books[b1 - 1], c1, v1), "Berean", wx.ICON_EXCLAMATION | wx.OK)
                    return
                if start != stop:
                    if b1 == b2 and c1 == c2:
                        results.append("<p><a href='%d.%d.%d'>%s %d:%d-%d</a><br />%s</p>" % (b1, c1, v1, books[b1 - 1], c1, v1, v2, " ".join(result)))
                    elif b1 == b2:
                        results.append("<p><a href='%d.%d.%d'>%s %d:%d-%d:%d</a><br />%s</p>" % (b1, c1, v1, books[b1 - 1], c1, v1, c2, v2, " ".join(result)))
                    else:
                        results.append("<p><a href='%d.%d.%d'>%s %d:%d - %s %d:%d</a><br />%s</p>" % (b1, c1, v1, books[b1 - 1], c1, v1, books[b2 - 1], c2, v2, " ".join(result)))
            self.html = "<html><body><font size=%d>%s</font></body></html>" % (self._parent.zoom, "".join(results))
            self.results.SetPage(self.html)
            self.toolbar.EnableTool(wx.ID_PRINT, True)
            ##self.toolbar.EnableTool(wx.ID_COPY, True)
            self.toolbar.Refresh(False)
            self.lastversion = version
            wx.CallAfter(self.results.SetFocus)
        except:
            wx.MessageBox(_("Sorry, but I cannot understand all of those references.\nMake sure that they exist\n(i.e., are not like Mark 17 or Psalms 1:66).\n\nIf you think that Berean should accept them,\nplease email <timothysw@objectmail.com>."), "Berean", wx.ICON_EXCLAMATION | wx.OK)

    def OnPrintMenu(self, event):
        id = event.GetId()
        if id != wx.ID_PAGE_SETUP:
            text = self.html.replace("</b></a>", " (%s)</b></a>" % self.lastversion, 1)
            if wx.VERSION_STRING >= "2.8.11.0":
                self._parent.printer.SetName(_("Search Results"))
            if id == wx.ID_PRINT:
                self._parent.printer.PrintText(text)
            elif id == wx.ID_PREVIEW:
                self._parent.printer.PreviewText(text)
        else:
            self._parent.printer.PageSetup()

    def OnPrintDropdown(self, event):
        if event.IsDropDownClicked():
            self.toolbar.SetToolSticky(wx.ID_PRINT, True)
            menu = wx.Menu()
            menu.Append(wx.ID_PRINT, _("&Print..."))
            menu.Append(wx.ID_PAGE_SETUP, _("Page Set&up..."))
            menu.Append(wx.ID_PREVIEW, _("Print Previe&w..."))
            self.toolbar.PopupMenu(menu, self._parent.toolbar.GetPopupPos(self.toolbar, wx.ID_PRINT))
            self.toolbar.SetToolSticky(wx.ID_PRINT, False)

    def OnHtmlLinkClicked(self, event):
        if self._parent.notebook.GetPageText(self._parent.notebook.GetSelection()) != self.lastversion:
            self._parent.notebook.SetSelection(self._parent.versions.index(self.lastversion))
        self._parent.LoadChapter(*[int(item) for item in event.GetLinkInfo().GetHref().split(".")])

    def OnContextMenu(self, event):
        if not len(self.html):
            return
        menu = wx.Menu()
        selection = self.results.SelectionToText()
        if len(selection):
            menu.Append(wx.ID_COPY, _("&Copy\tCtrl+C"))
        menu.Append(wx.ID_SELECTALL, _("Select &All\tCtrl+A"))
        self.Bind(wx.EVT_MENU, self.results.OnSelectAll, id=wx.ID_SELECTALL)
        menu.AppendSeparator()
        menu.Append(wx.ID_PRINT, _("&Print...\tCtrl+P"))
        menu.Append(wx.ID_PREVIEW, _("P&rint Preview...\tCtrl+Alt+P"))
        self.results.PopupMenu(menu)

    def OnClose(self, event):
        self._parent._app.settings["LastVerses"] = self.references.GetValue()
        self.Destroy()
