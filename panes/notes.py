"""notes.py - notes pane class"""

import cPickle
import cStringIO
import os.path

import wx
from wx import aui, richtext

from config import *

_ = wx.GetTranslation


class BookChapterVerseSelector(aui.AuiToolBar):
    def __init__(self, parent, reference):
        super(BookChapterVerseSelector, self).__init__(parent, -1, (-1, -1),
            (-1, -1), aui.AUI_TB_DEFAULT_STYLE | aui.AUI_TB_OVERFLOW)
        self._parent = parent
        self.book = wx.Choice(self, -1, choices=BOOK_NAMES)
        self.AddControl(self.book)
        self.chapter = wx.Choice(self, -1, size=(60, -1))
        self.AddControl(self.chapter)
        self.verse = wx.Choice(self, -1, size=(60, -1))
        self.AddControl(self.verse)
        self.Bind(wx.EVT_CHOICE, self.OnChoice)
        self.AddTool(wx.ID_DELETE, "", parent._frame.get_bitmap("delete"),
            _("Delete"))
        self.Bind(wx.EVT_MENU, self.OnDelete, id=wx.ID_DELETE)
        self.Realize()
        self.set_reference(*reference)

    def set_reference(self, book, chapter, verse=-1, update_choices=True):
        if update_choices:
            self.book.SetSelection(book - 1)
            self.chapter.SetItems([str(i) for i in range(1,
                BOOK_LENGTHS[book - 1] + 1)])
            self.chapter.SetSelection(chapter - 1)
            self.verse.SetItems(["--"] + [str(i) for i in range(1,
                CHAPTER_LENGTHS[book - 1][chapter - 1] + 1)])
            self.verse.SetSelection(max(0, verse))
        key = "%d.%d.%d" % (book, chapter, verse)
        self.EnableTool(wx.ID_DELETE, key in self._parent.notes_dict)
        self.Refresh(False)

    def get_reference(self):
        verse = self.verse.GetSelection()
        if verse == 0:
            verse = -1
        return (self.book.GetSelection() + 1, self.chapter.GetSelection() + 1,
            verse)

    def OnChoice(self, event):
        verse = self.verse.GetSelection()
        if verse == 0:
            verse = -1
        self._parent.load_text(self.book.GetSelection() + 1,
            self.chapter.GetSelection() + 1, verse)

    def OnDelete(self, event):
        delete = wx.MessageBox(_("Are you sure you want to delete your " \
            "notes on this passage?"), _("Berean"),
            wx.ICON_QUESTION | wx.YES_NO)
        if delete == wx.YES:
            key = "%d.%d.%d" % self.get_reference()
            if key in self._parent.notes_dict:
                self._parent.notes_dict.pop(key)
            self._parent.editor.Clear()
            self.EnableTool(wx.ID_DELETE, False)
            self.Refresh(False)


class TopicSelector(aui.AuiToolBar):
    def __init__(self, parent):
        super(TopicSelector, self).__init__(parent, -1, (-1, -1), (-1, -1),
            aui.AUI_TB_DEFAULT_STYLE | aui.AUI_TB_OVERFLOW)
        self._parent = parent
        self.topic_list = parent._frame._app.config.ReadList("Notes/TopicList")
        self.topic = wx.Choice(self, -1, choices=self.topic_list)
        self.AddControl(self.topic)
        self.AddTool(wx.ID_NEW, "", parent._frame.get_bitmap("new"), _("New"))
        self.AddTool(-1, "", parent._frame.get_bitmap("rename"), _("Rename"))
        self.AddTool(wx.ID_DELETE, "", parent._frame.get_bitmap("delete"),
            _("Delete"))
        self.Realize()


