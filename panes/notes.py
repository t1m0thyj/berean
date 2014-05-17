"""notes.py - notes pane class"""

import anydbm
import cStringIO
import os.path

import wx
from wx import aui, gizmos, richtext

from config import *

_ = wx.GetTranslation


class BaseSelector(gizmos.EditableListBox):
    def __init__(self, parent):
        super(BaseSelector, self).__init__(parent, label=_("Notes"),
            style=gizmos.EL_DEFAULT_STYLE | gizmos.EL_NO_REORDER)
        self._grandparent = parent.GetParent()
        self.searchctrl = wx.SearchCtrl(self)
        self.searchctrl.Bind(wx.EVT_TEXT, self.OnSearchCtrlText)
        for child in self.GetChildren():
            if isinstance(child, wx.ListCtrl):
                self.listctrl = child
                break
        self.SetStrings(
            sorted(self._grandparent.notes_db.keys(), key=str.lower))
        self.GetSizer().Insert(1, self.searchctrl, 0,
            (wx.ALL ^ wx.TOP) | wx.EXPAND, 1)

    def OnSearchCtrlText(self, event):
        self.searchctrl.ShowCancelButton(not self.searchctrl.IsEmpty())


class ReferenceSelector(BaseSelector):
    def __init__(self, parent):
        super(ReferenceSelector, self).__init__(parent)


class TopicSelector(BaseSelector):
    def __init__(self, parent):
        super(TopicSelector, self).__init__(parent)


