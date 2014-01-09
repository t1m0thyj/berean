"""menu.py - menubar and taskbar icon classes for Berean"""

import os

import wx
from wx import gizmos

from refalize import *

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
        self.favorites_list = frame._app.settings["FavoritesList"]

        self.file_menu = wx.Menu()
        self.file_menu.Append(wx.ID_SAVEAS, _("&Save As...\tCtrl+S"),
            _("Saves the current chapter as an HTML document"))
        frame.Bind(wx.EVT_MENU, self.OnSaveAs, id=wx.ID_SAVEAS)
        self.file_menu.AppendSeparator()
        self.file_menu.Append(wx.ID_PRINT, _("&Print...\tCtrl+P"),
            _("Prints the current chapter"))
        frame.Bind(wx.EVT_MENU, self.OnPrint, id=wx.ID_PRINT)
        self.file_menu.Append(wx.ID_PRINT_SETUP,
            _("Page &Setup...\tCtrl+Shift+P"),
            _("Changes page layout settings"))
        frame.Bind(wx.EVT_MENU, self.OnPageSetup, id=wx.ID_PRINT_SETUP)
        self.file_menu.Append(wx.ID_PREVIEW,
            _("P&rint Preview...\tCtrl+Alt+P"),
            _("Previews a printing of the current chapter"))
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
        self.Append(self.edit_menu, _("&Edit"))

        self.view_menu = wx.Menu()
        self.goto_verse_item = self.view_menu.Append(-1,
            _("&Go to Verse"), _("Goes to the specified verse"))
        frame.Bind(wx.EVT_MENU, self.OnGotoVerse, self.goto_verse_item)
        self.view_menu.Append(wx.ID_BACKWARD, _("Go &Back\tAlt+Left"),
            _("Returns to the previous chapter"))
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
            _("Restores the text to the default size"))
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
            _("&Search Pane\tCtrl+Shift+S"), _("Shows or hides the search pane"))
        frame.Bind(wx.EVT_MENU, self.OnSearchPane, self.search_pane_item)
        self.notes_pane_item = self.view_menu.AppendCheckItem(-1,
            _("&Notes Pane\tCtrl+Shift+N"), _("Shows or hides the notes pane"))
        frame.Bind(wx.EVT_MENU, self.OnNotesPane, self.notes_pane_item)
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

        self.tools_menu = wx.Menu()
        multiple_verse_search_item = self.tools_menu.Append(-1,
            _("&Multiple Verse Search...\tCtrl+M"))
        frame.Bind(wx.EVT_MENU, self.OnMultiverse, multiple_verse_search_item)
        self.tools_menu.Append(wx.ID_PREFERENCES, _("&Preferences..."),
            _("Configures program settings"))
        frame.Bind(wx.EVT_MENU, self.OnPreferences, id=wx.ID_PREFERENCES)
        self.Append(self.tools_menu, _("&Tools"))

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
            self.favorites_menu.Remove(wx.ID_HIGHEST + i - 2)
        if len(self.favorites_list):
            for i in range(len(self.favorites_list)):
                self.favorites_menu.Insert(i + 3, wx.ID_HIGHEST + i,
                    self.favorites_list[i])
                self._frame.Bind(wx.EVT_MENU, self.OnFavorite,
                    id=wx.ID_HIGHEST + i)
        else:
            empty_item = self.favorites_menu.Insert(3, -1, _("(Empty)"))
            self.favorites_menu.Enable(empty_item.GetId(), False)

    def multiple_verse_search(self, references=None):
        from dialogs import multiple_verse_search
        dialog = multiple_verse_search.MultipleVerseSearchDialog(self._frame,
            references)
        dialog.Show()

    def OnSaveAs(self, event):
        self._frame.printer.save_as()

    def OnPrint(self, event):
        self._frame.printer.print_chapter()

    def OnPageSetup(self, event):
        self._frame.printer.PageSetup()

    def OnPrintPreview(self, event):
        self._frame.printer.preview_chapter()

    def OnCopy(self, event):
        self._frame.Copy()

    def OnGotoVerse(self, event):
        self._frame.toolbar.OnSearch(event)

    def OnBack(self, event):
        self._frame.toolbar.OnBack(event)

    def OnForward(self, event):
        self._frame.toolbar.OnForward(event)

    def OnZoomIn(self, event):
        self._frame.Zoom(1)

    def OnZoomOut(self, event):
        self._frame.Zoom(-1)

    def OnZoomDefault(self, event):
        self._frame.Zoom(0)

    def OnToolbar(self, event):
        self._frame.aui.GetPane("toolbar").Show(event.IsChecked())
        self._frame.aui.Update()

    def OnTreePane(self, event):
        self._frame.aui.GetPane("tree_pane").Show(event.IsChecked())
        self._frame.aui.Update()

    def OnSearchPane(self, event):
        self._frame.aui.GetPane("search_pane").Show(event.IsChecked())
        self._frame.aui.Update()

    def OnNotesPane(self, event):
        self._frame.aui.GetPane("notes_pane").Show(event.IsChecked())
        self._frame.aui.Update()

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
        reference = self.favorites_list[wx.ID_HIGHEST - event.GetId()]
        try:
            self._frame.LoadChapter(*refalize(reference))
        except:
            wx.MessageBox(_("Sorry, but I do not understand '%s'.\n\nIf you think that Berean should accept it,\nplease email <timothysw@objectmail.com>.") % reference, "Berean", wx.ICON_EXCLAMATION | wx.OK)

    def OnViewAll(self, event):
        self.multiple_verse_search("\n".join(self.favorites_list))

    def OnMultiverse(self, event):
        self.multiple_verse_search()

    def OnPreferences(self, event):
        from dialogs import preferences
        dialog = preferences.PreferencesDialog(self._frame)
        dialog.Show()

    def OnHelp(self, event):
        self._frame.help.show_help_window()

    def OnAbout(self, event):
        self._frame.help.show_about_box()


