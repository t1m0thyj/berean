"""parent.py - parent frame class"""

import os

import wx
from wx import aui

import help
import html
import menu
import panes
import parallel
import toolbar
from info import *

_ = wx.GetTranslation

class MainFrame(wx.Frame):
    def __init__(self, app):
        super(MainFrame, self).__init__(None, -1, "Berean",
            app.settings["WindowPos"], app.settings["WindowSize"])
        self._app = app

        self.help = help.HelpSystem(self)
        self.printer = html.Printer(self)
        self.rect = wx.RectPS(app.settings["WindowPos"],
            app.settings["WindowSize"])
        self.reference = (app.settings["SelectedBook"],
            app.settings["SelectedChapter"], app.settings["ActiveVerse"])
        self.versions = app.settings["VersionList"]
        self.zoom_level = app.settings["ZoomLevel"]

        icons = wx.IconBundle()
        icons.AddIconFromFile(os.path.join(app.cwd, "images", "berean-16.png"),
            wx.BITMAP_TYPE_PNG)
        icons.AddIconFromFile(os.path.join(app.cwd, "images", "berean-32.png"),
            wx.BITMAP_TYPE_PNG)
        self.SetIcons(icons)
        versiondir = os.path.join(app.userdatadir, "versions")
        if not os.path.isdir(versiondir):
            os.mkdir(versiondir)

        self.aui = aui.AuiManager(self, aui.AUI_MGR_DEFAULT |
            aui.AUI_MGR_ALLOW_ACTIVE_PANE)

        self.menubar = menu.MenuBar(self)
        self.SetMenuBar(self.menubar)

        self.toolbar = toolbar.MainToolBar(self)
        self.aui.AddPane(self.toolbar,
            aui.AuiPaneInfo().Name("toolbar").Caption("Main Toolbar").ToolbarPane().Top())

        self.statusbar = self.CreateStatusBar(2)
        self.zoombar = wx.ToolBar(self.statusbar, -1, style=wx.TB_FLAT | wx.TB_NODIVIDER)
        self.zoombar.AddLabelTool(wx.ID_ZOOM_OUT, "", self.Bitmap("zoom-out"), shortHelp=_("Zoom Out (Ctrl+-)"))
        self.zoombar.EnableTool(wx.ID_ZOOM_OUT, self.zoom_level > 1)
        self.zoomctrl = wx.Slider(self.zoombar, -1, self.zoom_level, 1, 7, size=(100, -1))
        self.zoomctrl.Bind(wx.EVT_SCROLL_CHANGED, self.OnZoomCtrl)
        self.zoombar.AddControl(self.zoomctrl)
        self.zoombar.AddLabelTool(wx.ID_ZOOM_IN, "", self.Bitmap("zoom-in"), shortHelp=_("Zoom In (Ctrl++)"))
        self.zoombar.EnableTool(wx.ID_ZOOM_IN, self.zoom_level < 7)
        self.zoombar.Realize()
        self.zoombarwidth = (self.zoombar.GetToolSize()[0] + self.zoombar.GetToolSeparation()) * 2 + self.zoomctrl.GetSize()[0]
        if wx.VERSION_STRING >= "2.9.0.0":
            self.statusbar.SetStatusWidths([-1, self.zoombarwidth - 8])
        else:
            self.statusbar.SetStatusWidths([-1, self.zoombarwidth + 1])

        self.notebook = aui.AuiNotebook(self, -1,
            style=(aui.AUI_NB_DEFAULT_STYLE ^ aui.AUI_NB_TAB_MOVE ^
                aui.AUI_NB_CLOSE_ON_ACTIVE_TAB ^
                aui.AUI_NB_MIDDLE_CLICK_CLOSE) | wx.BORDER_NONE |
                aui.AUI_NB_WINDOWLIST_BUTTON)
        v = 0
        while v < len(self.versions):
            window = html.ChapterWindow(self.notebook, self.versions[v])
            if hasattr(window, "Bible"):
                self.notebook.AddPage(window, self.versions[v],
                    v == app.settings["ActiveTab"])
                self.notebook.SetPageBitmap(v,
                    self.Bitmap(os.path.join("flags", window.flag)))
                if wx.VERSION_STRING >= "2.9.4.0":
                    self.notebook.SetPageToolTip(v, window.description)
                v += 1
            else:
                self.versions.pop(v)
                if 0 < app.settings["ActiveTab"] <= v:
                    app.settings["ActiveTab"] -= 1
        if len(self.versions) > 1:
            self.notebook.AddPage(parallel.ParallelPanel(self.notebook),
                _("Parallel"),
                app.settings["ActiveTab"] == len(self.versions))
            if wx.VERSION_STRING >= "2.9.4.0":
                self.notebook.SetPageToolTip(len(self.versions),
                    self.parallel.description)
        else:
            self.notebook.SetTabCtrlHeight(0)
        self.aui.AddPane(self.notebook,
            aui.AuiPaneInfo().Name("notebook").CenterPane().PaneBorder(False))

        self.tree = panes.TreePane(self)
        self.aui.AddPane(self.tree, aui.AuiPaneInfo().Name("tree_pane").Caption(_("Tree")).Left().Layer(1).BestSize((150, -1)))

        self.search = panes.SearchPane(self)
        self.aui.AddPane(self.search, aui.AuiPaneInfo().Name("search_pane").Caption(_("Search")).MaximizeButton(True).Right().Layer(1).BestSize((300, -1)))

        self.notes = panes.NotesPane(self)
        self.aui.AddPane(self.notes, aui.AuiPaneInfo().Name("notes_pane").Caption(_("Notes")).MaximizeButton(True).Bottom().Layer(0).BestSize((-1, 220)))

        filename = os.path.join(app.userdatadir, "layout.dat")
        if os.path.isfile(filename):
            layout = open(filename, 'r')
            self.aui.LoadPerspective(layout.read())
            layout.close()

        self.LoadChapter(self.reference[0], self.reference[1], self.reference[2], True)

        self.menubar.Check(self.menubar.toolbar_item.GetId(),
            self.aui.GetPane("toolbar").IsShown())
        for pane in ("tree_pane", "search_pane", "notes_pane"):
            self.menubar.Check(getattr(self.menubar, "%s_item" % pane).GetId(), self.aui.GetPane(pane).IsShown())
        self.aui.Update()
        if app.settings["MaximizeState"]:
            self.Maximize()
            self.Layout()

        self.notebook.Bind(aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.OnAuiNotebookPageChanged)
        self.Bind(aui.EVT_AUI_PANE_CLOSE, self.OnAuiPaneClose)
        self.Bind(wx.EVT_MOVE, self.OnMove)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_ICONIZE, self.OnIconize)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def Bitmap(self, name):
        return wx.Bitmap(os.path.join(self._app.cwd, "images", "%s.png" % name), wx.BITMAP_TYPE_PNG)

    def GetBrowser(self, tab=-1):
        if tab == -1:
            tab = self.notebook.GetSelection()
        if tab == len(self.versions) and len(self.versions) > 1:
            return self.parallel
        return self.notebook.GetPage(tab)

    def LoadChapter(self, book, chapter, verse=-1, history=False):
        browser = self.GetBrowser()
        browser.LoadChapter(book, chapter, verse)
        tab = self.notebook.GetSelection()
        version = self.notebook.GetPageText(tab)
        self.SetTitle("Berean - %s %d (%s)" % (BOOK_NAMES[book - 1], chapter, version))
        if verse == -1:
            reference = "%s %d" % (BOOK_NAMES[book - 1], chapter)
        else:
            reference = "%s %d:%d" % (BOOK_NAMES[book - 1], chapter, verse)
        if reference not in self.toolbar.verse_history:
            self.toolbar.verse_history = self.toolbar.verse_history[:self.toolbar.history_item + 1]
            self.toolbar.verse_history.append(reference)
            if len(self.toolbar.verse_history) > 16:  # Only 15 visible items, since current one is hidden
                self.toolbar.verse_history.pop(0)
            self.toolbar.set_history_item(-1)
        elif history:
            self.toolbar.set_history_item(self.toolbar.verse_history.index(reference))
        else:
            self.toolbar.verse_history.remove(reference)
            self.toolbar.verse_history.append(reference)
            self.toolbar.set_history_item(-1)
        self.skipevents = True
        if book != self.reference[0]:
            self.tree.ExpandItem(book)
        if CHAPTER_LENGTHS[book - 1] > 1:
            item = self.tree.root_nodes[book - 1]
            child, cookie = self.tree.GetFirstChild(item)
            i = 1
            while i < chapter:
                child, cookie = self.tree.GetNextChild(item, cookie)
                i += 1
            self.tree.SelectItem(child)
        else:
            self.tree.SelectItem(self.tree.root_nodes[book - 1])
        self.skipevents = False
        if self.search.rangechoice.GetSelection() == len(self.search.ranges):
            self.search.start.SetSelection(book - 1)
            self.search.stop.SetSelection(book - 1)
        for i in range(self.notes.GetPageCount()):
            page = self.notes.GetPage(i)
            page.SaveText()
            page.LoadText(book, chapter)
        self.statusbar.SetStatusText("%s %d (%s)" % (BOOK_NAMES[book - 1], chapter, browser.description), 0)
        self.reference = (book, chapter, verse)
        for i in range(self.notebook.GetPageCount()):
            if i != tab:
                self.GetBrowser(i).verse = verse
        wx.CallAfter(browser.SetFocus)

    def Copy(self):
        focus = self.FindFocus()
        if not hasattr(focus, "SelectionToText"):
            return
        data = wx.TextDataObject()
        data.SetText(focus.SelectionToText())
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(data)
            wx.TheClipboard.Flush()
            wx.TheClipboard.Close()

    def Zoom(self, zoom):
        if zoom != 0:
            self.zoom_level += zoom
        else:
            self.zoom_level = 0
        self.GetBrowser().LoadChapter(*self.reference)
        self.zoombar.EnableTool(wx.ID_ZOOM_OUT, self.zoom_level > 1)
        if self.zoomctrl.GetValue() != self.zoom_level:
            self.zoomctrl.SetValue(self.zoom_level)
        self.zoombar.EnableTool(wx.ID_ZOOM_IN, self.zoom_level < 7)
        self.menubar.Enable(wx.ID_ZOOM_IN, self.zoom_level < 7)
        self.menubar.Enable(wx.ID_ZOOM_OUT, self.zoom_level > 1)

    def OnZoomCtrl(self, event):
        self.Zoom(event.GetPosition() - self.zoom_level)

    def OnAuiNotebookPageChanged(self, event):
        new = event.GetSelection()
        browser = self.GetBrowser()
        browser.LoadChapter(*self.reference)
        version = self.notebook.GetPageText(new)
        self.SetTitle("Berean - %s %d (%s)" % (BOOK_NAMES[self.reference[0] - 1], self.reference[1], version))
        self.statusbar.SetStatusText("%s %d (%s)" % (BOOK_NAMES[self.reference[0] - 1], self.reference[1], browser.description), 0)
        if new < len(self.versions):
            self.search.version.SetSelection(new)

    def OnAuiPaneClose(self, event):
        self.menubar.Check(getattr(self.menubar, "%s_item" % event.GetPane().name).GetId(), False)

    def OnMove(self, event):
        if self.HasCapture():
            self.rect.SetPosition(self.GetPosition())
        event.Skip()

    def OnSize(self, event):
        x, y, width, height = self.statusbar.GetFieldRect(1)
        self.zoombar.SetRect(wx.Rect(x, (y + height - 19) / 2 - self.zoombar.GetToolSeparation(), self.zoombarwidth, -1))
        if self.HasCapture():
            self.rect = wx.RectPS(self.GetPosition(), self.GetSize())

    def OnIconize(self, event):
        if self._app.settings["MinimizeToTray"] and event.Iconized() and not hasattr(self, "taskbaricon"):
            self.taskbaricon = TaskBarIcon(self)
            self.Hide()
        event.Skip()

    def OnClose(self, event):
        for i in range(self.notes.GetPageCount()):
            self.notes.GetPage(i).SaveNotes()
        self._app.SaveSettings()
        layout = open(os.path.join(self._app.userdatadir, "layout.dat"), 'w')
        layout.write(self.aui.SavePerspective())
        layout.close()
        self.aui.UnInit()
        del self.help
        del self.printer
        self._app.Exit()


class TaskBarIcon(wx.TaskBarIcon):
    def __init__(self, frame):
        super(TaskBarIcon, self).__init__()
        self._frame = frame
        self.SetIcon(wx.Icon(os.path.join(frame._app.cwd, "images",
            "berean-16.png"), wx.BITMAP_TYPE_PNG), frame.GetTitle())
        self.Bind(wx.EVT_TASKBAR_LEFT_DOWN, self.OnRestore)

    def OnRestore(self, event):
        self._frame.Iconize(False)
        self._frame.Show()
        self._frame.Raise()
        self.RemoveIcon()
        wx.CallAfter(self._frame.GetBrowser().SetFocus)
        del self._frame.taskbaricon

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
