"""menu.py - menubar class and favorites management"""

import wx
from wx import gizmos

import html
from globals import *
from refalize import refalize

_ = wx.GetTranslation


def find_favorite(reference, favorites_list):
    for i in range(len(favorites_list)):
        if refalize(favorites_list[i]) == reference:
            return i
    return -1


class MenuBar(wx.MenuBar):
    def __init__(self, frame):
        super(MenuBar, self).__init__()
        self._frame = frame
        self.favorites_list = frame._app.config.ReadList("FavoritesList")

        self.file_menu = wx.Menu()
        self.file_menu.Append(wx.ID_PRINT, _("&Print...\tCtrl+P"),
            _("Prints the current chapter"))
        frame.Bind(wx.EVT_MENU, self.OnPrint, id=wx.ID_PRINT)
        self.file_menu.Append(wx.ID_PRINT_SETUP, _("Page &Setup..."),
            _("Changes page layout settings"))
        frame.Bind(wx.EVT_MENU, self.OnPageSetup, id=wx.ID_PRINT_SETUP)
        self.file_menu.Append(wx.ID_PREVIEW, _("P&rint Preview..."),
            _("Previews the current chapter"))
        frame.Bind(wx.EVT_MENU, self.OnPrintPreview, id=wx.ID_PREVIEW)
        if '__WXMAC__' not in wx.PlatformInfo:
            self.file_menu.AppendSeparator()
        self.file_menu.Append(wx.ID_EXIT, _("E&xit\tAlt+F4"),
            _("Exits the application"))
        frame.Bind(wx.EVT_MENU, frame.OnClose, id=wx.ID_EXIT)
        self.Append(self.file_menu, _("&File"))

        self.edit_menu = wx.Menu()
        self.edit_menu.Append(wx.ID_COPY, _("&Copy\tCtrl+C"),
            _("Copies the selected text to the clipboard"))
        frame.Bind(wx.EVT_MENU, self.OnCopy, id=wx.ID_COPY)
        if '__WXMAC__' not in wx.PlatformInfo:
            self.edit_menu.AppendSeparator()
        self.edit_menu.Append(wx.ID_PREFERENCES, _("&Preferences..."),
            _("Configures program settings"))
        frame.Bind(wx.EVT_MENU, self.OnPreferences, id=wx.ID_PREFERENCES)
        self.Append(self.edit_menu, _("&Edit"))

        self.view_menu = wx.Menu()
        self.goto_verse_item = self.view_menu.Append(-1,
            _("&Go to Verse"), _("Goes to the specified verse"))
        frame.Bind(wx.EVT_MENU, self.OnGotoVerse, self.goto_verse_item)
        self.view_menu.Append(wx.ID_BACKWARD, _("Go &Back\tAlt+Left"),
            _("Goes to the previous chapter"))
        frame.Bind(wx.EVT_MENU, self.OnBack, id=wx.ID_BACKWARD)
        self.view_menu.Append(wx.ID_FORWARD, _("Go &Forward\tAlt+Right"),
            _("Goes to the next chapter"))
        frame.Bind(wx.EVT_MENU, self.OnForward, id=wx.ID_FORWARD)
        self.view_menu.AppendSeparator()
        self.view_menu.Append(wx.ID_ZOOM_IN, _("Zoom &In\tCtrl++"),
            _("Increases the text size"))
        self.view_menu.Enable(wx.ID_ZOOM_IN, frame.zoom_level < 7)
        frame.Bind(wx.EVT_MENU, self.OnZoomIn, id=wx.ID_ZOOM_IN)
        self.view_menu.Append(wx.ID_ZOOM_OUT, _("Zoom &Out\tCtrl+-"),
            _("Decreases the text size"))
        self.view_menu.Enable(wx.ID_ZOOM_OUT, frame.zoom_level > 1)
        frame.Bind(wx.EVT_MENU, self.OnZoomOut, id=wx.ID_ZOOM_OUT)
        self.view_menu.Append(wx.ID_ZOOM_100, _("Reset Zoom\tCtrl+0"),
            _("Resets the text size to the default"))
        frame.Bind(wx.EVT_MENU, self.OnZoomDefault, id=wx.ID_ZOOM_100)
        self.view_menu.AppendSeparator()
        self.toolbar_item = self.view_menu.AppendCheckItem(-1, _("&Toolbar"),
            _("Shows or hides the main toolbar"))
        frame.Bind(wx.EVT_MENU, self.OnToolbar, self.toolbar_item)
        self.view_menu.AppendSeparator()
        self.tree_pane_item = self.view_menu.AppendCheckItem(-1,
            _("T&ree Pane\tCtrl+Shift+T"), _("Shows or hides the tree pane"))
        frame.Bind(wx.EVT_MENU, self.OnTreePane, self.tree_pane_item)
        self.search_pane_item = self.view_menu.AppendCheckItem(-1,
            _("&Search Pane\tCtrl+Shift+S"),
            _("Shows or hides the search pane"))
        frame.Bind(wx.EVT_MENU, self.OnSearchPane, self.search_pane_item)
        self.notes_pane_item = self.view_menu.AppendCheckItem(-1,
            _("&Notes Pane\tCtrl+Shift+N"), _("Shows or hides the notes pane"))
        frame.Bind(wx.EVT_MENU, self.OnNotesPane, self.notes_pane_item)
        self.multiple_verse_search_item = self.view_menu.AppendCheckItem(-1,
            _("&Multiple Verse Search\tCtrl+M"),
            _("Shows or hides the Multiple Verse Search pane"))
        frame.Bind(wx.EVT_MENU, self.OnMultipleVerseSearch,
            self.multiple_verse_search_item)
        self.Append(self.view_menu, _("&View"))

        self.favorites_menu = wx.Menu()
        self.add_to_favorites_item = self.favorites_menu.Append(-1,
            _("&Add to Favorites\tCtrl+D"))
        frame.Bind(wx.EVT_MENU, self.OnAddToFavorites,
            self.add_to_favorites_item)
        self.manage_favorites_item = self.favorites_menu.Append(-1,
            _("&Manage Favorites..."))
        frame.Bind(wx.EVT_MENU, self.OnManageFavorites,
            self.manage_favorites_item)
        self.favorites_menu.AppendSeparator()
        self.favorites_menu.AppendSeparator()
        view_all_item = self.favorites_menu.Append(-1, _("View All"))
        frame.Bind(wx.EVT_MENU, self.OnViewAll, view_all_item)
        self.update_favorites()
        self.Append(self.favorites_menu, _("F&avorites"))

        self.help_menu = wx.Menu()
        self.help_menu.Append(wx.ID_HELP, _("&Contents...\tF1"),
            _("Shows the contents of the help file"))
        frame.Bind(wx.EVT_MENU, self.OnHelp, id=wx.ID_HELP)
        self.help_menu.Append(wx.ID_ABOUT, _("&About..."),
            _("Displays program information, version number, and copyright"))
        frame.Bind(wx.EVT_MENU, self.OnAbout, id=wx.ID_ABOUT)
        self.Append(self.help_menu, _("&Help"))

    def update_favorites(self):
        for i in range(2, self.favorites_menu.GetMenuItemCount() - 3):
            self.favorites_menu.Remove(wx.ID_HIGHEST + i - 1)
        if len(self.favorites_list):
            for i in range(len(self.favorites_list)):
                self.favorites_menu.Insert(i + 3, wx.ID_HIGHEST + i + 1,
                    self.favorites_list[i])
                self._frame.Bind(wx.EVT_MENU, self.OnFavorite,
                    id=wx.ID_HIGHEST + i + 1)
        else:
            self.favorites_menu.Insert(3, wx.ID_HIGHEST + 1, _("(Empty)"))
            self.favorites_menu.Enable(wx.ID_HIGHEST + 1, False)

    def OnPrint(self, event):
        self._frame.printing.print_chapter()

    def OnPageSetup(self, event):
        self._frame.printing.PageSetup()

    def OnPrintPreview(self, event):
        self._frame.printing.preview_chapter()

    def OnCopy(self, event):
        window = self._frame.FindFocus()
        if not isinstance(window, html.BaseHtmlWindow):
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

    def OnGotoVerse(self, event):
        self._frame.toolbar.OnGotoVerse(event)

    def OnBack(self, event):
        self._frame.toolbar.OnBack(event)

    def OnForward(self, event):
        self._frame.toolbar.OnForward(event)

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

    def OnMultipleVerseSearch(self, event):
        self._frame.show_multiple_verse_search(event.IsChecked())

    def OnAddToFavorites(self, event):
        if self._frame.reference[2] == -1:
            favorite = "%s %s" % (BOOK_NAMES[self._frame.reference[0] - 1],
                self._frame.reference[1])
        else:
            favorite = "%s %s:%s" % (BOOK_NAMES[self._frame.reference[0] - 1],
                self._frame.reference[1], self._frame.reference[2])
        if find_favorite(refalize(favorite), self.favorites_list) == -1:
            self.favorites_list.append(favorite)
            self.update_favorites()
        else:
            wx.MessageBox(_("%s is already in the favorites list.") % favorite,
                "Berean", wx.ICON_EXCLAMATION | wx.OK)

    def OnManageFavorites(self, event):
        dialog = FavoritesManager(self._frame)
        dialog.Show()

    def OnFavorite(self, event):
        reference = self.favorites_list[event.GetId() - wx.ID_HIGHEST - 1]
        try:
            self._frame.load_chapter(*refalize(reference))
        except:
            wx.MessageBox(_("Sorry, but I do not understand '%s'.\n\nIf you think that Berean should accept it,\nplease email <timothysw@objectmail.com>.") % reference, "Berean", wx.ICON_EXCLAMATION | wx.OK)

    def OnViewAll(self, event):
        self._frame.show_multiple_verse_search()
        self._frame.multiple_verse_search.verse_list.SetValue(
            "\n".join(self.favorites_list))
        self._frame.multiple_verse_search.OnSearch(None)

    def OnHelp(self, event):
        self._frame.help.show_help_window()

    def OnAbout(self, event):
        info = wx.AboutDialogInfo()
        info.SetName("Berean")
        info.SetVersion(VERSION)
        info.SetCopyright("Copyright (C) 2011-2014 Timothy Johnson")
        info.SetDescription(
            _("An open source, cross-platform Bible study tool"))
        info.SetWebSite("http://berean.sf.net")
        info.SetLicense(LICENSE)
        wx.AboutBox(info)


