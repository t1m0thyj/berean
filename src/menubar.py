"""menubar.py - menubar and bookmarks dialog classes"""

import webbrowser

import wx
from wx import gizmos

import html
from config import *
from refalize import refalize, reference_str

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
        self.menu_file.Append(wx.ID_PRINT, _("&Print...\tCtrl+P"),
            _("Prints the current chapter"))
        frame.Bind(wx.EVT_MENU, self.OnPrint, id=wx.ID_PRINT)
        self.menu_file.Append(wx.ID_PRINT_SETUP, _("Page &Setup..."),
            _("Changes page layout settings"))
        frame.Bind(wx.EVT_MENU, self.OnPageSetup, id=wx.ID_PRINT_SETUP)
        self.menu_file.Append(wx.ID_PREVIEW, _("P&rint Preview..."),
            _("Previews the current chapter"))
        frame.Bind(wx.EVT_MENU, self.OnPrintPreview, id=wx.ID_PREVIEW)
        if '__WXMAC__' not in wx.PlatformInfo:
            self.menu_file.AppendSeparator()
        self.menu_file.Append(wx.ID_EXIT, _("E&xit\tAlt+F4"),
            _("Exits the application"))
        frame.Bind(wx.EVT_MENU, frame.OnClose, id=wx.ID_EXIT)
        self.Append(self.menu_file, _("&File"))

        self.menu_edit = wx.Menu()
        self.menu_edit.Append(wx.ID_COPY, _("&Copy\tCtrl+C"),
            _("Copies the selected text to the clipboard"))
        frame.Bind(wx.EVT_MENU, self.OnCopy, id=wx.ID_COPY)
        if '__WXMAC__' not in wx.PlatformInfo:
            self.menu_edit.AppendSeparator()
        self.menu_edit.Append(wx.ID_PREFERENCES, _("&Preferences..."),
            _("Configures program settings"))
        frame.Bind(wx.EVT_MENU, self.OnPreferences, id=wx.ID_PREFERENCES)
        self.Append(self.menu_edit, _("&Edit"))

        self.menu_view = wx.Menu()
        self.go_to_verse_item = self.menu_view.Append(wx.ID_ANY,
            _("&Go to Verse"), _("Goes to the specified verse"))
        frame.Bind(wx.EVT_MENU, self.OnGoToVerse, self.go_to_verse_item)
        self.menu_view.Append(wx.ID_BACKWARD, _("Go &Back\tAlt+Left"),
            _("Goes to the previous chapter"))
        frame.Bind(wx.EVT_MENU, self.OnBack, id=wx.ID_BACKWARD)
        self.menu_view.Append(wx.ID_FORWARD, _("Go &Forward\tAlt+Right"),
            _("Goes to the next chapter"))
        frame.Bind(wx.EVT_MENU, self.OnForward, id=wx.ID_FORWARD)
        self.menu_view.AppendSeparator()
        self.menu_view.Append(wx.ID_ZOOM_IN, _("Zoom &In\tCtrl++"),
            _("Increases the text size"))
        self.menu_view.Enable(wx.ID_ZOOM_IN, frame.zoom_level < 7)
        frame.Bind(wx.EVT_MENU, self.OnZoomIn, id=wx.ID_ZOOM_IN)
        self.menu_view.Append(wx.ID_ZOOM_OUT, _("Zoom &Out\tCtrl+-"),
            _("Decreases the text size"))
        self.menu_view.Enable(wx.ID_ZOOM_OUT, frame.zoom_level > 1)
        frame.Bind(wx.EVT_MENU, self.OnZoomOut, id=wx.ID_ZOOM_OUT)
        self.menu_view.Append(wx.ID_ZOOM_100, _("Reset Zoom\tCtrl+0"),
            _("Resets the text size to the default"))
        frame.Bind(wx.EVT_MENU, self.OnZoomDefault, id=wx.ID_ZOOM_100)
        self.menu_view.AppendSeparator()
        self.toolbar_item = self.menu_view.AppendCheckItem(wx.ID_ANY,
            _("&Toolbar"))
        frame.Bind(wx.EVT_MENU, self.OnToolbar, self.toolbar_item)
        self.menu_view.AppendSeparator()
        self.tree_pane_item = self.menu_view.AppendCheckItem(wx.ID_ANY,
            _("T&ree Pane\tCtrl+Shift+T"))
        frame.Bind(wx.EVT_MENU, self.OnTreePane, self.tree_pane_item)
        self.search_pane_item = self.menu_view.AppendCheckItem(wx.ID_ANY,
            _("&Search Pane\tCtrl+Shift+S"))
        frame.Bind(wx.EVT_MENU, self.OnSearchPane, self.search_pane_item)
        self.notes_pane_item = self.menu_view.AppendCheckItem(wx.ID_ANY,
            _("&Notes Pane\tCtrl+Shift+N"))
        frame.Bind(wx.EVT_MENU, self.OnNotesPane, self.notes_pane_item)
        self.multiverse_pane_item = self.menu_view.AppendCheckItem(wx.ID_ANY,
            _("&Multi-Verse Retrieval\tCtrl+M"))
        frame.Bind(wx.EVT_MENU, self.OnMultiVersePane,
            self.multiverse_pane_item)
        self.Append(self.menu_view, _("&View"))

        self.menu_bookmarks = wx.Menu()
        self.add_to_bookmarks_item = self.menu_bookmarks.Append(wx.ID_ANY,
            _("&Add to Bookmarks\tCtrl+D"),
            _("Adds the current chapter to your bookmarks"))
        frame.Bind(wx.EVT_MENU, self.OnAddToBookmarks,
            self.add_to_bookmarks_item)
        self.manage_bookmarks_item = self.menu_bookmarks.Append(wx.ID_ANY,
            _("&Manage Bookmarks...\tCtrl+Shift+B"))
        frame.Bind(wx.EVT_MENU, self.OnManageBookmarks,
            self.manage_bookmarks_item)
        self.menu_bookmarks.AppendSeparator()
        self.menu_bookmarks.AppendSeparator()
        self.view_all_item = self.menu_bookmarks.Append(wx.ID_ANY,
            _("View All"))
        frame.Bind(wx.EVT_MENU, self.OnViewAll, self.view_all_item)
        self.update_bookmarks()
        self.Append(self.menu_bookmarks, _("&Bookmarks"))

        self.menu_help = wx.Menu()
        self.menu_help.Append(wx.ID_HELP, _("&Help...\tF1"),
            _("Shows the contents of the help file"))
        frame.Bind(wx.EVT_MENU, self.OnHelp, id=wx.ID_HELP)
        report_bug_item = self.menu_help.Append(-1, _("&Report Bug..."))
        frame.Bind(wx.EVT_MENU, self.OnReportBug, report_bug_item)
        self.menu_help.AppendSeparator()
        self.menu_help.Append(wx.ID_ABOUT, _("&About Berean..."),
            _("Displays program information, version number, and copyright"))
        frame.Bind(wx.EVT_MENU, self.OnAbout, id=wx.ID_ABOUT)
        self.Append(self.menu_help, _("&Help"))

    def update_bookmarks(self):
        for i in range(2, self.menu_bookmarks.GetMenuItemCount() - 3):
            self.menu_bookmarks.Remove(wx.ID_HIGHEST + i - 1)
        if self.bookmarks:
            for i in range(len(self.bookmarks)):
                self.menu_bookmarks.Insert(i + 3, wx.ID_HIGHEST + i + 1,
                    self.bookmarks[i])
                self._frame.Bind(wx.EVT_MENU, self.OnBookmark,
                    id=wx.ID_HIGHEST + i + 1)
        else:
            self.menu_bookmarks.Insert(3, wx.ID_HIGHEST + 1, _("(Empty)"))
            self.menu_bookmarks.Enable(wx.ID_HIGHEST + 1, False)
        self.menu_bookmarks.Enable(self.view_all_item.GetId(),
            len(self.bookmarks))

    def OnPrint(self, event):
        self._frame.printing.print_()

    def OnPageSetup(self, event):
        self._frame.printing.PageSetup()

    def OnPrintPreview(self, event):
        self._frame.printing.preview()

    def OnCopy(self, event):
        window = self._frame.FindFocus()
        if not isinstance(window, html.HtmlWindowBase):
            return
        data = wx.TextDataObject()
        data.SetText(window.SelectionToText())
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(data)
            wx.TheClipboard.Flush()
            wx.TheClipboard.Close()

    def OnPreferences(self, event):
        import preferences
        dialog = preferences.PreferencesDialog(self._frame)
        dialog.Show()

    def OnGoToVerse(self, event):
        self._frame.toolbar.OnGoToVerse(None)

    def OnBack(self, event):
        book, chapter, verse = refalize(
            self._frame.verse_history[self._frame.history_item - 1])
        self._frame.load_chapter(book, chapter, verse, False)

    def OnForward(self, event):
        book, chapter, verse = refalize(
            self._frame.verse_history[self._frame.history_item + 1])
        self._frame.load_chapter(book, chapter, verse, False)

    def OnZoomIn(self, event):
        self._frame.set_zoom(self._frame.zoom_level + 1)

    def OnZoomOut(self, event):
        self._frame.set_zoom(self._frame.zoom_level - 1)

    def OnZoomDefault(self, event):
        self._frame.set_zoom(0)

    def OnToolbar(self, event):
        self._frame.aui.GetPane("toolbar").Show(event.IsChecked())
        self._frame.aui.Update()

    def OnTreePane(self, event):
        self._frame.aui.GetPane("tree_pane").Show(event.IsChecked())
        self._frame.aui.Update()

    def OnSearchPane(self, event):
        self._frame.show_search_pane(event.IsChecked())

    def OnNotesPane(self, event):
        self._frame.aui.GetPane("notes_pane").Show(event.IsChecked())
        self._frame.aui.Update()

    def OnMultiVersePane(self, event):
        self._frame.show_multiverse_pane(event.IsChecked())

    def OnAddToBookmarks(self, event): 
        bookmark = reference_str(*self._frame.reference)
        if find_bookmark(self._frame.reference, self.bookmarks) == -1:
            self.bookmarks.append(bookmark)
            self.update_bookmarks()
        else:
            wx.MessageBox(_("A bookmark for %s already exists.") % bookmark,
                "Berean", wx.ICON_EXCLAMATION | wx.OK)

    def OnManageBookmarks(self, event):
        dialog = BookmarksDialog(self._frame)
        dialog.Show()

    def OnBookmark(self, event):
        reference = self.bookmarks[event.GetId() - wx.ID_HIGHEST - 1]
        try:
            self._frame.load_chapter(*refalize(reference))
        except Exception:
            wx.MessageBox(_("'%s' is not a valid reference.") % reference,
                "Berean", wx.ICON_EXCLAMATION | wx.OK)

    def OnViewAll(self, event):
        self._frame.show_multiverse_pane()
        self._frame.multiverse.verse_list.SetValue("\n".join(self.bookmarks))
        self._frame.multiverse.OnSearch(None)

    def OnHelp(self, event):
        self._frame.help.show_frame()

    def OnReportBug(self, event):
        webbrowser.open("mailto:berean_bugs@objectmail.com")

    def OnAbout(self, event):
        info = wx.AboutDialogInfo()
        info.SetName("Berean")
        info.SetVersion(VERSION)
        info.SetCopyright("Copyright (C) 2011-2014 Timothy Johnson")
        info.SetDescription(
            _("An open source, cross-platform Bible study tool"))
        ##info.SetWebSite("http://berean.sf.net")
        info.SetLicense(LICENSE)
        wx.AboutBox(info)


