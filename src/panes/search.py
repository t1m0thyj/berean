"""search.py - search pane class"""

import cPickle
import os
import re
import threading
import time

import wx
from wx import aui, html

from config import BOOK_NAMES, BOOK_RANGES
from html import HtmlWindowBase
from refalize import validate

_ = wx.GetTranslation


def index_version(version, Bible, indexdir):
    dialog = wx.ProgressDialog(_("Indexing %s") % version, "", 68)
    index = {}
    for b in range(1, 67):
        dialog.Update(b - 1, _("Processing %s...") % BOOK_NAMES[b - 1])
        for c in range(1, len(Bible[b])):
            for v in range(1, len(Bible[b][c])):
                verse = re.sub(r"[^\w\s'\-]", r"",
                               Bible[b][c][v].replace("--", " "),
                               flags=re.UNICODE)
                for word in set(verse.split()):  # Remove duplicates
                    index.setdefault(word, []).extend(
                        [chr(i) for i in (b, c, v)])
    dialog.Update(66, _("Saving index..."))
    for word in index:
        index[word] = "".join(index[word])
    with open(os.path.join(indexdir, "%s.idx" % version), 'wb') as fileobj:
        cPickle.dump(index, fileobj, -1)
    dialog.Update(68)
    dialog.Destroy()
    return index


