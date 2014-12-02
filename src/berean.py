#!/usr/bin/env python
"""berean.py - main script for Berean
Copyright (C) 2014 Timothy Johnson <timothysw@objectmail.com>

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

import getopt
import os
import sys

import wx

import debug
import mainwindow


class FileConfig(wx.FileConfig):
    def __init__(self, app):
        super(FileConfig, self).__init__(
            localFilename=os.path.join(app.userdatadir, "berean.ini"))
        self._app = app
        self.SetRecordDefaults(True)

    def ReadList(self, key, defaultVal=[]):
        if not self.HasGroup(key):
            return defaultVal
        i = 1
        value = []
        while self.HasEntry("%s/Item%d" % (key, i)):
            value.append(self.Read("%s/Item%d" % (key, i)))
            i += 1
        return value

    def save(self):
        self.SetPath("/Main")
        frame = self._app.frame
        self.Write("WindowPosition", ",".join(str(i) for i in
                                              frame.rect.GetPosition()))
        self.Write("WindowSize", ",".join(str(i) for i in
                                          frame.rect.GetSize()))
        self.WriteBool("IsMaximized", frame.IsMaximized())
        self.WriteInt("CurrentBook", frame.reference[0])
        self.WriteInt("CurrentChapter", frame.reference[1])
        self.WriteInt("CurrentVerse", frame.reference[2])
        self.Write("HtmlFontFace", frame.default_font["normal_face"])
        self.WriteInt("HtmlFontSize", frame.default_font["size"])
        self.WriteInt("ZoomLevel", frame.zoom_level)
        self.Write("LastVerse", frame.toolbar.verse_entry.GetValue())
        self.WriteInt("ActiveVersionTab", frame.notebook.GetSelection())
        self.WriteBool("MinimizeToTray", frame.minimize_to_tray)
        self.WriteList("../VersionList", frame.version_list)
        self.WriteList("../Bookmarks", frame.menubar.bookmarks)
        self.WriteList("../VerseHistory",
                       frame.toolbar.verse_entry.GetStrings())
        self.WriteList("../History", frame.verse_history)
        parallel_versions = []
        if hasattr(frame, "parallel"):
            for i, choice in enumerate(frame.parallel.choices):
                if i > 0 and choice.GetSelection() == 0:
                    continue
                version = choice.GetStringSelection()
                if version in frame.version_list:
                    parallel_versions.append(version)
        self.WriteList("../ParallelVersions", parallel_versions)
        self.SetPath("/Search")
        self.Write("LastSearch", frame.search.text.GetValue())
        self.WriteList("SearchHistory", frame.search.text.GetStrings())
        self.WriteInt("AbbrevResults", frame.search.abbrev_results)
        self.WriteBool("ShowOptions", frame.search.optionspane.IsExpanded())
        for option in frame.search.options:
            self.WriteBool(option,
                           getattr(frame.search, option).GetValue())
        self.SetPath("/Notes")
        self.WriteInt("ActiveTab", frame.notes.GetSelection())
        subject_notes = frame.notes.GetPage(0)
        ##self.Write("CurrentSubjectTopic", subject_notes.db_key)
        self.WriteInt("SplitterPosition1",
                      subject_notes.splitter.GetSashPosition())
        verse_notes = frame.notes.GetPage(1)
        ##self.Write("CurrentVerseTopic", verse_notes.db_key)
        self.WriteInt("SplitterPosition2",
                      verse_notes.splitter.GetSashPosition())
        self.SetPath("/MultiVerse")
        self.Write("LastVerseList", frame.multiverse.verse_list.GetValue())
        self.WriteInt("SplitterPosition",
                      frame.multiverse.splitter.GetSashPosition())
        self.Flush()

    def WriteList(self, key, value):
        if self.HasGroup(key):
            self.DeleteGroup(key)
        for i in range(len(value)):
            self.Write("%s/Item%d" % (key, i + 1), value[i])


class Berean(wx.App):
    def OnInit(self):
        self.SetAppName("Berean")
        optlist = dict(getopt.getopt(sys.argv[1:], "", ["datadir=", "nosplash",
                                                        "systemtray"])[0])
        if not hasattr(sys, "frozen"):
            self.cwd = os.path.dirname(__file__)
        else:
            self.cwd = os.path.dirname(sys.argv[0])
        show_splash = not ("--nosplash" in optlist or
                           "--systemtray" in optlist)
        if show_splash:
            splash = wx.SplashScreen(wx.Bitmap(os.path.join(self.cwd, "images",
                                                            "splash.png"),
                                               wx.BITMAP_TYPE_PNG),
                                     wx.SPLASH_CENTRE_ON_SCREEN |
                                     wx.SPLASH_NO_TIMEOUT, 0, None,
                                     style=wx.BORDER_SIMPLE)
            self.Yield()

        if "--datadir" in optlist:
            self.userdatadir = optlist["--datadir"]
            if not os.path.isabs(self.userdatadir):
                self.userdatadir = os.path.join(self.cwd, self.userdatadir)
        elif os.path.isfile(os.path.join(self.cwd, "portable.ini")):
            self.userdatadir = self.cwd
        else:
            self.userdatadir = wx.StandardPaths.Get().GetUserDataDir()
        if not os.path.isdir(self.userdatadir):
            os.mkdir(self.userdatadir)
        self.config = FileConfig(self)
        self.locale = wx.Locale(wx.LANGUAGE_DEFAULT)
        localedir = os.path.join(self.cwd, "locale")
        self.locale.AddCatalogLookupPathPrefix(localedir)
        language = self.locale.GetCanonicalName()
        if os.path.isfile(os.path.join(localedir, language, "LC_MESSAGES",
                                       "berean.mo")):
            self.locale.AddCatalog(language)

        self.frame = mainwindow.MainWindow(self)
        self.SetTopWindow(self.frame)
        self.Bind(wx.EVT_QUERY_END_SESSION, self.OnQueryEndSession)
        self.Bind(wx.EVT_END_SESSION, self.frame.OnClose)
        if "--systemtray" not in optlist:
            self.frame.Show()
        else:
            self.frame.taskbaricon = mainwindow.TaskBarIcon(self.frame)
        if show_splash:
            splash.Destroy()
        return True

    def OnQueryEndSession(self, event):
        pass


def main():
    sys.excepthook = debug.OnError
    app = Berean(False)
    app.MainLoop()


if __name__ == "__main__":
    main()
