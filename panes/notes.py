"""
notes.py - notes pane class for Berean
Copyright (C) 2013 Timothy Johnson <timothysw@objectmail.com>
"""

import cPickle
import cStringIO
import os
import wx
from wx import richtext

import aui

_ = wx.GetTranslation

class NotesPane(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent, -1)
		self._parent = parent
		
		self.background = parent._app.settings["LastBackColor"]
		self.foreground = parent._app.settings["LastForeColor"]
		self.path = os.path.join(parent._app.userdatadir, "notes")
		self.selection = parent._app.settings["ActiveNotes"]
		self.text = {}
		
		self.SetAcceleratorTable(wx.AcceleratorTable([(wx.ACCEL_CTRL, ord("X"), wx.ID_CUT),
													  (wx.ACCEL_CTRL, ord("C"), wx.ID_COPY),
													  (wx.ACCEL_CTRL, ord("V"), wx.ID_PASTE),
													  (wx.ACCEL_CTRL, ord("B"), wx.ID_BOLD),
													  (wx.ACCEL_CTRL, ord("I"), wx.ID_ITALIC),
													  (wx.ACCEL_CTRL, ord("U"), wx.ID_UNDERLINE),
													  (wx.ACCEL_CTRL, ord("L"), wx.ID_JUSTIFY_LEFT),
													  (wx.ACCEL_CTRL, ord("E"), wx.ID_JUSTIFY_CENTER),
													  (wx.ACCEL_CTRL, ord("R"), wx.ID_JUSTIFY_RIGHT)]))
		if not os.path.isdir(self.path):
			os.mkdir(self.path)
		name = os.path.join(self.path, _("Study Notes.nts"))
		if not os.path.isfile(name):
			new = open(name, 'wb')
			cPickle.dump({}, new, -1)
			new.close()
		if not len(parent._app.settings["NotesList"]):
			parent._app.settings["NotesList"] = [_("Study Notes")]
		for name in parent._app.settings["NotesList"]:
			if not os.path.isfile(os.path.join(self.path, "%s.nts" % name)):
				parent._app.settings["NotesList"].remove(name)
		
		self.toolbar = aui.AuiToolBar(self, -1, agwStyle=aui.AUI_TB_DEFAULT_STYLE | aui.AUI_TB_OVERFLOW)
		self.notes = wx.Choice(self.toolbar, -1, choices=parent._app.settings["NotesList"])
		self.notes.SetSelection(self.selection)
		self.toolbar.AddControl(self.notes)
		self.notes.Bind(wx.EVT_CHOICE, self.OnNotes)
		self.ID_MANAGE = wx.NewId()
		self.toolbar.AddSimpleTool(self.ID_MANAGE, "", parent.Bitmap("notes"), _("Manage Notes"))
		self.Bind(wx.EVT_MENU, self.OnManage, id=self.ID_MANAGE)
		self.toolbar.AddSimpleTool(wx.ID_UNDO, "", parent.Bitmap("undo"), _("Undo (Ctrl+Z)"))
		self.toolbar.Bind(wx.EVT_MENU, self.OnUndo, id=wx.ID_UNDO)
		self.toolbar.AddSimpleTool(wx.ID_REDO, "", parent.Bitmap("redo"), _("Redo (Ctrl+Y)"))
		self.toolbar.Bind(wx.EVT_MENU, self.OnRedo, id=wx.ID_REDO)
		self.toolbar.AddSeparator()
		self.toolbar.AddSimpleTool(wx.ID_CUT, "", parent.Bitmap("cut"), _("Cut (Ctrl+X)"))
		self.toolbar.Bind(wx.EVT_MENU, self.OnCut, id=wx.ID_CUT)
		self.toolbar.AddSimpleTool(wx.ID_COPY, "", parent.Bitmap("copy"), _("Copy (Ctrl+C)"))
		self.toolbar.Bind(wx.EVT_MENU, self.OnCopy, id=wx.ID_COPY)
		self.toolbar.AddSimpleTool(wx.ID_PASTE, "", parent.Bitmap("paste"), _("Paste (Ctrl+V)"))
		self.toolbar.Bind(wx.EVT_MENU, self.OnPaste, id=wx.ID_PASTE)
		self.toolbar.AddSeparator()
		self.fonts = sorted(wx.FontEnumerator.GetFacenames())
		self.font = wx.Choice(self.toolbar, -1, choices=self.fonts)
		self.font.SetSelection(0)
		self.toolbar.AddControl(self.font)
		self.font.Bind(wx.EVT_CHOICE, self.OnFont)
		if wx.Platform != "__WXGTK__":
			self.size = wx.ComboBox(self.toolbar, -1, "10", choices=sizes, style=wx.TE_PROCESS_ENTER)
		else:
			self.size = wx.ComboBox(self.toolbar, -1, "10", choices=sizes, size=(60, -1), style=wx.TE_PROCESS_ENTER)
		self.toolbar.AddControl(self.size)
		self.size.Bind(wx.EVT_TEXT_ENTER, self.OnSize)
		self.size.Bind(wx.EVT_COMBOBOX, self.OnSize)
		self.toolbar.AddCheckTool(wx.ID_BOLD, "", parent.Bitmap("bold"), wx.NullBitmap, _("Bold (Ctrl+B)"))
		self.Bind(wx.EVT_MENU, self.OnBold, id=wx.ID_BOLD)
		self.toolbar.AddCheckTool(wx.ID_ITALIC, "", parent.Bitmap("italic"), wx.NullBitmap, _("Italic (Ctrl+I)"))
		self.Bind(wx.EVT_MENU, self.OnItalic, id=wx.ID_ITALIC)
		self.toolbar.AddCheckTool(wx.ID_UNDERLINE, "", parent.Bitmap("underline"), wx.NullBitmap, _("Underline (Ctrl+U)"))
		self.Bind(wx.EVT_MENU, self.OnUnderline, id=wx.ID_UNDERLINE)
		self.toolbar.AddSeparator()
		self.toolbar.AddRadioTool(wx.ID_JUSTIFY_LEFT, "", parent.Bitmap("left"), wx.NullBitmap, _("Align Left (Ctrl+L)"))
		self.Bind(wx.EVT_MENU, self.OnAlignLeft, id=wx.ID_JUSTIFY_LEFT)
		self.toolbar.AddRadioTool(wx.ID_JUSTIFY_CENTER, "", parent.Bitmap("center"), wx.NullBitmap, _("Align Center (Ctrl+E)"))
		self.Bind(wx.EVT_MENU, self.OnAlignCenter, id=wx.ID_JUSTIFY_CENTER)
		self.toolbar.AddRadioTool(wx.ID_JUSTIFY_RIGHT, "", parent.Bitmap("right"), wx.NullBitmap, _("Align Right (Ctrl+R)"))
		self.Bind(wx.EVT_MENU, self.OnAlignRight, id=wx.ID_JUSTIFY_RIGHT)
		self.toolbar.AddSeparator()
		self.ID_BULLETS = wx.NewId()
		self.toolbar.AddSimpleTool(self.ID_BULLETS, "", parent.Bitmap("bullets"), _("Bullets"))
		self.Bind(wx.EVT_MENU, self.OnBullets, id=self.ID_BULLETS)
		self.ID_NUMBERING = wx.NewId()
		self.toolbar.AddSimpleTool(self.ID_NUMBERING, "", parent.Bitmap("numbering"), _("Numbering"))
		self.Bind(wx.EVT_MENU, self.OnNumbering, id=self.ID_NUMBERING)
		self.ID_DEDENT = wx.NewId()
		self.toolbar.AddSimpleTool(self.ID_DEDENT, "", parent.Bitmap("dedent"), _("Decrease Indent"))
		self.Bind(wx.EVT_MENU, self.OnDecreaseIndent, id=self.ID_DEDENT)
		self.ID_INDENT = wx.NewId()
		self.toolbar.AddSimpleTool(self.ID_INDENT, "", parent.Bitmap("indent"), _("Increase Indent"))
		self.Bind(wx.EVT_MENU, self.OnIncreaseIndent, id=self.ID_INDENT)
		self.toolbar.AddSeparator()
		self.ID_COLOR = wx.NewId()
		self.toolbar.AddSimpleTool(self.ID_COLOR, "", parent.Bitmap("font-color"), _("Font Color"))
		self.Bind(wx.EVT_MENU, self.OnColor, id=self.ID_COLOR)
		self.ID_HIGHLIGHT = wx.NewId()
		self.toolbar.AddSimpleTool(self.ID_HIGHLIGHT, "", parent.Bitmap("highlighting"), _("Highlighting"))
		self.Bind(wx.EVT_MENU, self.OnHighlighting, id=self.ID_HIGHLIGHT)
		self.toolbar.Realize()
		
		self.editor = richtext.RichTextCtrl(self, -1, style=wx.NO_BORDER | wx.WANTS_CHARS)
		if wx.Platform != "__WXGTK__":
			self.editor.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, faceName="Arial"))
		else:
			self.editor.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, faceName="Sans"))
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.toolbar, 0, wx.EXPAND)
		sizer.Add(self.editor, 1, wx.EXPAND)
		self.SetSizer(sizer)
		
		self.LoadNotes(self.notes.GetStringSelection())
		self.UpdateUI()
		
		self.editor.Bind(wx.EVT_CHAR, self.OnChar)
		self.editor.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
		self.editor.Bind(wx.EVT_LEFT_UP, self.OnKeyUp)
	
	def LoadNotes(self, name):
		if name != self.notes.GetStringSelection():
			self.selection = self.notes.GetStrings().index(name)
			self.notes.SetSelection(self.selection)
		notes = open(os.path.join(self.path, "%s.nts" % name), 'rb')
		self.text = cPickle.load(notes)
		notes.close()
		self.LoadText(self._parent.reference[0], self._parent.reference[1])
	
	def LoadText(self, book, chapter):
		key = "%d.%d" % (book, chapter)
		if key in self.text:
			stream = cStringIO.StringIO(self.text[key])
			richtext.RichTextXMLHandler().LoadStream(self.editor.GetBuffer(), stream)
	
	def UpdateUI(self):
		self.toolbar.EnableTool(wx.ID_UNDO, self.editor.CanUndo())
		self.toolbar.EnableTool(wx.ID_REDO, self.editor.CanRedo())
		self.toolbar.EnableTool(wx.ID_CUT, self.editor.CanCut())
		self.toolbar.EnableTool(wx.ID_COPY, self.editor.CanCopy())
		style = richtext.RichTextAttr()
		style.SetFlags(wx.TEXT_ATTR_FONT)
		if self.editor.GetStyle(self.editor.GetInsertionPoint(), style):
			font = style.GetFont()
			self.font.SetSelection(self.fonts.index(font.GetFaceName()))
			self.size.SetValue(str(font.GetPointSize()))
		self.toolbar.ToggleTool(wx.ID_BOLD, self.editor.IsSelectionBold())
		self.toolbar.ToggleTool(wx.ID_ITALIC, self.editor.IsSelectionItalics())
		self.toolbar.ToggleTool(wx.ID_UNDERLINE, self.editor.IsSelectionUnderlined())
		for alignment in ("LEFT", "CENTER", "RIGHT"):
			if self.editor.IsSelectionAligned(getattr(wx, "TEXT_ALIGNMENT_%s" % alignment)):
				self.toolbar.ToggleTool(getattr(wx, "ID_JUSTIFY_%s" % alignment), True)
				break
		self.toolbar.Refresh(False)
	
	def SaveText(self):
		key = "%d.%d" % (self._parent.reference[0], self._parent.reference[1])
		if self.editor.GetLastPosition() > 0:
			stream = cStringIO.StringIO()
			richtext.RichTextXMLHandler().SaveStream(self.editor.GetBuffer(), stream)
			self.text[key] = stream.getvalue()
		elif key in self.text:
			self.text.pop(key)
	
	def SaveNotes(self, name=None):
		if not name:
			name = self.notes.GetStringSelection()
		self.SaveText()
		notes = open(os.path.join(self.path, "%s.nts" % name), 'wb')
		cPickle.dump(self.text, notes, -1)
		notes.close()
	
	def OnNotes(self, event):
		self.SaveNotes(self.notes.GetString(self.selection))
		self.LoadNotes(event.GetString())
		self.selection = event.GetSelection()
	
	def OnManage(self, event):
		self.toolbar.SetToolSticky(self.ID_MANAGE, True)
		menu = wx.Menu()
		menu.Append(wx.ID_NEW, _("New..."))
		self._parent.Bind(wx.EVT_MENU, self.OnNew, id=wx.ID_NEW)
		menu.Append(wx.ID_DELETE, _("Delete"))
		self._parent.Bind(wx.EVT_MENU, self.OnDelete, id=wx.ID_DELETE)
		ID_RENAME = wx.NewId()
		menu.Append(ID_RENAME, _("Rename..."))
		self._parent.Bind(wx.EVT_MENU, self.OnRename, id=ID_RENAME)
		editable = self.notes.GetStringSelection() != _("Study Notes")
		menu.Enable(wx.ID_DELETE, editable)
		menu.Enable(ID_RENAME, editable)
		self.toolbar.PopupMenu(menu, self._parent.toolbar.GetPopupPos(self.toolbar, self.ID_MANAGE))
		self.toolbar.SetToolSticky(self.ID_MANAGE, False)
	
	def OnNew(self, event):
		name = wx.GetTextFromUser(_("Enter a name for the new note set:"), _("New Note Set"), "", self._parent)
		while name in self.notes.GetItems():
			wx.MessageBox(_("The name '%s' already exists.\nPlease choose a different name for the note set.") % name, _("New Note Set"), wx.ICON_EXCLAMATION | wx.OK)
			name = wx.GetTextFromUser(_("Enter a name for the new note set:"), _("New Note Set"), "", self._parent)
		if len(name):
			new = open(os.path.join(self.path, "%s.nts" % name), 'wb')
			cPickle.dump({}, new, -1)
			new.close()
			notes = self.notes.GetItems()
			notes.append(name)
			notes.sort()
			self.notes.SetItems(notes)
			self.LoadNotes(name)
	
	def OnDelete(self, event):
		selection = self.notes.GetSelection()
		name = self.notes.GetStringSelection()
		delete = wx.MessageBox(_("Are you sure that you want to permanently delete the note set '%s'?") % name, _("Delete Note Set"), wx.ICON_EXCLAMATION | wx.YES_NO | wx.NO_DEFAULT)
		if delete == wx.YES:
			os.remove(os.path.join(self.path, "%s.nts" % name))
			notes = self.notes.GetItems()
			notes.remove(name)
			self.notes.SetItems(notes)
			self.LoadNotes(self.notes.GetString(selection - 1))
	
	def OnRename(self, event):
		old = self.notes.GetStringSelection()
		new = wx.GetTextFromUser(_("Enter a new name for the note set '%s':") % old, _("Rename Note Set"), old, self._parent)
		if new != old:
			while new in self.notes.GetItems():
				wx.MessageBox(_("The name '%s' already exists.\nPlease choose a different name for the note set.") % new, _("Rename Note Set"), wx.ICON_EXCLAMATION | wx.OK)
				new = wx.GetTextFromUser(_("Enter a new name for the note set '%s':") % old, _("Rename Note Set"), old, self._parent)
			if len(new):
				os.rename(os.path.join(self.path, "%s.nts" % old), os.path.join(self.path, "%s.nts" % new))
				notes = self.notes.GetItems()
				notes.remove(old)
				notes.append(new)
				notes.sort()
				self.notes.SetItems(notes)
				self.LoadNotes(new)
	
	def OnUndo(self, event):
		self.editor.Undo()
	
	def OnRedo(self, event):
		self.editor.Redo()
	
	def OnCut(self, event):
		self.editor.Cut()
	
	def OnCopy(self, event):
		self.editor.Copy()
	
	def OnPaste(self, event):
		self.editor.Paste()
	
	def OnFont(self, event):
		style = richtext.RichTextAttr()
		style.SetFlags(wx.TEXT_ATTR_FONT_FACE | wx.TEXT_ATTR_FONT_SIZE)
		style.SetFontFaceName(event.GetString())
		style.SetFontSize(int(self.size.GetValue()))
		if self.editor.HasSelection():
			self.editor.SetStyle(self.editor.GetSelectionRange(), style)
		else:
			self.BeginStyle(style)
	
	def OnSize(self, event):
		style = richtext.RichTextAttr()
		style.SetFlags(wx.TEXT_ATTR_FONT_FACE | wx.TEXT_ATTR_FONT_SIZE)
		style.SetFontFaceName(self.font.GetValue())
		style.SetFontSize(int(self.size.GetValue()))
		if self.editor.HasSelection():
			self.editor.SetStyle(self.editor.GetSelectionRange(), style)
		else:
			self.BeginStyle(style)
	
	def OnBold(self, event):
		if self.editor.HasFocus():	# Toolbar item must be manually toggled if hotkey was used
			self.toolbar.ToggleTool(wx.ID_BOLD, not self.editor.IsSelectionBold())
			self.toolbar.Refresh(False)
		self.editor.ApplyBoldToSelection()
	
	def OnItalic(self, event):
		if self.editor.HasFocus():
			self.toolbar.ToggleTool(wx.ID_ITALIC, not self.editor.IsSelectionItalics())
			self.toolbar.Refresh(False)
		self.editor.ApplyItalicToSelection()
	
	def OnUnderline(self, event):
		if self.editor.HasFocus():
			self.toolbar.ToggleTool(wx.ID_UNDERLINE, not self.editor.IsSelectionUnderlined())
			self.toolbar.Refresh(False)
		self.editor.ApplyUnderlineToSelection()
	
	def OnAlignLeft(self, event):
		if self.editor.HasFocus():
			self.toolbar.ToggleTool(wx.ID_JUSTIFY_LEFT, not self.editor.IsSelectionAligned(wx.TEXT_ALIGNMENT_LEFT))
			self.toolbar.Refresh(False)
		self.editor.ApplyAlignmentToSelection(wx.TEXT_ALIGNMENT_LEFT)
	
	def OnAlignCenter(self, event):
		if self.editor.HasFocus():
			self.toolbar.ToggleTool(wx.ID_JUSTIFY_CENTER, not self.editor.IsSelectionAligned(wx.TEXT_ALIGNMENT_CENTER))
			self.toolbar.Refresh(False)
		self.editor.ApplyAlignmentToSelection(wx.TEXT_ALIGNMENT_CENTER)
	
	def OnAlignRight(self, event):
		if self.editor.HasFocus():
			self.toolbar.ToggleTool(wx.ID_JUSTIFY_RIGHT, not self.editor.IsSelectionAligned(wx.TEXT_ALIGNMENT_RIGHT))
			self.toolbar.Refresh(False)
		self.editor.ApplyAlignmentToSelection(wx.TEXT_ALIGNMENT_RIGHT)
	
	def OnBullets(self, event):
		if self.editor.HasSelection():
			selection = self.editor.GetSelectionRange()
		else:
			start = self.editor.XYToPosition(0, self.editor.PositionToXY(self.editor.GetInsertionPoint())[1])
			selection = (start, start + 1)
		style = richtext.RichTextAttr()
		style.SetFlags(wx.TEXT_ATTR_LEFT_INDENT | wx.TEXT_ATTR_BULLET_STYLE | wx.TEXT_ATTR_BULLET_NAME)
		if (not self.editor.GetStyle(selection[0], style)) or style.GetBulletStyle() != wx.TEXT_ATTR_BULLET_STYLE_STANDARD:
			style.SetLeftIndent(10, 40)
			style.SetBulletStyle(wx.TEXT_ATTR_BULLET_STYLE_STANDARD)
			style.SetBulletName("standard/circle")
		else:
			style.SetLeftIndent(0, 0)
			style.SetBulletStyle(wx.TEXT_ATTR_BULLET_STYLE_NONE)
		self.editor.SetStyle(selection, style)
	
	def OnNumbering(self, event):
		style = richtext.RichTextAttr()
		style.SetFlags(wx.TEXT_ATTR_LEFT_INDENT | wx.TEXT_ATTR_BULLET_STYLE | wx.TEXT_ATTR_BULLET_NUMBER)
		if not self.editor.HasSelection():
			start = self.editor.XYToPosition(0, self.editor.PositionToXY(self.editor.GetInsertionPoint())[1])
			if (not self.editor.GetStyle(start, style)) or not style.GetBulletStyle() & wx.TEXT_ATTR_BULLET_STYLE_ARABIC:
				style.SetLeftIndent(10, 40)
				style.SetBulletStyle(wx.TEXT_ATTR_BULLET_STYLE_ARABIC | wx.TEXT_ATTR_BULLET_STYLE_PERIOD)
				style.SetBulletNumber(1)
			else:
				style.SetLeftIndent(0, 0)
				style.SetBulletStyle(wx.TEXT_ATTR_BULLET_STYLE_NONE)
			self.editor.SetStyle((start, start + 1), style)
		else:
			selection = self.editor.GetSelectionRange()
			if self.editor.GetStyle(selection[0], style) and not style.GetBulletStyle() & wx.TEXT_ATTR_BULLET_STYLE_ARABIC:
				style.SetBulletStyle(wx.TEXT_ATTR_BULLET_STYLE_ARABIC | wx.TEXT_ATTR_BULLET_STYLE_PERIOD)
				numbering = True
			else:
				style.SetLeftIndent(0, 0)
				style.SetBulletStyle(wx.TEXT_ATTR_BULLET_STYLE_NONE)
				numbering = False
			pos = selection[0]
			number = 1
			while pos < selection[1]:
				if numbering:
					style.SetLeftIndent(10, len(str(number)) * 20 + 20)
					style.SetBulletNumber(number)
				line = self.editor.PositionToXY(pos)[1]
				pos = self.editor.XYToPosition(0, line)
				self.editor.SetStyle((pos, pos + 1), style)
				pos += self.editor.GetLineLength(line) + 1
				number += 1
	
	def OnDecreaseIndent(self, event):
		style = richtext.RichTextAttr()
		style.SetFlags(wx.TEXT_ATTR_LEFT_INDENT)
		pos = self.editor.GetInsertionPoint()
		if self.editor.GetStyle(pos, style):
			selection = (pos, pos)
			if self.editor.HasSelection():
				selection = self.editor.GetSelectionRange()
		if style.GetLeftIndent() >= 100:
			style.SetLeftIndent(style.GetLeftIndent() - 100)
			style.SetFlags(wx.TEXT_ATTR_LEFT_INDENT)
			self.editor.SetStyle(selection, style)
	
	def OnIncreaseIndent(self, event):
		style = richtext.RichTextAttr()
		style.SetFlags(wx.TEXT_ATTR_LEFT_INDENT)
		pos = self.editor.GetInsertionPoint()
		if self.editor.GetStyle(pos, style):
			selection = (pos, pos)
			if self.editor.HasSelection():
				selection = self.editor.GetSelectionRange()
			style.SetLeftIndent(style.GetLeftIndent() + 100)
			style.SetFlags(wx.TEXT_ATTR_LEFT_INDENT)
			self.editor.SetStyle(selection, style)
	
	def OnColor(self, event):
		self.toolbar.SetToolSticky(self.ID_COLOR, True)
		style = richtext.RichTextAttr()
		style.SetFlags(wx.TEXT_ATTR_TEXT_COLOUR)
		data = wx.ColourData()
		color = wx.NullColour
		if self.editor.GetStyle(self.editor.GetInsertionPoint(), style):
			color = style.GetBackgroundColour()
		if color == wx.NullColour:
			color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
		data.SetColour(color)
		data.SetCustomColour(0, self.foreground)
		dialog = wx.ColourDialog(self._parent, data)
		pos = list(self.toolbar.ClientToScreen(self._parent.toolbar.GetPopupPos(self.toolbar, self.ID_COLOR)))
		width, height = dialog.GetSize()
		display = wx.GetDisplaySize()
		if pos[0] + width > display[0]:
			pos[0] -= (width - self.toolbar.GetToolRect(self.ID_COLOR)[2] + wx.SystemSettings.GetMetric(wx.SYS_FRAMESIZE_X) * 2 - 1)
		if pos[1] + height > display[1]:
			pos[1] -= (height + self.toolbar.GetToolRect(self.ID_COLOR)[3] + wx.SystemSettings.GetMetric(wx.SYS_FRAMESIZE_Y) * 2 - 1)
		dialog.SetPosition(pos)
		dialog.SetTitle(_("Font Color"))
		if dialog.ShowModal() == wx.ID_OK:
			color = dialog.GetColourData().GetColour()
			style.SetTextColour(color)
			if not self.editor.HasSelection():
				pos = self.editor.GetInsertionPoint()
				self.editor.SetStyle((pos, pos + 1), style)
			else:
				self.editor.SetStyle(self.editor.GetSelectionRange(), style)
			self.foreground = color.GetAsString(wx.C2S_HTML_SYNTAX)
		dialog.Destroy()
		self.toolbar.SetToolSticky(self.ID_COLOR, False)
	
	def OnHighlighting(self, event):
		self.toolbar.SetToolSticky(self.ID_HIGHLIGHT, True)
		style = richtext.RichTextAttr()
		style.SetFlags(wx.TEXT_ATTR_BACKGROUND_COLOUR)
		data = wx.ColourData()
		color = wx.NullColour
		if self.editor.GetStyle(self.editor.GetInsertionPoint(), style):
			color = style.GetBackgroundColour()
		if color == wx.NullColour:
			color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
		data.SetColour(color)
		data.SetCustomColour(0, self.background)
		dialog = wx.ColourDialog(self._parent, data)
		pos = list(self.toolbar.ClientToScreen(self._parent.toolbar.GetPopupPos(self.toolbar, self.ID_HIGHLIGHT)))
		width, height = dialog.GetSize()
		display = wx.GetDisplaySize()
		if pos[0] + width > display[0]:
			pos[0] -= (width - self.toolbar.GetToolRect(self.ID_COLOR)[2] + wx.SystemSettings.GetMetric(wx.SYS_FRAMESIZE_X) * 2 - 1)
		if pos[1] + height > display[1]:
			pos[1] -= (height + self.toolbar.GetToolRect(self.ID_COLOR)[3] + wx.SystemSettings.GetMetric(wx.SYS_FRAMESIZE_Y) * 2 - 1)
		dialog.SetPosition(pos)
		dialog.SetTitle(_("Highlighting"))
		if dialog.ShowModal() == wx.ID_OK:
			color = dialog.GetColourData().GetColour()
			style.SetBackgroundColour(color)
			if not self.editor.HasSelection():
				pos = self.editor.GetInsertionPoint()
				self.editor.SetStyle((pos, pos + 1), style)
			else:
				self.editor.SetStyle(self.editor.GetSelectionRange(), style)
			self.background = color.GetAsString(wx.C2S_HTML_SYNTAX)
		dialog.Destroy()
		self.toolbar.SetToolSticky(self.ID_HIGHLIGHT, False)
	
	def OnChar(self, event):
		key = event.GetKeyCode()
		if key == wx.WXK_DELETE and self.editor.GetLastPosition() == 0:
			self.editor.Delete((0, 1))
		else:
			pos = self.editor.GetInsertionPoint()
			column, line = self.editor.PositionToXY(pos)
			if (key == wx.WXK_BACK and column == 0) or key == wx.WXK_RETURN or (key == wx.WXK_DELETE and column == self.editor.GetLineLength(line)):
				style = richtext.RichTextAttr()
				style.SetFlags(wx.TEXT_ATTR_BULLET_NUMBER)
				if self.editor.GetStyle(self.editor.XYToPosition(0, line), style) and style.HasBulletNumber():
					number = style.GetBulletNumber()
					if not (key == wx.WXK_BACK and number == 1):
						pos -= column
						if key != wx.WXK_RETURN:
							number -= 1
						while self.editor.GetStyle(pos, style) and style.HasBulletNumber():
							style2 = richtext.RichTextAttr()
							style2.SetFlags(wx.TEXT_ATTR_LEFT_INDENT | wx.TEXT_ATTR_BULLET_NUMBER)
							number += 1
							style2.SetLeftIndent(10, len(str(number)) * 20 + 20)
							style2.SetBulletNumber(number)
							pos += self.editor.GetLineLength(line) + 1
							wx.CallAfter(self.editor.SetStyle, (pos, pos + 1), style2)
							line += 1
		event.Skip()
	
	def OnKeyUp(self, event):
		self.UpdateUI()
		event.Skip()

sizes = ["8", "9", "10", "11", "12", "14", "16", "18", "20", "22", "24", "26", "28", "36", "48", "72"]