class BookmarksDialog(wx.Dialog):
    def __init__(self, parent):
        super(BookmarksDialog, self).__init__(parent,
            title=_("Manage Bookmarks"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self._parent = parent
        self.listbox = gizmos.EditableListBox(self, label=_("Bookmarks"))
        self.listbox.SetStrings(parent.menubar.bookmarks)
        self.listbox.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.OnListEndLabelEdit)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.listbox, 1, wx.ALL | wx.EXPAND, 5)
        button_sizer = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        self.Bind(wx.EVT_BUTTON, self.OnOk, id=wx.ID_OK)
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
        except Exception:
            wx.MessageBox(_("'%s' is not a valid reference.") % label,
                "Berean", wx.ICON_EXCLAMATION | wx.OK)
            event.Veto()
            return
        index = find_bookmark(reference, self.listbox.GetStrings())
        if index != -1 and index != event.GetIndex():
            wx.MessageBox(_("A bookmark for %s already exists.") %
                reference_str(*reference), "Berean",
                wx.ICON_EXCLAMATION | wx.OK)
            event.Veto()
        else:
            event.Skip()

    def OnOk(self, event):
        self._parent.menubar.bookmarks = self.listbox.GetStrings()
        self._parent.menubar.update_bookmarks()
        self.Destroy()


LICENSE = """This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>."""
