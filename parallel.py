"""
parallel.py - parallel window classes for Berean
Copyright (C) 2013 Timothy Johnson <timothysw@objectmail.com>
"""

import wx

from htmlwin import HtmlWindow

_ = wx.GetTranslation

class ParallelWindow(HtmlWindow):
	def __init__(self, parent):
		super(ParallelWindow, self).__init__(parent, parent.GetGrandParent())
		self._parent = parent
		
		self.verses = 0
		
		self.SetDescription(self._frame._app.settings["ParallelVersions"])
	
	def SetDescription(self, versions):
		if len(versions) <= 2:
			self.description = _(" and ").join(versions)
		else:
			self.description = _("%s, and %s") % (", ".join(versions[:-1]), versions[-1])
	
	def GetPage(self, book, chapter, verse=-1):
		Bibles = []
		versions = []
		for i in range(len(self._parent.choices)):
			selection = self._parent.choices[i].GetSelection()
			if i > 0:
				selection -= 1
			if selection > 0:
				Bibles.append(self._frame.notebook.GetPage(selection).Bible)
				versions.append(self._frame.versions[selection])
		items = []
		if len(Bibles):
			items.append("<tr>")
			for i in range(len(Bibles)):
				items.append("\t<td><div align=center><font size=+1><b>%s %d (%s)</b></font></div></td>" % (Bibles[i][book][0], chapter, versions[i]))
				if Bibles[i][book][chapter][0]:
					items[-1] = "%s<br>%s</div></td>" % (items[-1][:-11], Bibles[i][book][chapter][0].replace("[", "<i>").replace("]", "</i>"))
			items.append("</tr>")
			for i in range(1, max([len(Bible[book][chapter]) for Bible in Bibles])):
				items.append("<tr>")
				if i < len(Bibles[0][book][chapter]):
					items.append("\t<td><font size=-1>%d&nbsp;</font>%s<a name=\"%d\"></a></td>" % (i, Bibles[0][book][chapter][i].replace("[", "<i>").replace("]", "</i>"), i + 1))
					if i == verse:
						items[-1] = "<b>%s</b>" % items[-1]
				else:
					items.append("\t<td><a name=\"%d\"></a></td>" % (i + 1))
				for j in range(1, len(Bibles)):
					if i < len(Bibles[j][book][chapter]):
						items.append("\t<td><font size=-1>%d&nbsp;</font>%s</td>" % (i, Bibles[j][book][chapter][i].replace("[", "<i>").replace("]", "</i>")))
						if i == verse:
							items[-1] = "<b>%s</b>" % items[-1]
					else:
						items.append("\t<td></td>")
				items.append("</tr>")
			self.verses = i
		self.SetDescription(versions)
		return body % (self._frame.zoom, "\n\t\t".join(items))
	
	def LoadChapter(self, book, chapter, verse=-1):
		self.SetPage(self.GetPage(book, chapter, verse))
		self._frame.statusbar.SetStatusText(self.description, 1)
		if verse > 1 and self._parent.choices[0].GetSelection() > 0:
			wx.CallAfter(self.ScrollToAnchor, str(verse))
			self.verse = -1

body = """<html>
<body>
	<font size=%d><table valign=top cellspacing=2 cellpadding=0><tbody>
		%s
	</tbody></table></font>
</body>
</html>"""

class ParallelPanel(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent, -1)
		self._frame = parent.GetParent()
		
		self.choicedata = wx.CustomDataObject("ParallelPanel")
		
		self.choices = []
		self._frame._app.settings["ParallelVersions"] = filter(lambda item: item in self._frame.versions, self._frame._app.settings["ParallelVersions"])
		for i in range(len(self._frame.versions)):
			if i == 0:
				self.choices.append(wx.Choice(self, -1, choices=self._frame.versions))
			else:
				self.choices.append(wx.Choice(self, -1, choices=[_("(none)")] + self._frame.versions))
			self.choices[-1].SetDropTarget(ChoiceDropTarget(self, i))
			self.choices[-1].Bind(wx.EVT_RIGHT_DOWN, self.OnChoiceRightDown)
			if i >= len(self._frame._app.settings["ParallelVersions"]):
				self.choices[-1].SetSelection(0)
				if i != len(self._frame._app.settings["ParallelVersions"]):
					self.choices[-1].Disable()
			elif i == 0:
				self.choices[-1].SetSelection(self._frame.versions.index(self._frame._app.settings["ParallelVersions"][i]))
			else:
				self.choices[-1].SetSelection(self._frame.versions.index(self._frame._app.settings["ParallelVersions"][i]) + 1)
		self._frame.parallel = ParallelWindow(self)
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer2 = wx.BoxSizer(wx.HORIZONTAL)
		for choice in self.choices:
			sizer2.Add(choice, 1, wx.ALL | wx.EXPAND, 1)
		sizer.Add(sizer2, 0, wx.ALL | wx.EXPAND, 1)
		sizer.Add(self._frame.parallel, 1, wx.EXPAND)
		self.SetSizer(sizer)
		
		self.Bind(wx.EVT_CHOICE, self.OnChoice)
	
	def OnChoiceRightDown(self, event):
		choice = event.GetEventObject()
		selection = choice.GetSelection()
		if selection > 0 or self.choices.index(choice) == 0:
			choice.SetFocus()
			self.choicedata.SetData("%s,%s" % (self.choices.index(choice), selection))
			source = wx.DropSource(self)
			source.SetData(self.choicedata)
			source.DoDragDrop(wx.Drag_DefaultMove)
			wx.CallAfter(self._frame.parallel.SetFocus)
	
	def OnChoice(self, event):
		index = self.choices.index(event.GetEventObject())
		if event.GetSelection() == 0 and index > 0:
			for i in range(index, len(self.choices)):
				if i > index:
					self.choices[i - 1].SetSelection(self.choices[i].GetSelection())
				self.choices[i].SetSelection(0)
				if i < len(self.choices) - 1 and self.choices[i + 1].GetSelection() == 0:
					self.choices[i + 1].Disable()
		elif index < len(self.choices) - 1:
			self.choices[index + 1].Enable()
		self._frame.parallel.LoadChapter(*self._frame.reference)
		wx.CallAfter(self._frame.parallel.SetFocus)

class ChoiceDropTarget(wx.DropTarget):
	def __init__(self, panel, index):
		wx.DropTarget.__init__(self)
		self._panel = panel
		
		self.index = index
		self.data = wx.CustomDataObject("ParallelPanel")
		self.SetDataObject(self.data)
	
	def OnDragOver(self, x, y, default):
		if self.index > 0 and self._panel.choices[self.index].GetSelection() == 0:
			return wx.DragNone
		return default
	
	def OnData(self, x, y, default):
		self.GetData()
		index, new = map(int, self.data.GetData().split(","))
		if index != self._panel.choices[self.index]:
			old = self._panel.choices[self.index].GetSelection()
			self._panel.choices[self.index].SetSelection(new)
			self._panel.choices[index].SetSelection(old)
			self._panel._frame.parallel.LoadChapter(*self._panel._frame.reference)
		return default