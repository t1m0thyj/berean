"""search.py - search functions and pane class for Berean"""

import cPickle
import os
import re

import wx
from wx import aui, html

import dialogs.index as indexer
from htmlwin import BaseHtmlWindow

_ = wx.GetTranslation

def refalize(reference):
    groups = re.match(r'((?:[1-3]\s?|i{1,3}\s)?[A-Za-z]+)\s*(\d+)?\W*(\d+)?', reference.lstrip(), flags=re.IGNORECASE).groups()
    abbrev = groups[0].replace(" ", "").lower()
    if abbrev not in abbrevs:
        for i in range(len(books)):
            if books[i].startswith(abbrev):
                book = i + 1
                break
    else:
        book = abbrevs[abbrev]
    if groups[2]:
        return (book, int(groups[1]), int(groups[2]))
    elif not groups[1]:
        return (book, 1, -1)
    elif book not in (31, 57, 63, 64, 65):
        return (book, int(groups[1]), -1)
    else:
        return (book, 1, int(groups[1]))


def refalize2(references, Bible):
    references = filter(None, [reference.lstrip() for reference in re.split(r'[,;\n]', references)])
    pattern = re.compile(r'((?:[1-3]\s?|i{1,3}\s)?[A-Za-z]+)?\s*(\d+)?\W*(\d+)?', flags=re.IGNORECASE)
    style = 1   # 0 = full reference, 1 = reference with no verse, 2 = reference with no chapter
    for i in range(len(references)):
        if "-" in references[i]:
            first, last = references[i].split("-")
        else:
            first = references[i]
            last = None
        match = pattern.match(first)
        groups = match.groups()
        if groups[0] and (groups[0].lower() not in ("c", "ch", "chap", "v", "ver", "vv")):
            abbrev = groups[0].replace(" ", "").lower()
            if abbrev not in abbrevs:
                for j in range(len(books)):
                    if books[j].startswith(abbrev):
                        book = j + 1
                        break
            else:
                book = abbrevs[abbrev]
        else:
            book = references[i - 1][1][0]
        if groups[2]:
            chapter = int(groups[1])
            verse = int(groups[2])
            style = 0
        elif book in (31, 57, 63, 64, 65):
            chapter = 1
            verse = int(groups[1])
            style = 2
        elif style != 1 and ((not groups[0]) or groups[0].lower() in ("v", "ver", "vv")):
            chapter = references[i - 1][1][1]
            verse = int(groups[1])
            style = 2
        else:
            chapter = int(groups[1])
            verse = 1
            style = 1
        first = (book, chapter, verse)
        if last:
            match2 = pattern.match(last.lstrip())
            if match2:
                groups2 = match2.groups()
                if groups2[0] and (groups2[0].lower() not in ("c", "ch", "chap", "v", "ver", "vv")):
                    abbrev = groups2[0].replace(" ", "").lower()
                    if abbrev not in abbrevs:
                        for j in range(len(books)):
                            if books[j].startswith(abbrev):
                                book = j + 1
                                break
                    else:
                        book = abbrevs[abbrev]
                else:
                    book = first[0]
                if groups2[1] and groups2[2]:
                    chapter = int(groups2[1])
                    verse = int(groups2[2])
                    style = 0
                elif groups2[1] and not groups2[2]:
                    if book in (31, 57, 63, 64, 65):
                        chapter = 1
                        verse = int(groups2[1])
                    elif style != 1:
                        chapter = first[1]
                        verse = int(groups2[1])
                    else:
                        chapter = int(groups2[1])
                        verse = len(Bible[book][chapter]) - 1
                last = (book, chapter, verse)
            else:
                last = None
        elif re.search(r'\W*ff', references[i][match.end(len(groups)):], flags=re.IGNORECASE):  # Recognize 'ff'
            if style != 1:
                last = (book, chapter, len(Bible[book][chapter]) - 1)
            else:
                last = (book, len(Bible[book]) - 1, len(Bible[book][-1]) - 1)
        if not last:
            last = first
            if style == 1:
                last = (last[0], last[1], len(Bible[last[0]][last[1]]) - 1)
        references[i] = (first, last)
    return references


def validate(reference, numbers=False):
    reference = reference.strip()
    if reference[-1].isdigit():
        return True
    if not numbers:
        book = reference.replace(" ", "").lower()
        if book not in abbrevs:
            for i in range(len(books)):
                if books[i].startswith(book):
                    return True
        else:
            return True
    return False