class NotesPage(wx.Panel):
    def __init__(self, parent, name):
        super(NotesPage, self).__init__(parent, -1)
        self._frame = parent.GetParent()
        self.name = name
        filename = os.path.join(self._frame._app.userdatadir, "%s.not" % name)
        if not os.path.isfile(filename):
            with open(filename, 'wb') as notes:
                cPickle.dump({}, notes, -1)
            self.notes_dict = {}
        else:
            with open(filename, 'rb') as notes:
                self.notes_dict = cPickle.load(notes)

        ##self.selector = BookChapterVerseSelector(self, self._frame.reference)
        self.toolbar = aui.AuiToolBar(self, -1, (-1, -1), (-1, -1),
            aui.AUI_TB_DEFAULT_STYLE | aui.AUI_TB_OVERFLOW)
        self.toolbar.AddTool(wx.ID_SAVE, "", self._frame.get_bitmap("save"),
            _("Save (Ctrl+S)"))
        self.toolbar.Bind(wx.EVT_MENU, self.OnSave, id=wx.ID_SAVE)
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
        self.font_name = wx.Choice(self.toolbar, -1,
            choices=self._frame.facenames)
        self.font_name.SetSelection(0)
        self.toolbar.AddControl(self.font_name)
        self.font_name.Bind(wx.EVT_CHOICE, self.OnFontName)
        if '__WXGTK__' not in wx.PlatformInfo:
            self.font_size = wx.ComboBox(self.toolbar, -1, choices=FONT_SIZES,
                style=wx.TE_PROCESS_ENTER)
        else:
            self.font_size = wx.ComboBox(self.toolbar, -1, choices=FONT_SIZES,
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
        self.ID_HIGHLIGHTING = wx.NewId()
        self.toolbar.AddTool(self.ID_HIGHLIGHTING, "",
            self._frame.get_bitmap("highlighting"), _("Highlighting"))
        self.Bind(wx.EVT_MENU, self.OnHighlighting, id=self.ID_HIGHLIGHTING)
        self.ID_FONT_COLOR = wx.NewId()
        self.toolbar.AddTool(self.ID_FONT_COLOR, "",
            self._frame.get_bitmap("font-color"), _("Font Color"))
        self.Bind(wx.EVT_MENU, self.OnFontColor, id=self.ID_FONT_COLOR)
        self.toolbar.Realize()
        self.SetAcceleratorTable(wx.AcceleratorTable([
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

        self.editor = richtext.RichTextCtrl(self, -1, style=wx.BORDER_NONE |
            wx.WANTS_CHARS)
        self.editor.SetFont(wx.FFont(self._frame.default_font["size"],
            wx.DEFAULT, face=self._frame.default_font["normal_face"]))
        self.editor.Bind(wx.EVT_CHAR, self.OnChar)
        self.editor.Bind(wx.EVT_KEY_UP, self.OnModified)
        self.editor.Bind(wx.EVT_LEFT_UP, self.OnModified)

        sizer = wx.BoxSizer(wx.VERTICAL)
        ##sizer.Add(self.selector, 0)
        sizer.Add(self.toolbar, 0)
        sizer.Add(self.editor, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.load_text(self._frame.reference[0], self._frame.reference[1])

    def load_text(self, book, chapter):##, verse=-1):
        key = "%d.%d" % (book, chapter)
        ##key = "%d.%d.%d" % (book, chapter, verse)
        if key in self.notes_dict:
            stream = cStringIO.StringIO(self.notes_dict[key])
            richtext.RichTextXMLHandler().LoadStream(self.editor.GetBuffer(),
                stream)
            self.editor.Refresh()
        else:
            self.editor.SetValue("")
        ##self.selector.set_reference(book, chapter, verse,
        ##    self.selector.get_reference() != (book, chapter, verse))
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
        self.toolbar.ToggleTool(wx.ID_UNDERLINE,
            self.editor.IsSelectionUnderlined())
        for alignment in ("LEFT", "CENTER", "RIGHT"):
            if self.editor.IsSelectionAligned(getattr(wx,
                    "TEXT_ALIGNMENT_%s" % alignment)):
                self.toolbar.ToggleTool(getattr(wx, "ID_JUSTIFY_%s" % \
                    alignment), True)
                break
        self.toolbar.Refresh(False)

    def save_text(self):
        key = "%d.%d" % (self._frame.reference[0], self._frame.reference[1])
        ##key = "%d.%d.%d" % self.selector.get_reference()
        if not self.editor.IsEmpty():
            stream = cStringIO.StringIO()
            richtext.RichTextXMLHandler().SaveStream(self.editor.GetBuffer(),
                stream)
            self.notes_dict[key] = stream.getvalue()
        elif key in self.notes_dict:
            self.notes_dict.pop(key)

    def OnSave(self, event):
        self.save_text()
        with open(os.path.join(self._frame._app.userdatadir,
                "%s.not" % self.name), 'wb') as notes:
            cPickle.dump(self.notes_dict, notes, -1)

    def OnPrint(self, event):
        if wx.VERSION_STRING >= "2.8.11.0" and wx.VERSION_STRING != "2.9.0.0":
            ##self._frame.printing.SetName(_(self.name))
            self._frame.printing.SetName(self.name)
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
            self.BeginStyle(style)
        else:
            self.editor.SetStyle(self.editor.GetSelectionRange(), style)

    def OnFontSize(self, event):
        style = richtext.RichTextAttr()
        style.SetFlags(wx.TEXT_ATTR_FONT_SIZE)
        style.SetFontSize(int(self.font_size.GetValue()))
        if not self.editor.HasSelection():
            self.BeginStyle(style)
        else:
            self.editor.SetStyle(self.editor.GetSelectionRange(), style)

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
    def __init__(self, parent):
        super(NotesPane, self).__init__(parent, -1, style=wx.BORDER_NONE |
            aui.AUI_NB_TOP | aui.AUI_NB_SCROLL_BUTTONS)
        self.AddPage(NotesPage(self, "Study Notes"), _("Study Notes"))
        self.AddPage(NotesPage(self, "Topic Notes"), _("Topic Notes"))
        self.SetSelection(parent._app.config.ReadInt("Notes/ActiveNotesTab"))
