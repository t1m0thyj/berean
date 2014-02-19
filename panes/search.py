"""search.py - search pane class"""

import cPickle
import os
import re

import wx
from wx import aui, html

from html import BaseHtmlWindow
from globals import *
from refalize import validate

_ = wx.GetTranslation


def index_version(Bible, version, indexdir):
    dialog = wx.ProgressDialog(_("Indexing %s") % version, "", 70)
    index = {}
    for b in range(1, len(Bible)):
        dialog.Update(b - 1, _("Processing %s...") % BOOK_NAMES[b - 1])
        for c in range(1, len(Bible[b])):
            for v in range(1, len(Bible[b][c])):
                verse = Bible[b][c][v]
                if "<div" in verse:
                    verse = verse[:verse.index("<div")]
                verse = re.sub(r'[^\w\s\-\']', r'', verse, flags=re.UNICODE)
                for word in set(verse.split()): # Remove duplicates
                    if word not in index:
                        index[word] = []
                    index[word] += [chr(i) for i in (b, c, v)]
    dialog.Update(66, _("Saving index..."))
    for word in index:
        index[word] = "".join(index[word])
    dialog.Update(68)
    fileobj = open(os.path.join(indexdir, "%s.idx" % version), 'wb')
    cPickle.dump(index, fileobj, -1)
    fileobj.close()
    dialog.Destroy()
    return index


