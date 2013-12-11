"""
berean.py - main script for Berean
Copyright (C) 2013 Timothy Johnson <timothysw@objectmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import codecs
import ConfigParser
import getopt
import os
import sys

import wx

import debug
import parent

_version = debug._version = "1.5.0"
# Make ConfigParser work with Unicode
ConfigParser.str = lambda value: value.encode("utf_8")

class FileConfig(ConfigParser.RawConfigParser):
    def __init__(self):
        ConfigParser.RawConfigParser.__init__(self)

        self.optionxform = str  # Don't make option names lowercase

    def getunicode(self, section, option):
        return self.get(section, option).decode("utf_8")

    def getlist(self, section, option=None):
        if option:
            section = "%s\\%s" % (section, option)
        option = "Item1"
        sequence = []
        i = 1
        while self.has_option(section, option):
            sequence.append(self.getunicode(section, option))
            i += 1
            option = "Item%d" % i
        return sequence

    def setlist(self, section, option, value):
        if option:
            section = "%s\\%s" % (section, option)
        if not self.has_section(section):
            self.add_section(section)
        else:
            for option in self.options(section):
                self.remove_option(section, option)
        for i in range(len(value)):
            self.set(section, "Item%d" % (i + 1), value[i])


class Berean(wx.App):
    def OnInit(self):
        wx.App.__init__(self)

        self.SetAppName("Berean")
        options, args = getopt.getopt(sys.argv[1:], "",
            ["datadir=", "systemtray"])
        options = dict(options)

        if not hasattr(sys, "frozen"):
            self.cwd = os.path.dirname(__file__)
        else:
            self.cwd = os.path.dirname(sys.argv[0])
        if "--datadir" in options:
            self.userdatadir = options["--datadir"]
            if not os.path.isabs(self.userdatadir):
                self.userdatadir = os.path.join(self.cwd, self.userdatadir)
        elif os.path.isfile(os.path.join(self.cwd, "portable.ini")):
            self.userdatadir = self.cwd
        elif wx.Platform != "__WXGTK__":
            self.userdatadir = os.path.join(wx.StandardPaths.Get(). \
                GetUserDataDir(), "Berean")
        else:
            self.userdatadir = os.path.join(wx.StandardPaths.Get(). \
                GetUserDataDir(), ".berean")
        if not os.path.isdir(self.userdatadir):
            os.makedirs(self.userdatadir)

        systemtray = "--systemtray" in options
        if not systemtray:
            splash_screen = wx.SplashScreen(wx.Bitmap(os.path.join(self.cwd,
                "images", "splash.png"), wx.BITMAP_TYPE_PNG),
                wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_NO_TIMEOUT, 0, None,
                -1, style=wx.BORDER_SIMPLE | wx.FRAME_NO_TASKBAR)
            self.Yield()

        self.LoadSettings()
        self.locale = wx.Locale(wx.LANGUAGE_ENGLISH_US)
        localedir = os.path.join(self.cwd, "locale")
        self.locale.AddCatalogLookupPathPrefix(localedir)
        language = self.locale.GetCanonicalName()
        if os.path.isfile(os.path.join(localedir, language, "LC_MESSAGES", "berean.mo")):
            self.locale.AddCatalog(language)
        self.version = _version

        self.frame = parent.MainFrame(self)
        self.SetTopWindow(self.frame)
        self.frame.Show()
        if not systemtray:
            splash_screen.Destroy()
        else:
            self.frame.Iconize()

        return True

    def LoadSettings(self):
        self.config = FileConfig()
        filename = os.path.join(self.userdatadir, "berean.ini")
        if os.path.isfile(filename):
            ini = open(filename, 'r')
            ini.seek(ini.readline().index("[")) # Seek past UTF8 BOM
            self.config.readfp(ini)
            ini.close()
        display_size = wx.GetDisplaySize()
        best_size = (int(display_size[0] * 0.8), int(display_size[1] * 0.8))
        self.settings = {"WindowPos": wx.DefaultPosition,
            "WindowSize": best_size, "MaximizeState": False,
            "MinimizeToTray": False, "SelectedBook": 1, "SelectedChapter": 1,
            "ZoomLevel": 3, "ActiveVerse": -1, "ActiveTab": 0,
            "LastReference": "", "ActiveNotes": 0,
            "VersionList": ["KJV", "WEB"], "ParallelVersions": ["KJV", "WEB"],
            "FavoritesList": [], "ReferenceHistory": [], "ChapterHistory": [],
            "AbbrevSearchResults": False, "LastSearch": "",
            "OptionsPane": True, "AllWords": True, "CaseSensitive": False,
            "ExactMatch": False, "Phrase": False, "RegularExpression": False,
            "SearchHistory": [], "LastVerses": ""}
        if self.config.has_option("Main", "WindowPos"):
            self.settings["WindowPos"] = map(int, self.config.getunicode("Main", "WindowPos").split(","))
        if self.config.has_option("Main", "WindowSize"):
            self.settings["WindowSize"] = map(int, self.config.getunicode("Main", "WindowSize").split(","))
        if not (0 - self.settings["WindowSize"][0] < self.settings["WindowPos"][0] < display_size[0] and 0 - self.settings["WindowSize"][1] < self.settings["WindowPos"][1] < display_size[1]):
            self.settings["WindowPos"] = wx.DefaultPosition
            self.settings["WindowSize"] = best_size
        for option in ("MaximizeState", "MinimizeToTray", "ActiveNotes"):
            if self.config.has_option("Main", option):
                self.settings[option] = self.config.getboolean("Main", option)
        for option in ("SelectedBook", "SelectedChapter", "ZoomLevel", "ActiveVerse", "ActiveTab"):
            if self.config.has_option("Main", option):
                self.settings[option] = self.config.getint("Main", option)
        if self.config.has_option("Main", "LastReference"):
            self.settings["LastReference"] = self.config.getunicode("Main", "LastReference")
        if self.config.has_section("VersionList"):
            self.settings["VersionList"] = self.config.getlist("VersionList")
        if self.config.has_section("ParallelVersions"):
            self.settings["ParallelVersions"] = self.config.getlist("ParallelVersions")
        if self.config.has_section("FavoritesList"):
            self.settings["FavoritesList"] = self.config.getlist("FavoritesList")
        if self.config.has_section("ReferenceHistory"):
            self.settings["ReferenceHistory"] = self.config.getlist("ReferenceHistory")
        if self.config.has_section("ChapterHistory"):
            self.settings["ChapterHistory"] = self.config.getlist("ChapterHistory")
        if self.config.has_option("Search", "AbbrevSearchResults"):
            self.settings["AbbrevSearchResults"] = self.config.getboolean("Search", "AbbrevSearchResults")
        if self.config.has_option("Search", "LastSearch"):
            self.settings["LastSearch"] = self.config.getunicode("Search", "LastSearch")
        if self.config.has_option("Search", "OptionsPane"):
            self.settings["OptionsPane"] = self.config.getboolean("Search", "OptionsPane")
        for option in ("AllWords", "CaseSensitive", "ExactMatch", "Phrase", "RegularExpression"):
            if self.config.has_option("Search", option):
                self.settings[option] = self.config.getint("Search", option)
        if self.config.has_option("Search", "LastVerses"):
            self.settings["LastVerses"] = self.config.getunicode("Search", "LastVerses")
        if self.config.has_section("Search\\SearchHistory"):
            self.settings["SearchHistory"] = self.config.getlist("Search", "SearchHistory")

    def SaveSettings(self):
        if not self.config.has_section("Main"):
            self.config.add_section("Main")
        self.config.set("Main", "WindowPos", ",".join(map(str, self.frame.rect.GetPosition())))
        self.config.set("Main", "WindowSize", ",".join(map(str, self.frame.rect.GetSize())))
        self.config.set("Main", "MaximizeState", str(self.frame.IsMaximized()))
        self.config.set("Main", "MinimizeToTray", str(self.settings["MinimizeToTray"]))
        self.config.set("Main", "SelectedBook", str(self.frame.reference[0]))
        self.config.set("Main", "SelectedChapter", str(self.frame.reference[1]))
        self.config.set("Main", "ZoomLevel", str(self.frame.zoom))
        self.config.set("Main", "ActiveVerse", str(self.frame.reference[2]))
        self.config.set("Main", "ActiveTab", str(self.frame.notebook.GetSelection()))
        self.config.set("Main", "LastReference", self.frame.main_toolbar.reference.GetValue())
        self.config.set("Main", "ActiveNotes", str(self.frame.notes.GetSelection()))
        self.config.setlist("VersionList", None, self.frame.versions)
        parallel = []
        if hasattr(self.frame, "parallel") and len(self.frame.versions) > 1:
            for i, choice in enumerate(self.frame.parallel._parent.choices):
                if choice.GetSelection() > 0 or i == 0:
                    parallel.append(choice.GetStringSelection())
        self.config.setlist("ParallelVersions", None, parallel)
        self.config.setlist("FavoritesList", None, self.frame.menubar.Favorites.favorites)
        self.config.setlist("ReferenceHistory", None, self.frame.main_toolbar.reference.GetStrings())
        self.config.setlist("ChapterHistory", None, self.frame.main_toolbar.history)
        if not self.config.has_section("Search"):
            self.config.add_section("Search")
        self.config.set("Search", "AbbrevSearchResults", str(self.settings["AbbrevSearchResults"]))
        self.config.setlist("Search", "SearchHistory", self.frame.search.text.GetStrings())
        self.config.set("Search", "LastSearch", self.frame.search.text.GetValue())
        self.config.set("Search", "OptionsPane", str(self.frame.search.optionspane.IsExpanded()))
        for option in self.frame.search.options:
            state = getattr(self.frame.search, option).Get3StateValue()
            if state == wx.CHK_UNDETERMINED:
                state += self.frame.search.states[option]
            self.config.set("Search", option, str(state))
        self.config.set("Search", "LastVerses", self.settings["LastVerses"])
        ini = open(os.path.join(self.userdatadir, "berean.ini"), 'w')
        ini.write(codecs.BOM_UTF8)
        self.config.write(ini)
        ini.close()

    def Exit(self):
        del self.locale
        self.frame.Destroy()
        self.ExitMainLoop()


def main():
    sys.excepthook = debug.OnError
    app = Berean()
    app.MainLoop()

if __name__ == "__main__":
    main()
