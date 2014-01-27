"""toolbar.py - main toolbar class"""

import wx
from wx import aui

from info import *
from refalize import *

_ = wx.GetTranslation

class MainToolBar(aui.AuiToolBar):
    def __init__(self, parent):
        super(MainToolBar, self).__init__(parent, -1, (-1, -1), (-1, -1),
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
        self.AddTool(parent.menubar.goto_verse_item.GetId(), "",
            parent.get_bitmap("goto-verse"), _("Go to Verse"))
        self.AddSeparator()
        self.AddTool(wx.ID_BACKWARD, _("Back"), parent.get_bitmap("go-back"),
            _("Go Back (Alt+Left)"))
        self.SetToolDropDown(wx.ID_BACKWARD, True)
        self.Bind(wx.EVT_MENU, self.OnBack, id=wx.ID_BACKWARD)
        self.Bind(aui.EVT_AUITOOLBAR_TOOL_DROPDOWN, self.OnBackDropdown,
            id=wx.ID_BACKWARD)
        self.AddTool(wx.ID_FORWARD, _("Forward"),
            parent.get_bitmap("go-forward"), _("Go Forward (Alt+Right)"))
        self.SetToolDropDown(wx.ID_FORWARD, True)
        self.Bind(wx.EVT_MENU, self.OnForward, id=wx.ID_FORWARD)
        self.Bind(aui.EVT_AUITOOLBAR_TOOL_DROPDOWN, self.OnForwardDropdown,
            id=wx.ID_FORWARD)
        self.AddSeparator()
        self.AddTool(wx.ID_PRINT, "", parent.get_bitmap("print"),
            _("Print (Ctrl+P)"))
        self.AddTool(wx.ID_COPY, "", parent.get_bitmap("copy"),
            _("Copy (Ctrl+C)"))
        self.AddSeparator()
        self.AddTool(parent.menubar.add_to_favorites_item.GetId(), "",
            parent.get_bitmap("add-favorite"), _("Add to Favorites (Ctrl+D)"))
        self.AddTool(parent.menubar.manage_favorites_item.GetId(), "",
            parent.get_bitmap("manage-favorites"), _("Manage Favorites"))

        self.Refresh(False)

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
                if chapter > CHAPTER_LENGTHS[book - 1]:
                    wx.MessageBox(_("The book of %s has only %d chapters.") % (BOOK_NAMES[book - 1], CHAPTER_LENGTHS[book - 1], "Berean", wx.ICON_EXCLAMATION | wx.OK))
                    return
                elif verse > VERSE_LENGTHS[book - 1][chapter - 1]:
                    wx.MessageBox(_("%s chapter %d has only %d verses.") % (BOOK_NAMES[book - 1], chapter, VERSE_LENGTHS[book - 1][chapter - 1]), "Berean", wx.ICON_EXCLAMATION | wx.OK)
                    return
                self._parent.load_chapter(book, chapter, verse)
                if reference not in self.verse_entry.GetStrings():
                    self.verse_entry.Insert(reference, 0)
                    if self.verse_entry.GetCount() > 10:
                        self.verse_entry.Delete(10)
            except:
                wx.MessageBox(_("'%s' is not a valid reference.\n\nIf you think that Berean should accept it,\nplease email <timothysw@objectmail.com>.") % reference, "Berean", wx.ICON_EXCLAMATION | wx.OK)
        else:
            if not self._parent.aui.GetPane("search_pane").IsShown():
                self._parent.show_search_pane()
            self._parent.search.text.SetValue(reference)
            self.verse_entry.SetValue(self.verse_entry.GetString(0))
            self._parent.search.OnSearch(None)

    def OnBack(self, event):
        book, chapter, verse = refalize(
            self.verse_history[self.history_item - 1])
        self._parent.load_chapter(book, chapter, verse, True)

    def OnBackDropdown(self, event):
        if event.IsDropDownClicked():
            self.SetToolSticky(wx.ID_BACKWARD, True)
            menu = wx.Menu()
            for i in reversed(range(0, self.history_item)):
                menu.Append(wx.ID_HIGHEST + i + 1, self.verse_history[i])
                self.Bind(wx.EVT_MENU, self.OnHistoryItem, id=wx.ID_HIGHEST +
                    i + 1)
            self.PopupMenu(menu, self.get_popup_pos(self, wx.ID_BACKWARD))
            self.SetToolSticky(wx.ID_BACKWARD, False)

    def OnHistoryItem(self, event):
        book, chapter, verse = refalize(
            self.verse_history[event.GetId() - wx.ID_HIGHEST - 1])
        self._parent.load_chapter(book, chapter, verse, True)

    def OnForward(self, event):
        book, chapter, verse = refalize(
            self.verse_history[self.history_item + 1])
        self._parent.load_chapter(book, chapter, verse, True)

    def OnForwardDropdown(self, event):
        if event.IsDropDownClicked():
            self.SetToolSticky(wx.ID_FORWARD, True)
            menu = wx.Menu()
            for i in range(self.history_item + 1, len(self.verse_history)):
                menu.Append(wx.ID_HIGHEST + i + 1, self.verse_history[i])
                self.Bind(wx.EVT_MENU, self.OnHistoryItem, id=wx.ID_HIGHEST +
                    i + 1)
            self.PopupMenu(menu, self.get_popup_pos(self, wx.ID_FORWARD))
            self.SetToolSticky(wx.ID_FORWARD, False)


class ZoomBar(wx.ToolBar):
    def __init__(self, parent, frame):
        super(ZoomBar, self).__init__(parent, -1,
            style=wx.TB_FLAT | wx.TB_NODIVIDER)
        self._frame = frame
        self.AddLabelTool(wx.ID_ZOOM_OUT, "", frame.get_bitmap("zoom-out"),
            shortHelp=_("Zoom Out (Ctrl+-)"))
        self.EnableTool(wx.ID_ZOOM_OUT, frame.zoom_level > 1)
        self.slider = wx.Slider(self, -1, frame.zoom_level, 1, 7,
            size=(100, -1))
        self.slider.Bind(wx.EVT_SLIDER, self.OnSlider)
        self.AddControl(self.slider)
        self.AddLabelTool(wx.ID_ZOOM_IN, "", frame.get_bitmap("zoom-in"),
            shortHelp=_("Zoom In (Ctrl++)"))
        self.EnableTool(wx.ID_ZOOM_IN, frame.zoom_level < 7)
        self.Realize()
        self.width = (self.GetToolSize()[0] + self.GetToolSeparation()) * 2 + \
            self.slider.GetSize()[0]

    def OnSlider(self, event):
        self._frame.set_zoom(event.GetSelection())
