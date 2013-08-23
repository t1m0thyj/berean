"""
__init__.py - add-on management classes for Berean
Copyright (C) 2013 Timothy Johnson <timothysw@objectmail.com>
"""

import os
import shutil
import sys
import wx
import zipfile
from wx.html import EVT_HTML_LINK_CLICKED
from xml.etree import ElementTree

_ = wx.GetTranslation

class AddonManager:
	def __init__(self, frame):
		self._frame = frame
		
		self.enabled = frame._app.settings["AddonsEnabled"]
		self.events = {}
		self.names = frame._app.settings["AddonList"]
		self.states = [0 for i in range(len(self.names))]
		self.tempdirs = {}
		
		if len(self.names) > 1:
			info = zip(self.names, self.enabled)
			info.sort(key=lambda item: (not item[1], item[0]))	# Sort add-ons by enabled state, then by name
			self.names, self.enabled = map(list, zip(*info))
		
		addondir = os.path.join(frame._app.userdatadir, "addons")
		if not os.path.isdir(addondir):
			os.mkdir(addondir)
		sys.path.insert(0, addondir)
		
		self.addons = []
		failed = []
		for i in range(len(self.names)):
			if not self.LoadAddon(self.names[i], self.enabled[i]):
				failed.append(self.names[i])
		if len(failed):
			failed = "\n".join([" " * 4 + name.replace("_", " ") for name in failed])
			wx.MessageBox(_("The following add-ons failed to start and have been disabled:\n\n%s") % failed, "Berean", wx.ICON_WARNING | wx.OK)
	
	def LoadAddon(self, name, enabled, index=-1):
		module = getattr(__import__("%s.__init__" % name), "__init__")
		try:
			if index == -1:
				self.addons.append(module.Addon_(self, name, enabled))
			else:
				self.addons.insert(index, module.Addon_(self, name, enabled))
		except:
			self.enabled[self.names.index(name)] = False
			self.LoadAddon(name, False, index)
		else:
			return True
		return False
	
	def GetBitmap(self, addon, name="icon"):
		return wx.Bitmap(os.path.join(self._frame._app.userdatadir, "addons", addon, "%s.png" % name), wx.BITMAP_TYPE_PNG)
	
	def RegisterEvent(self, event, func1, func2, window):
		key = (window, event._getEvtType())
		if key not in self.events:
			self.events[key] = []
			if func1:
				self.events[key].append(func1)
			window.Bind(event, self.OnRegisteredEvent)
		self.events[key].append(func2)
	
	def OnRegisteredEvent(self, event):
		window = event.GetEventObject()
		while window:
			key = (window, event.GetEventType())
			if key in self.events:
				for func in self.events[key]:
					func(event)
			window = window.GetParent()
		event.Skip()
	
	def UnregisterEvent(self, func):
		for event in self.events:
			if func in self.events[event]:
				self.events[event].remove(func)
				if not len(self.events[event]):
					wx.CallAfter(self.events.pop, event)
	
	def PostInit(self):
		for addon in self.addons:
			if hasattr(addon, "OnInit"):
				addon.OnInit()
	
	def RemoveAddon(self, name):
		item = self.names.index(name)
		if self.states[item] == 3 and self.enabled[item] and hasattr(self.addons[item], "OnDisable"):
			self.addons[item].OnDisable()
		if hasattr(self.addons[item], "OnRemove"):
			self.addons[item].OnRemove()
		self.addons.pop(item)
		self.enabled.pop(item)
		self.names.pop(item)
		self.states.pop(item)
	
	def UnInit(self):
		i = 0
		while i < len(self.states):
			if 3 <= self.states[i] <= 5:
				self.RemoveAddon(self.names[i])
			else:
				i += 1
		tempdir = wx.StandardPaths.Get().GetTempDir()
		for name in self.tempdirs:
			shutil.rmtree(os.path.join(tempdir, self.tempdirs[name]), True)
		for addon in self.addons:
			addon.OnExit()