class FavoritesManager(wx.Dialog):
    def __init__(self, parent):
        super(FavoritesManager, self).__init__(parent, -1,
            _("Manage Favorites"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self._parent = parent
        self.listbox = gizmos.EditableListBox(self, -1, _("Favorites List"))
        self.listbox.SetStrings(parent.menubar.favorites_list)
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
        if not event.IsEditCancelled():
            label = event.GetLabel()
            try:
                reference = refalize(label)
            except:
                wx.MessageBox(_("Sorry, but I do not understand '%s'.\n\nIf you think that Berean should accept it,\nplease email <timothysw@objectmail.com>.") % label, _("Manage Favorites"), wx.ICON_EXCLAMATION | wx.OK)
                event.Veto()
                return
            index = find_favorite(reference, self.listbox.GetStrings())
            if index != -1 and index != event.GetIndex():
                if reference[2] == -1:
                    wx.MessageBox(_("%s %d is already in the favorites list.") % (BOOK_NAMES[reference[0] - 1], reference[1]), _("Manage Favorites"), wx.ICON_EXCLAMATION | wx.OK)
                else:
                    wx.MessageBox(_("%s %d:%d is already in the favorites list.") % (BOOK_NAMES[reference[0] - 1], reference[1], reference[2]), _("Manage Favorites"), wx.ICON_EXCLAMATION | wx.OK)
                event.Veto()
                return
        event.Skip()

    def OnOk(self, event):
        self._parent.menubar.favorites_list = self.listbox.GetStrings()
        self._parent.menubar.update_favorites()
        self.Close()


LICENSE = """This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
