"""
htmlwin.py - HTML window classes for Berean
Copyright (C) 2013 Timothy Johnson <timothysw@objectmail.com>
"""

import cPickle
import os.path
import urllib
import wx
import wx.lib.dragscroller
from wx import html

_ = wx.GetTranslation

class BaseHtmlWindow(html.HtmlWindow):
	def __init__(self, parent):
		html.HtmlWindow.__init__(self, parent)
		
		self.dragscroller = wx.lib.dragscroller.DragScroller(self)
		
		self.SetAcceleratorTable(wx.AcceleratorTable([(wx.ACCEL_CTRL, ord("A"), wx.ID_SELECTALL)]))
		
		self.Bind(wx.EVT_MENU, self.OnSelectAll, id=wx.ID_SELECTALL)
		self.Bind(wx.EVT_MIDDLE_DOWN, self.OnMiddleDown)
		self.Bind(wx.EVT_MIDDLE_UP, self.OnMiddleUp)
	
	def OnSelectAll(self, event):
		self.SelectAll()
	
	def OnMiddleDown(self, event):
		self.dragscroller.Start(event.GetPosition())
	
	def OnMiddleUp(self, event):
		self.dragscroller.Stop()

class HtmlWindow(BaseHtmlWindow):
	def __init__(self, parent, frame):
		BaseHtmlWindow.__init__(self, parent)
		self._frame = frame
		
		self.verse = -1
		
		self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
	
	def LoadChapter(self, book, chapter, verse=-1):
		self.SetPage(self.GetPage(book, chapter, verse))
		if verse > 1 and self.HasAnchor(str(verse)):
			wx.CallAfter(self.ScrollToAnchor, str(verse))
			self.verse = -1
	
	def OnContextMenu(self, event):
		menu = wx.Menu()
		selection = self.SelectionToText()
		if len(selection):
			menu.Append(wx.ID_COPY, _("&Copy\tCtrl+C"))
		menu.Append(wx.ID_SELECTALL, _("Select &All\tCtrl+A"))
		menu.AppendSeparator()
		if len(selection):
			ID_FIND_TEXT = wx.NewId()
			menu.Append(ID_FIND_TEXT, _("&Search for Selected Text"))
			self.Bind(wx.EVT_MENU, self.OnFindText, id=ID_FIND_TEXT)
			menu.AppendSeparator()
		menu.Append(wx.ID_PRINT, _("&Print...\tCtrl+P"))
		menu.Append(wx.ID_PREVIEW, _("P&rint Preview...\tCtrl+Alt+P"))
		self.PopupMenu(menu)
	
	def OnFindText(self, event):
		if not self._frame.aui.GetPane("searchpane").IsShown():
			self._frame.ShowSearchPane()
		self._frame.search.text.SetValue(self.SelectionToText().strip().lstrip("1234567890 "))
		self._frame.search.OnSearch(None)

class ChapterWindow(HtmlWindow):
	def __init__(self, parent, version):
		super(ChapterWindow, self).__init__(parent, parent.GetParent())
		
		self.version = version
		
		filename = os.path.join(self._frame._app.cwd, "versions", "%s.bbl" % version)
		if not os.path.isfile(filename):
			filename = os.path.join(self._frame._app.userdatadir, "versions", "%s.bbl" % version)
		try:
			self.LoadBible(filename)
		except:
			button = wx.MessageBox(_("The %s could not be found. Do you want to download it now?") % version, "Berean", wx.ICON_QUESTION | wx.YES_NO)
			if button == wx.YES:
				downloaded = download(version, os.path.join(self._frame._app.userdatadir, "versions"))
				if downloaded:
					self.LoadBible(filename)
	
	def LoadBible(self, filename):
		Bible = open(filename, 'rb')
		try:
			self.Bible = cPickle.load(Bible)
		finally:
			Bible.close()
		self.description, self.flag = self.Bible[0]
	
	def GetPage(self, book, chapter, verse=-1):
		if self.Bible[book][chapter] != (None,):
			items = ["<div align=center><font size=+1><b>%s %d</b></font></div>" % (self.Bible[book][0], chapter)]
			if self.Bible[book][chapter][0]:
				items[0] = "%s<br>%s</div>" % (items[0][:-6], self.Bible[book][chapter][0].replace("[", "<i>").replace("]", "</i>"))
			for i in range(1, len(self.Bible[book][chapter])):
				items.append("<font size=-1>%d&nbsp;</font>%s<a name=\"%d\"></a>" % (i, self.Bible[book][chapter][i].replace("[", "<i>").replace("]", "</i>"), i + 1))
				if i == verse:
					items[-1] = "<b>%s</b>" % items[-1]
		else:
			items = [_("<font color=gray>%s %s is not in the %s.</font>") % (self._frame.books[book - 1], chapter, self.version)]
		return body % (self._frame.zoom, "<br>\n\t\t".join(items))

def download(version, versiondir):
	def reporthook(blocks, size, total):
		dialog.Update(float(blocks * size) / total * 100)
	
	dialog = wx.ProgressDialog(_("Downloading"), _("Please wait, downloading the %s...") % version, style=wx.PD_AUTO_HIDE | wx.PD_ELAPSED_TIME | wx.PD_REMAINING_TIME)
	try:
		urllib.urlretrieve("http://berean.sf.net/files/versions/%s.bbl" % version, os.path.join(versiondir, "%s.bbl" % version), reporthook)
	except:
		dialog.Destroy()
		wx.MessageBox(_("Downloading the %s failed.\nMake sure you are connected to the Internet.") % version, "Berean", wx.ICON_EXCLAMATION | wx.OK)
	else:
		dialog.Destroy()
		return True
	return False

body = """<html>
<body>
	<font size=%d>
		%s
	</font>
</body>
</html>"""