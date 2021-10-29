"""berean.py - main script for Berean
Copyright (c) 2021 Timothy Johnson <pythoneer@outlook.com>

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import getopt
import os
import sys

import wx
from wx import adv

import bugreport
import mainwindow

_ = wx.GetTranslation


class FileConfig(wx.FileConfig):
    def __init__(self, app):
        super(FileConfig, self).__init__(localFilename=os.path.join(app.userdatadir, "berean.ini"))
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
        self.Write("Language", self._app.language)
        self.WriteBool("SingleInstance", self._app.single_instance)
        self.Write("WindowPosition", ",".join(str(i) for i in frame.rect.GetPosition()))
        self.Write("WindowSize", ",".join(str(i) for i in frame.rect.GetSize()))
        self.WriteBool("IsMaximized", frame.IsMaximized())
        self.WriteBool("MinimizeToTray", frame.minimize_to_tray)
        self.WriteInt("CurrentBook", frame.reference[0])
        self.WriteInt("CurrentChapter", frame.reference[1])
        self.WriteInt("CurrentVerse", frame.reference[2])
        self.Write("HtmlFontFace", frame.default_font["normal_face"])
        self.WriteInt("HtmlFontSize", frame.default_font["size"])
        self.WriteInt("ZoomLevel", frame.zoom_level)
        self.Write("LastVerse", frame.toolbar.verse_entry.GetValue())
        self.WriteBool("AutocompBooks", frame.toolbar.autocomp_books)
        self.WriteInt("ActiveVersionTab", frame.notebook.GetSelection())
        self.WriteList("../VersionList", frame.version_list)
        self.WriteList("../Bookmarks", frame.menubar.bookmarks)
        self.WriteList("../VerseHistory", frame.toolbar.verse_entry.GetStrings())
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
            self.WriteBool(option, getattr(frame.search, option).GetValue())
        self.SetPath("/MultiVerse")
        self.Write("LastVerseList", frame.multiverse.verse_list.GetValue())
        self.WriteInt("SplitterPosition", frame.multiverse.GetSashPosition())
        self.Flush()

    def WriteList(self, key, value):
        if self.HasGroup(key):
            self.DeleteGroup(key)
        for i in range(len(value)):
            self.Write("%s/Item%d" % (key, i + 1), value[i])


class Berean(wx.App):
    def OnInit(self):
        self.SetAppName("Berean")
        optlist = dict(getopt.getopt(sys.argv[1:], "", ["datadir=", "nosplash", "systemtray"])[0])
        if not hasattr(sys, "frozen"):
            self.cwd = os.path.dirname(__file__)
        else:
            self.cwd = os.path.dirname(sys.argv[0])

        self.portable = True
        if "--datadir" in optlist:
            self.userdatadir = optlist["--datadir"]
            if not os.path.isabs(self.userdatadir):
                self.userdatadir = os.path.join(self.cwd, self.userdatadir)
        elif os.path.isfile(os.path.join(self.cwd, "portable.ini")):
            self.userdatadir = self.cwd
        else:
            self.userdatadir = wx.StandardPaths.Get().GetUserDataDir()
            self.portable = False
        if not os.path.isdir(self.userdatadir):
            os.mkdir(self.userdatadir)
        self.config = FileConfig(self)
        locale = wx.Locale(wx.LANGUAGE_DEFAULT)
        self.language = self.config.Read("Main/Language", locale.GetCanonicalName())
        self.locale = wx.Locale(locale.FindLanguageInfo(self.language).Language)
        localedir = os.path.join(self.cwd, "locale")
        self.locale.AddCatalogLookupPathPrefix(localedir)
        if os.path.isfile(os.path.join(localedir, self.language, "LC_MESSAGES", "berean.mo")):
            self.locale.AddCatalog("berean")

        self.single_instance = self.config.ReadBool("Main/SingleInstance", True)
        if self.single_instance:
            self.SetSingleInstance(True)
            if self.checker.IsAnotherRunning():
                wx.MessageBox(_("Berean is already running."), "Berean", wx.ICON_ERROR)
                wx.Exit()
        self.frame = mainwindow.MainWindow(self)
        self.SetTopWindow(self.frame)
        self.Bind(wx.EVT_QUERY_END_SESSION, self.OnQueryEndSession)
        self.Bind(wx.EVT_END_SESSION, self.frame.OnClose)
        if "--systemtray" not in optlist:
            self.frame.Show()
        else:
            self.frame.taskbaricon = mainwindow.TaskBarIcon(self.frame)
        return True

    def SetSingleInstance(self, single_instance):
        if single_instance:
            self.checker = wx.SingleInstanceChecker("berean-%s" % wx.GetUserName())
        elif hasattr(self, "checker"):
            del self.checker

    def OnQueryEndSession(self, event):
        pass


def main():
    sys.excepthook = bugreport.OnError
    app = Berean(False)
    app.MainLoop()


if __name__ == "__main__":
    main()
