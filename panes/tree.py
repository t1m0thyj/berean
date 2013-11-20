"""
tree.py - tree pane class for Berean
Copyright (C) 2013 Timothy Johnson <timothysw@objectmail.com>
"""

import wx

_ = wx.GetTranslation

class TreePane(wx.TreeCtrl):
	def __init__(self, parent):
		wx.TreeCtrl.__init__(self, parent, -1, style=wx.NO_BORDER | wx.TR_DEFAULT_STYLE | wx.TR_TWIST_BUTTONS | wx.TR_NO_LINES | wx.TR_FULL_ROW_HIGHLIGHT | wx.TR_HIDE_ROOT)
		self._parent = parent
		
		self.items = [self.AddRoot("")] + range(66)
		if not parent._app.settings["HebrewBookOrder"]:
			order = range(1, len(parent.books) + 1)
		else:
			order = range(1, 8) + range(9, 13) + [23, 24, 26] + range(28, 40) + [19, 20, 18, 22, 8, 25, 21, 17, 27, 15, 16, 13, 14] + range(40, 67)
		for i in range(len(parent.books)):
			j = order[i]
			self.items[j] = [self.AppendItem(self.items[0], parent.books[j - 1])]
			self.SetItemHasChildren(self.items[j][0], True)
		self.ShowChapters(parent.reference[0])
		
		self.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.OnSelChanged)
		self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged)
	
	def ShowChapters(self, book):
		item = self.items[book][0]
		if not self.IsExpanded(item):
			for i in range(1, self._parent.chapters[book - 1] + 1):
				self.items[book].append(self.AppendItem(item, str(i)))
			self.Expand(item)
	
	def OnSelChanged(self, event):
		item = event.GetItem()
		if self.ItemHasChildren(item):
			book = self._parent.books.index(self.GetItemText(item)) + 1
			if not self.GetChildrenCount(item):
				self.ShowChapters(book)
			else:
				self.HideChapters(book)
		else:
			book = self._parent.books.index(self.GetItemText(self.GetItemParent(item))) + 1
			for i in range(1, len(self.items)):
				if i != book and self.IsExpanded(self.items[i][0]):
					self.HideChapters(i)
					break
			if not self._parent.skipevents:
				chapter = int(self.GetItemText(item))
				self._parent.LoadChapter(book, chapter)
	
	def HideChapters(self, book):
		item = self.items[book][0]
		if self.IsExpanded(item):
			self.Collapse(item)
			self.DeleteChildren(item)
			self.items[book] = [self.items[book][0]]