class SearchPane(wx.Panel):
    def __init__(self, parent):
        super(SearchPane, self).__init__(parent, -1)
        self._parent = parent
        self.checkbox_states = {}
        self.html = ""
        self.indexes = []
        self.last_version = -1
        self.options = ("AllWords", "CaseSensitive", "ExactMatch", "Phrase",
            "RegularExpression")
        self.ranges = ((0, 65), (0, 38), (0, 4), (5, 16), (17, 21), (22, 26),
            (27, 38), (39, 65), (39, 43), (44, 56), (57, 64), (65, 65))
        self.verses = 0

        indexdir = os.path.join(parent._app.userdatadir, "indexes")
        if not os.path.isdir(indexdir):
            os.mkdir(indexdir)
        for i in range(len(parent.version_list)):
            filename = os.path.join(indexdir, "%s.idx" % parent.version_list[i])
            if os.path.isfile(filename):
                index = open(filename, 'rb')
                self.indexes.append(cPickle.load(index))
                index.close()
            else:
                self.indexes.append(index_version(parent.get_htmlwindow(i).
                    Bible, parent.version_list[i], indexdir))
        for option in ("AllWords", "ExactMatch", "Phrase"):
            state = parent._app.config.ReadInt("Search/" + option,
                int(option == "AllWords"))
            if state >= wx.CHK_UNDETERMINED:
                state -= wx.CHK_UNDETERMINED
                parent._app.settings[option] -= state
            self.checkbox_states[option] = state

        self.text = wx.ComboBox(self, -1,
            choices=parent._app.config.ReadList("Search/SearchHistory"),
            style=wx.TE_PROCESS_ENTER)
        self.text.SetValue(parent._app.config.Read("Search/LastSearch"))
        self.text.Bind(wx.EVT_TEXT_ENTER, self.OnSearch)
        style = aui.AUI_TB_DEFAULT_STYLE
        if wx.VERSION_STRING >= "2.9.5.0":
            style |= aui.AUI_TB_PLAIN_BACKGROUND
        self.toolbar = aui.AuiToolBar(self, -1, (-1, -1), (-1, -1), style)
        search_item = self.toolbar.AddTool(-1, "", parent.get_bitmap("search"),
            _("Search"))
        self.toolbar.Bind(wx.EVT_MENU, self.OnSearch, search_item)
        self.toolbar.AddTool(wx.ID_PRINT, "", parent.get_bitmap("print"),
            _("Print Search Results"))
        self.toolbar.EnableTool(wx.ID_PRINT, False)
        self.toolbar.Bind(wx.EVT_MENU, self.OnPrint, id=wx.ID_PRINT)
        self.toolbar.Realize()
        self.results = BaseHtmlWindow(self)
        self.results.Bind(html.EVT_HTML_LINK_CLICKED, self.OnHtmlLinkClicked)
        if wx.VERSION_STRING >= "2.9.0.0":
            self.results.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        else:   # wxHtmlWindow doesn't generate EVT_CONTEXT_MENU in 2.8
            self.results.Bind(wx.EVT_RIGHT_UP, self.OnContextMenu)
        self.optionspane = wx.CollapsiblePane(self, -1, _("Options"),
            style=wx.CP_DEFAULT_STYLE | wx.CP_NO_TLW_RESIZE)
        optionspane = self.optionspane.GetPane()
        self.AllWords = wx.CheckBox(optionspane, -1, _("All Words in Verse"),
            style=wx.CHK_3STATE)
        self.CaseSensitive = wx.CheckBox(optionspane, -1, _("Case Sensitive"))
        self.ExactMatch = wx.CheckBox(optionspane, -1, _("Exact Match Needed"),
            style=wx.CHK_3STATE)
        self.Phrase = wx.CheckBox(optionspane, -1, _("Phrase in Order"),
            style=wx.CHK_3STATE)
        self.RegularExpression = wx.CheckBox(optionspane, -1,
            _("Regular Expression"))
        for option in self.options:
            checkbox = getattr(self, option)
            checkbox.Set3StateValue(parent._app.config.ReadInt(
                "Search/" + option, int(option == "AllWords")))
            checkbox.Bind(wx.EVT_CHECKBOX, self.OnCheckbox)
        self.version = wx.Choice(optionspane, -1, choices=parent.version_list)
        selection = parent.notebook.GetSelection()
        if selection < len(parent.version_list):
            self.version.SetSelection(selection)
        else:
            self.version.SetSelection(0)
        ranges = (_("Entire Bible"), _("Old Testament"),
            _("Pentateuch (Gen - Deut)"), _("History (Josh - Esth)"),
            _("Wisdom (Job - Song)"), _("Major Prophets (Isa - Dan)"),
            _("Minor Prophets (Hos - Mal)"), _("New Testament"),
            _("Gospels & Acts (Matt - Acts)"), _("Paul's Letters (Rom - Heb)"),
            _("General Letters (Jas - Jude)"), _("Apocalypse (Rev)"),
            _("Just Current Book"), _("Custom..."))
        self.rangechoice = wx.Choice(optionspane, -1, choices=ranges)
        self.rangechoice.SetSelection(0)
        self.rangechoice.Bind(wx.EVT_CHOICE, self.OnRange)
        self.start = wx.Choice(optionspane, -1, choices=BOOK_NAMES)
        self.start.SetSelection(0)
        self.start.Bind(wx.EVT_CHOICE, self.OnStart)
        self.rangetext = wx.StaticText(optionspane, -1, _("to"))
        self.stop = wx.Choice(optionspane, -1, choices=BOOK_NAMES)
        self.stop.SetSelection(65)
        for item in (self.start, self.rangetext, self.stop):
            item.Disable()
        self.optionspane.Collapse(
            not parent._app.config.ReadBool("Search/ShowOptions", True))
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnCollapsiblePaneChanged)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(self.text, 1, wx.ALL ^ wx.RIGHT, 2)
        sizer2.Add(self.toolbar, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(sizer2, 0, wx.EXPAND)
        sizer.Add(self.results, 1, wx.EXPAND)
        sizer3 = wx.BoxSizer(wx.VERTICAL)
        for option in self.options:
            sizer3.Add(getattr(self, option), 1, wx.ALL, 2)
        box = wx.StaticBox(optionspane, -1, _("Search in"))
        sizer4 = wx.StaticBoxSizer(box, wx.VERTICAL)
        sizer5 = wx.BoxSizer(wx.HORIZONTAL)
        sizer5.Add(self.version, 0, wx.ALL | wx.EXPAND, 2)
        sizer5.Add(self.rangechoice, 1, wx.ALL | wx.EXPAND, 2)
        sizer4.Add(sizer5, 1, wx.EXPAND)
        sizer6 = wx.BoxSizer(wx.HORIZONTAL)
        sizer6.Add(self.start, 1, wx.ALL | wx.EXPAND, 2)
        sizer6.Add(self.rangetext, 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
        sizer6.Add(self.stop, 1, wx.ALL | wx.EXPAND, 2)
        sizer4.Add(sizer6, 1, wx.EXPAND)
        sizer3.Add(sizer4, 0, wx.ALL | wx.EXPAND, 2)
        optionspane.SetSizer(sizer3)
        sizer.Add(self.optionspane, 0, wx.ALL | wx.EXPAND, 2)
        self.SetSizer(sizer)

    def OnSearch(self, event):
        text = self.text.GetValue()
        if not len(text):
            return
        elif validate(text, False):
            self._parent.toolbar.reference.SetValue(text)
            self.text.SetValue(self.text.GetString(0))
            self._parent.toolbar.OnSearch(None)
            return
        wx.BeginBusyCursor()
        msec = wx.GetLocalTimeMillis()
        results, number = self.find_text(text)
        version = self.version.GetStringSelection()
        msec = max(1, wx.GetLocalTimeMillis() - msec)
        if number > 0:
            results.insert(0, _("<font color=gray>%d verses in the %s " \
                "(%d&nbsp;msec)</font>") % (number, version, msec))
        else:
            results.append(_("<font color=gray>0 verses in the %s " \
                "(%d&nbsp;msec)</font><p></p><b>Suggestions:</b><ul><li> " \
                "Make your search less specific.<li> Edit the search " \
                "options.<li> Search in a different version.</ul>") %
                (version, msec))
        self.html = "<html><body><font size=\"%d\">%s</font></body></html>" % \
            (self._parent.zoom_level, "".join(results))
        self.results.SetPage(self.html)
        wx.EndBusyCursor()
        if text not in self.text.GetStrings():
            self.text.Insert(text, 0)
            if self.text.GetCount() > 10:
                self.text.Delete(10)
        self.toolbar.EnableTool(wx.ID_PRINT, number > 0)
        self.toolbar.Refresh(False)
        self.verses = number
        wx.CallAfter(self.results.SetFocus)

    def find_text(self, text):
        options = [getattr(self, option).Get3StateValue() == wx.CHK_CHECKED
            for option in self.options]
        flags = re.UNICODE
        if not options[1]:  # not Case Sensitive
            flags |= re.IGNORECASE
        self.last_version = self.version.GetSelection()
        Bible = self._parent.get_htmlwindow(self.last_version).Bible
        start = self.start.GetSelection() + 1
        stop = self.stop.GetSelection() + 1
        if not options[4]:  # not Regular Expression
            words = [re.sub(r'[^\w\-\']', r'', word, flags=re.UNICODE) for
                word in text.split()]
            if options[0] or options[3]:    # All Words or Phrase
                longest = ""
                for word in words:
                    if len(word) >= len(longest):
                        longest = word
                matches = self.find_word(longest, options)
                if options[0]:  # All Words
                    words.remove(longest)
                    if options[2]:  # Exact Match
                        words = [r'\b%s\b' % word for word in words]
                        longest = r'\b%s\b' % longest
                    for word in words:
                        pattern = re.compile(word, flags)
                        matches = filter(lambda item: pattern.search(Bible[item[0]][item[1]][item[2]]), matches)
                    words.insert(0, longest)
                    pattern = re.compile(r'(%s)' % "|".join(words), flags)
                elif options[3]:    # Phrase
                    pattern = re.compile(r'\[?\b%s\b\]?' % r'\W+'.join(words), flags)
                    matches = filter(lambda item: pattern.search(Bible[item[0]][item[1]][item[2]]), matches)
            else:
                matches = []
                for word in words:
                    matches += self.find_word(word, options)
                if options[2]:  # Exact Match
                    pattern = re.compile(r'(%s)' % "|".join([r'\b%s\b' % word for word in words]), flags)
                    matches = filter(lambda item: pattern.search(Bible[item[0]][item[1]][item[2]]), matches)
                else:
                    pattern = re.compile(r'(%s)' % "|".join(words), flags)
            matches = filter(lambda match: start <= match[0] <= stop, matches)
            matches.sort()
            i = 0
            previous = None
            while i < len(matches):
                if matches[i] == previous:  # Don't repeat the same verse
                    matches.pop(i)
                    continue
                previous = matches[i]
                i += 1
        else:
            matches = []
            pattern = re.compile(text, flags)
            for b in range(start, stop + 1):
                for c in range(1, len(Bible[b])):
                    for v in range(1, len(Bible[b][c])):
                        verse = Bible[b][c][v]
                        if "<div" in verse:
                            verse = verse[:verse.index("<div")]
                        if pattern.search(verse):
                            matches.append([b, c, v])
        i = 0
        results = []
        if len(matches) <= 1000:
            while i < len(matches):
                b, c, v = matches[i]
                verses = []
                while i < len(matches):
                    if matches[i] == [b, c, v + len(verses)]:
                        verse = Bible[matches[i][0]][matches[i][1]][matches[i][2]]
                        if "<div" in verse:
                            verse = verse[:verse.index("<div")]
                        offset = 0
                        for match in pattern.finditer(verse):
                            start, end = match.span(0)
                            verse = verse[:start + offset] + "<b>" + verse[start + offset:end + offset] + "</b>" + verse[end + offset:]
                            offset += 7
                        verses.append(verse.replace("[", "<i>").replace("]", "</i>"))
                        i += 1
                    else:
                        break
                if len(verses) == 1:
                    results.append("<p><a href=\"%d.%d.%d\">%s %d:%d</a><br />%s</p>" % (b, c, v, BOOK_NAMES[b - 1], c, v, verses[0]))
                else:
                    for j in range(len(verses)):
                        verses[j] = "<font size=\"-1\"><a href=\"%d.%d.%d\">%d</a>&nbsp;</font>%s" % (b, c, v + j, v + j, verses[j])
                    results.append("<p><a href=\"%d.%d.%d\">%s %d:%d-%d</a><br />%s</p>" % (b, c, v, BOOK_NAMES[b - 1], c, v, v + len(verses) - 1, " ".join(verses)))
        else:
            lastbook = 0
            while i < len(matches):
                b, c, v = matches[i]
                verses = 0
                while i < len(matches):
                    if matches[i] == [b, c, v + verses]:
                        verses += 1
                        i += 1
                    else:
                        break
                if verses == 1:
                    results.append(", <a href=\"%d.%d.%d\">%d:%d</a>" % (b, c, v, c, v))
                else:
                    results.append(", <a href=\"%d.%d.%d\">%d:%d-%d</a>" % (b, c, v, c, v, v + verses - 1))
                if b != lastbook:
                    results[-1] = "<br /><b>%s</b>%s" % (BOOK_NAMES[b - 1].upper(), results[-1][1:])
                lastbook = b
            results.insert(0, "<br />")
        return (results, len(matches))

    def find_word(self, word, options):
        index = self.indexes[self.last_version]
        matches = []
        if not options[1]:  # not Case Sensitive
            cases = [word.lower(), word.capitalize(), word.upper()]
            if "-" in word: # Elelohe-Israel, not Elelohe-israel
                cases.append(word.title())
            for case in cases:
                if case in index:
                    matches += [[ord(char) for char in index[case][i:i + 3]] for i in range(0, len(index[case]), 3)]
        elif word in index:
            matches += [[ord(char) for char in index[word][i:i + 3]] for i in range(0, len(index[word]), 3)]
        if not (options[2] or options[3]):  # not Exact Match or Phrase
            if not options[1]:  # not Case Sensitive
                lower = word.lower()
                for word2 in index:
                    lower2 = word2.lower()
                    if lower in lower2 and lower != lower2:
                        matches += self.find_word(word2, [False, options[1], True, False, False])
            else:
                for word2 in index:
                    if word in word2 and word != word2:
                        matches += self.find_word(word2, [False, options[1], True, False, False])
        return matches

    def OnPrint(self, event):
        header = _("<div align=center><b>Search results for \"%s\" in the %s (%d&nbsp;verses)</b></div>") % (self.text.GetValue(), self.version.GetString(self.last_version), self.verses)
        text = self.html[:12] + header + self.html[self.html.index("</font>") + 7:]
        if wx.VERSION_STRING >= "2.8.11.0" and wx.VERSION_STRING != "2.9.0.0":
            self._parent.printing.SetName(_("Search Results"))
        if event.GetId() == wx.ID_PRINT:
            self._parent.printing.PrintText(text)
        else:
            self._parent.printing.PreviewText(text)

    def OnHtmlLinkClicked(self, event):
        if self._parent.notebook.GetSelection() != self.last_version:
            self._parent.notebook.SetSelection(self.last_version)
        self._parent.load_chapter(*map(int,
            event.GetLinkInfo().GetHref().split(".")))

    def OnContextMenu(self, event):
        if not len(self.html):
            return
        menu = wx.Menu()
        if len(self.results.SelectionToText()):
            menu.Append(wx.ID_COPY, _("&Copy\tCtrl+C"))
        menu.Append(wx.ID_SELECTALL, _("Select &All\tCtrl+A"))
        menu.AppendSeparator()
        print_item = menu.Append(wx.ID_PRINT, _("&Print...\tCtrl+P"))
        self.Bind(wx.EVT_MENU, self.OnPrint, print_item)
        preview_item = menu.Append(wx.ID_PREVIEW,
            _("P&rint Preview...\tCtrl+Alt+P"))
        self.Bind(wx.EVT_MENU, self.OnPrint, preview_item)
        self.results.PopupMenu(menu)

    def OnCheckbox(self, event):
        checkbox = event.GetEventObject()
        ph, re = self.Phrase.Get3StateValue(), self.RegularExpression.GetValue()
        if checkbox == self.RegularExpression:
            if event.IsChecked():
                for option in ("AllWords", "ExactMatch", "Phrase"):
                    checkbox = getattr(self, option)
                    state = checkbox.Get3StateValue()
                    if state != wx.CHK_UNDETERMINED:
                        self.checkbox_states[option] = state
                    checkbox.Set3StateValue(wx.CHK_UNDETERMINED)
            else:
                if self.checkbox_states["Phrase"] == wx.CHK_CHECKED:
                    for option in ("AllWords", "ExactMatch"):
                        getattr(self, option).Set3StateValue(wx.CHK_UNDETERMINED)
                else:
                    for option in ("AllWords", "ExactMatch"):
                        getattr(self, option).Set3StateValue(self.checkbox_states[option])
                self.Phrase.Set3StateValue(self.checkbox_states["Phrase"])
        elif ph == wx.CHK_CHECKED or re:
            if checkbox == self.AllWords:
                self.AllWords.Set3StateValue(wx.CHK_CHECKED)
                self.ExactMatch.Set3StateValue(self.checkbox_states["ExactMatch"])
                self.Phrase.Set3StateValue(wx.CHK_UNCHECKED)
            elif checkbox == self.ExactMatch:
                self.AllWords.Set3StateValue(self.checkbox_states["AllWords"])
                self.ExactMatch.Set3StateValue(wx.CHK_CHECKED)
                if ph == wx.CHK_CHECKED:
                    self.Phrase.Set3StateValue(wx.CHK_UNCHECKED)
                elif re:
                    self.Phrase.Set3StateValue(self.checkbox_states["Phrase"])
            elif checkbox == self.Phrase:
                for option in ("AllWords", "ExactMatch"):
                    checkbox = getattr(self, option)
                    state = checkbox.Get3StateValue()
                    if state != wx.CHK_UNDETERMINED:
                        self.checkbox_states[option] = state
                    checkbox.Set3StateValue(wx.CHK_UNDETERMINED)
                if re:
                    self.Phrase.Set3StateValue(wx.CHK_CHECKED)
            if re:
                self.RegularExpression.SetValue(False)
        elif checkbox == self.Phrase:
            for option in ("AllWords", "ExactMatch"):
                getattr(self, option).Set3StateValue(self.checkbox_states[option])

    def OnRange(self, event):
        selection = event.GetSelection()
        if selection < len(self.ranges) + 1:
            if selection < len(self.ranges):
                self.start.SetSelection(self.ranges[selection][0])
                self.stop.SetSelection(self.ranges[selection][1])
            else:
                self.start.SetSelection(self._parent.reference[0] - 1)
                self.stop.SetSelection(self._parent.reference[0] - 1)
            if self.start.IsEnabled():
                for item in (self.start, self.rangetext, self.stop):
                    item.Disable()
        else:
            for item in (self.start, self.rangetext, self.stop):
                item.Enable()

    def OnStart(self, event):
        self.stop.SetSelection(event.GetSelection())

    def OnCollapsiblePaneChanged(self, event):
        self.Layout()