class SearchPane(wx.Panel):
    def __init__(self, parent):
        super(SearchPane, self).__init__(parent)
        self._parent = parent
        self.abbrev_results = parent._app.config. \
            ReadInt("Search/AbbrevResults", 1000)
        self.html = ""
        self.indexes = {}
        self.last_search = (None, -1, -1)  # Text, Number of Verses, Version
        self.options = ("AllWords", "CaseSensitive", "ExactMatch", "Phrase",
                        "RegularExpression")

        indexdir = os.path.join(parent._app.userdatadir, "indexes")
        if not os.path.isdir(indexdir):
            os.mkdir(indexdir)
        for i in range(len(parent.version_list)):
            if not os.path.isfile(os.path.join(indexdir, "%s.idx" %
                                               parent.version_list[i])):
                self.indexes[parent.version_list[i]] = index_version(
                    parent.version_list[i], parent.get_htmlwindow(i).Bible,
                    indexdir)
        if len(self.indexes) < len(parent.version_list):  # If not all loaded
            thread = threading.Thread(target=self.load_indexes)
            thread.start()
            wx.CallAfter(thread.join)

        self.text = wx.ComboBox(self,
                                choices=parent._app.config.
                                ReadList("Search/SearchHistory"),
                                style=wx.TE_PROCESS_ENTER)
        self.text.SetValue(parent._app.config.Read("Search/LastSearch"))
        self.text.Bind(wx.EVT_TEXT_ENTER, self.OnSearch)
        style = aui.AUI_TB_DEFAULT_STYLE
        if wx.VERSION_STRING >= "2.9.5":
            style |= aui.AUI_TB_PLAIN_BACKGROUND
        self.toolbar = aui.AuiToolBar(self, wx.ID_ANY, wx.DefaultPosition,
                                      wx.DefaultSize, style)
        ID_SEARCH = wx.NewId()
        self.toolbar.AddTool(ID_SEARCH, "", parent.get_bitmap("search"),
                             _("Search"))
        self.toolbar.Bind(wx.EVT_MENU, self.OnSearch, id=ID_SEARCH)
        self.toolbar.AddTool(wx.ID_PREVIEW, "", parent.get_bitmap("print"),
                             _("Print Results"))
        self.toolbar.EnableTool(wx.ID_PREVIEW, False)
        self.toolbar.Bind(wx.EVT_MENU, self.OnPrint, id=wx.ID_PREVIEW)
        self.toolbar.Realize()
        self.htmlwindow = HtmlWindowBase(self, parent)
        self.htmlwindow.Bind(html.EVT_HTML_LINK_CLICKED,
                             self.OnHtmlLinkClicked)
        self.htmlwindow.BindContextMenuEvent(self.OnContextMenu)
        self.optionspane = wx.CollapsiblePane(self, label=_("Options"),
                                              style=wx.CP_DEFAULT_STYLE |
                                              wx.CP_NO_TLW_RESIZE)
        optionspane = self.optionspane.GetPane()
        options = (_("All Words in Verse"), _("Case Sensitive"),
                   _("Exact Match Needed"), _("Phrase in Order"),
                   _("Regular Expression"))
        for i, label in enumerate(options):
            setattr(self, self.options[i],
                    wx.CheckBox(optionspane, label=label))
            getattr(self, self.options[i]).SetValue(
                parent._app.config.ReadBool("Search/" + self.options[i],
                                            i == 0))
        if self.RegularExpression.GetValue():
            for option in ("AllWords", "ExactMatch", "Phrase"):
                getattr(self, option).Disable()
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckbox)
        self.version = wx.Choice(optionspane, choices=parent.version_list)
        tab = parent.notebook.GetSelection()
        self.version.SetSelection(int(tab < len(parent.version_list)) and tab)
        ranges = (_("Entire Bible"), _("Old Testament"),
                  _("Pentateuch (Gen - Deut)"), _("History (Josh - Esth)"),
                  _("Wisdom (Job - Song)"), _("Major Prophets (Isa - Dan)"),
                  _("Minor Prophets (Hos - Mal)"), _("New Testament"),
                  _("Gospels & Acts (Matt - Acts)"),
                  _("Paul's Letters (Rom - Heb)"),
                  _("General Letters (Jas - Jude)"), _("Apocalypse (Rev)"),
                  _("Just Current Book"), _("Custom..."))
        self.range_choice = wx.Choice(optionspane, choices=ranges)
        self.range_choice.SetSelection(0)
        self.range_choice.Bind(wx.EVT_CHOICE, self.OnRange)
        self.start = wx.Choice(optionspane, choices=BOOK_NAMES)
        self.start.SetSelection(0)
        self.start.Bind(wx.EVT_CHOICE, self.OnStart)
        self.rangetext = wx.StaticText(optionspane, label=_("to"))
        self.stop = wx.Choice(optionspane, choices=BOOK_NAMES)
        self.stop.SetSelection(65)
        self.stop.Bind(wx.EVT_CHOICE, self.OnStop)
        for item in (self.start, self.rangetext, self.stop):
            item.Disable()
        wx.CallAfter(self.optionspane.Collapse,
                     not parent._app.config.ReadBool("Search/ShowOptions",
                                                     True))
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED,
                  self.OnCollapsiblePaneChanged)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(self.text, 1, wx.ALL ^ wx.RIGHT, 2)
        sizer2.Add(self.toolbar, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(sizer2, 0, wx.EXPAND)
        sizer.Add(self.htmlwindow, 1, wx.EXPAND)
        sizer3 = wx.BoxSizer(wx.VERTICAL)
        for option in self.options:
            sizer3.Add(getattr(self, option), 0, wx.ALL, 2)
        box = wx.StaticBox(optionspane, label=_("Search in"))
        sizer4 = wx.StaticBoxSizer(box, wx.VERTICAL)
        sizer5 = wx.BoxSizer(wx.HORIZONTAL)
        sizer5.Add(self.version, 0, wx.ALL, 2)
        sizer5.Add(self.range_choice, 1, wx.ALL | wx.EXPAND, 2)
        sizer4.Add(sizer5, 1, wx.EXPAND)
        sizer6 = wx.BoxSizer(wx.HORIZONTAL)
        sizer6.Add(self.start, 1, wx.ALL, 2)
        sizer6.Add(self.rangetext, 0,
                   wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
        sizer6.Add(self.stop, 1, wx.ALL, 2)
        sizer4.Add(sizer6, 1, wx.EXPAND)
        sizer3.Add(sizer4, 0, wx.ALL, 2)
        optionspane.SetSizer(sizer3)
        sizer.Add(self.optionspane, 0, wx.ALL | wx.EXPAND, 2)
        self.SetSizer(sizer)

    def load_indexes(self):
        indexdir = os.path.join(self._parent._app.userdatadir, "indexes")
        for version in self._parent.version_list:
            if version not in self.indexes:
                with open(os.path.join(indexdir, "%s.idx" % version),
                          'rb') as fileobj:
                    self.indexes[version] = cPickle.load(fileobj)

    def OnSearch(self, event):
        text = self.text.GetValue().strip()
        if not text:
            return
        elif validate(text, False):
            self._parent.toolbar.verse_entry.SetValue(text)
            self.text.SetValue(self.text.GetString(0))
            self._parent.toolbar.OnGoToVerse(None)
            return
        version_name = self.version.GetStringSelection()
        try:
            self._parent.statusbar.PushStatusText(_("Searching %s...") %
                                                  version_name, 0)
            with wx.BusyCursor():
                sec = time.time()
                results, count = self.get_results(text)
                results.insert(0, _("<font color=\"gray\">%d verses in the %s "
                                    "(%d&nbsp;msec)</font>") %
                               (count, version_name,
                                max(1, (time.time() - sec) * 1000)))
                if count == 0:
                    results.append(_("<p>No verses were found.</p>"))
                self.html = "<html><body><font size=\"%d\">%s</font></body>" \
                    "</html>" % (self._parent.zoom_level, "".join(results))
                self.htmlwindow.SetPage(self.html)
        finally:
            self._parent.statusbar.PopStatusText(0)
        if self.text.FindString(text) == -1:
            self.text.Insert(text, 0)
            if self.text.GetCount() > 10:
                self.text.Delete(10)
        self.toolbar.EnableTool(wx.ID_PREVIEW, count > 0)
        self.toolbar.Refresh(False)
        self.last_search = (text, count, self.version.GetSelection())
        self.htmlwindow.SetFocus()

    def get_results(self, text):
        text = text.replace(u"\u2019", "'")
        Bible = self._parent.get_htmlwindow(self.version.GetSelection()).Bible
        options = {}
        for option in self.options:
            options[option] = getattr(self, option).GetValue()
        flags = re.UNICODE
        if not options["CaseSensitive"]:
            flags |= re.IGNORECASE
        if not options["RegularExpression"]:
            return self.get_indexed_results(re.escape(text), Bible, options,
                                            flags)
        else:
            matches = []
            pattern = re.compile(text, flags)
            for b in range(self.start.GetSelection() + 1,
                           self.stop.GetSelection() + 2):
                for c in range(1, len(Bible[b])):
                    for v in range(1, len(Bible[b][c])):
                        verse = Bible[b][c][v].replace("[", ""). \
                            replace("]", "")
                        if pattern.search(verse):
                            matches.append((b, c, v))
            return (self.format_matches(matches, pattern, options),
                    len(matches))

    def get_indexed_results(self, text, Bible, options, re_flags):
        words = [re.sub(r"[^\w'\-]", r"", word, flags=re.UNICODE) for
                 word in text.split()]
        if options["AllWords"] or options["Phrase"]:
            longest = ""
            for word in words:
                if len(word) >= len(longest):
                    longest = word
            matches = self.get_word_matches(longest, options)
            if not matches:
                return ([], 0)
            if options["Phrase"]:
                pattern = re.compile(r"\b%s\b" % r"\W+".join(words), re_flags)
                matches = [item for item in matches if
                           pattern.search(Bible[item[0]][item[1]][item[2]])]
            elif options["AllWords"]:
                words.remove(longest)
                if options["ExactMatch"]:
                    words = [r"\b%s\b" % word for word in words]
                    longest = r"\b%s\b" % longest
                for word in words:
                    pattern = re.compile(word, re_flags)
                    matches = [item for item in matches if
                               pattern.search(Bible[item[0]][item[1]]
                                              [item[2]])]
                pattern = re.compile(r"(%s)" % "|".join([longest] + words),
                                     re_flags)
        else:
            matches = []
            for word in words:
                matches.extend(self.get_word_matches(word, options))
            if not matches:
                return ([], 0)
            if options["ExactMatch"]:
                pattern = re.compile(r"(%s)" % "|".join([r"\b%s\b" % word for
                                                         word in words]),
                                     re_flags)
                matches = [item for item in matches if
                           pattern.search(Bible[item[0]][item[1]][item[2]])]
            else:
                pattern = re.compile(r"(%s)" % "|".join(words), re_flags)
        start = self.start.GetSelection() + 1
        stop = self.stop.GetSelection() + 1
        matches = [item for item in matches if start <= item[0] <= stop]
        if not matches:
            return ([], 0)
        matches.sort()
        last = matches[-1]
        for i in xrange(len(matches) - 2, -1, -1):  # Remove duplicates
            if matches[i] == last:
                del matches[i]
            else:
                last = matches[i]
        return (self.format_matches(matches, pattern, options), len(matches))

    def get_word_matches(self, word, options, recursive=False):
        index = self.indexes[self.version.GetStringSelection()]
        matches = []
        if not options["CaseSensitive"]:
            cases = [word.lower(), word.capitalize(), word.upper()]
            if "-" in word:  # Elelohe-Israel, not Elelohe-israel
                cases.append(word.title())
            for case in cases:
                if case in index:
                    matches.extend([bytearray(index[case][i:i + 3]) for i in
                                    xrange(0, len(index[case]), 3)])
        elif word in index:
            matches.extend([bytearray(index[word][i:i + 3]) for i in
                            xrange(0, len(index[word]), 3)])
        if not (recursive or options["ExactMatch"] or options["Phrase"]):
            if not options["CaseSensitive"]:
                lower = word.lower()
                for word2 in index:
                    lower2 = word2.lower()
                    if lower in lower2 and lower2 != lower:
                        matches. \
                            extend(self.
                                   get_word_matches(word2,
                                                    {"CaseSensitive":
                                                     options["CaseSensitive"]},
                                                    True))
            else:
                for word2 in index:
                    if word in word2 and word2 != word:
                        matches. \
                            extend(self.
                                   get_word_matches(word2,
                                                    {"CaseSensitive":
                                                     options["CaseSensitive"]},
                                                    True))
        return matches

    def format_matches(self, matches, pattern, options):
        Bible = self._parent.get_htmlwindow(self.version.GetSelection()).Bible
        results = []
        if len(matches) <= self.abbrev_results or self.abbrev_results == -1:
            for b, c, v in matches:
                verse = Bible[b][c][v]
                offset = 0
                if not options["RegularExpression"]:
                    for match in pattern.finditer(verse):
                        start, end = match.span(0)
                        verse = verse[:start + offset] + "<b>" + \
                            verse[start + offset:end + offset] + "</b>" + \
                            verse[end + offset:]
                        offset += 7
                else:
                    for match in pattern.finditer(verse.replace("[", "").
                                                  replace("]", "")):
                        start, end = match.span(0)
                        offset += verse.count("[", offset, start + offset) + \
                            verse.count("]", offset, start + offset)
                        offset2 = offset + verse.count("[", start + offset,
                                                       end + offset) + \
                            verse.count("]", start + offset, end + offset)
                        verse = verse[:start + offset] + "<b>" + \
                            verse[start + offset:end + offset2] + "</b>" + \
                            verse[end + offset2:]
                        offset += 7
                results.append("<p><a href=\"%d.%d.%d\">%s %d:%d</a><br>%s"
                               "</p>" % (b, c, v, BOOK_NAMES[b - 1], c, v,
                                         verse.replace("[", "<i>").
                                         replace("]", "</i>")))
        else:
            results.append("<br>")
            i = last_book = 0
            while i < len(matches):
                b, c, v = matches[i]
                verses = 1
                while (i + verses < len(matches) and
                        matches[i + verses] == (b, c, v + verses)):
                    verses += 1
                if verses == 1:
                    results.append(", <a href=\"%d.%d.%d\">%d:%d</a>" %
                                   (b, c, v, c, v))
                else:
                    results.append(", <a href=\"%d.%d.%d\">%d:%d-%d</a>" %
                                   (b, c, v, c, v, v + verses - 1))
                if b > last_book:
                    results[-1] = "<br><b>%s</b>" % \
                        BOOK_NAMES[b - 1].upper() + results[-1][1:]
                    last_book = b
                i += verses
        return results

    def OnPrint(self, event):
        header = _("<div align=\"center\"><font size=\"+1\"><b>Search Results "
                   "for \"%s\" (%d verses in the %s)</b></font></div>") % \
            (self.last_search[0], self.last_search[1],
             self.version.GetString(self.last_search[2]))
        text = self.html[:self.html.index("<font color=\"gray\">")] + \
            header + self.html[self.html.index("</font>") + 7:]
        if wx.VERSION_STRING >= "2.9.1":
            self._parent.printing.SetName(_("Search Results"))
        if event.GetId() == wx.ID_PRINT:
            self._parent.printing.PrintText(text)
        else:
            self._parent.printing.PreviewText(text)

    def OnHtmlLinkClicked(self, event):
        if (self._parent.notebook.GetSelection() != self.last_search[2] and
                not wx.GetKeyState(wx.WXK_CONTROL)):
            self._parent.notebook.SetSelection(self.last_search[2])
        self._parent.load_chapter(*[int(i) for i in
                                    event.GetLinkInfo().GetHref().split(".")])

    def OnContextMenu(self, event):
        if not self.html:
            return
        menu = wx.Menu()
        if self.htmlwindow.SelectionToText():
            menu.Append(wx.ID_COPY, _("&Copy"))
        menu.Append(wx.ID_SELECTALL, _("Select &All"))
        menu.AppendSeparator()
        print_item = menu.Append(wx.ID_PRINT, _("&Print..."))
        self.Bind(wx.EVT_MENU, self.OnPrint, print_item)
        preview_item = menu.Append(wx.ID_PREVIEW, _("P&rint Preview"))
        self.Bind(wx.EVT_MENU, self.OnPrint, preview_item)
        self.htmlwindow.PopupMenu(menu)

    def OnCheckbox(self, event):
        checkbox = event.GetEventObject()
        checked = event.IsChecked()
        if ((checkbox == self.AllWords or checkbox == self.ExactMatch) and
                checked and self.Phrase.IsChecked()):
            self.Phrase.SetValue(False)
        elif checkbox == self.RegularExpression:
            for option in ("AllWords", "ExactMatch", "Phrase"):
                getattr(self, option).Enable(not checked)

    def OnRange(self, event):
        selection = event.GetSelection()
        if selection < len(BOOK_RANGES) + 1:
            if selection < len(BOOK_RANGES):
                self.start.SetSelection(BOOK_RANGES[selection][0] - 1)
                self.stop.SetSelection(BOOK_RANGES[selection][1] - 1)
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
        start = event.GetSelection()
        if start > self.stop.GetSelection():
            self.stop.SetSelection(start)

    def OnStop(self, event):
        stop = event.GetSelection()
        if stop < self.start.GetSelection():
            self.start.SetSelection(stop)

    def OnCollapsiblePaneChanged(self, event):
        self.Layout()
