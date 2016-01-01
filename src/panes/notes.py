"""notes.py - notes pane class"""

import cStringIO
import os.path
import sqlite3

import wx
from wx import aui, richtext

from config import FONT_SIZES

_ = wx.GetTranslation


class TopicsPaneBase(wx.Panel):
    def __init__(self, parent):
        super(TopicsPaneBase, self).__init__(parent)
        self.searchctrl = wx.SearchCtrl(self)
        self.searchctrl.Bind(wx.EVT_TEXT, self.OnSearchCtrlText)
        self.listbox = wx.ListBox(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.searchctrl, 0, wx.ALL | wx.EXPAND, 1)
        sizer.Add(self.listbox, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def OnSearchCtrlText(self, event):
        text = self.searchctrl.GetValue()
        if text:
            for i, topic in enumerate(self.listbox.GetStrings()):
                if topic.startswith(text):
                    self.listbox.SetSelection(i)
                    break
        self.searchctrl.ShowCancelButton(len(text) > 0)


class SubjectTopicsPane(TopicsPaneBase):
    def __init__(self, parent):
        super(SubjectTopicsPane, self).__init__(parent)


class VerseTopicsPane(TopicsPaneBase):
    def __init__(self, parent):
        super(VerseTopicsPane, self).__init__(parent)


class NotesPage(wx.Panel):
    def __init__(self, parent, tab):
        super(NotesPage, self).__init__(parent)
        self._parent = parent
        self._frame = parent.GetParent()
        self.conn = sqlite3.connect(os.path.join(self._frame._app.userdatadir,
                                                 "%s.sqlite" % NotesPane.names[tab]),
                                    isolation_level=None)
        self.conn.execute("CREATE TABLE IF NOT EXISTS notes(topic TEXT PRIMARY KEY, "
                          "xml TEXT NOT NULL)")
        self.db_key = "%d.%d" % self._frame.reference[:2]

        self.toolbar = aui.AuiToolBar(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
                                      aui.AUI_TB_DEFAULT_STYLE | aui.AUI_TB_OVERFLOW)
        self.ID_SHOW_TOPICS_PANE = wx.NewId()
        self.toolbar.AddTool(self.ID_SHOW_TOPICS_PANE, "",
                             self._frame.get_bitmap("show-topics-pane"), _("Show Topics Pane"),
                             wx.ITEM_CHECK)
        sash_pos = self._frame._app.config.ReadInt("Notes/SplitterPosition%d" % (tab + 1), 150)
        if sash_pos > 0:
            self.toolbar.ToggleTool(self.ID_SHOW_TOPICS_PANE, True)
        self.toolbar.Bind(wx.EVT_MENU, self.OnShowTopicsPane, id=self.ID_SHOW_TOPICS_PANE)
        self.toolbar.AddSeparator()
        self.toolbar.AddTool(wx.ID_SAVE, "", self._frame.get_bitmap("save"), _("Save (Ctrl+S)"))
        self.Bind(wx.EVT_MENU, self.OnSave, id=wx.ID_SAVE)
        self.toolbar.AddTool(wx.ID_PRINT, "", self._frame.get_bitmap("print"), _("Print Notes"))
        self.Bind(wx.EVT_MENU, self.OnPrint, id=wx.ID_PRINT)
        self.toolbar.AddSeparator()
        self.toolbar.AddTool(wx.ID_CUT, "", self._frame.get_bitmap("cut"), _("Cut (Ctrl+X)"))
        self.toolbar.Bind(wx.EVT_MENU, self.OnCut, id=wx.ID_CUT)
        self.toolbar.AddTool(wx.ID_COPY, "", self._frame.get_bitmap("copy"), _("Copy (Ctrl+C)"))
        self.toolbar.Bind(wx.EVT_MENU, self.OnCopy, id=wx.ID_COPY)
        self.toolbar.AddTool(wx.ID_PASTE, "", self._frame.get_bitmap("paste"), _("Paste (Ctrl+V)"))
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
            self.font_size = wx.ComboBox(self.toolbar, choices=FONT_SIZES, size=(60, -1),
                                         style=wx.TE_PROCESS_ENTER)
        self.font_size.Bind(wx.EVT_COMBOBOX, self.OnFontSize)
        self.font_size.Bind(wx.EVT_TEXT_ENTER, self.OnFontSize)
        self.toolbar.AddControl(self.font_size)
        self.toolbar.AddSeparator()
        self.toolbar.AddTool(wx.ID_BOLD, "", self._frame.get_bitmap("bold"), _("Bold (Ctrl+B)"),
                             wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.OnBold, id=wx.ID_BOLD)
        self.toolbar.AddTool(wx.ID_ITALIC, "", self._frame.get_bitmap("italic"),
                             _("Italic (Ctrl+I)"), wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.OnItalic, id=wx.ID_ITALIC)
        self.toolbar.AddTool(wx.ID_UNDERLINE, "", self._frame.get_bitmap("underline"),
                             _("Underline (Ctrl+U)"), wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.OnUnderline, id=wx.ID_UNDERLINE)
        self.toolbar.AddSeparator()
        self.toolbar.AddTool(wx.ID_JUSTIFY_LEFT, "", self._frame.get_bitmap("align-left"),
                             _("Align Left (Ctrl+L)"), wx.ITEM_RADIO)
        self.Bind(wx.EVT_MENU, self.OnAlignLeft, id=wx.ID_JUSTIFY_LEFT)
        self.toolbar.AddTool(wx.ID_JUSTIFY_CENTER, "", self._frame.get_bitmap("align-center"),
                             _("Align Center (Ctrl+E)"), wx.ITEM_RADIO)
        self.Bind(wx.EVT_MENU, self.OnAlignCenter, id=wx.ID_JUSTIFY_CENTER)
        self.toolbar.AddTool(wx.ID_JUSTIFY_RIGHT, "", self._frame.get_bitmap("align-right"),
                             _("Align Right (Ctrl+R)"), wx.ITEM_RADIO)
        self.Bind(wx.EVT_MENU, self.OnAlignRight, id=wx.ID_JUSTIFY_RIGHT)
        self.toolbar.AddSeparator()
        ID_NUMBERING = wx.NewId()
        self.toolbar.AddTool(ID_NUMBERING, "", self._frame.get_bitmap("numbering"), _("Numbering"))
        self.Bind(wx.EVT_MENU, self.OnNumbering, id=ID_NUMBERING)
        ID_BULLETS = wx.NewId()
        self.toolbar.AddTool(ID_BULLETS, "", self._frame.get_bitmap("bullets"), _("Bullets"))
        self.Bind(wx.EVT_MENU, self.OnBullets, id=ID_BULLETS)
        ID_DECREASE_INDENT = wx.NewId()
        self.toolbar.AddTool(ID_DECREASE_INDENT, "", self._frame.get_bitmap("decrease-indent"),
                             _("Decrease Indent"))
        self.Bind(wx.EVT_MENU, self.OnDecreaseIndent, id=ID_DECREASE_INDENT)
        ID_INCREASE_INDENT = wx.NewId()
        self.toolbar.AddTool(ID_INCREASE_INDENT, "", self._frame.get_bitmap("increase-indent"),
                             _("Increase Indent"))
        self.Bind(wx.EVT_MENU, self.OnIncreaseIndent, id=ID_INCREASE_INDENT)
        self.toolbar.AddSeparator()
        ID_HIGHLIGHTING = wx.NewId()
        self.toolbar.AddTool(ID_HIGHLIGHTING, "", self._frame.get_bitmap("highlighting"),
                             _("Highlighting"))
        self.Bind(wx.EVT_MENU, self.OnHighlighting, id=ID_HIGHLIGHTING)
        ID_FONT_COLOR = wx.NewId()
        self.toolbar.AddTool(ID_FONT_COLOR, "", self._frame.get_bitmap("font-color"),
                             _("Font Color"))
        self.Bind(wx.EVT_MENU, self.OnFontColor, id=ID_FONT_COLOR)
        self.toolbar.Realize()

        self.splitter = wx.SplitterWindow(self)
        if tab == 0:
            self.topics_pane = SubjectTopicsPane(self.splitter)
        else:
            self.topics_pane = VerseTopicsPane(self.splitter)
        self.editor = richtext.RichTextCtrl(self.splitter, style=wx.BORDER_NONE | wx.WANTS_CHARS)
        self.set_default_style(self._frame.default_font)
        self.editor.SetModified(False)
        self.editor.Bind(wx.EVT_CHAR, self.OnChar)
        self.editor.Bind(wx.EVT_KEY_UP, self.OnModified)
        self.editor.Bind(wx.EVT_LEFT_UP, self.OnModified)
        if sash_pos > 0:
            wx.CallAfter(self.splitter.SplitVertically, self.topics_pane, self.editor, sash_pos)
        else:
            self.splitter.Initialize(self.editor)
        self.splitter.Bind(wx.EVT_SPLITTER_UNSPLIT, self.OnSplitterUnsplit)
        self.splitter.Bind(wx.EVT_SPLITTER_DCLICK, self.OnSplitterDclick)

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

    def set_default_style(self, font):
        style = self.editor.GetBasicStyle()
        style.SetFontFaceName(font["normal_face"])
        style.SetFontSize(font["size"])
        self.editor.SetBasicStyle(style)
        self.update_toolbar()

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
        self.toolbar.ToggleTool(wx.ID_UNDERLINE, self.editor.IsSelectionUnderlined())
        for alignment in ("LEFT", "CENTER", "RIGHT"):
            if self.editor.IsSelectionAligned(getattr(wx, "TEXT_ALIGNMENT_%s" % alignment)):
                self.toolbar.ToggleTool(getattr(wx, "ID_JUSTIFY_%s" % alignment), True)
                break
        self.toolbar.Refresh(False)

    def load_text(self, db_key):
        row = self.conn.execute("SELECT xml FROM notes WHERE topic=?", (db_key,)).fetchone()
        if row:
            stream = cStringIO.StringIO(row[0])
            self.editor.GetBuffer().LoadStream(stream, richtext.RICHTEXT_TYPE_XML)
            self.editor.Refresh()
        else:
            self.editor.Clear()
        self.update_toolbar()
        self.db_key = db_key

    def save_text(self):
        if not self.editor.IsModified():
            return
        if not self.editor.IsEmpty():
            stream = cStringIO.StringIO()
            self.editor.GetBuffer().SaveStream(stream, richtext.RICHTEXT_TYPE_XML)
            self.conn.execute("INSERT OR REPLACE INTO notes VALUES(?,?)",
                              (self.db_key, stream.getvalue()))
            self.editor.SetModified(False)
        else:
            self.conn.execute("DELETE FROM notes WHERE topic=?", (self.db_key,))

    def OnShowTopicsPane(self, event):
        if self.splitter.IsSplit():
            self.splitter.Unsplit(self.topics_pane)
        else:
            self.splitter.SplitVertically(self.topics_pane, self.editor, 150)

    def OnSave(self, event):
        self.save_text()

    def OnPrint(self, event):
        if wx.VERSION_STRING >= "2.9.1":
            self._frame.printing.SetName(NotesPane.names[self._parent.GetPageIndex(self)])
        stream = cStringIO.StringIO()
        richtext.RichTextHTMLHandler().SaveStream(self.editor.GetBuffer(), stream)
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
            pos = self.editor.XYToPosition(0, self.editor.PositionToXY(self.editor.
                                                                       GetInsertionPoint())[1])
            if self.editor.GetStyle(pos, style):
                if not (style.GetBulletStyle() & wx.TEXT_ATTR_BULLET_STYLE_ARABIC):
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
                if not (style.GetBulletStyle() & wx.TEXT_ATTR_BULLET_STYLE_ARABIC):
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
            start = self.editor.XYToPosition(0, self.editor.PositionToXY(self.editor.
                                                                         GetInsertionPoint())[1])
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
            if ((key == wx.WXK_BACK and column == 0) or key == wx.WXK_RETURN or
                    (key == wx.WXK_DELETE and column == self.editor.GetLineLength(line))):
                style = richtext.RichTextAttr()
                style.SetFlags(wx.TEXT_ATTR_BULLET_NUMBER)
                if (self.editor.GetStyle(self.editor.XYToPosition(0, line), style) and
                        style.HasBulletNumber()):
                    number = style.GetBulletNumber()
                    if not (key == wx.WXK_BACK and number == 1):
                        pos -= column
                        if key != wx.WXK_RETURN:
                            number -= 1
                        while self.editor.GetStyle(pos, style) and style.HasBulletNumber():
                            style2 = richtext.RichTextAttr()
                            style2.SetFlags(wx.TEXT_ATTR_LEFT_INDENT | wx.TEXT_ATTR_BULLET_NUMBER)
                            number += 1
                            style2.SetLeftIndent(50, len(str(number)) * 20 + 30)
                            style2.SetBulletNumber(number)
                            pos += self.editor.GetLineLength(line) + 1
                            wx.CallAfter(self.editor.SetStyle, (pos, pos + 1), style2)
                            line += 1
        event.Skip()

    def OnModified(self, event):
        self.update_toolbar()
        event.Skip()

    def OnSplitterUnsplit(self, event):
        self.toolbar.ToggleTool(self.ID_SHOW_TOPICS_PANE, False)
        self.toolbar.Refresh(False)

    def OnSplitterDclick(self, event):
        self.splitter.Unsplit(self.topics_pane)
        self.OnSplitterUnsplit(None)
        event.Veto()


class NotesPane(aui.AuiNotebook):
    names = (_("Subject Notes"), _("Verse Notes"))

    def __init__(self, parent):
        super(NotesPane, self).__init__(parent, style=wx.BORDER_NONE | aui.AUI_NB_TOP |
                                        aui.AUI_NB_SCROLL_BUTTONS)
        self._parent = parent
        richtext.RichTextBuffer.AddHandler(richtext.RichTextXMLHandler())
        self.AddPage(NotesPage(self, 0), NotesPane.names[0])
        self.AddPage(NotesPage(self, 1), NotesPane.names[1])
        self.SetSelection(parent._app.config.ReadInt("Notes/ActiveTab"))
        self.Bind(aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.OnAuiNotebookPageChanged)

    def OnAuiNotebookPageChanged(self, event):
        tab = event.GetSelection()
        page = self.GetPage(tab)
        db_key = "%d.%d" % self._parent.reference[:2]
        if tab == 1 and page.db_key != db_key:
            page.save_text()
            page.load_text(db_key)