class AddonDialog(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, -1, _("Add-on Manager"), size=(600, 440))
		self._parent = parent
		
		self.olditems = {}
		self.restart = []
		self.tempdir = wx.StandardPaths.Get().GetTempDir()
		
		self.listbox = HtmlListBox(self)
		self.listbox.SetDropTarget(AddonDropTarget(self))
		for i in range(len(parent.addons.names)):
			if parent.addons.states[i] < 3 or parent.addons.states[i] == 6:
				root = ElementTree.parse(os.path.join(parent._app.userdatadir, "addons", parent.addons.names[i], "addon.xml")).getroot()
			else:
				root = ElementTree.parse(os.path.join(self.tempdir, parent.addons.tempdirs[parent.addons.names[i]], "addon.xml")).getroot()
			text = "<font><b>%s</b> %s<br>%s</font><div align=right>" % (root[0].text, root[1].text, root[2].text)
			if parent.addons.states[i] < 6:
				if parent.addons.enabled[i]:
					if hasattr(parent.addons.addons[i], "OnOptions"):
						text += _("<a href='%s;0'>Options</a> ") % parent.addons.names[i]
					text += _("<a href='%s;1'>Disable</a> ") % parent.addons.names[i]
				else:
					text = text.replace("<font>", "<font color=gray>").replace("<br>", _(" (disabled)<br>"))
					text += _("<a href='%s;2'>Enable</a> ") % parent.addons.names[i]
				text += _("<a href='%s;3'>Remove</a>") % parent.addons.names[i] + " </div>"
			if 1 <= parent.addons.states[i] <= 5:
				self.olditems[parent.addons.names[i]] = text
				if parent.addons.states[i] == 1:
					text2 = _("<font color=gray>This add-on will be disabled when you restart Berean. <a href=';4'>Restart&nbsp;Now</a> <a href='%s;5'>Undo</a></font><br>") % parent.addons.names[i]
					text = text2 + text[:text.index("<div align=right>")]
				elif parent.addons.states[i] == 2:
					text2 = _("<font color=green>This add-on will be enabled when you restart Berean. <a href=';4'>Restart&nbsp;Now</a> <a href='%s;5'>Undo</a></font><br>") % parent.addons.names[i]
					text = text2 + text[:text.index("<div align=right>")]
				elif parent.addons.states[i] == 3:
					text = _("<font color=gray><b>%s</b> has been removed. <a href=';4'>Restart&nbsp;Now</a> <a href='%s;5'>Undo</a></font>") % (root[0].text, parent.addons.names[i])
				else:
					text = _("<font color=gray><b>%s</b> has been removed. <a href='%s;5'>Undo</a></font>") % (root[0].text, parent.addons.names[i])
			elif parent.addons.states[i] == 6:
				text2 = _("<font color=green>This add-on will be installed when you restart Berean. <a href=';4'>Restart&nbsp;Now</a> <a href='%s;5'>Undo</a></font><br>") % parent.addons.names[i]
				text = text2 + text[:text.index("<div align=right>")]
			self.listbox.items.append(text)
			self.restart.append(root[3].text.lower() == "yes")
		self.listbox.SetItemCount(len(self.listbox.items))
		self.install = wx.HyperlinkCtrl(self, -1, _("Install add-on from file..."), "", style=wx.HL_ALIGN_LEFT)
		self.close = wx.Button(self, wx.ID_CLOSE)
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.listbox, 1, wx.ALL | wx.EXPAND, 2)
		sizer2 = wx.BoxSizer(wx.HORIZONTAL)
		sizer2.Add(self.install, 1, wx.ALIGN_CENTER_VERTICAL)
		sizer2.Add(self.close, 0, wx.EXPAND)
		sizer.Add(sizer2, 0, wx.ALL | wx.EXPAND, 5)
		self.SetSizer(sizer)
		
		self.listbox.Bind(EVT_HTML_LINK_CLICKED, self.OnLinkClicked)
		self.install.Bind(wx.EVT_HYPERLINK, self.OnHyperlink)
		self.close.Bind(wx.EVT_BUTTON, self.OnClose)
		self.Bind(wx.EVT_CLOSE, self.OnClose)
	
	def OnLinkClicked(self, event):
		name, action = event.GetLinkInfo().GetHref().split(";")
		self.HandleLinkEvent(name, int(action))
	
	def HandleLinkEvent(self, name, action, update=True):
		if len(name):
			item = self._parent.addons.names.index(name)
		if action == 0:	# Options
			self._parent.addons.addons[item].OnOptions()
		elif action == 1:	# Disable
			self._parent.addons.enabled[item] = False
			self.olditems[name] = self.listbox.items[item]
			if self.restart[item]:
				text = _("<font color=gray>This add-on will be disabled when you restart Berean. <a href=';4'>Restart&nbsp;Now</a> <a href='%s;5'>Undo</a></font><br>") % name
				text2 = self.listbox.items[item]
				self.listbox.items[item] = text + text2[:text2.index("<div align=right>")]
				self._parent.addons.states[item] = 1	# 1 = will be disabled on restart
			else:
				if hasattr(self._parent.addons.addons[item], "OnDisable"):
					self._parent.addons.addons[item].OnDisable()
				self.listbox.items[item] = self.listbox.items[item].replace("<font>", "<font color=gray>", 1).replace("<br>", _(" (disabled)<br>"), 1)
				self.listbox.items[item] = self.listbox.items[item].replace("<div align=right>" + _("<a href='%s;0'>Options</a> ") % name, "<div align=right>")
				self.listbox.items[item] = self.listbox.items[item].replace(_("<a href='%s;1'>Disable</a> ") % name, _("<a href='%s;2'>Enable</a> ") % name)
		elif action == 2:	# Enable
			self._parent.addons.enabled[item] = True
			self.olditems[name] = self.listbox.items[item]
			if self.restart[item]:
				text = _("<font color=green>This add-on will be enabled when you restart Berean. <a href=';4'>Restart&nbsp;Now</a> <a href='%s;5'>Undo</a></font><br>") % name
				text2 = self.listbox.items[item]
				self.listbox.items[item] = text + text2[:text2.index("<div align=right>")]
				self._parent.addons.states[item] = 2	# 2 = will be enabled on restart
			else:
				self._parent.addons.addons[item].__init__(self._parent.addons, name, True)
				if hasattr(self._parent.addons.addons[item], "OnEnable"):
					self._parent.addons.addons[item].OnEnable()
				self.listbox.items[item] = self.listbox.items[item].replace("<font color=gray>", "<font>", 1).replace(_(" (disabled)<br>"), "<br>", 1)
				if hasattr(self._parent.addons.addons[item], "OnOptions"):
					self.listbox.items[item] = self.listbox.items[item].replace("<div align=right>", "<div align=right>" + _("<a href='%s;0'>Options</a> ") % name)
				self.listbox.items[item] = self.listbox.items[item].replace(_("<a href='%s;2'>Enable</a> ") % name, _("<a href='%s;1'>Disable</a> ") % name)
		elif action == 3:	# Remove
			addondir = os.path.join(self._parent._app.userdatadir, "addons")
			self._parent.addons.tempdirs[name] = "berean-%s" % name
			os.rename(os.path.join(addondir, name), os.path.join(addondir, self._parent.addons.tempdirs[name]))
			shutil.move(os.path.join(addondir, self._parent.addons.tempdirs[name]), self.tempdir)
			self.olditems[name] = self.listbox.items[item]
			if self.restart[item]:
				text = _("<font color=gray><b>%s</b> has been removed. <a href=';4'>Restart&nbsp;Now</a> <a href='%s;5'>Undo</a></font>") % (name.replace("_", " "), name)
				self._parent.addons.states[item] = 3	# 3 = will be disabled and removed on restart
			else:	# Add-ons are never completely removed until program shutdown
				if self._parent.addons.enabled[item]:
					if hasattr(self._parent.addons.addons[item], "OnDisable"):
						self._parent.addons.addons[item].OnDisable()
					self._parent.addons.states[item] = 4	# 4 = was enabled, will be removed
				else:
					self._parent.addons.states[item] = 5	# 5 = was disabled, will be removed
				text = _("<font color=gray><b>%s</b> has been removed. <a href='%s;5'>Undo</a></font>") % (name.replace("_", " "), name)
			self.listbox.items[item] = text
		elif action == 4:	# Restart Now
			self._parent._app.Restart()
		elif action == 5:	# Undo
			if self._parent.addons.states[item] < 6:
				if 3 <= self._parent.addons.states[item] <= 5:
					addondir = os.path.join(self._parent._app.userdatadir, "addons")
					shutil.move(os.path.join(self.tempdir, self._parent.addons.tempdirs[name]), addondir)
					os.rename(os.path.join(addondir, self._parent.addons.tempdirs[name]), os.path.join(addondir, name))
					self._parent.addons.tempdirs.pop(name)
				if self._parent.addons.states[item] == 4:
					self._parent.addons.addons[item].__init__(self._parent.addons, name, True)
					if hasattr(self._parent.addons.addons[item], "OnEnable"):
						self._parent.addons.addons[item].OnEnable()
				self.listbox.items[item] = self.olditems.pop(name)
				self._parent.addons.states[item] = 0
			else:
				shutil.rmtree(os.path.join(self._parent._app.userdatadir, "addons", name))
				self._parent.addons.RemoveAddon(name)
				self.restart.pop(item)
				self.listbox.items.pop(item)
		if action != 0 and action != 4 and update:	# not Options or Restart Now
			self.listbox.SetItemCount(len(self.listbox.items))
			self.listbox.Refresh()
			self.listbox.Update()
	
	def InstallAddonFromFile(self, filenames):
		info = []
		try:
			installed = []
			for filename in filenames:
				bzip = zipfile.ZipFile(filename, 'r')
				xml = bzip.open("%saddon.xml" % bzip.namelist()[0], 'r')
				root = ElementTree.fromstring(xml.read())
				xml.close()
				name = root[0].text.replace(" ", "_")
				if name in self._parent.addons.names:
					item = self._parent.addons.names.index(name)
					if self._parent.addons.states[item] < 3 or self._parent.addons.states[item] == 6:
						root2 = ElementTree.parse(os.path.join(self._parent._app.userdatadir, "addons", name, "addon.xml")).getroot()
					else:
						root2 = ElementTree.parse(os.path.join(wx.StandardPaths.Get().GetTempDir(), self._parent.addons.tempdirs[name], "addon.xml")).getroot()
					if root2[1].text == root[1].text:
						if self._parent.addons.states[item] < 3 or self._parent.addons.states[item] == 6:
							installed.append("%s %s" % (root2[0].text, root2[1].text))
						else:
							self.HandleLinkEvent(name, 5, False)
						bzip.close()
						continue
					else:
						shutil.rmtree(os.path.join(self._parent._app.userdatadir, "addons", name))
						self._parent.addons.states[item] = 3
						self._parent.addons.RemoveAddon(name)
						self.restart.pop(item)
						self.listbox.items.pop(item)
				info.append((bzip, root, name))
			if len(installed):
				installed = "\n".join([" " * 4 + name for name in installed])
				wx.MessageBox(_("The following add-ons are already installed:\n\n%s") % installed, _("Add-on Manager"), wx.ICON_EXCLAMATION | wx.OK, self)
			if not len(info):
				return
			names = "\n".join([" " * 4 + item[1][0].text for item in info])
			install = wx.MessageBox(_("Are you sure you want to install the following add-ons?\n\n%s") % names, _("Add-on Manager"), wx.ICON_QUESTION | wx.YES_NO, self)
			if install != wx.YES:
				return
			addondir = os.path.join(self._parent._app.userdatadir, "addons")
			disabled = 0
			for i in range(len(self._parent.addons.names) - 1, -1, -1):
				if self._parent.addons.enabled[i] or self._parent.addons.states[i] == 1:
					break
				disabled += 1
			names = self._parent.addons.names[:]
			if disabled > 0:
				names = names[:-disabled]
			if len(info) > 1:
				dialog = wx.ProgressDialog("Berean", "", len(info))
				i = 0
			for bzip, root, name in info:
				if len(info) > 1:
					dialog.Update(i, _("Installing %s...") % root[0].text)
					i += 1
				bzip.extractall(addondir)
				names.append(name)
				names.sort()
				item = names.index(name)
				self._parent.addons.names.insert(item, name)
				self._parent.addons.enabled.insert(item, True)
				restart = root[3].text.lower() == "yes"
				self._parent.addons.LoadAddon(name, not restart, item)
				text = "<font><b>%s</b> %s<br>%s</font><div align=right>" % (root[0].text, root[1].text, root[2].text)
				if hasattr(self._parent.addons.addons[item], "OnInstall"):
					self._parent.addons.addons[item].OnInstall()
				if restart:
					text2 = _("<font color=green>This add-on will be installed when you restart Berean. <a href=';4'>Restart&nbsp;Now</a> <a href='%s;5'>Undo</a></font><br>") % name
					text = text2 + text[:text.index("<div align=right>")]
					self._parent.addons.states.insert(item, 6)	# 6 = will be installed on restart
				else:
					if hasattr(self._parent.addons.addons[item], "OnEnable"):
						self._parent.addons.addons[item].OnEnable()
					if hasattr(self._parent.addons.addons[item], "OnOptions"):
						text += _("<a href='%s;0'>Options</a> ") % name
					text += _("<a href='%s;1'>Disable</a> ") % name + _("<a href='%s;3'>Remove</a>") % name + " </div>"
					self._parent.addons.states.insert(item, 0)
				self.listbox.items.insert(item, text)
				self.restart.insert(item, restart)
			self.listbox.SetItemCount(len(self.listbox.items))
			self.listbox.Refresh()
			self.listbox.Update()
			if len(info) > 1:
				dialog.Destroy()
		finally:
			for item in info:
				item[0].close()
	
	def OnHyperlink(self, event):
		dialog = wx.FileDialog(self._parent, _("Install Add-on from File"), os.path.join(self._parent._app.userdatadir, "addons"), wildcard=_("Berean Add-ons (*.bzip)|*.bzip"), style=wx.OPEN | wx.MULTIPLE)
		if dialog.ShowModal() == wx.ID_OK:
			self.InstallAddonFromFile(dialog.GetPaths())
		dialog.Destroy()
	
	def OnClose(self, event):
		self.Destroy()

