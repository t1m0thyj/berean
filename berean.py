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
        self.Write("WindowPosition", ",".join(str(i) for i in
            self._app.frame.rect.GetPosition()))
        self.Write("WindowSize", ",".join(str(i) for i in
            self._app.frame.rect.GetSize()))
        self.WriteBool("IsMaximized", self._app.frame.IsMaximized())
        self.WriteInt("CurrentBook", self._app.frame.reference[0])
        self.WriteInt("CurrentChapter", self._app.frame.reference[1])
        self.WriteInt("CurrentVerse", self._app.frame.reference[2])
        self.Write("HtmlFontFace", self._app.frame.default_font["normal_face"])
        self.WriteInt("HtmlFontSize", self._app.frame.default_font["size"])
        self.WriteInt("ZoomLevel", self._app.frame.zoom_level)
        self.Write("LastVerse", self._app.frame.toolbar.verse_entry.GetValue())
        self.WriteInt("ActiveVersionTab",
            self._app.frame.notebook.GetSelection())
        self.WriteBool("MinimizeToTray", self._app.frame.minimize_to_tray)
        self.WriteList("../VersionList", self._app.frame.version_list)
        self.WriteList("../FavoritesList",
            self._app.frame.menubar.favorites_list)
        self.WriteList("../VerseHistory",
            self._app.frame.toolbar.verse_entry.GetStrings())
        self.WriteList("../History", self._app.frame.verse_history)
        parallel_versions = []
        if hasattr(self._app.frame, "parallel"):
            for i, choice in enumerate(self._app.frame.parallel.choices):
                if i > 0 and choice.GetSelection() == 0:
                    continue
                version = choice.GetStringSelection()
                if version in self._app.frame.version_list:
                    parallel_versions.append(version)
        self.WriteList("../ParallelVersions", parallel_versions)
        self.SetPath("/Search")
        self.Write("LastSearch", self._app.frame.search.text.GetValue())
        self.WriteList("SearchHistory",
            self._app.frame.search.text.GetStrings())
        self.WriteBool("ShowOptions",
            self._app.frame.search.optionspane.IsExpanded())
        for option in self._app.frame.search.options:
            self.WriteBool(option,
                getattr(self._app.frame.search, option).GetValue())
        self.Write("LastMultiVerseRetrieval",
            self._app.frame.multiverse.verse_list.GetValue())
        self.SetPath("/Notes")
        self.WriteInt("ActiveNotesTab", self._app.frame.notes.GetSelection())
        ##self.WriteList("TopicList",
        ##    self._app.frame.notes.GetPage(1).selector.topic_list)
        self.Flush()

    def WriteList(self, key, value):
        if self.HasGroup(key):
            self.DeleteGroup(key)
        for i in range(len(value)):
            self.Write("%s/Item%d" % (key, i + 1), value[i])


class Berean(wx.App):
    def OnInit(self):
        super(Berean, self).__init__()
        self.SetAppName("Berean")
        options = dict(getopt.getopt(sys.argv[1:], "",
            ["datadir=", "nosplash", "systemtray"])[0])
        if not hasattr(sys, "frozen"):
            self.cwd = os.path.dirname(__file__)
        else:
            self.cwd = os.path.dirname(sys.argv[0])
        show_splash = not ("--nosplash" in options or
            "--systemtray" in options)
        if show_splash:
            splash = wx.SplashScreen(wx.Bitmap(os.path.join(self.cwd,
                "images", "splash.png"), wx.BITMAP_TYPE_PNG),
                wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_NO_TIMEOUT, 0, None, -1,
                style=wx.BORDER_SIMPLE | wx.FRAME_NO_TASKBAR)
            self.Yield()

        if "--datadir" in options:
            self.userdatadir = options["--datadir"]
            if not os.path.isabs(self.userdatadir):
                self.userdatadir = os.path.join(self.cwd, self.userdatadir)
        elif os.path.isfile(os.path.join(self.cwd, "portable.ini")):
            self.userdatadir = self.cwd
        elif '__WXGTK__' not in wx.PlatformInfo:
            self.userdatadir = os.path.join(
                wx.StandardPaths.Get().GetUserDataDir(), "Berean")
        else:
            self.userdatadir = os.path.join(
                wx.StandardPaths.Get().GetUserDataDir(), ".berean")
        if not os.path.isdir(self.userdatadir):
            os.makedirs(self.userdatadir)
        self.config = FileConfig(self)
        self.locale = wx.Locale(wx.LANGUAGE_ENGLISH_US)
        localedir = os.path.join(self.cwd, "locale")
        self.locale.AddCatalogLookupPathPrefix(localedir)
        language = self.locale.GetCanonicalName()
        if os.path.isfile(os.path.join(localedir, language, "LC_MESSAGES",
                "berean.mo")):
            self.locale.AddCatalog(language)
        self.frame = mainwindow.MainWindow(self)
        self.SetTopWindow(self.frame)
        if "--systemtray" not in options:
            self.frame.Show()
        else:
            self.frame.taskbaricon = mainwindow.TaskBarIcon(self.frame)
        if show_splash:
            splash.Destroy()
        return True


def main():
    sys.excepthook = debug.OnError
    app = Berean()
    app.MainLoop()


if __name__ == "__main__":
    main()
