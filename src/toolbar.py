"""toolbar.py - toolbar classes"""

import wx
from wx import aui

from config import BOOK_NAMES, BOOK_LENGTHS, CHAPTER_LENGTHS
from refalize import refalize, validate

_ = wx.GetTranslation


class ToolBar(aui.AuiToolBar):
    def __init__(self, parent):
        super(ToolBar, self).__init__(parent, wx.ID_ANY,
                                      wx.DefaultPosition, wx.DefaultSize,
                                      aui.AUI_TB_DEFAULT_STYLE |
                                      aui.AUI_TB_OVERFLOW |
                                      aui.AUI_TB_HORZ_TEXT)
        self._parent = parent
        self.autocomp_books = parent._app.config.ReadBool("Main/AutocompBooks",
                                                          True)

        self.verse_entry = wx.ComboBox(self,
                                       choices=parent._app.config.
                                       ReadList("VerseHistory"),
                                       size=(150, -1),
                                       style=wx.TE_PROCESS_ENTER)
        if self.autocomp_books and wx.VERSION_STRING >= "2.9":
            self.verse_entry.AutoComplete(BOOK_NAMES)
        self.verse_entry.SetValue(
            parent._app.config.Read("Main/LastVerse", "Genesis 1"))
        self.verse_entry.Bind(wx.EVT_KEY_DOWN, self.OnVerseEntryKeyDown)
        self.AddControl(self.verse_entry)
        self.AddTool(parent.menubar.go_to_verse_item.GetId(), "",
                     parent.get_bitmap("search"), _("Go to Verse"))
        self.AddSeparator()
        self.AddTool(wx.ID_BACKWARD, _("Back"), parent.get_bitmap("go-back"),
                     _("Go Back (Alt+Left)"))
        self.SetToolDropDown(wx.ID_BACKWARD, True)
        self.Bind(aui.EVT_AUITOOLBAR_TOOL_DROPDOWN, self.OnBack,
                  id=wx.ID_BACKWARD)
        self.AddTool(wx.ID_FORWARD, _("Forward"),
                     parent.get_bitmap("go-forward"),
                     _("Go Forward (Alt+Right)"))
        self.SetToolDropDown(wx.ID_FORWARD, True)
        self.Bind(aui.EVT_AUITOOLBAR_TOOL_DROPDOWN, self.OnForward,
                  id=wx.ID_FORWARD)
        self.AddSeparator()
        self.bookctrl = wx.Choice(self, choices=BOOK_NAMES)
        self.bookctrl.SetSelection(parent.reference[0] - 1)
        self.AddControl(self.bookctrl)
        self.bookctrl.Bind(wx.EVT_CHOICE, self.OnBook)
        if '__WXGTK__' not in wx.PlatformInfo:
            self.chapterctrl = wx.SpinCtrl(self,
                                           value=str(parent.reference[1]),
                                           size=(60, -1), min=1,
                                           max=BOOK_LENGTHS[parent.
                                                            reference[0] - 1])
        else:
            self.chapterctrl = wx.SpinCtrl(self,
                                           value=str(parent.reference[1]),
                                           min=1,
                                           max=BOOK_LENGTHS[parent.
                                                            reference[0] - 1])
        self.AddControl(self.chapterctrl)
        self.chapterctrl.Bind(wx.EVT_SPINCTRL, self.OnChapter)
        self.chapterctrl.Bind(wx.EVT_TEXT_ENTER, self.OnChapter)
        self.AddSeparator()
        self.AddTool(wx.ID_PRINT, "", parent.get_bitmap("print"),
                     _("Print (Ctrl+P)"))
        self.AddTool(wx.ID_COPY, "", parent.get_bitmap("copy"),
                     _("Copy (Ctrl+C)"))
        self.ID_READER_VIEW = wx.NewId()
        self.AddTool(self.ID_READER_VIEW, "",
                     parent.get_bitmap("reader-view"),
                     _("Reader View (Ctrl+R)"), wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.OnReaderView, id=self.ID_READER_VIEW)
        self.AddSeparator()
        self.AddTool(parent.menubar.add_to_bookmarks_item.GetId(), "",
                     parent.get_bitmap("add-to-bookmarks"),
                     _("Add to Bookmarks (Ctrl+D)"))
        self.AddTool(parent.menubar.manage_bookmarks_item.GetId(), "",
                     parent.get_bitmap("manage-bookmarks"),
                     _("Manage Bookmarks (Ctrl+Shift+B)"))
        self.Realize()

    def OnVerseEntryKeyDown(self, event):
        if event.GetKeyCode() == wx.WXK_RETURN:
            self.OnGoToVerse(event)
        event.Skip()

    def OnGoToVerse(self, event):
        reference = self.verse_entry.GetValue().strip()
        if not reference:
            return
        else:
            kw_match = None
            for bookmark in self._parent.menubar.bookmarks:
                if bookmark.partition("=")[2] == reference:
                    kw_match = bookmark[:bookmark.index("=")]
                    break
            if kw_match:
                reference = kw_match
                self.verse_entry.SetValue(reference)
            elif not validate(reference):
                if not self._parent.aui.GetPane("search_pane").IsShown():
                    self._parent.show_search_pane()
                self._parent.search.text.SetValue(reference)
                self.verse_entry.SetValue(self.verse_entry.GetString(0))
                self._parent.search.OnSearch(None)
                return
        try:
            book, chapter, verse = refalize(reference)
            if chapter > BOOK_LENGTHS[book - 1]:
                wx.MessageBox(_("The book of %s has only %d chapters.") %
                              (BOOK_NAMES[book - 1], BOOK_LENGTHS[book - 1]),
                              "Berean", wx.ICON_EXCLAMATION | wx.OK)
                return
            elif verse > CHAPTER_LENGTHS[book - 1][chapter - 1]:
                wx.MessageBox(_("%s chapter %d has only %d verses.") %
                              (BOOK_NAMES[book - 1], chapter,
                               CHAPTER_LENGTHS[book - 1][chapter - 1]),
                              "Berean", wx.ICON_EXCLAMATION | wx.OK)
                return
            self._parent.load_chapter(book, chapter, verse)
        except (IndexError, ValueError):
            wx.MessageBox(_("'%s' is not a valid reference.") % reference,
                          "Berean", wx.ICON_EXCLAMATION | wx.OK)
        else:
            if self.verse_entry.FindString(reference) == -1:
                self.verse_entry.Insert(reference, 0)
                if self.verse_entry.GetCount() > 10:
                    self.verse_entry.Delete(10)

    def OnHistoryItem(self, event):
        book, chapter, verse = refalize(
            self._parent.verse_history[event.GetId() - wx.ID_HIGHEST - 1])
        self._parent.load_chapter(book, chapter, verse, False)

    def OnBack(self, event):
        if not event.IsDropDownClicked():
            self._parent.menubar.OnBack(None)
        else:
            menu = wx.Menu()
            for i in range(self._parent.history_item - 1, -1, -1):
                menu.Append(wx.ID_HIGHEST + i + 1,
                            self._parent.verse_history[i])
                self.Bind(wx.EVT_MENU, self.OnHistoryItem,
                          id=wx.ID_HIGHEST + i + 1)
            x, y, width, height = self.GetToolRect(wx.ID_BACKWARD)
            self.PopupMenu(menu, (x, y + height))

    def OnForward(self, event):
        if not event.IsDropDownClicked():
            self._parent.menubar.OnForward(None)
        else:
            menu = wx.Menu()
            for i in range(self._parent.history_item + 1,
                           len(self._parent.verse_history)):
                menu.Append(wx.ID_HIGHEST + i + 1,
                            self._parent.verse_history[i])
                self.Bind(wx.EVT_MENU, self.OnHistoryItem,
                          id=wx.ID_HIGHEST + i + 1)
            x, y, width, height = self.GetToolRect(wx.ID_FORWARD)
            self.PopupMenu(menu, (x, y + height))

    def OnBook(self, event):
        book = self.bookctrl.GetSelection() + 1
        chapter = min(self._parent.reference[1], BOOK_LENGTHS[book - 1])
        self.chapterctrl.SetRange(1, BOOK_LENGTHS[book - 1])
        if chapter != self._parent.reference[1]:
            self.chapterctrl.SetValue(chapter)
        self._parent.load_chapter(book, chapter)

    def OnChapter(self, event):
        self._parent.load_chapter(self._parent.reference[0],
                                  self.chapterctrl.GetValue())

    def OnReaderView(self, event):
        self._parent.toggle_reader_view(update_toolbar=False)


