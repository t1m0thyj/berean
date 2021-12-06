"""menu.py - menubar and bookmarks dialog classes"""

import webbrowser

import wx
from wx import adv

import html2
from refalize import refalize, reference_str
from constants import LICENSE_TEXT, VERSION

_ = wx.GetTranslation


def find_bookmark(reference, bookmarks):
    for i in range(len(bookmarks)):
        if refalize(bookmarks[i]) == reference:
            return i
    return -1


class MenuBar(wx.MenuBar):
    def __init__(self, frame):
        super(MenuBar, self).__init__()
        self._frame = frame
        self.bookmarks = frame._app.config.ReadList("Bookmarks")

        self.menu_file = wx.Menu()
        self.menu_file.Append(wx.ID_PRINT_SETUP, _("Page Set&up..."),
                              _("Changes page layout settings"))
        frame.Bind(wx.EVT_MENU, self.OnPageSetup, id=wx.ID_PRINT_SETUP)
        self.menu_file.Append(wx.ID_PREVIEW, _("Print Pre&view"),
                              _("Previews the current chapter"))
        frame.Bind(wx.EVT_MENU, self.OnPrintPreview, id=wx.ID_PREVIEW)
        self.menu_file.Append(wx.ID_PRINT, _("&Print...\tCtrl+P"), _("Prints the current chapter"))
        frame.Bind(wx.EVT_MENU, self.OnPrint, id=wx.ID_PRINT)
        if '__WXMAC__' not in wx.PlatformInfo:
            self.menu_file.AppendSeparator()
        self.menu_file.Append(wx.ID_EXIT, _("E&xit"), _("Exits the application"))
        frame.Bind(wx.EVT_MENU, frame.OnClose, id=wx.ID_EXIT)
        self.Append(self.menu_file, _("&File"))

        self.menu_edit = wx.Menu()
        self.menu_edit.Append(wx.ID_COPY, _("&Copy\tCtrl+C"),
                              _("Copies the selected text to the clipboard"))
        frame.Bind(wx.EVT_MENU, self.OnCopy, id=wx.ID_COPY)
        if '__WXMAC__' not in wx.PlatformInfo:
            self.menu_edit.AppendSeparator()
        self.menu_edit.Append(wx.ID_PREFERENCES, _("&Preferences"),
                              _("Configures program settings"))
        frame.Bind(wx.EVT_MENU, self.OnPreferences, id=wx.ID_PREFERENCES)
        self.Append(self.menu_edit, _("&Edit"))

        self.menu_view = wx.Menu()
        self.go_to_verse_item = self.menu_view.Append(wx.ID_ANY, _("&Go to Verse"),
                                                      _("Goes to the specified verse"))
        frame.Bind(wx.EVT_MENU, self.OnGoToVerse, self.go_to_verse_item)
        self.menu_view.Append(wx.ID_BACKWARD, _("Go &Back\tAlt+Left"),
                              _("Goes to the previous chapter"))
        frame.Bind(wx.EVT_MENU, self.OnBack, id=wx.ID_BACKWARD)
        self.menu_view.Append(wx.ID_FORWARD, _("Go &Forward\tAlt+Right"),
                              _("Goes to the next chapter"))
        frame.Bind(wx.EVT_MENU, self.OnForward, id=wx.ID_FORWARD)
        self.menu_view.AppendSeparator()
        self.menu_view.Append(wx.ID_ZOOM_IN, _("Zoom &In\tCtrl++"), _("Increases the text size"))
        self.menu_view.Enable(wx.ID_ZOOM_IN, frame.zoom_level < 7)
        frame.Bind(wx.EVT_MENU, self.OnZoomIn, id=wx.ID_ZOOM_IN)
        self.menu_view.Append(wx.ID_ZOOM_OUT, _("Zoom &Out\tCtrl+-"), _("Decreases the text size"))
        self.menu_view.Enable(wx.ID_ZOOM_OUT, frame.zoom_level > 1)
        frame.Bind(wx.EVT_MENU, self.OnZoomOut, id=wx.ID_ZOOM_OUT)
        self.menu_view.Append(wx.ID_ZOOM_100, _("&Reset Zoom\tCtrl+0"),
                              _("Resets the text size to the default"))
        frame.Bind(wx.EVT_MENU, self.OnZoomDefault, id=wx.ID_ZOOM_100)
        self.menu_view.AppendSeparator()
        self.toolbar_item = self.menu_view.AppendCheckItem(wx.ID_ANY, _("&Toolbar"))
        frame.Bind(wx.EVT_MENU, self.OnToolbar, self.toolbar_item)
        self.menu_view.AppendSeparator()
        self.tree_pane_item = self.menu_view.AppendCheckItem(wx.ID_ANY,
                                                             _("Tr&ee Pane\tCtrl+Shift+T"))
        frame.Bind(wx.EVT_MENU, self.OnTreePane, self.tree_pane_item)
        self.search_pane_item = self.menu_view.AppendCheckItem(wx.ID_ANY,
                                                               _("&Search Pane\tCtrl+Shift+S"))
        frame.Bind(wx.EVT_MENU, self.OnSearchPane, self.search_pane_item)
        self.multiverse_pane_item = self.menu_view.AppendCheckItem(wx.ID_ANY,
                                                                   _("&Multi-Verse Retrieval\t"
                                                                     "Ctrl+Shift+M"))
        frame.Bind(wx.EVT_MENU, self.OnMultiVersePane, self.multiverse_pane_item)
        self.Append(self.menu_view, _("&View"))

        self.menu_bookmarks = wx.Menu()
        self.add_to_bookmarks_item = self.menu_bookmarks.Append(wx.ID_ANY,
                                                                _("&Add to Bookmarks\tCtrl+D"),
                                                                _("Adds the current chapter to "
                                                                  "your bookmarks"))
        frame.Bind(wx.EVT_MENU, self.OnAddToBookmarks, self.add_to_bookmarks_item)
        self.manage_bookmarks_item = self.menu_bookmarks.Append(wx.ID_ANY, _("&Manage Bookmarks\t"
                                                                             "Ctrl+Shift+B"))
        frame.Bind(wx.EVT_MENU, self.OnManageBookmarks, self.manage_bookmarks_item)
        self.menu_bookmarks.AppendSeparator()
        self.menu_bookmarks.AppendSeparator()
        self.view_all_item = self.menu_bookmarks.Append(wx.ID_ANY, _("View All"))
        frame.Bind(wx.EVT_MENU, self.OnViewAll, self.view_all_item)
        self.update_bookmarks()
        self.Append(self.menu_bookmarks, _("&Bookmarks"))

        self.menu_help = wx.Menu()
        self.menu_help.Append(wx.ID_HELP, _("Online &Help\tF1"),
                              _("Launches Berean help in your web browser"))
        frame.Bind(wx.EVT_MENU, self.OnHelp, id=wx.ID_HELP)
        self.menu_help.Append(wx.ID_ABOUT, _("&About Berean"),
                              _("Displays program information, version number, and copyright"))
        frame.Bind(wx.EVT_MENU, self.OnAbout, id=wx.ID_ABOUT)
        self.Append(self.menu_help, _("&Help"))

    def update_bookmarks(self):
        for i in range(2, self.menu_bookmarks.GetMenuItemCount() - 3):
            self.menu_bookmarks.Remove(wx.ID_HIGHEST + i - 1)
        if self.bookmarks:
            for i in range(len(self.bookmarks)):
                self.menu_bookmarks.Insert(i + 3, wx.ID_HIGHEST + i + 1,
                                           *self.bookmarks[i].split("|"))
                self._frame.Bind(wx.EVT_MENU, self.OnBookmark, id=wx.ID_HIGHEST + i + 1)
        else:
            self.menu_bookmarks.Insert(3, wx.ID_HIGHEST + 1, _("(Empty)"))
            self.menu_bookmarks.Enable(wx.ID_HIGHEST + 1, False)

    def OnPageSetup(self, event):
        self._frame.printing.PageSetup()

    def OnPrintPreview(self, event):
        self._frame.printing.preview_chapter()

    def OnPrint(self, event):
        self._frame.printing.print_chapter()

    def OnCopy(self, event):
        window = self._frame.FindFocus()
        if not isinstance(window, html2.HtmlWindowBase):
            return
        data = wx.TextDataObject(window.SelectionToText())
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(data)
            wx.TheClipboard.Flush()
            wx.TheClipboard.Close()

    def OnPreferences(self, event):
        import preferences
        dialog = preferences.PreferencesDialog(self._frame)
        dialog.ShowModal()

    def OnGoToVerse(self, event):
        self._frame.toolbar.OnGoToVerse(None)

    def OnBack(self, event):
        if self._frame.history_item <= 0:
            return
        book, chapter, verse = refalize(self._frame.verse_history[self._frame.history_item - 1])
        self._frame.load_chapter(book, chapter, verse, False)

    def OnForward(self, event):
        if self._frame.history_item >= len(self._frame.verse_history) - 1:
            return
        book, chapter, verse = refalize(self._frame.verse_history[self._frame.history_item + 1])
        self._frame.load_chapter(book, chapter, verse, False)

    def OnZoomIn(self, event):
        self._frame.set_zoom(self._frame.zoom_level + 1)

    def OnZoomOut(self, event):
        self._frame.set_zoom(self._frame.zoom_level - 1)

    def OnZoomDefault(self, event):
        self._frame.set_zoom(3)

    def OnToolbar(self, event):
        self._frame.aui.GetPane("toolbar").Show(event.IsChecked())
        self._frame.aui.Update()

    def OnTreePane(self, event):
        self._frame.aui.GetPane("tree_pane").Show(event.IsChecked())
        self._frame.aui.Update()

    def OnSearchPane(self, event):
        self._frame.show_search_pane(event.IsChecked())

    def OnMultiVersePane(self, event):
        self._frame.show_multiverse_pane(event.IsChecked())

    def OnAddToBookmarks(self, event):
        bookmark = reference_str(*self._frame.reference)
        if find_bookmark(self._frame.reference, self.bookmarks) == -1:
            self.bookmarks.append(bookmark)
            self.update_bookmarks()
        else:
            wx.MessageBox(_("A bookmark for %s already exists.") % bookmark, "Berean",
                          wx.ICON_EXCLAMATION | wx.OK)

    def OnManageBookmarks(self, event):
        dialog = BookmarksDialog(self._frame)
        dialog.ShowModal()

    def OnBookmark(self, event):
        reference = self.bookmarks[event.GetId() - wx.ID_HIGHEST - 1]
        try:
            self._frame.load_chapter(*refalize(reference))
        except StandardError:
            wx.MessageBox(_("'%s' is not a valid reference.") % reference, "Berean",
                          wx.ICON_EXCLAMATION | wx.OK)

    def OnViewAll(self, event):
        self._frame.show_multiverse_pane()
        bookmarks = [bookmark.partition("=")[0] for bookmark in self.bookmarks]
        self._frame.multiverse.verse_list.SetValue("\n".join(bookmarks))
        self._frame.multiverse.OnSearch(None)

    def OnHelp(self, event):
        webbrowser.open("https://github.com/t1m0thyj/berean/wiki")

    def OnAbout(self, event):
        info = adv.AboutDialogInfo()
        info.SetName("Berean")
        info.SetVersion(VERSION)
        info.SetCopyright("Copyright (c) 2011-2021 Timothy Johnson")
        info.SetDescription(_("An open source, cross-platform Bible study program"))
        info.SetWebSite("https://github.com/t1m0thyj/berean")
        info.SetLicense(LICENSE_TEXT)
        info.SetArtists([
            "FamFamFam Flag Icons (Copyright (c) Mark James)",
            "Fugue Icons (Copyright (c) Yusuke Kamiyamane)"
        ])
        adv.AboutBox(info)


