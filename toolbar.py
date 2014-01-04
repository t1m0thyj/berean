"""toolbar.py - main toolbar class"""

import wx
from wx import aui

from info import *
from refalize import *

_ = wx.GetTranslation

class MainToolBar(aui.AuiToolBar):
    def __init__(self, parent):
        aui.AuiToolBar.__init__(self, parent, -1, (-1, -1), (-1, -1),
            aui.AUI_TB_DEFAULT_STYLE | aui.AUI_TB_OVERFLOW |
            aui.AUI_TB_HORZ_TEXT)
        self._parent = parent
        self.history_item = len(parent._app.settings["ChapterHistory"]) - 1
        self.verse_history = parent._app.settings["ChapterHistory"]

        self.verse_entry = wx.ComboBox(self, -1,
            choices=parent._app.settings["ReferenceHistory"], size=(150, -1),
            style=wx.TE_PROCESS_ENTER)
        self.verse_entry.SetValue(parent._app.settings["LastReference"])
        self.verse_entry.Bind(wx.EVT_TEXT_ENTER, self.OnGotoVerse)
        self.AddControl(self.verse_entry)
        goto_verse_item = self.AddTool(-1, "", parent.Bitmap("goto-verse"),
            _("Go to Verse (Ctrl+F)"))
        self.Bind(wx.EVT_MENU, self.OnGotoVerse, id=goto_verse_item.GetId())
        self.AddSeparator()
        self.AddTool(wx.ID_BACKWARD, _("Back"), parent.Bitmap("go-back"),
            _("Go Back (Alt+Left)"))
        self.SetToolDropDown(wx.ID_BACKWARD, True)
        self.Bind(wx.EVT_MENU, self.OnBack, id=wx.ID_BACKWARD)
        self.Bind(aui.EVT_AUITOOLBAR_TOOL_DROPDOWN, self.OnBackDropdown,
            id=wx.ID_BACKWARD)
        self.AddTool(wx.ID_FORWARD, _("Forward"), parent.Bitmap("go-forward"),
            _("Go Forward (Alt+Right)"))
        self.SetToolDropDown(wx.ID_FORWARD, True)
        self.Bind(wx.EVT_MENU, self.OnForward, id=wx.ID_FORWARD)
        self.Bind(aui.EVT_AUITOOLBAR_TOOL_DROPDOWN, self.OnForwardDropdown,
            id=wx.ID_FORWARD)
        self.AddSeparator()
        self.AddTool(parent.menubar.add_to_favorites_item.GetId(), "",
            parent.Bitmap("add-favorite"), _("Add to Favorites (Ctrl+D)"))
        self.AddTool(parent.menubar.manage_favorites_item.GetId(), "",
            parent.Bitmap("manage-favorites"), _("Manage Favorites"))

        self.Realize()

    def set_history_item(self, history_item):
        if history_item == -1:
            history_item = len(self.verse_history) - 1
        self.EnableTool(wx.ID_BACKWARD, history_item >= 0)
        self.EnableTool(wx.ID_FORWARD, history_item < len(self.verse_history) - 1)
        self.Refresh(False)
        self._parent.menubar.Enable(wx.ID_BACKWARD, history_item >= 0)
        self._parent.menubar.Enable(wx.ID_FORWARD, history_item < len(self.verse_history) - 1)
        self.history_item = history_item

    def get_popup_pos(self, toolbar, id):
        if toolbar.GetToolFits(id):
            x, y, width, height = toolbar.GetToolRect(id)
            return (x, y + height)
        else:
            x, y = toolbar.GetPosition()
            width, height = toolbar.GetSize()
            return (x + width - 16, y + height)

    def OnGotoVerse(self, event):
        reference = self.verse_entry.GetValue()
        if not len(reference):
            return
        if validate(reference):
            try:
                book, chapter, verse = refalize(reference)
                Bible = self._parent.GetBrowser(0).Bible
                if not 1 <= chapter < len(Bible[book]):
                    wx.MessageBox(_("The book of %s has only %d chapters.") % (BOOK_NAMES[book - 1], len(Bible[book]) - 1), "Berean", wx.ICON_EXCLAMATION | wx.OK)
                    return
                elif (not 1 <= verse < len(Bible[book][chapter])) and verse != -1:
                    wx.MessageBox(_("%s chapter %d has only %d verses.") % (BOOK_NAMES[book - 1], chapter, len(Bible[book][chapter]) - 1), "Berean", wx.ICON_EXCLAMATION | wx.OK)
                    return
                self._parent.LoadChapter(book, chapter, verse)
                if reference not in self.verse_entry.GetStrings():
                    self.verse_entry.Insert(reference, 0)
                    if self.verse_entry.GetCount() > 10:
                        self.verse_entry.Delete(10)
            except:
                wx.MessageBox(_("'%s' is not a valid reference.\n\nIf you think that Berean should accept it,\nplease email <timothysw@objectmail.com>.") % reference, "Berean", wx.ICON_EXCLAMATION | wx.OK)
        else:
            if not self._parent.aui.GetPane("searchpane").IsShown():
                self._parent.ShowSearchPane()
            self._parent.search.text.SetValue(reference)
            self.verse_entry.SetValue(self.verse_entry.GetString(0))
            self._parent.search.OnSearch(None)

    def OnBack(self, event):
        book, chapter, verse = refalize(self.verse_history[self.history_item - 1])
        self._parent.LoadChapter(book, chapter, verse, True)

    def OnBackDropdown(self, event):
        if event.IsDropDownClicked():
            self.SetToolSticky(wx.ID_BACKWARD, True)
            menu = wx.Menu()
            for i in range(self.history_item - 1, -1, -1):
                menu.Append(wx.ID_HIGHEST + i, self.verse_history[i])
                self.Bind(wx.EVT_MENU, self.OnHistoryItem, id=wx.ID_HIGHEST + i)
            self.PopupMenu(menu, self.GetPopupPos(self, wx.ID_BACKWARD))
            self.SetToolSticky(wx.ID_BACKWARD, False)

    def OnHistoryItem(self, event):
        book, chapter, verse = refalize(self.verse_history[event.GetId() - wx.ID_HIGHEST])
        self._parent.LoadChapter(book, chapter, verse, True)

    def OnForward(self, event):
        book, chapter, verse = refalize(self.verse_history[self.history_item + 1])
        self._parent.LoadChapter(book, chapter, verse, True)

    def OnForwardDropdown(self, event):
        if event.IsDropDownClicked():
            self.SetToolSticky(wx.ID_FORWARD, True)
            menu = wx.Menu()
            for i in range(self.history_item + 1, len(self.verse_history)):
                menu.Append(wx.ID_HIGHEST + i, self.verse_history[i])
                self.Bind(wx.EVT_MENU, self.OnHistoryItem, id=wx.ID_HIGHEST + i)
            self.PopupMenu(menu, self.GetPopupPos(self, wx.ID_FORWARD))
            self.SetToolSticky(wx.ID_FORWARD, False)
