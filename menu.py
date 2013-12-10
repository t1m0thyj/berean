"""
menu.py - menu and menubar classes for Berean
Copyright (C) 2013 Timothy Johnson <timothysw@objectmail.com>
"""

import os

import wx

import favorites

_ = wx.GetTranslation

class MenuBar(wx.MenuBar):
    def __init__(self, frame):
        wx.MenuBar.__init__(self)
        self._frame = frame

        self.File = wx.Menu()
        self.File.Append(wx.ID_SAVEAS, _("&Save As...\tCtrl+S"), _("Saves the current chapter as an HTML document"))
        frame.Bind(wx.EVT_MENU, self.OnSaveAs, id=wx.ID_SAVEAS)
        self.File.AppendSeparator()
        self.File.Append(wx.ID_PRINT, _("&Print...\tCtrl+P"), _("Prints the current chapter"))
        frame.Bind(wx.EVT_MENU, self.OnPrint, id=wx.ID_PRINT)
        self.File.Append(wx.ID_PRINT_SETUP, _("Page &Setup...\tCtrl+Shift+P"), _("Changes page layout settings"))
        frame.Bind(wx.EVT_MENU, self.OnPageSetup, id=wx.ID_PRINT_SETUP)
        self.File.Append(wx.ID_PREVIEW, _("P&rint Preview...\tCtrl+Alt+P"), _("Previews a printing of the current chapter"))
        frame.Bind(wx.EVT_MENU, self.OnPrintPreview, id=wx.ID_PREVIEW)
        if wx.Platform != "__WXMAC__":
            self.File.AppendSeparator()
        self.File.Append(wx.ID_EXIT, _("E&xit\tAlt+F4"), _("Exits the application"))
        frame.Bind(wx.EVT_MENU, frame.OnClose, id=wx.ID_EXIT)
        self.Append(self.File, _("&File"))

        self.Edit = wx.Menu()
        self.Edit.Append(wx.ID_COPY, _("&Copy\tCtrl+C"), _("Copies the selected text to the clipboard"))
        frame.Bind(wx.EVT_MENU, self.OnCopy, id=wx.ID_COPY)
        self.Append(self.Edit, _("&Edit"))

        self.View = wx.Menu()
        self.View.Append(wx.ID_FIND, _("Go to Reference\tCtrl+F"), _("Goes to the specified reference"))
        frame.Bind(wx.EVT_MENU, self.OnReference, id=wx.ID_FIND)
        self.View.Append(wx.ID_BACKWARD, _("Go &Back\tAlt+Left"), _("Returns to the previous chapter"))
        frame.Bind(wx.EVT_MENU, self.OnBack, id=wx.ID_BACKWARD)
        self.View.Append(wx.ID_FORWARD, _("Go &Forward\tAlt+Right"), _("Goes to the next chapter"))
        frame.Bind(wx.EVT_MENU, self.OnForward, id=wx.ID_FORWARD)
        self.View.AppendSeparator()
        self.View.Append(wx.ID_ZOOM_IN, _("Zoom &In\tCtrl++"), _("Increases the text size"))
        frame.Bind(wx.EVT_MENU, self.OnZoomIn, id=wx.ID_ZOOM_IN)
        self.View.Append(wx.ID_ZOOM_OUT, _("Zoom &Out\tCtrl+-"), _("Decreases the text size"))
        frame.Bind(wx.EVT_MENU, self.OnZoomOut, id=wx.ID_ZOOM_OUT)
        self.View.Append(wx.ID_ZOOM_100, _("Reset Zoom\tCtrl+0"), _("Restores the text to the default size"))
        frame.Bind(wx.EVT_MENU, self.OnZoomDefault, id=wx.ID_ZOOM_100)
        self.View.AppendSeparator()
        self.ID_MAIN_TOOLBAR = wx.NewId()
        self.View.AppendCheckItem(self.ID_MAIN_TOOLBAR, _("&Main Toolbar"), _("Shows or hides the main toolbar"))
        frame.Bind(wx.EVT_MENU, self.OnMainToolBar, id=self.ID_MAIN_TOOLBAR)
        self.ID_CHAPTER_TOOLBAR = wx.NewId()
        self.View.AppendCheckItem(self.ID_CHAPTER_TOOLBAR, _("&Chapter Toolbar"), _("Shows or hides the chapter toolbar"))
        frame.Bind(wx.EVT_MENU, self.OnChapterToolBar, id=self.ID_CHAPTER_TOOLBAR)
        self.View.AppendSeparator()
        self.ID_TREEPANE = wx.NewId()
        self.View.AppendCheckItem(self.ID_TREEPANE, _("T&ree Pane\tCtrl+Alt+T"), _("Shows or hides the tree pane"))
        frame.Bind(wx.EVT_MENU, self.OnTreePane, id=self.ID_TREEPANE)
        self.ID_SEARCHPANE = wx.NewId()
        self.View.AppendCheckItem(self.ID_SEARCHPANE, _("&Search Pane\tCtrl+Alt+S"), _("Shows or hides the search pane"))
        frame.Bind(wx.EVT_MENU, self.OnSearchPane, id=self.ID_SEARCHPANE)
        self.ID_NOTESPANE = wx.NewId()
        self.View.AppendCheckItem(self.ID_NOTESPANE, _("&Notes Pane\tCtrl+Alt+N"), _("Shows or hides the notes pane"))
        frame.Bind(wx.EVT_MENU, self.OnNotesPane, id=self.ID_NOTESPANE)
        self.Append(self.View, _("&View"))

        self.Favorites = favorites.FavoritesMenu(frame)
        self.Append(self.Favorites, _("F&avorites"))

        self.Tools = wx.Menu()
        self.ID_MULTIVERSE = wx.NewId()
        self.Tools.Append(self.ID_MULTIVERSE, _("&Multiple Verse Search...\tCtrl+M"))
        frame.Bind(wx.EVT_MENU, self.OnMultiverse, id=self.ID_MULTIVERSE)
        self.Tools.Append(wx.ID_PREFERENCES, _("&Preferences..."), _("Configures program settings"))
        frame.Bind(wx.EVT_MENU, self.OnPreferences, id=wx.ID_PREFERENCES)
        self.Append(self.Tools, _("&Tools"))

        self.Help = wx.Menu()
        self.Help.Append(wx.ID_HELP, _("&Contents...\tF1"), _("Shows the contents of the help file"))
        frame.Bind(wx.EVT_MENU, self.OnHelp, id=wx.ID_HELP)
        self.Help.Append(wx.ID_ABOUT, _("&About..."), _("Displays program information, version number, and copyright"))
        frame.Bind(wx.EVT_MENU, self.OnAbout, id=wx.ID_ABOUT)
        self.Append(self.Help, _("&Help"))

        self.Enable(wx.ID_ZOOM_IN, frame.zoom < 7)
        self.Enable(wx.ID_ZOOM_OUT, frame.zoom > 1)

    def OnSaveAs(self, event):
        self._frame.printer.SaveAs()

    def OnPrint(self, event):
        self._frame.printer.Print()

    def OnPageSetup(self, event):
        self._frame.printer.PageSetup()

    def OnPrintPreview(self, event):
        self._frame.printer.Preview()

    def OnCopy(self, event):
        self._frame.Copy()

    def OnReference(self, event):
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

    def OnMainToolBar(self, event):
        self._frame.ShowMainToolBar(event.IsChecked())

    def OnChapterToolBar(self, event):
        self._frame.ShowChapterToolBar(event.IsChecked())

    def OnTreePane(self, event):
        self._frame.ShowTreePane(event.IsChecked())

    def OnSearchPane(self, event):
        self._frame.ShowSearchPane(event.IsChecked())

    def OnNotesPane(self, event):
        self._frame.ShowNotesPane(event.IsChecked())

    def OnMultiverse(self, event):
        self._frame.MultiverseSearch()

    def OnPreferences(self, event):
        self._frame.Preferences()

    def OnHelp(self, event):
        self._frame.helper.ShowHelpFrame()

    def OnAbout(self, event):
        self._frame.helper.ShowAboutBox()


class TaskBarIcon(wx.TaskBarIcon):
    def __init__(self, frame):
        wx.TaskBarIcon.__init__(self)
        self._frame = frame

        self.SetIcon(wx.Icon(os.path.join(frame._app.cwd, "images", "berean-16.png"), wx.BITMAP_TYPE_PNG), frame.GetTitle())

        self.Bind(wx.EVT_TASKBAR_LEFT_DOWN, self.OnRestore)

    def OnRestore(self, event):
        self._frame.Iconize(False)
        self._frame.Show()
        self._frame.Raise()
        self.RemoveIcon()
        wx.CallAfter(self._frame.GetBrowser().SetFocus)
        del self._frame.trayicon

    def OnExit(self, event):
        wx.CallAfter(self._frame.Close)
        self.OnRestore(event)

    def CreatePopupMenu(self):
        menu = wx.Menu()
        menu.Append(wx.ID_DEFAULT, _("&Restore"))
        self.Bind(wx.EVT_MENU, self.OnRestore, id=wx.ID_DEFAULT)
        menu.Append(wx.ID_EXIT, _("E&xit"))
        self.Bind(wx.EVT_MENU, self.OnExit, id=wx.ID_EXIT)
        return menu