class NotesPage(wx.Panel):
    def __init__(self, parent, tab):
        super(NotesPage, self).__init__(parent)
        self._parent = parent
        self._frame = parent.GetParent()
        self.db_key = "%d.%d" % self._frame.reference[:2]
        self.notes_db = anydbm.open(os.path.join(self._frame._app.userdatadir,
            "%s.db" % NotesPane.names[tab]), 'c')

        self.toolbar = aui.AuiToolBar(self, wx.ID_ANY, wx.DefaultPosition,
            wx.DefaultSize, aui.AUI_TB_DEFAULT_STYLE | aui.AUI_TB_OVERFLOW)
        self.toolbar.AddTool(wx.ID_SAVE, "", self._frame.get_bitmap("save"),
            _("Save (Ctrl+S)"))
        self.Bind(wx.EVT_MENU, self.OnSave, id=wx.ID_SAVE)
        self.toolbar.AddTool(wx.ID_PRINT, "", self._frame.get_bitmap("print"),
            _("Print Notes"))
        self.Bind(wx.EVT_MENU, self.OnPrint, id=wx.ID_PRINT)
        self.toolbar.AddSeparator()
        self.toolbar.AddTool(wx.ID_CUT, "", self._frame.get_bitmap("cut"),
            _("Cut (Ctrl+X)"))
        self.toolbar.Bind(wx.EVT_MENU, self.OnCut, id=wx.ID_CUT)
        self.toolbar.AddTool(wx.ID_COPY, "", self._frame.get_bitmap("copy"),
            _("Copy (Ctrl+C)"))
        self.toolbar.Bind(wx.EVT_MENU, self.OnCopy, id=wx.ID_COPY)
        self.toolbar.AddTool(wx.ID_PASTE, "", self._frame.get_bitmap("paste"),
            _("Paste (Ctrl+V)"))
        self.toolbar.Bind(wx.EVT_MENU, self.OnPaste, id=wx.ID_PASTE)
        self.toolbar.AddSeparator()
        self.font_name = wx.Choice(self.toolbar, choices=self._frame.facenames)
        self.font_name.SetSelection(0)
        self.toolbar.AddControl(self.font_name)
        self.font_name.Bind(wx.EVT_CHOICE, self.OnFontName)
        if '__WXGTK__' not in wx.PlatformInfo:
            self.font_size = wx.ComboBox(self.toolbar, choices=FONT_SIZES,
                style=wx.TE_PROCESS_ENTER)
        else:
            self.font_size = wx.ComboBox(self.toolbar, choices=FONT_SIZES,
                size=(60, -1), style=wx.TE_PROCESS_ENTER)
        self.font_size.Bind(wx.EVT_COMBOBOX, self.OnFontSize)
        self.font_size.Bind(wx.EVT_TEXT_ENTER, self.OnFontSize)
        self.toolbar.AddControl(self.font_size)
        self.toolbar.AddSeparator()
        self.toolbar.AddTool(wx.ID_BOLD, "", self._frame.get_bitmap("bold"),
            _("Bold (Ctrl+B)"), wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.OnBold, id=wx.ID_BOLD)
        self.toolbar.AddTool(wx.ID_ITALIC, "",
            self._frame.get_bitmap("italic"), _("Italic (Ctrl+I)"),
            wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.OnItalic, id=wx.ID_ITALIC)
        self.toolbar.AddTool(wx.ID_UNDERLINE, "",
            self._frame.get_bitmap("underline"), _("Underline (Ctrl+U)"),
            wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.OnUnderline, id=wx.ID_UNDERLINE)
        self.toolbar.AddSeparator()
        self.toolbar.AddTool(wx.ID_JUSTIFY_LEFT, "",
            self._frame.get_bitmap("align-left"), _("Align Left (Ctrl+L)"),
            wx.ITEM_RADIO)
        self.Bind(wx.EVT_MENU, self.OnAlignLeft, id=wx.ID_JUSTIFY_LEFT)
        self.toolbar.AddTool(wx.ID_JUSTIFY_CENTER, "",
            self._frame.get_bitmap("align-center"),
            _("Align Center (Ctrl+E)"), wx.ITEM_RADIO)
        self.Bind(wx.EVT_MENU, self.OnAlignCenter, id=wx.ID_JUSTIFY_CENTER)
        self.toolbar.AddTool(wx.ID_JUSTIFY_RIGHT, "",
            self._frame.get_bitmap("align-right"), _("Align Right (Ctrl+R)"),
            wx.ITEM_RADIO)
        self.Bind(wx.EVT_MENU, self.OnAlignRight, id=wx.ID_JUSTIFY_RIGHT)
        self.toolbar.AddSeparator()
        ID_NUMBERING = wx.NewId()
        self.toolbar.AddTool(ID_NUMBERING, "",
            self._frame.get_bitmap("numbering"), _("Numbering"))
        self.Bind(wx.EVT_MENU, self.OnNumbering, id=ID_NUMBERING)
        ID_BULLETS = wx.NewId()
        self.toolbar.AddTool(ID_BULLETS, "",
            self._frame.get_bitmap("bullets"), _("Bullets"))
        self.Bind(wx.EVT_MENU, self.OnBullets, id=ID_BULLETS)
        ID_DECREASE_INDENT = wx.NewId()
        self.toolbar.AddTool(ID_DECREASE_INDENT, "",
            self._frame.get_bitmap("decrease-indent"), _("Decrease Indent"))
        self.Bind(wx.EVT_MENU, self.OnDecreaseIndent, id=ID_DECREASE_INDENT)
        ID_INCREASE_INDENT = wx.NewId()
        self.toolbar.AddTool(ID_INCREASE_INDENT, "",
            self._frame.get_bitmap("increase-indent"), _("Increase Indent"))
        self.Bind(wx.EVT_MENU, self.OnIncreaseIndent, id=ID_INCREASE_INDENT)
        self.toolbar.AddSeparator()
        ID_HIGHLIGHTING = wx.NewId()
        self.toolbar.AddTool(ID_HIGHLIGHTING, "",
            self._frame.get_bitmap("highlighting"), _("Highlighting"))
        self.Bind(wx.EVT_MENU, self.OnHighlighting, id=ID_HIGHLIGHTING)
        ID_FONT_COLOR = wx.NewId()
        self.toolbar.AddTool(ID_FONT_COLOR, "",
            self._frame.get_bitmap("font-color"), _("Font Color"))
        self.Bind(wx.EVT_MENU, self.OnFontColor, id=ID_FONT_COLOR)
        self.toolbar.Realize()

        self.splitter = wx.SplitterWindow(self)
        self.splitter.SetMinimumPaneSize(1)
        if tab == 0:
            self.selector = ReferenceSelector(self.splitter)
        else:
            self.selector = TopicSelector(self.splitter)
        self.editor = richtext.RichTextCtrl(self.splitter,
            style=wx.BORDER_NONE | wx.WANTS_CHARS)
        style = self.editor.GetBasicStyle()
        style.SetFontFaceName(self._frame.default_font["normal_face"])
        style.SetFontSize(self._frame.default_font["size"])
        self.editor.SetBasicStyle(style)
        self.editor.SetModified(False)
        self.editor.Bind(wx.EVT_CHAR, self.OnChar)
        self.editor.Bind(wx.EVT_KEY_UP, self.OnModified)
        self.editor.Bind(wx.EVT_LEFT_UP, self.OnModified)
        self.splitter.SplitVertically(self.selector, self.editor, 150)

        self.SetAcceleratorTable(wx.AcceleratorTable([
            (wx.ACCEL_CTRL, ord("S"), wx.ID_SAVE),
            (wx.ACCEL_CTRL, ord("X"), wx.ID_CUT),
            (wx.ACCEL_CTRL, ord("C"), wx.ID_COPY),
            (wx.ACCEL_CTRL, ord("V"), wx.ID_PASTE),
            (wx.ACCEL_CTRL, ord("B"), wx.ID_BOLD),
            (wx.ACCEL_CTRL, ord("I"), wx.ID_ITALIC),
            (wx.ACCEL_CTRL, ord("U"), wx.ID_UNDERLINE),
            (wx.ACCEL_CTRL, ord("L"), wx.ID_JUSTIFY_LEFT),
            (wx.ACCEL_CTRL, ord("E"), wx.ID_JUSTIFY_CENTER),
            (wx.ACCEL_CTRL, ord("R"), wx.ID_JUSTIFY_RIGHT),
            (wx.ACCEL_SHIFT, 9, ID_DECREASE_INDENT),
            (wx.ACCEL_NORMAL, 9, ID_INCREASE_INDENT)]))
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.toolbar, 0)
        sizer.Add(self.splitter, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.update_toolbar()

    def load_text(self, db_key):
        if db_key in self.notes_db:
            stream = cStringIO.StringIO(self.notes_db[db_key])
            self.editor.GetBuffer().LoadStream(stream,
                richtext.RICHTEXT_TYPE_XML)
            self.editor.Refresh()
        else:
            self.editor.Clear()
        self.update_toolbar()
        self.db_key = db_key

    def update_toolbar(self):
        self.toolbar.EnableTool(wx.ID_CUT, self.editor.CanCut())
        self.toolbar.EnableTool(wx.ID_COPY, self.editor.CanCopy())
        style = richtext.RichTextAttr()
        style.SetFlags(wx.TEXT_ATTR_FONT)
        if self.editor.GetStyle(self.editor.GetInsertionPoint(), style):
            font = style.GetFont()
            self.font_name.SetStringSelection(font.GetFaceName())
            self.font_size.SetValue(str(font.GetPointSize()))
        self.toolbar.ToggleTool(wx.ID_BOLD, self.editor.IsSelectionBold())
        self.toolbar.ToggleTool(wx.ID_ITALIC, self.editor.IsSelectionItalics())
        self.toolbar.ToggleTool(wx.ID_UNDERLINE,
            self.editor.IsSelectionUnderlined())
        for alignment in ("LEFT", "CENTER", "RIGHT"):
            if self.editor.IsSelectionAligned(
                    getattr(wx, "TEXT_ALIGNMENT_%s" % alignment)):
                self.toolbar.ToggleTool(
                    getattr(wx, "ID_JUSTIFY_%s" % alignment), True)
                break
        self.toolbar.Refresh(False)

    def save_text(self):
        if not self.editor.IsModified():
            return
        if not self.editor.IsEmpty():
            stream = cStringIO.StringIO()
            self.editor.GetBuffer().SaveStream(stream,
                richtext.RICHTEXT_TYPE_XML)
            self.notes_db[self.db_key] = stream.getvalue()
            self.editor.SetModified(False)
        elif self.db_key in self.notes_db:
            del self.notes_db[self.db_key]

    def OnSave(self, event):
        self.save_text()
        self.notes_db.sync()

    def OnPrint(self, event):
        if wx.VERSION_STRING >= "2.8.11.0" and wx.VERSION_STRING != "2.9.0.0":
            self._frame.printing.SetName(
                NotesPane.names[self._parent.GetPageIndex(self)])
        stream = cStringIO.StringIO()
        richtext.RichTextHTMLHandler().SaveStream(self.editor.GetBuffer(),
            stream)
        self._frame.printing.PreviewText(stream.getvalue())

    def OnCut(self, event):
        self.editor.Cut()

    def OnCopy(self, event):
        self.editor.Copy()

    def OnPaste(self, event):
        self.editor.Paste()

    def OnFontName(self, event):
        style = richtext.RichTextAttr()
        style.SetFlags(wx.TEXT_ATTR_FONT_FACE)
        style.SetFontFaceName(event.GetString())
        if not self.editor.HasSelection():
            self.editor.BeginStyle(style)
        else:
            self.editor.SetStyle(self.editor.GetSelectionRange(), style)
        self.editor.SetFocus()

    def OnFontSize(self, event):
        style = richtext.RichTextAttr()
        style.SetFlags(wx.TEXT_ATTR_FONT_SIZE)
        style.SetFontSize(int(self.font_size.GetValue()))
        if not self.editor.HasSelection():
            self.editor.BeginStyle(style)
        else:
            self.editor.SetStyle(self.editor.GetSelectionRange(), style)
        self.editor.SetFocus()

    def OnBold(self, event):
        # Toolbar item needs to be toggled if hotkey was used
        if self.editor.HasFocus():
            self.toolbar.ToggleTool(wx.ID_BOLD,
                not self.editor.IsSelectionBold())
            self.toolbar.Refresh(False)
        self.editor.ApplyBoldToSelection()

    def OnItalic(self, event):
        if self.editor.HasFocus():
            self.toolbar.ToggleTool(wx.ID_ITALIC,
                not self.editor.IsSelectionItalics())
            self.toolbar.Refresh(False)
        self.editor.ApplyItalicToSelection()

    def OnUnderline(self, event):
        if self.editor.HasFocus():
            self.toolbar.ToggleTool(wx.ID_UNDERLINE,
                not self.editor.IsSelectionUnderlined())
            self.toolbar.Refresh(False)
        self.editor.ApplyUnderlineToSelection()

    def OnAlignLeft(self, event):
        if self.editor.HasFocus():
            self.toolbar.ToggleTool(wx.ID_JUSTIFY_LEFT,
                not self.editor.IsSelectionAligned(wx.TEXT_ALIGNMENT_LEFT))
            self.toolbar.Refresh(False)
        self.editor.ApplyAlignmentToSelection(wx.TEXT_ALIGNMENT_LEFT)

    def OnAlignCenter(self, event):
        if self.editor.HasFocus():
            self.toolbar.ToggleTool(wx.ID_JUSTIFY_CENTER,
                not self.editor.IsSelectionAligned(wx.TEXT_ALIGNMENT_CENTER))
            self.toolbar.Refresh(False)
        self.editor.ApplyAlignmentToSelection(wx.TEXT_ALIGNMENT_CENTER)

    def OnAlignRight(self, event):
        if self.editor.HasFocus():
            self.toolbar.ToggleTool(wx.ID_JUSTIFY_RIGHT,
                not self.editor.IsSelectionAligned(wx.TEXT_ALIGNMENT_RIGHT))
            self.toolbar.Refresh(False)
        self.editor.ApplyAlignmentToSelection(wx.TEXT_ALIGNMENT_RIGHT)

    def OnNumbering(self, event):
        style = richtext.RichTextAttr()
        style.SetFlags(wx.TEXT_ATTR_LEFT_INDENT | wx.TEXT_ATTR_BULLET_STYLE |
            wx.TEXT_ATTR_BULLET_NUMBER)
        if not self.editor.HasSelection():
            pos = self.editor.XYToPosition(0,
                self.editor.PositionToXY(self.editor.GetInsertionPoint())[1])
            if self.editor.GetStyle(pos, style):
                if not style.GetBulletStyle() & \
                        wx.TEXT_ATTR_BULLET_STYLE_ARABIC:
                    style.SetLeftIndent(50, 50)
                    style.SetBulletStyle(wx.TEXT_ATTR_BULLET_STYLE_ARABIC |
                        wx.TEXT_ATTR_BULLET_STYLE_PERIOD)
                    style.SetBulletNumber(1)
                else:
                    style.SetLeftIndent(0, 0)
                    style.SetBulletStyle(wx.TEXT_ATTR_BULLET_STYLE_NONE)
                self.editor.SetStyle((pos, pos + 1), style)
        else:
            selection = self.editor.GetSelectionRange()
            if self.editor.GetStyle(selection[0], style):
                if not style.GetBulletStyle() & \
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
                        style.SetLeftIndent(50, len(str(number)) * 20 + 30)
                        style.SetBulletNumber(number)
                    line = self.editor.PositionToXY(pos)[1]
                    pos = self.editor.XYToPosition(0, line)
                    self.editor.SetStyle((pos, pos + 1), style)
                    pos += self.editor.GetLineLength(line) + 1
                    number += 1

    def OnBullets(self, event):
        if not self.editor.HasSelection():
            start = self.editor.XYToPosition(0,
                self.editor.PositionToXY(self.editor.GetInsertionPoint())[1])
            richtext_range = (start, start + 1)
        else:
            richtext_range = self.editor.GetSelectionRange()
        style = richtext.RichTextAttr()
        style.SetFlags(wx.TEXT_ATTR_LEFT_INDENT | wx.TEXT_ATTR_BULLET_STYLE |
            wx.TEXT_ATTR_BULLET_NAME)
        if self.editor.GetStyle(richtext_range[0], style):
            if style.GetBulletStyle() != wx.TEXT_ATTR_BULLET_STYLE_STANDARD:
                style.SetLeftIndent(50, 50)
                style.SetBulletStyle(wx.TEXT_ATTR_BULLET_STYLE_STANDARD)
                style.SetBulletName("standard/circle")
            else:
                style.SetLeftIndent(0, 0)
                style.SetBulletStyle(wx.TEXT_ATTR_BULLET_STYLE_NONE)
            self.editor.SetStyle(richtext_range, style)

    def OnDecreaseIndent(self, event):
        pos = self.editor.GetInsertionPoint()
        style = richtext.RichTextAttr()
        style.SetFlags(wx.TEXT_ATTR_LEFT_INDENT)
        if self.editor.GetStyle(pos, style):
            if not self.editor.HasSelection():
                richtext_range = (pos, pos + 1)
            else:
                richtext_range = self.editor.GetSelectionRange()
            if style.GetLeftIndent() >= 100:
                style.SetLeftIndent(style.GetLeftIndent() - 100)
                self.editor.SetStyle(richtext_range, style)

    def OnIncreaseIndent(self, event):
        pos = self.editor.GetInsertionPoint()
        style = richtext.RichTextAttr()
        style.SetFlags(wx.TEXT_ATTR_LEFT_INDENT)
        if self.editor.GetStyle(pos, style):
            if not self.editor.HasSelection():
                richtext_range = (pos, pos + 1)
            else:
                richtext_range = self.editor.GetSelectionRange()
            style.SetLeftIndent(style.GetLeftIndent() + 100)
            self.editor.SetStyle(richtext_range, style)

    def OnHighlighting(self, event):
        pos = self.editor.GetInsertionPoint()
        style = richtext.RichTextAttr()
        style.SetFlags(wx.TEXT_ATTR_BACKGROUND_COLOUR)
        data = wx.ColourData()
        if self.editor.GetStyle(self.editor.GetInsertionPoint(), style):
            data.SetColour(style.GetBackgroundColour())
        dialog = wx.ColourDialog(self._frame, data)
        dialog.SetTitle(_("Highlighting"))
        dialog.Center()
        if dialog.ShowModal() == wx.ID_OK:
            if not self.editor.HasSelection():
                richtext_range = (pos, pos + 1)
            else:
                richtext_range = self.editor.GetSelectionRange()
            style.SetBackgroundColour(dialog.GetColourData().GetColour())
            self.editor.SetStyle(richtext_range, style)
        dialog.Destroy()

    def OnFontColor(self, event):
        style = richtext.RichTextAttr()
        style.SetFlags(wx.TEXT_ATTR_TEXT_COLOUR)
        data = wx.ColourData()
        if self.editor.GetStyle(self.editor.GetInsertionPoint(), style):
            data.SetColour(style.GetTextColour())
        dialog = wx.ColourDialog(self._frame, data)
        dialog.SetTitle(_("Font Color"))
        dialog.Center()
        if dialog.ShowModal() == wx.ID_OK:
            color = dialog.GetColourData().GetColour()
            if not self.editor.HasSelection():
                self.editor.BeginTextColour(color)
            else:
                style.SetTextColour(color)
                self.editor.SetStyle(self.editor.GetSelectionRange(), style)
        dialog.Destroy()

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
                            style2.SetLeftIndent(50,
                                len(str(number)) * 20 + 30)
                            style2.SetBulletNumber(number)
                            pos += self.editor.GetLineLength(line) + 1
                            wx.CallAfter(self.editor.SetStyle, (pos, pos + 1),
                                style2)
                            line += 1
        event.Skip()

    def OnModified(self, event):
        self.update_toolbar()
        event.Skip()


class NotesPane(aui.AuiNotebook):
    names = (_("Study Notes"), _("Topic Notes"))
    def __init__(self, parent):
        super(NotesPane, self).__init__(parent, style=wx.BORDER_NONE |
            aui.AUI_NB_TOP | aui.AUI_NB_SCROLL_BUTTONS)
        self._parent = parent
        richtext.RichTextBuffer.AddHandler(richtext.RichTextXMLHandler())
        self.AddPage(NotesPage(self, 0), NotesPane.names[0])
        self.AddPage(NotesPage(self, 1), NotesPane.names[1])
        self.SetSelection(parent._app.config.ReadInt("Notes/ActiveTab"))
        self.Bind(aui.EVT_AUINOTEBOOK_PAGE_CHANGED,
            self.OnAuiNotebookPageChanged)

    def OnAuiNotebookPageChanged(self, event):
        page = self.GetCurrentPage()
        if (event.GetSelection() == 0 and
                page.db_key != "%d.%d" % self._parent.reference[:2]):
            page.save_text()
            page.load_text(*self._parent.reference[:2])