class HtmlListBox(wx.HtmlListBox):
	def __init__(self, parent):
		wx.HtmlListBox.__init__(self, parent, -1)
		self._parent = parent
		
		self.items = []
		
		self.Bind(wx.EVT_LISTBOX, self.OnListbox)
	
	def OnDrawSeparator(self, dc, rect, item):
		dc.SetPen(wx.Pen(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE)))
		dc.DrawLine(0, rect.y + rect.height - 1, rect.width, rect.y + rect.height - 1)
		rect.height -= 1
	
	def OnGetItem(self, item):
		text = self.items[item]
		if self.IsSelected(item):
			text = text.replace("<font color=gray>", "<font>").replace("<font color=green>", "<font>")
			if self._parent.FindFocus() == self:
				text = "<font color=%s>%s</font>" % (wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT).GetAsString(wx.C2S_HTML_SYNTAX), text)
			else:
				text = "<font color=%s>%s</font>" % (wx.SystemSettings.GetColour(wx.SYS_COLOUR_LISTBOXHIGHLIGHTTEXT).GetAsString(wx.C2S_HTML_SYNTAX), text)
		return text
	
	def OnListbox(self, event):
		self.SetItemCount(len(self.items))
		self.Update()

class AddonDropTarget(wx.FileDropTarget):
	def __init__(self, dialog):
		wx.FileDropTarget.__init__(self)
		self._dialog = dialog
	
	def OnDropFiles(self, x, y, filenames):
		filenames = filter(lambda filename: os.path.splitext(filename)[1].lower() == ".bzip", filenames)
		self._dialog.InstallAddonFromFile(filenames)
		return wx.DragCopy