class FavoritesManager(wx.Dialog):
    def __init__(self, parent):
        super(FavoritesManager, self).__init__(parent, -1,
            _("Manage Favorites"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self._parent = parent

        self.listbox = gizmos.EditableListBox(self, -1, _("Favorites List"))
        self.listbox.SetStrings(parent.menubar.favorites_list)
        self.listbox.Bind(wx.EVT_LIST_END_LABEL_EDIT,
            self.OnListboxEndLabelEdit)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.listbox, 1, wx.ALL | wx.EXPAND, 5)
        button_sizer = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        sizer.Add(button_sizer, 0, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(sizer)
        self.Layout()
        self.Bind(wx.EVT_BUTTON, self.OnOk, id=wx.ID_OK)

    def OnListboxEndLabelEdit(self, event):
        if not event.IsEditCancelled():
            label = event.GetLabel()
            try:
                reference = refalize(label)
            except:
                wx.MessageBox(_("Sorry, but I do not understand '%s'.\n\nIf you think that Berean should accept it,\nplease email <timothysw@objectmail.com>.") % label, _("Manage Favorites"), wx.ICON_EXCLAMATION | wx.OK)
                event.Veto()
            else:
                index = find_favorite(reference, self.listbox.GetStrings())
                if index != -1 and index != event.GetIndex():
                    if reference[2] == -1:
                        wx.MessageBox(_("%s %d is already in the favorites list.") % (BOOK_NAMES[reference[0] - 1], reference[1]), _("Manage Favorites"), wx.ICON_EXCLAMATION | wx.OK)
                    else:
                        wx.MessageBox(_("%s %d:%d is already in the favorites list.") % (BOOK_NAMES[reference[0] - 1], reference[1], reference[2]), _("Manage Favorites"), wx.ICON_EXCLAMATION | wx.OK)
                    event.Veto()
                else:
                    event.Skip()

    def OnOk(self, event):
        self._parent.menubar.favorites_list = self.listbox.GetStrings()
        self._parent.menubar.update_favorites()
        self.Close()