class SearchPane(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self._parent = parent

        self.frequent = []
        self.html = ""
        self.indexes = []
        self.lastversion = None
        self.options = ("AllWords", "CaseSensitive", "ExactMatch", "Phrase", "RegularExpression")
        self.ranges = ((0, 65), (0, 38), (0, 4), (5, 16), (17, 21), (22, 26), (27, 38), (39, 65), (39, 43), (44, 56), (57, 64), (65, 65))
        self.states = {}
        self.verses = 0

        indexdir = os.path.join(parent._app.userdatadir, "indexes")
        if not os.path.isdir(indexdir):
            os.mkdir(indexdir)
        for i in range(len(parent.versions)):
            filename = os.path.join(indexdir, "%s.idx" % parent.versions[i])
            if os.path.isfile(filename):
                index = open(filename, 'rb')
                self.indexes.append(cPickle.load(index))
                index.close()
            else:
                self.indexes.append(indexer.index(parent._app, parent.GetBrowser(i).Bible, parent.versions[i]))
        for option in ("AllWords", "ExactMatch", "Phrase"):
            if parent._app.settings[option] >= wx.CHK_UNDETERMINED:
                state = parent._app.settings[option] - wx.CHK_UNDETERMINED
                parent._app.settings[option] -= state
            else:
                state = parent._app.settings[option]
            self.states[option] = state

        self.text = wx.ComboBox(self, -1, choices=parent._app.settings["SearchHistory"], style=wx.TE_PROCESS_ENTER)
        self.text.SetValue(parent._app.settings["LastSearch"])
        style = aui.AUI_TB_DEFAULT_STYLE
        if wx.VERSION_STRING >= "2.9.5.0":
            style |= aui.AUI_TB_PLAIN_BACKGROUND
        self.toolbar = aui.AuiToolBar(self, -1, (-1, -1), (-1, -1), style)
        self.ID_SEARCH = wx.NewId()
        self.toolbar.AddTool(self.ID_SEARCH, "", parent.Bitmap("search"), _("Search"))
        self.toolbar.AddTool(wx.ID_PRINT, "", parent.Bitmap("print"), _("Print Search Results"))
        self.toolbar.SetToolDropDown(wx.ID_PRINT, True)
        self.toolbar.EnableTool(wx.ID_PRINT, False)
        self.toolbar.Realize()
        self.results = BaseHtmlWindow(self)
        self.optionspane = wx.CollapsiblePane(self, -1, _("Options"), style=wx.CP_DEFAULT_STYLE | wx.CP_NO_TLW_RESIZE)
        optionspane = self.optionspane.GetPane()
        self.AllWords = wx.CheckBox(optionspane, -1, _("All Words in Verse"), style=wx.CHK_3STATE)
        self.CaseSensitive = wx.CheckBox(optionspane, -1, _("Case Sensitive"))
        self.ExactMatch = wx.CheckBox(optionspane, -1, _("Exact Match Needed"), style=wx.CHK_3STATE)
        self.Phrase = wx.CheckBox(optionspane, -1, _("Phrase in Order"), style=wx.CHK_3STATE)
        self.RegularExpression = wx.CheckBox(optionspane, -1, _("Regular Expression"))
        for option in self.options:
            getattr(self, option).Set3StateValue(parent._app.settings[option])
        self.version = wx.Choice(optionspane, -1, choices=parent.versions)
        self.rangechoice = wx.Choice(optionspane, -1, choices=ranges)
        self.rangechoice.SetSelection(0)
        self.start = wx.Choice(optionspane, -1, choices=parent.books)
        self.start.SetSelection(0)
        self.rangetext = wx.StaticText(optionspane, -1, _("to"))
        self.stop = wx.Choice(optionspane, -1, choices=parent.books)
        self.stop.SetSelection(65)
        for item in (self.start, self.rangetext, self.stop):
            item.Disable()

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

        self.optionspane.Collapse(not parent._app.settings["OptionsPane"])
        if parent._app.settings["ActiveTab"] < len(parent.versions):
            self.version.SetSelection(parent._app.settings["ActiveTab"])
        else:
            self.version.SetSelection(0)

        self.text.Bind(wx.EVT_TEXT_ENTER, self.OnSearch)
        self.toolbar.Bind(wx.EVT_MENU, self.OnSearch, id=self.ID_SEARCH)
        for id in (wx.ID_PRINT, wx.ID_PAGE_SETUP, wx.ID_PREVIEW):
            self.Bind(wx.EVT_MENU, self.OnPrintMenu, id=id)
        self.toolbar.Bind(aui.EVT_AUITOOLBAR_TOOL_DROPDOWN, self.OnPrintDropdown, id=wx.ID_PRINT)
        self.results.Bind(html.EVT_HTML_LINK_CLICKED, self.OnHtmlLinkClicked)
        self.results.Bind(wx.EVT_RIGHT_UP, self.OnContextMenu)  # EVT_CONTEXT_MENU doesn't work for wxHtmlWindow in 2.8
        for option in ("AllWords", "ExactMatch", "Phrase", "RegularExpression"):
            getattr(self, option).Bind(wx.EVT_CHECKBOX, self.OnCheckbox)
        self.rangechoice.Bind(wx.EVT_CHOICE, self.OnRange)
        self.start.Bind(wx.EVT_CHOICE, self.OnStart)
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnCollapsiblePaneChanged)

    def OnSearch(self, event):
        text = self.text.GetValue()
        if not len(text):
            return
        elif validate(text, True):
            self.text.SetValue(self.text.GetString(0))
            self._parent.toolbar.reference.SetValue(text)
            self._parent.toolbar.OnSearch(None)
            return
        wx.BeginBusyCursor()
        millis = wx.GetLocalTimeMillis()
        results, number = self.FindText(text)
        if len(results):
            results.insert(0, _("<font color=gray>%d verses in the %s (%d&nbsp;msec)</font>") % (number, self.lastversion, max(1, wx.GetLocalTimeMillis() - millis)))
        else:
            results.append(_("<font color=gray>0 verses in the %s (%d&nbsp;msec)</font><p></p><b>Suggestions:</b><ul><li> Make your search less specific.<li> Edit the search options.<li> Search in a different version.</ul>") % (self.lastversion, max(1, wx.GetLocalTimeMillis() - millis)))
        self.html = "<html><body><font size=%d>%s</font></body></html>" % (self._parent.zoom, "".join(results))
        self.results.SetPage(self.html)
        wx.EndBusyCursor()
        if text not in self.text.GetStrings():
            self.text.Insert(text, 0)
            if self.text.GetCount() > 10:
                self.text.Delete(10)
        self.toolbar.EnableTool(wx.ID_PRINT, True)
        self.toolbar.Refresh(False)
        self.verses = number
        wx.CallAfter(self.results.SetFocus)

    def FindText(self, text):
        options = [getattr(self, option).Get3StateValue() == wx.CHK_CHECKED for option in self.options]
        flags = re.UNICODE
        if not options[1]:  # not Case Sensitive
            flags |= re.IGNORECASE
        self.lastversion = self.version.GetStringSelection()
        browser = self._parent.GetBrowser(self._parent.versions.index(self.lastversion))
        start = self.start.GetSelection() + 1
        stop = self.stop.GetSelection() + 1
        if not options[4]:  # not Regular Expression
            words = [re.compile(r'\W', re.UNICODE).sub(r'', word) for word in text.split()]
            if options[0] or options[3]:    # All Words or Phrase
                longest = ""
                for word in words:
                    if len(word) >= len(longest):
                        longest = word
                matches = self.FindWord(longest, options)
                if options[0]:  # All Words
                    words.remove(longest)
                    if options[2]:  # Exact Match
                        words = [r'\b%s\b' % word for word in words]
                        longest = r'\b%s\b' % longest
                    for word in words:
                        pattern = re.compile(word, flags)
                        matches = filter(lambda item: pattern.search(browser.Bible[item[0]][item[1]][item[2]]), matches)
                    words.insert(0, longest)
                    pattern = re.compile(r'(%s)' % "|".join(words), flags)
                elif options[3]:    # Phrase
                    pattern = re.compile(r'\[?\b%s\b\]?' % r'\W+'.join(words), flags)
                    matches = filter(lambda item: pattern.search(browser.Bible[item[0]][item[1]][item[2]]), matches)
            else:
                matches = []
                for word in words:
                    matches += self.FindWord(word, options)
                if options[2]:  # Exact Match
                    pattern = re.compile(r'(%s)' % "|".join([r'\b%s\b' % word for word in words]), flags)
                    matches = filter(lambda item: pattern.search(browser.Bible[item[0]][item[1]][item[2]]), matches)
                else:
                    pattern = re.compile(r'(%s)' % "|".join(words), flags)
            matches = filter(lambda item: start <= item[0] <= stop, matches)
            matches.sort()
            i = 0
            previous = None
            while i < len(matches):
                if matches[i] == previous:  # Avoid showing the same verse multiple times
                    matches.pop(i)
                    continue
                previous = matches[i]
                i += 1
        else:
            matches = []
            pattern = re.compile(text, flags)
            for b in range(start, stop + 1):
                for c in range(1, len(browser.Bible[b])):
                    for v in range(1, len(browser.Bible[b][c])):
                        verse = browser.Bible[b][c][v]
                        if "<div" in verse:
                            verse = verse[:verse.index("<div")]
                        if pattern.search(verse):
                            matches.append([b, c, v])
        i = 0
        results = []
        if self._parent._app.settings["AbbrevSearchResults"]:
            books = self._parent.abbrevs
        else:
            books = self._parent.books
        if len(matches) <= 1000:
            while i < len(matches):
                b, c, v = matches[i]
                verses = []
                while i < len(matches):
                    if matches[i] == [b, c, v + len(verses)]:
                        verse = browser.Bible[matches[i][0]][matches[i][1]][matches[i][2]]
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
                    results.append("<p><a href='%d.%d.%d'>%s %d:%d</a><br />%s</p>" % (b, c, v, books[b - 1], c, v, verses[0]))
                else:
                    for j in range(len(verses)):
                        verses[j] = "<font size=-1><a href='%d.%d.%d'>%d</a>&nbsp;</font>%s" % (b, c, v + j, v + j, verses[j])
                    results.append("<p><a href='%d.%d.%d'>%s %d:%d-%d</a><br />%s</p>" % (b, c, v, books[b - 1], c, v, v + len(verses) - 1, " ".join(verses)))
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
                    results.append(", <a href='%d.%d.%d'>%d:%d</a>" % (b, c, v, c, v))
                else:
                    results.append(", <a href='%d.%d.%d'>%d:%d-%d</a>" % (b, c, v, c, v, v + verses - 1))
                if b != lastbook:
                    results[-1] = "<br /><b>%s</b>%s" % (books[b - 1].upper(), results[-1][1:])
                lastbook = b
            results.insert(0, "<br />")
        return (results, len(matches))

    def FindWord(self, word, options):
        index = self.indexes[self._parent.versions.index(self.lastversion)]
        matches = []
        if not options[1]:  # not Case Sensitive
            cases = [word.lower(), word.capitalize(), word.upper()]
            if "-" in word: # Elelohe-Israel, not Elelohe-israel
                cases.append("-".join([item.capitalize() for item in word.split("-")]))
            for case in cases:
                if case in index:
                    matches += [[ord(char) - 32 for char in index[case][i:i + 3]] for i in range(0, len(index[case]), 3)]
        elif word in index:
            matches += [[ord(char) - 32 for char in index[word][i:i + 3]] for i in range(0, len(index[word]), 3)]
        if not (options[2] or options[3]):  # not Exact Match or Phrase
            if not options[1]:  # not Case Sensitive
                lower = word.lower()
                for word2 in index:
                    lower2 = word2.lower()
                    if lower in lower2 and lower != lower2:
                        matches += self.FindWord(word2, [False, options[1], True, False, False])
            else:
                for word2 in index:
                    if word in word2 and word != word2:
                        matches += self.FindWord(word2, [False, options[1], True, False, False])
        return matches

    def OnPrintMenu(self, event):
        id = event.GetId()
        if id != wx.ID_PAGE_SETUP:
            header = _("<div align=center><b>Search results for \"%s\" in the %s (%d&nbsp;verses)</b></div>") % (self.text.GetValue(), self.lastversion, self.verses)
            text = self.html[:12] + header + self.html[self.html.index("</font>") + 7:]
            if wx.VERSION_STRING >= "2.8.11.0":
                self._parent.printer.SetName(_("Search Results"))
            if id == wx.ID_PRINT:
                self._parent.printer.PrintText(text)
            elif id == wx.ID_PREVIEW:
                self._parent.printer.PreviewText(text)
        else:
            self._parent.printer.PageSetup()

    def OnPrintDropdown(self, event):
        if event.IsDropDownClicked():
            self.toolbar.SetToolSticky(wx.ID_PRINT, True)
            menu = wx.Menu()
            menu.Append(wx.ID_PRINT, _("&Print..."))
            menu.Append(wx.ID_PAGE_SETUP, _("Page Set&up..."))
            menu.Append(wx.ID_PREVIEW, _("Print Previe&w..."))
            self.toolbar.PopupMenu(menu, self._parent.main_toolbar.GetPopupPos(self.toolbar, wx.ID_PRINT))
            self.toolbar.SetToolSticky(wx.ID_PRINT, False)

    def OnHtmlLinkClicked(self, event):
        if self._parent.notebook.GetPageText(self._parent.notebook.GetSelection()) != self.lastversion:
            self._parent.notebook.SetSelection(self._parent.versions.index(self.lastversion))
        self._parent.LoadChapter(*[int(item) for item in event.GetLinkInfo().GetHref().split(".")])

    def OnKeyDown(self, event):
        if wx.MOD_CONTROL & event.GetModifiers() and event.GetKeyCode() == ord("A"):
            event.GetEventObject().SelectAll()
        event.Skip()

    def OnContextMenu(self, event):
        if not len(self.html):
            return
        menu = wx.Menu()
        selection = self.results.SelectionToText()
        if len(selection):
            menu.Append(wx.ID_COPY, _("&Copy\tCtrl+C"))
        menu.Append(wx.ID_SELECTALL, _("Select &All\tCtrl+A"))
        self.Bind(wx.EVT_MENU, self.results.OnSelectAll, id=wx.ID_SELECTALL)
        menu.AppendSeparator()
        menu.Append(wx.ID_PRINT, _("&Print...\tCtrl+P"))
        menu.Append(wx.ID_PREVIEW, _("P&rint Preview...\tCtrl+Alt+P"))
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
                        self.states[option] = state
                    checkbox.Set3StateValue(wx.CHK_UNDETERMINED)
            else:
                if self.states["Phrase"] == wx.CHK_CHECKED:
                    for option in ("AllWords", "ExactMatch"):
                        getattr(self, option).Set3StateValue(wx.CHK_UNDETERMINED)
                else:
                    for option in ("AllWords", "ExactMatch"):
                        getattr(self, option).Set3StateValue(self.states[option])
                self.Phrase.Set3StateValue(self.states["Phrase"])
        elif ph == wx.CHK_CHECKED or re:
            if checkbox == self.AllWords:
                self.AllWords.Set3StateValue(wx.CHK_CHECKED)
                self.ExactMatch.Set3StateValue(self.states["ExactMatch"])
                self.Phrase.Set3StateValue(wx.CHK_UNCHECKED)
            elif checkbox == self.ExactMatch:
                self.AllWords.Set3StateValue(self.states["AllWords"])
                self.ExactMatch.Set3StateValue(wx.CHK_CHECKED)
                if ph == wx.CHK_CHECKED:
                    self.Phrase.Set3StateValue(wx.CHK_UNCHECKED)
                elif re:
                    self.Phrase.Set3StateValue(self.states["Phrase"])
            elif checkbox == self.Phrase:
                for option in ("AllWords", "ExactMatch"):
                    checkbox = getattr(self, option)
                    state = checkbox.Get3StateValue()
                    if state != wx.CHK_UNDETERMINED:
                        self.states[option] = state
                    checkbox.Set3StateValue(wx.CHK_UNDETERMINED)
                if re:
                    self.Phrase.Set3StateValue(wx.CHK_CHECKED)
            if re:
                self.RegularExpression.SetValue(False)
        elif checkbox == self.Phrase:
            for option in ("AllWords", "ExactMatch"):
                getattr(self, option).Set3StateValue(self.states[option])

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

abbrevs = {"jdg": 7, "1kgs": 11, "2kgs": 12, "ca": 22, "can": 22, "cant": 22,
    "canti": 22, "cantic": 22, "canticl": 22, "canticle": 22, "canticles": 22,
    "mk": 41, "mrk": 41, "lk": 42, "jh": 43, "jhn": 43, "php": 50, "phm": 57,
    "jas": 59, "1jh": 62, "1jhn": 62, "2jh": 63, "2jhn": 63, "3jh": 64,
    "3jhn": 64, "jde": 65}
ranges = map(_, ["Entire Bible", "Old Testament", "Pentateuch (Gen - Deut)",
    "History (Josh - Esth)", "Wisdom (Job - Song)", "Major Prophets (Isa - Dan)",
    "Minor Prophets (Hos - Mal)", "New Testament",
    "Gospels & Acts (Matt - Acts)", "Paul's Letters (Rom - Heb)",
    "General Letters (Jas - Jude)", "Apocalypse (Rev)", "Just Current Book",
    "Custom..."])
