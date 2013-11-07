"""
preferences.py - preference dialog class for Berean
Copyright (C) 2013 Timothy Johnson <timothysw@objectmail.com>
"""

import os
import wx

_ = wx.GetTranslation

class PreferenceDialog(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, title=_("Preferences"), size=(600, 440))
		self._parent = parent
		
		self.abbrevs = ("ASV", "KJV", "WBS", "WEB", "WNT", "YLT", "DSV", "LSG", "RVA")
		self.titles = ("American Standard Version", "King James Version",
					   "Webster's Bible", "World English Bible",
					   "Wycliffe New Testament", "Young's Literal Translation",
					   "Dutch Statenvertaling [Dutch]", "Louis Segond [French]",
					   "Reina-Valera Antigua [Spanish]")
		
		self.listbook = wx.Listbook(self, -1)
		images = wx.ImageList(24, 24)
		for name in ("general", "versions"):
			images.Add(parent.Bitmap(name))
		self.listbook.AssignImageList(images)
		
		self.general = wx.Panel(self.listbook, -1)
		self.MinimizeToTray = wx.CheckBox(self.general, -1, _("Minimize to system tray"))
		self.MinimizeToTray.SetValue(parent._app.settings["MinimizeToTray"])
		self.HebrewBookOrder = wx.CheckBox(self.general, -1, _("Use Hebrew Old Testament book order in tree pane*"))
		self.HebrewBookOrder.SetValue(parent._app.settings["HebrewBookOrder"])
		self.AbbrevSearchResults = wx.CheckBox(self.general, -1, _("Abbreviate book names in search results"))
		self.AbbrevSearchResults.SetValue(parent._app.settings["AbbrevSearchResults"])
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.MinimizeToTray, 0, wx.ALL, 2)
		sizer.Add(self.HebrewBookOrder, 0, wx.ALL, 2)
		sizer.Add(self.AbbrevSearchResults, 0, wx.ALL, 2)
		self.general.SetSizer(sizer)
		self.listbook.AddPage(self.general, _("General"), imageId=0)
		
		self.versions = wx.Panel(self.listbook, -1)
		self.VersionList = wx.CheckListBox(self.versions, -1)
		for i in range(len(self.abbrevs)):
			self.VersionList.Append("%s (%s)" % (self.titles[i], self.abbrevs[i]))
			if self.abbrevs[i] in parent.versions:
				self.VersionList.Check(i)
		self.VersionList.Bind(wx.EVT_CHECKLISTBOX, self.OnVersionList)
		sizer = wx.BoxSizer()
		sizer.Add(self.VersionList, 1, wx.EXPAND)
		self.versions.SetSizer(sizer)
		self.listbook.AddPage(self.versions, _("Versions*"), imageId=1)
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.listbook, 1, wx.ALL | wx.EXPAND, 2)
		statictext = wx.StaticText(self, -1, _("*Takes effect after you restart Berean"))
		statictext.SetForegroundColour("#808080")
		sizer.Add(statictext, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
		sizer2 = wx.StdDialogButtonSizer()
		sizer2.AddButton(wx.Button(self, wx.ID_OK))
		sizer2.AddButton(wx.Button(self, wx.ID_CANCEL))
		sizer2.AddButton(wx.Button(self, wx.ID_APPLY))
		sizer2.Realize()
		sizer.Add(sizer2, 0, wx.ALL | wx.EXPAND, 5)
		self.SetSizer(sizer)
		
		self.Bind(wx.EVT_BUTTON, self.OnOk, id=wx.ID_OK)
		self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)
		self.Bind(wx.EVT_BUTTON, self.OnApply, id=wx.ID_APPLY)
	
	def OnVersionList(self, event):
		item = event.GetInt()
		if not self.VersionList.IsChecked(item):
			selections = False
			for i in range(self.VersionList.GetCount()):
				if self.VersionList.IsChecked(i):
					selections = True
					break
			if not selections:
				self.VersionList.Check(item)
				wx.MessageBox(_("You must have at least one version selected."), _("Berean"), wx.ICON_EXCLAMATION | wx.OK)
	
	def OnOk(self, event):
		self.OnApply(None)
		self.Destroy()
	
	def OnCancel(self, event):
		self.Destroy()
	
	def OnApply(self, event):
		self._parent._app.settings["MinimizeToTray"] = self.MinimizeToTray.GetValue()
		self._parent._app.settings["HebrewBookOrder"] = self.HebrewBookOrder.GetValue()
		self._parent._app.settings["AbbrevSearchResults"] = self.AbbrevSearchResults.GetValue()
		versions = []
		for i in range(len(self.abbrevs)):
			if self.VersionList.IsChecked(i):
				versions.append(self.abbrevs[i])
		if versions != self._parent.versions:
			for version in self._parent.versions:	# Delete old indexes
				if version not in versions:
					wx.CallAfter(os.remove, os.path.join(self._parent._app.userdatadir, "indexes", "%s.idx" % version))
			self._parent.versions = versions