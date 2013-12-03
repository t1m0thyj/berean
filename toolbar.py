"""
toolbar.py - toolbar class for Berean
Copyright (C) 2013 Timothy Johnson <timothysw@objectmail.com>
"""

import wx

import aui
from panes.search import refalize, validate

_ = wx.GetTranslation

class ToolBar(aui.AuiToolBar):
    def __init__(self, parent):
        super(ToolBar, self).__init__(parent, -1, agwStyle=aui.AUI_TB_DEFAULT_STYLE | aui.AUI_TB_OVERFLOW | aui.AUI_TB_HORZ_TEXT)
        self._parent = parent

        self.current = len(parent._app.settings["ChapterHistory"]) - 1
        self.history = parent._app.settings["ChapterHistory"]

        self.reference = wx.ComboBox(self, -1, choices=parent._app.settings["ReferenceHistory"], size=(150, -1), style=wx.TE_PROCESS_ENTER)
        self.reference.SetValue(parent._app.settings["LastReference"])
        self.AddControl(self.reference)
        self.reference.Bind(wx.EVT_TEXT_ENTER, self.OnSearch)
        self.AddSimpleTool(wx.ID_FIND, "", parent.Bitmap("goto"), _("Go to Reference (Ctrl+F)"))
        self.Bind(wx.EVT_MENU, self.OnSearch, id=wx.ID_FIND)
        self.AddSeparator()
        self.AddSimpleTool(wx.ID_BACKWARD, _("Back"), parent.Bitmap("back"), _("Go Back (Alt+Left)"))
        self.SetToolDropDown(wx.ID_BACKWARD, True)
        self.Bind(wx.EVT_MENU, self.OnBack, id=wx.ID_BACKWARD)
        self.Bind(aui.EVT_AUITOOLBAR_TOOL_DROPDOWN, self.OnBackDropdown, id=wx.ID_BACKWARD)
        self.AddSimpleTool(wx.ID_FORWARD, _("Forward"), parent.Bitmap("forward"), _("Go Forward (Alt+Right)"))
        self.SetToolDropDown(wx.ID_FORWARD, True)
        self.Bind(wx.EVT_MENU, self.OnForward, id=wx.ID_FORWARD)
        self.Bind(aui.EVT_AUITOOLBAR_TOOL_DROPDOWN, self.OnForwardDropdown, id=wx.ID_FORWARD)
        self.AddSeparator()
        self.books = wx.Choice(self, -1, choices=parent.books)
        self.books.SetSelection(parent.reference[0] - 1)
        self.AddControl(self.books)
        self.books.Bind(wx.EVT_CHOICE, self.OnBook)
        self.chapter = wx.SpinCtrl(self, -1, str(parent.reference[1]), size=(60, -1), min=1, max=parent.chapters[parent.reference[0] - 1])
        self.AddControl(self.chapter)
        self.chapter.Bind(wx.EVT_TEXT_ENTER, self.OnChapter)
        self.chapter.Bind(wx.EVT_SPINCTRL, self.OnChapter)
        self.AddSimpleTool(wx.ID_PRINT, "", parent.Bitmap("print"), _("Print (Ctrl+P)"))
        self.AddSeparator()
        self.AddSimpleTool(parent.menubar.Favorites.ID_ADD, "", parent.Bitmap("add-favorite"), _("Add to Favorites (Ctrl+D)"))
        self.AddSimpleTool(parent.menubar.Favorites.ID_MANAGE, "", parent.Bitmap("favorites"), _("Manage Favorites"))

        self.Realize()

    def SetCurrent(self, current):
        if current == -1:
            current = len(self.history) - 1
        self.EnableTool(wx.ID_BACKWARD, current >= 0)
        self.EnableTool(wx.ID_FORWARD, current < len(self.history) - 1)
        self.Refresh(False)
        self._parent.menubar.Enable(wx.ID_BACKWARD, current >= 0)
        self._parent.menubar.Enable(wx.ID_FORWARD, current < len(self.history) - 1)
        self.current = current

    def GetPopupPos(self, toolbar, id):
        if toolbar.GetToolFits(id):
            x, y, width, height = toolbar.GetToolRect(id)
            return (x, y + height)
        else:
            x, y = toolbar.GetPosition()
            width, height = toolbar.GetSize()
            return (x + width - 16, y + height)

    def OnSearch(self, event):
        reference = self.reference.GetValue()
        if not len(reference):
            return
        if validate(reference):
            try:
                book, chapter, verse = refalize(reference)
                Bible = self._parent.GetBrowser(0).Bible
                if not 1 <= chapter < len(Bible[book]):
                    wx.MessageBox(_("The book of %s has only %d chapters.") % (self._parent.books[book - 1], len(Bible[book]) - 1), "Berean", wx.ICON_EXCLAMATION | wx.OK)
                    return
                elif (not 1 <= verse < len(Bible[book][chapter])) and verse != -1:
                    wx.MessageBox(_("%s chapter %d has only %d verses.") % (self._parent.books[book - 1], chapter, len(Bible[book][chapter]) - 1), "Berean", wx.ICON_EXCLAMATION | wx.OK)
                    return
                self._parent.LoadChapter(book, chapter, verse)
                if reference not in self.reference.GetStrings():
                    self.reference.Insert(reference, 0)
                    if self.reference.GetCount() > 10:
                        self.reference.Delete(10)
            except:
                wx.MessageBox(_("'%s' is not a valid reference.\n\nIf you think that Berean should accept it,\nplease email <timothysw@objectmail.com>.") % reference, "Berean", wx.ICON_EXCLAMATION | wx.OK)
        else:
            if not self._parent.aui.GetPane("searchpane").IsShown():
                self._parent.ShowSearchPane()
            self._parent.search.text.SetValue(reference)
            self.reference.SetValue(self.reference.GetString(0))
            self._parent.search.OnSearch(None)

    def OnBack(self, event):
        book, chapter, verse = refalize(self.history[self.current - 1])
        self._parent.LoadChapter(book, chapter, verse, True)

    def OnBackDropdown(self, event):
        if event.IsDropDownClicked():
            self.SetToolSticky(wx.ID_BACKWARD, True)
            menu = wx.Menu()
            for i in range(self.current - 1, -1, -1):
                menu.Append(wx.ID_HIGHEST + i, self.history[i])
                self.Bind(wx.EVT_MENU, self.OnHistoryItem, id=wx.ID_HIGHEST + i)
            self.PopupMenu(menu, self.GetPopupPos(self, wx.ID_BACKWARD))
            self.SetToolSticky(wx.ID_BACKWARD, False)

    def OnHistoryItem(self, event):
        book, chapter, verse = refalize(self.history[event.GetId() - wx.ID_HIGHEST])
        self._parent.LoadChapter(book, chapter, verse, True)

    def OnForward(self, event):
        book, chapter, verse = refalize(self.history[self.current + 1])
        self._parent.LoadChapter(book, chapter, verse, True)

    def OnForwardDropdown(self, event):
        if event.IsDropDownClicked():
            self.SetToolSticky(wx.ID_FORWARD, True)
            menu = wx.Menu()
            for i in range(self.current + 1, len(self.history)):
                menu.Append(wx.ID_HIGHEST + i, self.history[i])
                self.Bind(wx.EVT_MENU, self.OnHistoryItem, id=wx.ID_HIGHEST + i)
            self.PopupMenu(menu, self.GetPopupPos(self, wx.ID_FORWARD))
            self.SetToolSticky(wx.ID_FORWARD, False)

    def OnBook(self, event):
        book = self.books.GetSelection() + 1
        if self._parent.reference[1] > self._parent.chapters[book - 1]:
            chapter = self._parent.chapters[book - 1]
        else:
            chapter = self._parent.reference[1]
        self.chapter.SetRange(1, self._parent.chapters[book - 1])
        self.chapter.SetValue(chapter)
        self._parent.LoadChapter(book, chapter)

    def OnChapter(self, event):
        if not self._parent.skipevents:
            self._parent.LoadChapter(self._parent.reference[0], self.chapter.GetValue())
