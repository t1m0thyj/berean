"""
parent.py - parent frame class for Berean
Copyright (C) 2013 Timothy Johnson <timothysw@objectmail.com>
"""

import os
import wx

import aui
import helper
import htmlwin
import menu
import panes
import parallel
import printing
import toolbar

_ = wx.GetTranslation
if wx.VERSION_STRING < "2.9.0.0":
	##from wx.aui import AuiDefaultToolBarArt
	##aui.auibar.MakeDisabledBitmap = AuiDefaultToolBarArt.MakeDisabledBitmap
	aui.framemanager.sc.SizedParent = aui.framemanager.sc.SizedPanel
aui.auibook.AuiTabCtrl.ShowTooltip = lambda self: None

class MainFrame(wx.Frame):
	def __init__(self, app):
		wx.Frame.__init__(self, None, -1, "Berean", app.settings["WindowPos"], app.settings["WindowSize"])
		self._app = app
		
		self.abbrevs = ("Gen", "Exo", "Lev", "Num", "Deu", "Jos", "Jdg", "Rut", "1Sa", "2Sa", "1Ki",
						"2Ki", "1Ch", "2Ch", "Ezr", "Neh", "Est", "Job", "Psa", "Pro", "Ecc", "Son",
						"Isa", "Jer", "Lam", "Eze", "Dan", "Hos", "Joe", "Amo", "Oba", "Jon", "Mic",
						"Nah", "Hab", "Zep", "Hag", "Zec", "Mal", "Mat", "Mar", "Luk", "Joh", "Act",
						"Rom", "1Co", "2Co", "Gal", "Eph", "Php", "Col", "1Th", "2Th", "1Ti", "2Ti",
						"Tit", "Phm", "Heb", "Jam", "1Pe", "2Pe", "1Jo", "2Jo", "3Jo", "Jde", "Rev")
		self.books = ("Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua",
					  "Judges", "Ruth", "1 Samuel", "2 Samuel", "1 Kings", "2 Kings",
					  "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah", "Esther", "Job",
					  "Psalms", "Proverbs", "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah",
					  "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel", "Amos",
					  "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah",
					  "Haggai", "Zechariah", "Malachi", "Matthew", "Mark", "Luke",
					  "John", "Acts", "Romans", "1 Corinthians", "2 Corinthians", "Galatians",
					  "Ephesians", "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians", "1 Timothy",
					  "2 Timothy", "Titus", "Philemon", "Hebrews", "James", "1 Peter",
					  "2 Peter", "1 John", "2 John", "3 John", "Jude", "Revelation")
		self.chapters = (50, 40, 27, 36, 34, 24, 21, 4, 31, 24, 22, 25, 29, 36, 10, 13, 10, 42, 150, 31, 12, 8,
						 66, 52, 5, 48, 12, 14, 3, 9, 1, 4, 7, 3, 3, 3, 2, 14, 4, 28, 16, 24, 21, 28,
						 16, 16, 13, 6, 6, 4, 4, 5, 3, 6, 4, 3, 1, 13, 5, 5, 3, 5, 1, 1, 1, 22)
		self.helper = helper.HelpSystem(self)
		self.printer = printing.Printer(self)
		self.rect = wx.RectPS(app.settings["WindowPos"], app.settings["WindowSize"])
		self.reference = (app.settings["SelectedBook"], app.settings["SelectedChapter"], app.settings["ActiveVerse"])
		self.skipevents = False
		self.tooltip = None
		self.versions = app.settings["VersionList"]
		self.zoom = app.settings["ZoomLevel"]
		
		icons = wx.IconBundle()
		icons.AddIconFromFile(os.path.join(app.cwd, "images", "berean-16.png"), wx.BITMAP_TYPE_PNG)
		icons.AddIconFromFile(os.path.join(app.cwd, "images", "berean-32.png"), wx.BITMAP_TYPE_PNG)
		self.SetIcons(icons)
		versiondir = os.path.join(app.userdatadir, "versions")
		if not os.path.isdir(versiondir):
			os.mkdir(versiondir)
		display = wx.GetDisplaySize()
		
		self.aui = aui.AuiManager(self, agwFlags=aui.AUI_MGR_DEFAULT | aui.AUI_MGR_ALLOW_ACTIVE_PANE | aui.AUI_MGR_USE_NATIVE_MINIFRAMES)
		self.aui.GetArtProvider().SetFont(aui.AUI_DOCKART_CAPTION_FONT, self.GetFont())
		
		self.menubar = menu.MenuBar(self)
		self.SetMenuBar(self.menubar)
		
		self.toolbar = toolbar.ToolBar(self)
		self.aui.AddPane(self.toolbar, aui.AuiPaneInfo().Name("toolbar").ToolbarPane().PaneBorder(False).Top())
		
		self.statusbar = self.CreateStatusBar(4)
		self.zoombar = wx.ToolBar(self.statusbar, -1, style=wx.TB_FLAT | wx.TB_NODIVIDER)
		self.zoombar.AddLabelTool(wx.ID_ZOOM_OUT, "", self.Bitmap("zoom-out"), shortHelp=_("Zoom Out (Ctrl+-)"))
		self.zoombar.EnableTool(wx.ID_ZOOM_OUT, self.zoom > 1)
		self.zoomctrl = wx.Slider(self.zoombar, -1, self.zoom, 1, 7, size=(100, -1), style=wx.SL_AUTOTICKS)
		self.zoomctrl.Bind(wx.EVT_SCROLL_CHANGED, self.OnZoomCtrl)
		self.zoombar.AddControl(self.zoomctrl)
		self.zoombar.AddLabelTool(wx.ID_ZOOM_IN, "", self.Bitmap("zoom-in"), shortHelp=_("Zoom In (Ctrl++)"))
		self.zoombar.EnableTool(wx.ID_ZOOM_IN, self.zoom < 7)
		self.zoombar.Realize()
		self.zoombarwidth = (self.zoombar.GetToolSize()[0] + self.zoombar.GetToolSeparation()) * 2 + self.zoomctrl.GetSize()[0]
		self.statusbar.SetStatusWidths([-2, -1, -1, self.zoombarwidth - 7])
		
		self.notebook = aui.AuiNotebook(self, -1, agwStyle=(aui.AUI_NB_DEFAULT_STYLE ^ aui.AUI_NB_TAB_MOVE ^ aui.AUI_NB_CLOSE_ON_ACTIVE_TAB ^ aui.AUI_NB_MIDDLE_CLICK_CLOSE) | aui.AUI_NB_HIDE_ON_SINGLE_TAB)
		self.notebook.SetSashDClickUnsplit(True)
		v = 0
		while v < len(self.versions):
			window = htmlwin.ChapterWindow(self.notebook, self.versions[v])
			if hasattr(window, "Bible"):
				self.notebook.AddPage(window, self.versions[v], v == app.settings["ActiveTab"], self.Bitmap(os.path.join("flags", window.flag)))
				v += 1
			else:
				self.versions.pop(v)
				if 0 < app.settings["ActiveTab"] <= v:
					app.settings["ActiveTab"] -= 1
		if len(self.versions) > 1:
			self.notebook.AddPage(parallel.ParallelPanel(self.notebook), _("Parallel"), app.settings["ActiveTab"] == len(self.versions))
		self.aui.AddPane(self.notebook, aui.AuiPaneInfo().Name("notebook").CenterPane().PaneBorder(False))
		
		self.tree = panes.TreePane(self)
		self.aui.AddPane(self.tree, aui.AuiPaneInfo().Name("treepane").Caption(_("Bible")).Left().Layer(1).BestSize((150, -1)))
		
		self.search = panes.SearchPane(self)
		self.aui.AddPane(self.search, aui.AuiPaneInfo().Name("searchpane").Caption(_("Search")).Right().Layer(1).BestSize((display[0] / 4, -1)))
		panes.search.books = [book.replace(" ", "").lower() for book in self.books]
		
		self.notes = panes.NotesPane(self)
		self.aui.AddPane(self.notes, aui.AuiPaneInfo().Name("notespane").Caption(_("Notes")).Bottom().Layer(0).BestSize((-1, display[1] / 4)))
		
		filename = os.path.join(app.userdatadir, "berean.aui")
		if os.path.isfile(filename):
			perspective = open(filename, 'r')
			self.aui.LoadPerspective(perspective.read())
			perspective.close()
		
		self.LoadChapter(self.reference[0], self.reference[1], self.reference[2], True)
		browser = self.GetBrowser()
		if app.settings["ActiveTab"] != len(self.versions):
			self.statusbar.SetStatusText(browser.description, 1)
		browser.SetFocus()
		
		self.menubar.View.Check(self.menubar.ID_TOOLBAR, self.aui.GetPane("toolbar").IsShown())
		for pane in ("treepane", "searchpane", "notespane"):
			self.menubar.View.Check(getattr(self.menubar, "ID_%s" % pane.upper()), self.aui.GetPane(pane).IsShown())
		self.aui.Update()
		if app.settings["MaximizeState"]:
			self.Maximize()
			self.Layout()
		
		tabctrl = self.notebook.GetActiveTabCtrl()
		tabctrl.Bind(wx.EVT_MOTION, self.OnTabCtrlMotion)
		self.notebook.Bind(aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.OnAuiNotebookPageChanged)
		self.notebook.Bind(aui.EVT_AUINOTEBOOK_DRAG_DONE, self.OnAuiNotebookDragDone)
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
		self.SetTitle("Berean - %s %d (%s)" % (self.books[book - 1], chapter, version))
		if verse == -1:
			reference = "%s %d" % (self.books[book - 1], chapter)
		else:
			reference = "%s %d:%d" % (self.books[book - 1], chapter, verse)
		if reference not in self.toolbar.history:
			self.toolbar.history = self.toolbar.history[:self.toolbar.current + 1]
			self.toolbar.history.append(reference)
			if len(self.toolbar.history) > 16:	# Only 15 visible items, since current one is hidden
				self.toolbar.history.pop(0)
			self.toolbar.SetCurrent(-1)
		elif history:
			self.toolbar.SetCurrent(self.toolbar.history.index(reference))
		else:
			self.toolbar.history.remove(reference)
			self.toolbar.history.append(reference)
			self.toolbar.SetCurrent(-1)
		self.skipevents = True
		if book != self.reference[0]:
			self.toolbar.books.SetSelection(book - 1)
			self.toolbar.chapter.SetRange(1, self.chapters[book - 1])
			self.tree.ShowChapters(book)
		if chapter != self.reference[1]:
			self.toolbar.chapter.SetValue(chapter)
		self.tree.SelectItem(self.tree.items[book][chapter])
		self.skipevents = False
		if self.search.rangechoice.GetSelection() == len(self.search.ranges):
			self.search.start.SetSelection(book - 1)
			self.search.stop.SetSelection(book - 1)
		for i in range(self.notes.GetPageCount()):
			page = self.notes.GetPage(i)
			page.SaveText()
			page.LoadText(book, chapter)
		self.statusbar.SetStatusText("%s %d (%s)" % (self.books[book - 1], chapter, version), 0)
		if tab < len(self.versions):
			self.statusbar.SetStatusText(_("%d verses") % (len(browser.Bible[book][chapter]) - 1), 2)
		else:
			self.statusbar.SetStatusText(_("%d verses") % browser.verses, 2)
		self.reference = (book, chapter, verse)
		for i in range(self.notebook.GetPageCount()):
			if i != tab:
				self.GetBrowser(i).verse = verse
	
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
			self.zoom += zoom
		else:
			self.zoom = 0
		self.zoombar.EnableTool(wx.ID_ZOOM_OUT, self.zoom > 1)
		if self.zoomctrl.GetValue() != self.zoom:
			self.zoomctrl.SetValue(self.zoom)
		self.zoombar.EnableTool(wx.ID_ZOOM_IN, self.zoom < 7)
		self.GetBrowser().LoadChapter(*self.reference)
		self.menubar.Enable(wx.ID_ZOOM_IN, self.zoom < 7)
		self.menubar.Enable(wx.ID_ZOOM_OUT, self.zoom > 1)
	
	def ShowToolbar(self, show=True):
		self.aui.GetPane("toolbar").Show(show)
		self.aui.Update()
	
	def ShowTreePane(self, show=True):
		self.aui.GetPane("treepane").Show(show)
		self.aui.Update()
	
	def ShowSearchPane(self, show=True):
		self.aui.GetPane("searchpane").Show(show)
		self.aui.Update()
		if show:
			wx.CallAfter(self.search.results.SetFocus)
	
	def ShowNotesPane(self, show=True):
		self.aui.GetPane("notespane").Show(show)
		self.aui.Update()
		if show:
			wx.CallAfter(self.notes.editor.SetFocus)
	
	def MultiverseSearch(self, references=None):
		from dialogs import multiverse
		dialog = multiverse.MultiverseDialog(self, references)
		dialog.Show()
	
	def Preferences(self):
		from dialogs import preferences
		dialog = preferences.PreferenceDialog(self)
		dialog.Show()
	
	def OnZoomCtrl(self, event):
		self.Zoom(event.GetPosition() - self.zoom)
	
	def OnTabCtrlMotion(self, event):
		tabctrl = event.GetEventObject()
		tabctrl.OnMotion(event)
		x, y = event.GetX(), event.GetY()
		page = tabctrl.TabHitTest(x, y)
		hide = False
		if not event.LeftDown():
			if page:
				browser = self.GetBrowser(self.notebook.GetPageIndex(page))
				if self.tooltip != browser.description:
					self.tooltip = browser.description
					tabctrl.SetToolTipString(self.tooltip)
			else:
				hide = True
		elif self.tooltip:
			hide = True
		if hide:
			self.tooltip = None
			tabctrl.SetToolTipString("")
		event.Skip()
	
	def OnAuiNotebookPageChanged(self, event):
		new = event.GetSelection()
		browser = self.GetBrowser()
		browser.LoadChapter(*self.reference)
		version = self.notebook.GetPageText(new)
		self.SetTitle("Berean - %s %d (%s)" % (self.books[self.reference[0] - 1], self.reference[1], version))
		self.statusbar.SetStatusText("%s %d (%s)" % (self.books[self.reference[0] - 1], self.reference[1], version), 0)
		if new < len(self.versions):
			self.search.version.SetSelection(new)
		if new != len(self.versions):
			self.statusbar.SetStatusText(browser.description, 1)
		wx.CallAfter(browser.SetFocus)
	
	def OnAuiNotebookDragDone(self, event):
		self.notebook.GetActiveTabCtrl().Bind(wx.EVT_MOTION, self.OnTabCtrlMotion)
	
	def OnAuiPaneClose(self, event):
		name = event.GetPane().name
		if name.endswith("pane"):
			self.menubar.View.Check(getattr(self.menubar, "ID_%s" % name.upper()), False)
	
	def OnMove(self, event):
		if self.HasCapture():
			self.rect.SetPosition(self.GetPosition())
		event.Skip()
	
	def OnSize(self, event):
		x, y, width, height = self.statusbar.GetFieldRect(3)
		self.zoombar.SetRect(wx.Rect(x, (y + height - 19) / 2 - self.zoombar.GetToolSeparation(), self.zoombarwidth, -1))
		if self.aui.GetPane("notespane").IsShown():	# Adjust overflow state of notes pane toolbar if visible
			wx.CallAfter(self.notes.GetSizer().Layout)
		if self.HasCapture():
			self.rect = wx.RectPS(self.GetPosition(), self.GetSize())
	
	def OnIconize(self, event):
		if self._app.settings["MinimizeToTray"] and event.Iconized() and not hasattr(self, "trayicon"):
			self.trayicon = menu.TaskBarIcon(self)
			self.Hide()
		event.Skip()
	
	def OnClose(self, event):
		for i in range(self.notes.GetPageCount()):
			self.notes.GetPage(i).SaveNotes()
		self._app.UnInit()
		perspective = open(os.path.join(self._app.userdatadir, "berean.aui"), 'w')
		perspective.write(self.aui.SavePerspective())
		perspective.close()
		self.aui.UnInit()
		del self.helper
		del self.printer
		self._app.CloseFrame()