class BookmarksDialog(wx.Dialog):
    def __init__(self, parent):
        super(BookmarksDialog,
              self).__init__(parent, title=_("Manage Bookmarks"),
                             style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self._parent = parent
        self.listbox = adv.EditableListBox(self, label=_("Bookmarks"))
        self.listbox.SetStrings(parent.menubar.bookmarks)
        self.listbox.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.OnListEndLabelEdit)
        self.text = wx.StaticText(self, label=_("Tip: You can add keywords separated by a \"|\" character"))
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.listbox, 1, wx.ALL | wx.EXPAND, 5)
        sizer.Add(self.text, 0, wx.ALL ^ wx.TOP | wx.ALIGN_CENTER_HORIZONTAL, 5)
        button_sizer = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        self.Bind(wx.EVT_BUTTON, self.OnOk, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)
        sizer.Add(button_sizer, 0, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(sizer)
        self.Fit()
        self.Center()

    def OnListEndLabelEdit(self, event):
        if event.IsEditCancelled():
            event.Skip()
            return
        label = event.GetLabel()
        try:
            reference = refalize(label)
        except StandardError:
            wx.MessageBox(_("'%s' is not a valid reference.") % label, "Berean",
                          wx.ICON_EXCLAMATION | wx.OK)
            event.Veto()
            return
        index = find_bookmark(reference, self.listbox.GetStrings())
        if index != -1 and index != event.GetIndex():
            wx.MessageBox(_("A bookmark for %s already exists.") % reference_str(*reference),
                          "Berean", wx.ICON_EXCLAMATION | wx.OK)
            event.Veto()
        else:
            event.Skip()

    def OnOk(self, event):
        self._parent.menubar.bookmarks = self.listbox.GetStrings()
        self._parent.menubar.update_bookmarks()
        self.Destroy()

    def OnCancel(self, event):
        self.Destroy()
