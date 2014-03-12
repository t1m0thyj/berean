"""parallel.py - parallel window classes"""

import wx

from config import *
from html import BaseChapterWindow

_ = wx.GetTranslation


class ParallelWindow(BaseChapterWindow):
    def __init__(self, parent, version_list):
        super(ParallelWindow, self).__init__(parent, parent.GetGrandParent())
        self._parent = parent
        self.set_description(version_list)

    def set_description(self, version_list):
        if len(version_list) <= 2:
            self.description = _(" and ").join(version_list)
        else:
            self.description = _("%s, and %s") % (", ".join(version_list[:-1]),
                version_list[-1])

    def get_html(self, book, chapter, verse=-1):
        Bibles = []
        lines = ["<tr>"]
        version_list = []
        for i in range(len(self._parent.choices)):
            selection = self._parent.choices[i].GetSelection()
            if i > 0:
                if selection == 0:
                    continue
                selection -= 1
            Bibles.append(self._frame.notebook.GetPage(selection).Bible)
            version_list.append(self._frame.version_list[selection])
            heading = "<font size=\"+1\"><b>%s %d (%s)</b></font>" % \
                (Bibles[-1][book][0], chapter, version_list[-1])
            if not Bibles[-1][book][chapter][0]:
                lines.append("  <td align=center>%s</td>" % heading)
            else:
                lines += ["  <td align=center>", "  %s<br/>" % heading,
                    "  " + Bibles[-1][book][chapter][0].replace("[",
                    "<i>").replace("]", "</i>"), "  </td>"]
        lines.append("</tr>")
        for i in range(1, max([len(Bible[book][chapter]) for Bible in Bibles])):
            lines.append("<tr>")
            for j in range(len(Bibles)):
                line = ["  <td>"]
                if i < len(Bibles[j][book][chapter]) and \
                        len(Bibles[j][book][chapter][i]):
                    line.append("<font size=\"-1\">%d&nbsp;</font>%s" %
                        (i, Bibles[j][book][chapter][i].replace("[", "<i>").
                        replace("]", "</i>")))
                    if i == verse:
                        line.insert(1, "<b>")
                        line.append("</b>")
                if j == 0:
                    line.insert(1, "<a name=\"%d\">" % i)
                    line.append("</a>")
                lines.append("".join(line) + "</td>")
            lines.append("</tr>")
        self.set_description(version_list)
        title = "%s %d (%s)" % (BOOK_NAMES[book - 1], chapter, _("Parallel"))
        return HTML % (title, self._frame.zoom_level, "\n      ".join(lines))

    def load_chapter(self, book, chapter, verse=-1):
        self.SetPage(self.get_html(book, chapter, verse))
        self._frame.statusbar.SetStatusText("%s %d (%s)" %
            (BOOK_NAMES[book - 1], chapter, self.description), 0)
        if wx.VERSION_STRING >= "2.9.4.0":
            self._frame.notebook.SetPageToolTip(len(self._frame.version_list),
                self.description)
        if verse > 1:
            wx.CallAfter(self.ScrollToAnchor, str(verse))
            self.current_verse = -1


HTML = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <title>%s</title>
</head>
<body>
  <font size=\"%d\">
  <table valign=top cellspacing=2 cellpadding=0>
    <tbody>
      %s
    </tbody>
  </table>
  </font>
</body>
</html>
"""


class ChoiceDropTarget(wx.DropTarget):
    def __init__(self, panel, index):
        super(ChoiceDropTarget, self).__init__()
        self._panel = panel
        self.index = index
        self.data = wx.CustomDataObject("ParallelPanel")
        self.SetDataObject(self.data)

    def OnDragOver(self, x, y, default):
        if (self.index > 0 and
                self._panel.choices[self.index].GetSelection() == 0):
            return wx.DragNone
        return default

    def OnData(self, x, y, default):
        self.GetData()
        index = int(self.data.GetData())
        if index != self.index:
            version1 = self._panel.choices[index].GetStringSelection()
            version2 = self._panel.choices[self.index].GetStringSelection()
            self._panel.choices[index].SetStringSelection(version2)
            self._panel.choices[self.index].SetStringSelection(version1)
            self._panel.htmlwindow.load_chapter(*self._panel._frame.reference)
        return default


class ParallelPanel(wx.Panel):
    def __init__(self, parent):
        super(ParallelPanel, self).__init__(parent, -1)
        self._frame = parent.GetParent()
        self.choice_data = wx.CustomDataObject("ParallelPanel")

        self.choices = []
        version_list = self._frame._app.config.ReadList("ParallelVersions",
            self._frame.version_list[:2])
        for i in range(len(self._frame.version_list)):
            self.choices.append(wx.Choice(self, -1,
                choices=self._frame.version_list))
            if i > 0:
                self.choices[i].Insert(_("(none)"), 0)
            if i < len(version_list):
                self.choices[i].SetStringSelection(version_list[i])
            else:
                self.choices[i].SetSelection(0)
                if i > len(version_list):
                    self.choices[i].Disable()
            self.choices[i].SetDropTarget(ChoiceDropTarget(self, i))
            self.choices[i].Bind(wx.EVT_MIDDLE_UP, self.OnChoiceMiddleUp)
            self.choices[i].Bind(wx.EVT_RIGHT_DOWN, self.OnChoiceRightDown)
        self.Bind(wx.EVT_CHOICE, self.OnChoice)
        self.htmlwindow = ParallelWindow(self, version_list)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        for choice in self.choices:
            sizer2.Add(choice, 1, wx.ALL | wx.EXPAND, 1)
        sizer.Add(sizer2, 0, wx.ALL | wx.EXPAND, 1)
        sizer.Add(self.htmlwindow, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def select(self, index, selection):
        if index > 0 and selection == 0:
            for i in range(index, len(self.choices)):
                selection = self.choices[i].GetSelection()
                if selection == 0:
                    continue
                if i > index:
                    self.choices[i - 1].SetSelection(selection)
                self.choices[i].SetSelection(0)
                if (i < len(self.choices) - 1 and
                        self.choices[i + 1].GetSelection() == 0):
                    self.choices[i + 1].Disable()
        elif index < len(self.choices) - 1:
            self.choices[index + 1].Enable()
        self.htmlwindow.load_chapter(*self._frame.reference)
        wx.CallAfter(self.htmlwindow.SetFocus)

    def OnChoiceMiddleUp(self, event):
        index = self.choices.index(event.GetEventObject())
        if index > 0:
            self.select(index, 0)

    def OnChoiceRightDown(self, event):
        choice = event.GetEventObject()
        selection = choice.GetSelection()
        if selection > 0 or self.choices.index(choice) == 0:
            choice.SetFocus()
            self.choice_data.SetData(str(self.choices.index(choice)))
            source = wx.DropSource(self)
            source.SetData(self.choice_data)
            source.DoDragDrop(wx.Drag_DefaultMove)
            wx.CallAfter(self.htmlwindow.SetFocus)

    def OnChoice(self, event):
        self.select(self.choices.index(event.GetEventObject()),
            event.GetSelection())