class ZoomBar(wx.ToolBar):
    def __init__(self, parent, frame):
        super(ZoomBar, self).__init__(parent,
                                      style=wx.TB_FLAT | wx.TB_NODIVIDER)
        self._frame = frame
        self.AddLabelTool(wx.ID_ZOOM_OUT, "", frame.get_bitmap("zoom-out"),
                          shortHelp=_("Zoom Out (Ctrl+-)"))
        self.EnableTool(wx.ID_ZOOM_OUT, frame.zoom_level > 1)
        if '__WXGTK__' not in wx.PlatformInfo:
            self.slider = wx.Slider(self, value=frame.zoom_level, minValue=1,
                                    maxValue=7)
        else:
            self.slider = wx.Slider(self, value=frame.zoom_level, minValue=1,
                                    maxValue=7, size=(100, -1))
        self.slider.Bind(wx.EVT_SLIDER, self.OnSlider)
        self.AddControl(self.slider)
        self.AddLabelTool(wx.ID_ZOOM_IN, "", frame.get_bitmap("zoom-in"),
                          shortHelp=_("Zoom In (Ctrl++)"))
        self.EnableTool(wx.ID_ZOOM_IN, frame.zoom_level < 7)
        self.Realize()
        self.width = (self.GetToolSize()[0] + self.GetToolSeparation()) * 2 + \
            self.slider.GetSize()[0]
        if 'gtk3' in wx.PlatformInfo:
            self.width += 60

    def OnSlider(self, event):
        self._frame.set_zoom(event.GetSelection())
