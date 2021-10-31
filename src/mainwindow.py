"""mainwindow.py - main window and taskbar icon classes"""

import os

import wx
from wx import adv, aui

import html2
import menu
import parallel
import panes
import toolbar
from refalize import reference_str
from settings import BOOK_NAMES, BOOK_LENGTHS, BOOK_RANGES

_ = wx.GetTranslation


class MainWindow(wx.Frame):
    def __init__(self, app):
        pos = [int(i) for i in app.config.Read("Main/WindowPosition", "-1,-1").split(",")]
        display_size = wx.GetDisplaySize()
        default_size = (int(display_size[0] * 0.8), int(display_size[1] * 0.8))
        size = [int(i) for i in app.config.Read("Main/WindowSize", "%d,%d" % default_size).split(",")]
        self.rect = wx.Rect(pos, size)
        super(MainWindow, self).__init__(None, title="Berean", pos=pos, size=size)
        icons = wx.IconBundle()
        icons.AddIcon(os.path.join(app.cwd, "images", "berean-16.png"), wx.BITMAP_TYPE_PNG)
        icons.AddIcon(os.path.join(app.cwd, "images", "berean-32.png"), wx.BITMAP_TYPE_PNG)
        self.SetIcons(icons)
        if app.config.ReadBool("Main/IsMaximized"):
            self.Maximize()

        self._app = app
        self.reference = (app.config.ReadInt("Main/CurrentBook", 1),
                          app.config.ReadInt("Main/CurrentChapter", 1),
                          app.config.ReadInt("Main/CurrentVerse", -1))
        self.default_font = {
            "size": app.config.ReadInt("Main/HtmlFontSize", 12),
            "normal_face": app.config.Read("Main/HtmlFontFace",
                                           wx.FFont(-1, wx.ROMAN).GetFaceName())}
        self.facenames = sorted([facename for facename in wx.FontEnumerator.GetFacenames()
                                 if not facename.startswith("@")])
        self.zoom_level = app.config.ReadInt("Main/ZoomLevel", 3)
        self.minimize_to_tray = app.config.ReadBool("Main/MinimizeToTray")
        self.version_list = app.config.ReadList("VersionList", ["KJV"])
        self.verse_history = app.config.ReadList("History")
        self.history_item = -1
        self.old_versions = []
        self.printing = html2.PrintingSystem(self)

        self.aui = aui.AuiManager(self)
        self.menubar = menu.MenuBar(self)
        self.SetMenuBar(self.menubar)
        self.toolbar = toolbar.ToolBar(self)
        self.aui.AddPane(self.toolbar, aui.AuiPaneInfo().Name("toolbar").Caption("Toolbar").
                         ToolbarPane().Top())
        self.statusbar = self.CreateStatusBar(3)
        self.zoombar = toolbar.ZoomBar(self.statusbar, self)
        self.statusbar.SetStatusWidths([-1, -1, self.zoombar.width -
                                        wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_X) + 1])

        self.notebook = aui.AuiNotebook(self, style=aui.AUI_NB_TOP | aui.AUI_NB_SCROLL_BUTTONS |
                                                    aui.AUI_NB_WINDOWLIST_BUTTON)
        if not app.portable:
            self.versiondir = os.path.join(wx.StandardPaths.Get().GetUserLocalDataDir(),
                                           "versions")
        else:
            self.versiondir = os.path.join(app.userdatadir, "versions")
        if not os.path.isdir(self.versiondir):
            os.makedirs(self.versiondir)
        i = 0
        tab = app.config.ReadInt("Main/ActiveVersionTab")
        while i < len(self.version_list):
            window = html2.ChapterWindow(self.notebook, self.version_list[i])
            if hasattr(window, "Bible"):
                self.notebook.AddPage(window, self.version_list[i])
                self.notebook.SetPageBitmap(i, self.get_bitmap(os.path.join("flags", window.flag_name)))
                self.notebook.SetPageToolTip(i, window.description)
                i += 1
            else:
                del self.version_list[i]
                if tab > i:
                    tab -= 1
        if len(self.version_list) > 1:
            self.parallel = parallel.ParallelPanel(self.notebook)
            self.notebook.AddPage(self.parallel, _("Parallel"))
            self.notebook.SetPageToolTip(len(self.version_list), self.parallel.htmlwindow.description)
            self.notebook.SetSelection(min(tab, self.notebook.GetPageCount()))
        else:
            self.notebook.SetTabCtrlHeight(0)
        self.notebook.Bind(aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.OnAuiNotebookPageChanged)
        self.notebook.Bind(aui.EVT_AUINOTEBOOK_BG_DCLICK, self.OnAuiNotebookBgDclick)
        self.aui.AddPane(self.notebook, aui.AuiPaneInfo().Name("notebook").CenterPane().
                         PaneBorder(False))

        self.tree = panes.TreePane(self)
        self.aui.AddPane(self.tree, aui.AuiPaneInfo().Name("tree_pane").Caption(_("Tree")).
                         BestSize((150, 600)).Left().Layer(1).PinButton(True))
        self.search = panes.SearchPane(self)
        self.aui.AddPane(self.search, aui.AuiPaneInfo().Name("search_pane").Caption(_("Search")).
                         BestSize((300, 600)).Right().Layer(1).PinButton(True))
        self.multiverse = panes.MultiVersePane(self)
        self.aui.AddPane(self.multiverse, aui.AuiPaneInfo().Name("multiverse_pane").
                         Caption(_("Multi-Verse Retrieval")).BestSize((600, 300)).Bottom().
                         Hide().PinButton(True))

        filename = os.path.join(app.userdatadir, "layout.dat")
        if os.path.isfile(filename):
            with open(filename, 'r') as fileobj:
                self.aui.LoadPerspective(fileobj.read())
        self.aui.Update()
        for pane in ("toolbar", "tree_pane", "search_pane", "multiverse_pane"):
            self.menubar.Check(getattr(self.menubar, "%s_item" % pane).GetId(),
                               self.aui.GetPane(pane).IsShown())
        globals()["BOOK_NAMES"] = BOOK_NAMES[:18] + ("Psalm",) + BOOK_NAMES[19:]
        self.load_chapter(self.reference[0], self.reference[1], self.reference[2], False)
        self.Bind(aui.EVT_AUI_PANE_CLOSE, self.OnAuiPaneClose)
        self.Bind(wx.EVT_MOVE, self.OnMove)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_ICONIZE, self.OnIconize)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def get_bitmap(self, name):
        img_path = os.path.join(self._app.cwd, "images", "%s.png" % name)
        if not os.path.isfile(img_path):
            return wx.NullBitmap
        return wx.Bitmap(img_path, wx.BITMAP_TYPE_PNG)

    def get_htmlwindow(self, tab=-1):
        if tab == -1:
            tab = self.notebook.GetSelection()
        if tab == len(self.version_list) and len(self.version_list) > 1:
            return self.parallel.htmlwindow
        return self.notebook.GetPage(tab)

    def load_chapter(self, book, chapter, verse=-1, edit_history=True):
        htmlwindow = self.get_htmlwindow()
        htmlwindow.load_chapter(book, chapter, verse)
        tab = self.notebook.GetSelection()
        self.SetTitle("Berean - %s %d (%s)" %
                      (BOOK_NAMES[book - 1], chapter, self.notebook.GetPageText(tab)))
        reference = reference_str(book, chapter, verse)
        if reference not in self.verse_history:
            self.verse_history = self.verse_history[:self.history_item + 1]
            self.verse_history.append(reference)
            if len(self.verse_history) >= 15:
                del self.verse_history[0]
        elif edit_history:
            self.verse_history.remove(reference)
            self.verse_history.append(reference)
        self.history_item = self.verse_history.index(reference)
        self.toolbar.EnableTool(wx.ID_BACKWARD, self.history_item > 0)
        self.toolbar.EnableTool(wx.ID_FORWARD, self.history_item < len(self.verse_history) - 1)
        self.toolbar.Refresh(False)
        if book != self.reference[0]:
            self.toolbar.bookctrl.SetSelection(book - 1)
            self.toolbar.chapterctrl.SetRange(1, BOOK_LENGTHS[book - 1])
        if chapter != self.reference[1]:
            self.toolbar.chapterctrl.SetValue(chapter)
        self.tree.select_chapter(book, chapter)
        if self.search.range_choice.GetSelection() == len(BOOK_RANGES):
            self.search.start.SetSelection(book - 1)
            self.search.stop.SetSelection(book - 1)
        self.statusbar.SetStatusText("%s %d" % (BOOK_NAMES[book - 1], chapter), 0)
        self.statusbar.SetStatusText(htmlwindow.description, 1)
        self.menubar.Enable(wx.ID_BACKWARD, self.history_item > 0)
        self.menubar.Enable(wx.ID_FORWARD, self.history_item < len(self.verse_history) - 1)
        self.reference = (book, chapter, verse)
        for i in range(self.notebook.GetPageCount()):
            if i != tab:
                self.get_htmlwindow(i).current_verse = verse
        htmlwindow.SetFocus()

    def set_zoom(self, zoom):
        self.zoom_level = zoom
        self.get_htmlwindow().load_chapter(*self.reference)
        if self.zoombar.slider.GetValue() != zoom:
            self.zoombar.slider.SetValue(zoom)
        self.zoombar.EnableTool(wx.ID_ZOOM_OUT, zoom > 1)
        self.zoombar.EnableTool(wx.ID_ZOOM_IN, zoom < 7)
        self.menubar.Enable(wx.ID_ZOOM_IN, zoom < 7)
        self.menubar.Enable(wx.ID_ZOOM_OUT, zoom > 1)

    def toggle_reader_view(self, update_toolbar=True):
        pane = self.aui.GetPane("notebook")
        maximized = pane.IsMaximized()
        if not pane.IsMaximized():
            self.aui.MaximizePane(pane)
        else:
            self.aui.RestorePane(pane)
        self.aui.Update()
        self.menubar.Check(self.menubar.reader_view_item.GetId(), not maximized)
        if update_toolbar:
            self.toolbar.ToggleTool(self.toolbar.ID_READER_VIEW, not maximized)
            self.toolbar.Refresh(False)

    def show_search_pane(self, show=True):
        self.aui.GetPane("search_pane").Show(show)
        self.aui.Update()
        self.menubar.Check(self.menubar.search_pane_item.GetId(), show)

    def show_multiverse_pane(self, show=True):
        self.aui.GetPane("multiverse_pane").Show(show)
        self.aui.Update()
        self.menubar.Check(self.menubar.multiverse_pane_item.GetId(), show)

    def OnAuiNotebookPageChanged(self, event):
        tab = event.GetSelection()
        htmlwindow = self.get_htmlwindow()
        if htmlwindow.reference != self.reference or htmlwindow.zoom_level != self.zoom_level:
            htmlwindow.load_chapter(*self.reference)
        self.SetTitle("Berean - %s %d (%s)" %
                      (BOOK_NAMES[self.reference[0] - 1], self.reference[1],
                       self.notebook.GetPageText(tab)))
        self.statusbar.SetStatusText(htmlwindow.description, 1)
        if tab < len(self.version_list):
            self.search.version.SetSelection(tab)
            self.multiverse.version.SetSelection(tab)

    def OnAuiNotebookBgDclick(self, event):
        self.toggle_reader_view()

    def OnAuiPaneClose(self, event):
        self.menubar.Check(getattr(self.menubar, "%s_item" % event.GetPane().name).GetId(), False)

    def OnMove(self, event):
        if self.HasCapture():
            self.rect.SetPosition(self.GetPosition())
        event.Skip()

    def OnSize(self, event):
        x, y, width, height = self.statusbar.GetFieldRect(2)
        if 'gtk3' in wx.PlatformInfo:
            height -= 16
        self.zoombar.SetRect(wx.Rect(x, (y + height - 19) / 2 - self.zoombar.GetToolSeparation(),
                                     self.zoombar.width, -1))
        if self.HasCapture():
            self.rect = wx.Rect(self.GetPosition(), self.GetSize())

    def OnIconize(self, event):
        if self.minimize_to_tray and event.Iconized() and not hasattr(self, "taskbaricon"):
            self.taskbaricon = TaskBarIcon(self)
            self.Hide()
        event.Skip()

    def OnClose(self, event):
        for version in self.old_versions:  # Delete old indexes
            filename = os.path.join(self._app.userdatadir, "indexes", "%s.idx" % version)
            if os.path.isfile(filename):
                wx.CallAfter(os.remove, filename)
        self._app.config.save()
        with open(os.path.join(self._app.userdatadir, "layout.dat"), 'w') as fileobj:
            fileobj.write(self.aui.SavePerspective())
        self.aui.UnInit()
        self.Destroy()
        self._app.SetSingleInstance(False)
        del self._app.locale  # TODO Why?
        self._app.ExitMainLoop()


class TaskBarIcon(adv.TaskBarIcon):
    def __init__(self, frame):
        super(TaskBarIcon, self).__init__()
        self._frame = frame
        self.SetIcon(wx.Icon(os.path.join(frame._app.cwd, "images", "berean-16.png"),
                             wx.BITMAP_TYPE_PNG), frame.GetTitle())
        self.Bind(adv.EVT_TASKBAR_LEFT_DOWN, self.OnRestore)

    def CreatePopupMenu(self):
        menu = wx.Menu()
        restore_item = menu.Append(wx.ID_ANY, _("Restore"))
        self.Bind(wx.EVT_MENU, self.OnRestore, restore_item)
        exit_item = menu.Append(wx.ID_EXIT, _("Exit"))
        self.Bind(wx.EVT_MENU, self.OnExit, exit_item)
        return menu

    def OnRestore(self, event):
        self._frame.Iconize(False)
        self._frame.Show()
        self._frame.Raise()
        self.RemoveIcon()
        del self._frame.taskbaricon

    def OnExit(self, event):
        wx.CallAfter(self._frame.Close)
        self.OnRestore(None)
