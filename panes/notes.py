"""notes.py - notes pane class for Berean"""

import cPickle
import cStringIO
import os.path

import wx
from wx import aui, richtext

_ = wx.GetTranslation

class NotesPanel(wx.Panel):
    def __init__(self, parent, name):
        wx.Panel.__init__(self, parent, -1)
        self._frame = parent._parent

        self.background = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW). \
            GetAsString(wx.C2S_HTML_SYNTAX)
        self.foreground = wx.SystemSettings.GetColour(
            wx.SYS_COLOUR_WINDOWTEXT).GetAsString(wx.C2S_HTML_SYNTAX)
        self.name = name
        self.text = {}

        ID_SPELLCHECK = wx.NewId()
        self.SetAcceleratorTable(wx.AcceleratorTable([
            (wx.ACCEL_CTRL, ord("X"), wx.ID_CUT),
            (wx.ACCEL_CTRL, ord("C"), wx.ID_COPY),
            (wx.ACCEL_CTRL, ord("V"), wx.ID_PASTE),
            (wx.ACCEL_NORMAL, wx.WXK_F7, ID_SPELLCHECK),
            (wx.ACCEL_CTRL, ord("B"), wx.ID_BOLD),
            (wx.ACCEL_CTRL, ord("I"), wx.ID_ITALIC),
            (wx.ACCEL_CTRL, ord("U"), wx.ID_UNDERLINE),
            (wx.ACCEL_CTRL, ord("L"), wx.ID_JUSTIFY_LEFT),
            (wx.ACCEL_CTRL, ord("E"), wx.ID_JUSTIFY_CENTER),
            (wx.ACCEL_CTRL, ord("R"), wx.ID_JUSTIFY_RIGHT)]))
        filename = os.path.join(self._frame._app.userdatadir,
            _("%s.notes") % name)
        if not os.path.isfile(filename):
            new = open(filename, 'wb')
            cPickle.dump({}, new, -1)
            new.close()

        self.main_toolbar = aui.AuiToolBar(self, -1, (-1, -1), (-1, -1),
            aui.AUI_TB_DEFAULT_STYLE | aui.AUI_TB_OVERFLOW)
        self.main_toolbar.AddTool(wx.ID_SAVE, "", self._frame.Bitmap("save"),
            _("Save (Ctrl+S)"))
        self.main_toolbar.Bind(wx.EVT_MENU, self.OnSave, id=wx.ID_SAVE)
        self.main_toolbar.AddTool(wx.ID_PRINT, "", self._frame.Bitmap("print"),
            _("Print (Ctrl+P)"))
        self.main_toolbar.SetToolDropDown(wx.ID_PRINT, True)
        for id in (wx.ID_PRINT, wx.ID_PAGE_SETUP, wx.ID_PREVIEW):
            self.Bind(wx.EVT_MENU, self.OnPrintMenu, id=id)
        self.main_toolbar.Bind(aui.EVT_AUITOOLBAR_TOOL_DROPDOWN,
            self.OnPrintDropdown, id=wx.ID_PRINT)
        self.main_toolbar.AddSeparator()
        self.main_toolbar.AddTool(ID_SPELLCHECK, "",
            self._frame.Bitmap("spellcheck"), _("Check Spelling (F7)"))
        self.main_toolbar.EnableTool(ID_SPELLCHECK, False)
        self.main_toolbar.AddTool(wx.ID_FIND, "", self._frame.Bitmap("search-notes"),
            _("Search Notes"))
        self.main_toolbar.EnableTool(wx.ID_FIND, False)
        self.main_toolbar.AddSeparator()
        self.main_toolbar.AddTool(wx.ID_CUT, "", self._frame.Bitmap("cut"),
            _("Cut (Ctrl+X)"))
        self.main_toolbar.Bind(wx.EVT_MENU, self.OnCut, id=wx.ID_CUT)
        self.main_toolbar.AddTool(wx.ID_COPY, "", self._frame.Bitmap("copy"),
            _("Copy (Ctrl+C)"))
        self.main_toolbar.Bind(wx.EVT_MENU, self.OnCopy, id=wx.ID_COPY)
        self.main_toolbar.AddTool(wx.ID_PASTE, "", self._frame.Bitmap("paste"),
            _("Paste (Ctrl+V)"))
        self.main_toolbar.Bind(wx.EVT_MENU, self.OnPaste, id=wx.ID_PASTE)
        self.main_toolbar.AddSeparator()
        self.main_toolbar.AddTool(wx.ID_UNDO, "", self._frame.Bitmap("undo"),
            _("Undo (Ctrl+Z)"))
        self.main_toolbar.Bind(wx.EVT_MENU, self.OnUndo, id=wx.ID_UNDO)
        self.main_toolbar.AddTool(wx.ID_REDO, "", self._frame.Bitmap("redo"),
            _("Redo (Ctrl+Y)"))
        self.main_toolbar.Bind(wx.EVT_MENU, self.OnRedo, id=wx.ID_REDO)
        self.main_toolbar.AddSeparator()
        ID_HYPERLINK = wx.NewId()
        self.main_toolbar.AddTool(ID_HYPERLINK, "",
            self._frame.Bitmap("hyperlink"), _("Insert Hyperlink"))
        self.main_toolbar.EnableTool(ID_HYPERLINK, False)
        ID_PICTURE = wx.NewId()
        self.main_toolbar.AddTool(ID_PICTURE, "", self._frame.Bitmap("picture"),
            _("Insert Picture"))
        self.main_toolbar.Bind(wx.EVT_MENU, self.OnPicture, id=ID_PICTURE)
        self.main_toolbar.Realize()

        self.formatting_toolbar = aui.AuiToolBar(self, -1, (-1, -1), (-1, -1),
            aui.AUI_TB_DEFAULT_STYLE | aui.AUI_TB_OVERFLOW)
        self.fonts = sorted(wx.FontEnumerator.GetFacenames())
        self.font = wx.Choice(self.formatting_toolbar, -1, choices=self.fonts)
        self.font.SetSelection(0)
        self.formatting_toolbar.AddControl(self.font)
        self.font.Bind(wx.EVT_CHOICE, self.OnFont)
        if wx.Platform != "__WXGTK__":
            self.size = wx.ComboBox(self.formatting_toolbar, -1, "10", choices=sizes,
                style=wx.TE_PROCESS_ENTER)
        else:
            self.size = wx.ComboBox(self.formatting_toolbar, -1, "10", choices=sizes,
                size=(60, -1), style=wx.TE_PROCESS_ENTER)
        self.formatting_toolbar.AddControl(self.size)
        self.size.Bind(wx.EVT_TEXT_ENTER, self.OnSize)
        self.size.Bind(wx.EVT_COMBOBOX, self.OnSize)
        self.formatting_toolbar.AddTool(wx.ID_BOLD, "",
            self._frame.Bitmap("bold"), _("Bold (Ctrl+B)"), wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.OnBold, id=wx.ID_BOLD)
        self.formatting_toolbar.AddTool(wx.ID_ITALIC, "",
            self._frame.Bitmap("italic"), _("Italic (Ctrl+I)"), wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.OnItalic, id=wx.ID_ITALIC)
        self.formatting_toolbar.AddTool(wx.ID_UNDERLINE, "",
            self._frame.Bitmap("underline"), _("Underline (Ctrl+U)"),
            wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.OnUnderline, id=wx.ID_UNDERLINE)
        self.formatting_toolbar.AddSeparator()
        self.formatting_toolbar.AddTool(wx.ID_JUSTIFY_LEFT, "",
            self._frame.Bitmap("left"), _("Align Left (Ctrl+L)"),
            wx.ITEM_RADIO)
        self.Bind(wx.EVT_MENU, self.OnAlignLeft, id=wx.ID_JUSTIFY_LEFT)
        self.formatting_toolbar.AddTool(wx.ID_JUSTIFY_CENTER, "",
            self._frame.Bitmap("center"), _("Align Center (Ctrl+E)"),
            wx.ITEM_RADIO)
        self.Bind(wx.EVT_MENU, self.OnAlignCenter, id=wx.ID_JUSTIFY_CENTER)
        self.formatting_toolbar.AddTool(wx.ID_JUSTIFY_RIGHT, "",
            self._frame.Bitmap("right"), _("Align Right (Ctrl+R)"),
            wx.ITEM_RADIO)
        self.Bind(wx.EVT_MENU, self.OnAlignRight, id=wx.ID_JUSTIFY_RIGHT)
        self.formatting_toolbar.AddSeparator()
        self.ID_NUMBERING = wx.NewId()
        self.formatting_toolbar.AddTool(self.ID_NUMBERING, "",
            self._frame.Bitmap("numbering"), _("Numbering"))
        self.Bind(wx.EVT_MENU, self.OnNumbering, id=self.ID_NUMBERING)
        self.ID_BULLETS = wx.NewId()
        self.formatting_toolbar.AddTool(self.ID_BULLETS, "",
            self._frame.Bitmap("bullets"), _("Bullets"))
        self.Bind(wx.EVT_MENU, self.OnBullets, id=self.ID_BULLETS)
        self.ID_DEDENT = wx.NewId()
        self.formatting_toolbar.AddTool(self.ID_DEDENT, "",
            self._frame.Bitmap("dedent"), _("Decrease Indent"))
        self.Bind(wx.EVT_MENU, self.OnDecreaseIndent, id=self.ID_DEDENT)
        self.ID_INDENT = wx.NewId()
        self.formatting_toolbar.AddTool(self.ID_INDENT, "",
            self._frame.Bitmap("indent"), _("Increase Indent"))
        self.Bind(wx.EVT_MENU, self.OnIncreaseIndent, id=self.ID_INDENT)
        self.formatting_toolbar.AddSeparator()
        self.ID_COLOR = wx.NewId()
        self.formatting_toolbar.AddTool(self.ID_COLOR, "",
            self._frame.Bitmap("font-color"), _("Font Color"))
        self.Bind(wx.EVT_MENU, self.OnColor, id=self.ID_COLOR)
        self.ID_HIGHLIGHT = wx.NewId()
        self.formatting_toolbar.AddTool(self.ID_HIGHLIGHT, "",
            self._frame.Bitmap("highlighting"), _("Highlighting"))
        self.Bind(wx.EVT_MENU, self.OnHighlighting, id=self.ID_HIGHLIGHT)
        self.formatting_toolbar.Realize()

        self.editor = richtext.RichTextCtrl(self, -1, style=wx.BORDER_NONE |
            wx.WANTS_CHARS)
        if wx.Platform != "__WXGTK__":
            self.editor.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL,
                faceName="Arial"))
        else:
            self.editor.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL,
                faceName="Sans"))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.main_toolbar, 0)
        sizer.Add(self.formatting_toolbar, 0)
        sizer.Add(self.editor, 1, wx.EXPAND)
        self.SetSizer(sizer)

        notes = open(os.path.join(self._frame._app.userdatadir,
            "%s.notes" % name), 'rb')
        self.text = cPickle.load(notes)
        notes.close()
        self.LoadText(self._frame.reference[0], self._frame.reference[1])
        self.UpdateUI()

        self.editor.Bind(wx.EVT_CHAR, self.OnChar)
        self.editor.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
        self.editor.Bind(wx.EVT_LEFT_UP, self.OnKeyUp)

    def LoadText(self, book, chapter):
        key = "%d.%d" % (book, chapter)
        if key in self.text:
            stream = cStringIO.StringIO(self.text[key])
            richtext.RichTextXMLHandler().LoadStream(self.editor.GetBuffer(),
                stream)
            self.editor.Refresh()
        else:
            self.editor.SetValue("")
        self.UpdateUI()

    def UpdateUI(self):
        self.main_toolbar.EnableTool(wx.ID_CUT, self.editor.CanCut())
        self.main_toolbar.EnableTool(wx.ID_COPY, self.editor.CanCopy())
        self.main_toolbar.EnableTool(wx.ID_UNDO, self.editor.CanUndo())
        self.main_toolbar.EnableTool(wx.ID_REDO, self.editor.CanRedo())
        style = richtext.RichTextAttr()
        style.SetFlags(wx.TEXT_ATTR_FONT)
        if self.editor.GetStyle(self.editor.GetInsertionPoint(), style):
            font = style.GetFont()
            self.font.SetSelection(self.fonts.index(font.GetFaceName()))
            self.size.SetValue(str(font.GetPointSize()))
        self.formatting_toolbar.ToggleTool(wx.ID_BOLD, self.editor.IsSelectionBold())
        self.formatting_toolbar.ToggleTool(wx.ID_ITALIC,
            self.editor.IsSelectionItalics())
        self.formatting_toolbar.ToggleTool(wx.ID_UNDERLINE,
            self.editor.IsSelectionUnderlined())
        for alignment in ("LEFT", "CENTER", "RIGHT"):
            if self.editor.IsSelectionAligned(getattr(wx,
                    "TEXT_ALIGNMENT_%s" % alignment)):
                self.formatting_toolbar.ToggleTool(getattr(wx, "ID_JUSTIFY_%s" % \
                    alignment), True)
                break
        self.formatting_toolbar.Refresh(False)

    def SaveText(self):
        key = "%d.%d" % (self._frame.reference[0], self._frame.reference[1])
        if self.editor.GetLastPosition() > 0:
            stream = cStringIO.StringIO()
            richtext.RichTextXMLHandler().SaveStream(self.editor.GetBuffer(),
                stream)
            self.text[key] = stream.getvalue()
        elif key in self.text:
            self.text.pop(key)

    def SaveNotes(self):
        self.SaveText()
        notes = open(os.path.join(self._frame._app.userdatadir,
            "%s.notes" % self.name), 'wb')
        cPickle.dump(self.text, notes, -1)
        notes.close()

    def OnSave(self, event):
        self.SaveNotes()

    def OnPrintMenu(self, event):
        id = event.GetId()
        if id != wx.ID_PAGE_SETUP:
            stream = cStringIO.StringIO()
            richtext.RichTextXMLHandler().SaveStream(self.editor.GetBuffer(),
                stream)
            text = stream.getvalue()
            if wx.VERSION_STRING >= "2.8.11.0":
                self._frame.printer.SetName(self.name)
            if id == wx.ID_PRINT:
                self._frame.printer.PrintText(text)
            elif id == wx.ID_PREVIEW:
                self._frame.printer.PreviewText(text)
        else:
            self._frame.printer.PageSetup()

    def OnPrintDropdown(self, event):
        if event.IsDropDownClicked():
            self.main_toolbar.SetToolSticky(wx.ID_PRINT, True)
            menu = wx.Menu()
            menu.Append(wx.ID_PRINT, _("&Print..."))
            menu.Append(wx.ID_PAGE_SETUP, _("Page Set&up..."))
            menu.Append(wx.ID_PREVIEW, _("Print Previe&w..."))
            self.main_toolbar.PopupMenu(menu,
                self._frame.main_toolbar.GetPopupPos(self.toolbar, wx.ID_PRINT))
            self.main_toolbar.SetToolSticky(wx.ID_PRINT, False)

    def OnCut(self, event):
        self.editor.Cut()

    def OnCopy(self, event):
        self.editor.Copy()

    def OnPaste(self, event):
        self.editor.Paste()

    def OnUndo(self, event):
        self.editor.Undo()

    def OnRedo(self, event):
        self.editor.Redo()

    def OnPicture(self, event):
        filename = wx.FileSelector(_("Insert Picture"), wx.StandardPaths.Get().GetDocumentsDir(), wildcard=_("Picture Files (*.bmp;*.gif;*.jpg;*.jpeg;*.png)|*.bmp;*.gif;*.jpg;*.jpeg;*.png|All Files (*.*)|*.*"))
        if len(filename):
            self.editor.AddImage(wx.Image(filename))

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
        style.SetFontFaceName(self.font.GetStringSelection())
        style.SetFontSize(int(self.size.GetValue()))
        if self.editor.HasSelection():
            self.editor.SetStyle(self.editor.GetSelectionRange(), style)
        else:
            self.BeginStyle(style)

    def OnBold(self, event):
        # Toolbar item needs to be toggled if hotkey was used
        if self.editor.HasFocus():
            self.formatting_toolbar.ToggleTool(wx.ID_BOLD,
                not self.editor.IsSelectionBold())
            self.formatting_toolbar.Refresh(False)
        self.editor.ApplyBoldToSelection()

    def OnItalic(self, event):
        if self.editor.HasFocus():
            self.formatting_toolbar.ToggleTool(wx.ID_ITALIC,
                not self.editor.IsSelectionItalics())
            self.formatting_toolbar.Refresh(False)
        self.editor.ApplyItalicToSelection()

    def OnUnderline(self, event):
        if self.editor.HasFocus():
            self.formatting_toolbar.ToggleTool(wx.ID_UNDERLINE,
                not self.editor.IsSelectionUnderlined())
            self.formatting_toolbar.Refresh(False)
        self.editor.ApplyUnderlineToSelection()

    def OnAlignLeft(self, event):
        if self.editor.HasFocus():
            self.formatting_toolbar.ToggleTool(wx.ID_JUSTIFY_LEFT,
                not self.editor.IsSelectionAligned(wx.TEXT_ALIGNMENT_LEFT))
            self.formatting_toolbar.Refresh(False)
        self.editor.ApplyAlignmentToSelection(wx.TEXT_ALIGNMENT_LEFT)

    def OnAlignCenter(self, event):
        if self.editor.HasFocus():
            self.formatting_toolbar.ToggleTool(wx.ID_JUSTIFY_CENTER,
                not self.editor.IsSelectionAligned(wx.TEXT_ALIGNMENT_CENTER))
            self.formatting_toolbar.Refresh(False)
        self.editor.ApplyAlignmentToSelection(wx.TEXT_ALIGNMENT_CENTER)

    def OnAlignRight(self, event):
        if self.editor.HasFocus():
            self.formatting_toolbar.ToggleTool(wx.ID_JUSTIFY_RIGHT,
                not self.editor.IsSelectionAligned(wx.TEXT_ALIGNMENT_RIGHT))
            self.formatting_toolbar.Refresh(False)
        self.editor.ApplyAlignmentToSelection(wx.TEXT_ALIGNMENT_RIGHT)

    def OnNumbering(self, event):
        style = richtext.RichTextAttr()
        style.SetFlags(wx.TEXT_ATTR_LEFT_INDENT | wx.TEXT_ATTR_BULLET_STYLE |
            wx.TEXT_ATTR_BULLET_NUMBER)
        if not self.editor.HasSelection():
            start = self.editor.XYToPosition(0,
                self.editor.PositionToXY(self.editor.GetInsertionPoint())[1])
            if (not self.editor.GetStyle(start, style)) or \
                    not style.GetBulletStyle() & \
                    wx.TEXT_ATTR_BULLET_STYLE_ARABIC:
                style.SetLeftIndent(10, 40)
                style.SetBulletStyle(wx.TEXT_ATTR_BULLET_STYLE_ARABIC |
                    wx.TEXT_ATTR_BULLET_STYLE_PERIOD)
                style.SetBulletNumber(1)
            else:
                style.SetLeftIndent(0, 0)
                style.SetBulletStyle(wx.TEXT_ATTR_BULLET_STYLE_NONE)
            self.editor.SetStyle((start, start + 1), style)
        else:
            selection = self.editor.GetSelectionRange()
            if self.editor.GetStyle(selection[0], style) and \
                    not style.GetBulletStyle() & \
                    wx.TEXT_ATTR_BULLET_STYLE_ARABIC:
                style.SetBulletStyle(wx.TEXT_ATTR_BULLET_STYLE_ARABIC |
                    wx.TEXT_ATTR_BULLET_STYLE_PERIOD)
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

    def OnBullets(self, event):
        if self.editor.HasSelection():
            selection = self.editor.GetSelectionRange()
        else:
            start = self.editor.XYToPosition(0,
                self.editor.PositionToXY(self.editor.GetInsertionPoint())[1])
            selection = (start, start + 1)
        style = richtext.RichTextAttr()
        style.SetFlags(wx.TEXT_ATTR_LEFT_INDENT | wx.TEXT_ATTR_BULLET_STYLE |
            wx.TEXT_ATTR_BULLET_NAME)
        if (not self.editor.GetStyle(selection[0], style)) or \
                style.GetBulletStyle() != wx.TEXT_ATTR_BULLET_STYLE_STANDARD:
            style.SetLeftIndent(10, 40)
            style.SetBulletStyle(wx.TEXT_ATTR_BULLET_STYLE_STANDARD)
            style.SetBulletName("standard/circle")
        else:
            style.SetLeftIndent(0, 0)
            style.SetBulletStyle(wx.TEXT_ATTR_BULLET_STYLE_NONE)
        self.editor.SetStyle(selection, style)

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
        self.formatting_toolbar.SetToolSticky(self.ID_COLOR, True)
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
        dialog = wx.ColourDialog(self._frame, data)
        pos = list(self.formatting_toolbar.ClientToScreen(
            self._frame.main_toolbar.GetPopupPos(self.toolbar2, self.ID_COLOR)))
        width, height = dialog.GetSize()
        display = wx.GetDisplaySize()
        if pos[0] + width > display[0]:
            pos[0] -= (width - self.formatting_toolbar.GetToolRect(self.ID_COLOR)[2] +
                wx.SystemSettings.GetMetric(wx.SYS_FRAMESIZE_X) * 2 - 1)
        if pos[1] + height > display[1]:
            pos[1] -= (height + self.formatting_toolbar.GetToolRect(self.ID_COLOR)[3] +
                wx.SystemSettings.GetMetric(wx.SYS_FRAMESIZE_Y) * 2 - 1)
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
        self.formatting_toolbar.SetToolSticky(self.ID_COLOR, False)

    def OnHighlighting(self, event):
        self.formatting_toolbar.SetToolSticky(self.ID_HIGHLIGHT, True)
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
        dialog = wx.ColourDialog(self._frame, data)
        pos = list(self.formatting_toolbar.ClientToScreen(
            self._frame.main_toolbar.GetPopupPos(self.toolbar2,
            self.ID_HIGHLIGHT)))
        width, height = dialog.GetSize()
        display = wx.GetDisplaySize()
        if pos[0] + width > display[0]:
            pos[0] -= (width - self.formatting_toolbar.GetToolRect(self.ID_COLOR)[2] +
                wx.SystemSettings.GetMetric(wx.SYS_FRAMESIZE_X) * 2 - 1)
        if pos[1] + height > display[1]:
            pos[1] -= (height + self.formatting_toolbar.GetToolRect(self.ID_COLOR)[3] +
                wx.SystemSettings.GetMetric(wx.SYS_FRAMESIZE_Y) * 2 - 1)
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
        self.formatting_toolbar.SetToolSticky(self.ID_HIGHLIGHT, False)

    def OnChar(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_DELETE and self.editor.GetLastPosition() == 0:
            self.editor.Delete((0, 1))
        else:
            pos = self.editor.GetInsertionPoint()
            column, line = self.editor.PositionToXY(pos)
            if (key == wx.WXK_BACK and column == 0) or \
                    key == wx.WXK_RETURN or (key == wx.WXK_DELETE and \
                    column == self.editor.GetLineLength(line)):
                style = richtext.RichTextAttr()
                style.SetFlags(wx.TEXT_ATTR_BULLET_NUMBER)
                if self.editor.GetStyle(self.editor.XYToPosition(0, line),
                        style) and style.HasBulletNumber():
                    number = style.GetBulletNumber()
                    if not (key == wx.WXK_BACK and number == 1):
                        pos -= column
                        if key != wx.WXK_RETURN:
                            number -= 1
                        while (self.editor.GetStyle(pos, style) and
                                style.HasBulletNumber()):
                            style2 = richtext.RichTextAttr()
                            style2.SetFlags(wx.TEXT_ATTR_LEFT_INDENT |
                                wx.TEXT_ATTR_BULLET_NUMBER)
                            number += 1
                            style2.SetLeftIndent(10,
                                len(str(number)) * 20 + 20)
                            style2.SetBulletNumber(number)
                            pos += self.editor.GetLineLength(line) + 1
                            wx.CallAfter(self.editor.SetStyle, (pos, pos + 1),
                                style2)
                            line += 1
        event.Skip()

    def OnKeyUp(self, event):
        self.UpdateUI()
        event.Skip()


class NotesPane(aui.AuiNotebook):
    def __init__(self, parent):
        aui.AuiNotebook.__init__(self, parent, -1,
            style=(aui.AUI_NB_DEFAULT_STYLE ^ aui.AUI_NB_CLOSE_ON_ACTIVE_TAB ^
                aui.AUI_NB_MIDDLE_CLICK_CLOSE) | wx.BORDER_NONE)
        self._parent = parent

        self.AddPage(NotesPanel(self, _("Study Notes")), _("Study Notes"))
        self.AddPage(NotesPanel(self, _("Topic Notes")), _("Topic Notes"))
        self.SetSelection(parent._app.settings["ActiveNotes"])

        self.Bind(aui.EVT_AUINOTEBOOK_PAGE_CHANGED,
            self.OnAuiNotebookPageChanged)

    def OnAuiNotebookPageChanged(self, event):
        page = self.GetPage(event.GetSelection())
        page.GetSizer().Layout()    # Refresh overflow state of toolbars
        wx.CallAfter(self.GetCurrentPage().editor.SetFocus)

sizes = ["8", "9", "10", "11", "12", "14", "16", "18", "20", "22", "24", "26",
    "28", "36", "48", "72"]
