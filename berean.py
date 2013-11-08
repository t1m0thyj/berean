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

import ConfigParser
import getopt
import os
import sys
import wx

import debug
import parent

_version = debug._version = "1.4.6"
ConfigParser.str = lambda value: value.encode("utf_8")	# Make ConfigParser work with Unicode

class FileConfig(ConfigParser.RawConfigParser):
	def __init__(self, app):
		ConfigParser.RawConfigParser.__init__(self)
		self._app = app
		
		self.filename = os.path.join(app.userdatadir, "berean.ini")
		
		self.optionxform = str	# Don't make option names lowercase
		if os.path.isfile(self.filename):
			config = open(self.filename, 'r')
			self.readfp(config)
			config.close()
	
	def Load(self):
		display = wx.GetDisplaySize()
		best = (int(display[0] * 0.8), int(display[1] * 0.8))
		settings = {"WindowPos":wx.DefaultPosition, "WindowSize":best, "MaximizeState":False,
					"MinimizeToTray":False, "SelectedBook":1, "SelectedChapter":1, "ZoomLevel":3,
					"ActiveVerse":-1, "ActiveTab":0, "LastReference":"",
					"HebrewBookOrder":False, "ActiveNotes":0,
					"VersionList":["KJV", "YLT"], "ParallelVersions":["KJV", "YLT"],
					"FavoritesList":[], "ReferenceHistory":[], "ChapterHistory":[],
					"AbbrevSearchResults":False, "LastSearch":"", "OptionsPane":True,
					"AllWords":True, "CaseSensitive":False, "ExactMatch":False, "Phrase":False, "RegularExpression":False,
					"SearchHistory":[], "LastVerses":""}
		if self.has_option("Main", "WindowPos"):
			settings["WindowPos"] = map(int, self.getunicode("Main", "WindowPos").split(","))
		if self.has_option("Main", "WindowSize"):
			settings["WindowSize"] = map(int, self.getunicode("Main", "WindowSize").split(","))
		if not (0 - settings["WindowSize"][0] < settings["WindowPos"][0] < display[0] and 0 - settings["WindowSize"][1] < settings["WindowPos"][1] < display[1]):
			settings["WindowPos"] = wx.DefaultPosition
			settings["WindowSize"] = best
		for option in ("MaximizeState", "MinimizeToTray", "HebrewBookOrder", "ActiveNotes"):
			if self.has_option("Main", option):
				settings[option] = self.getboolean("Main", option)
		for option in ("SelectedBook", "SelectedChapter", "ZoomLevel", "ActiveVerse", "ActiveTab"):
			if self.has_option("Main", option):
				settings[option] = self.getint("Main", option)
		if self.has_option("Main", "LastReference"):
			settings["LastReference"] = self.getunicode("Main", "LastReference")
		if self.has_section("VersionList"):
			settings["VersionList"] = self.getlist("VersionList")
		if self.has_section("ParallelVersions"):
			settings["ParallelVersions"] = self.getlist("ParallelVersions")
		if self.has_section("FavoritesList"):
			settings["FavoritesList"] = self.getlist("FavoritesList")
		if self.has_section("ReferenceHistory"):
			settings["ReferenceHistory"] = self.getlist("ReferenceHistory")
		if self.has_section("ChapterHistory"):
			settings["ChapterHistory"] = self.getlist("ChapterHistory")
		if self.has_option("Search", "AbbrevSearchResults"):
			settings["AbbrevSearchResults"] = self.getboolean("Search", "AbbrevSearchResults")
		if self.has_option("Search", "LastSearch"):
			settings["LastSearch"] = self.getunicode("Search", "LastSearch")
		if self.has_option("Search", "OptionsPane"):
			settings["OptionsPane"] = self.getboolean("Search", "OptionsPane")
		for option in ("AllWords", "CaseSensitive", "ExactMatch", "Phrase", "RegularExpression"):
			if self.has_option("Search", option):
				settings[option] = self.getint("Search", option)
		if self.has_option("Search", "LastVerses"):
			settings["LastVerses"] = self.getunicode("Search", "LastVerses")
		if self.has_section("Search\\SearchHistory"):
			settings["SearchHistory"] = self.getlist("Search", "SearchHistory")
		return settings
	
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

	def Save(self, frame):
		if not self.has_section("Main"):
			self.add_section("Main")
		self.set("Main", "WindowPos", ",".join(map(str, frame.rect.GetPosition())))
		self.set("Main", "WindowSize", ",".join(map(str, frame.rect.GetSize())))
		self.set("Main", "MaximizeState", str(frame.IsMaximized()))
		self.set("Main", "MinimizeToTray", str(self._app.settings["MinimizeToTray"]))
		self.set("Main", "SelectedBook", str(frame.reference[0]))
		self.set("Main", "SelectedChapter", str(frame.reference[1]))
		self.set("Main", "ZoomLevel", str(frame.zoom))
		self.set("Main", "ActiveVerse", str(frame.reference[2]))
		self.set("Main", "ActiveTab", str(frame.notebook.GetSelection()))
		self.set("Main", "LastReference", frame.toolbar.reference.GetValue())
		self.set("Main", "HebrewBookOrder", str(self._app.settings["HebrewBookOrder"]))
		self.set("Main", "ActiveNotes", str(frame.notes.GetSelection()))
		self.setlist("VersionList", None, frame.versions)
		parallel = []
		if hasattr(frame, "parallel") and len(frame.versions) > 1:
			for i, choice in enumerate(frame.parallel._parent.choices):
				if choice.GetSelection() > 0 or i == 0:
					parallel.append(choice.GetStringSelection())
		self.setlist("ParallelVersions", None, parallel)
		self.setlist("FavoritesList", None, frame.menubar.Favorites.favorites)
		self.setlist("ReferenceHistory", None, frame.toolbar.reference.GetStrings())
		self.setlist("ChapterHistory", None, frame.toolbar.history)
		if not self.has_section("Search"):
			self.add_section("Search")
		self.set("Search", "AbbrevSearchResults", str(self._app.settings["AbbrevSearchResults"]))
		self.setlist("Search", "SearchHistory", frame.search.text.GetStrings())
		self.set("Search", "LastSearch", frame.search.text.GetValue())
		self.set("Search", "OptionsPane", str(frame.search.optionspane.IsExpanded()))
		for option in frame.search.options:
			state = getattr(frame.search, option).Get3StateValue()
			if state == wx.CHK_UNDETERMINED:
				state += frame.search.states[option]
			self.set("Search", option, str(state))
		self.set("Search", "LastVerses", self._app.settings["LastVerses"])
		config = open(self.filename, 'w')
		self.write(config)
		config.close()
	
	def setlist(self, section, option, value):
		if option:
			section = "%s\\%s" % (section, option)
		if not self.has_section(section):
			self.add_section(section)
		for i in range(len(value)):
			self.set(section, "Item%d" % (i + 1), value[i])

class Berean(wx.App):
	def OnInit(self):
		wx.App.__init__(self)
		
		self.SetAppName("Berean")
		options, args = getopt.getopt(sys.argv[1:], "", ["datadir=", "systemtray"])
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
			self.userdatadir = os.path.join(wx.StandardPaths.Get().GetUserDataDir(), "Berean")
		else:
			self.userdatadir = os.path.join(wx.StandardPaths.Get().GetUserDataDir(), ".berean")
		if not os.path.isdir(self.userdatadir):
			os.makedirs(self.userdatadir)
		
		systemtray = "--systemtray" in options
		if not systemtray:
			splash = wx.SplashScreen(wx.Bitmap(os.path.join(self.cwd, "images", "splash.png"), wx.BITMAP_TYPE_PNG), wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_NO_TIMEOUT, 1000, None, -1, style=wx.NO_BORDER | wx.FRAME_NO_TASKBAR)
			self.Yield()
		
		self.config = FileConfig(self)
		self.locale = wx.Locale(wx.LANGUAGE_ENGLISH_US)
		localedir = os.path.join(self.cwd, "locale")
		self.locale.AddCatalogLookupPathPrefix(localedir)
		language = self.locale.GetCanonicalName()
		if os.path.isfile(os.path.join(localedir, language, "LC_MESSAGES", "berean.mo")):
			self.locale.AddCatalog(language)
		self.settings = self.config.Load()
		self.version = _version
		
		self.frame = parent.MainFrame(self)
		self.SetTopWindow(self.frame)
		self.frame.Show()
		if not systemtray:
			splash.Destroy()
		else:
			self.frame.Iconize()
		
		return True
	
	def UnInit(self):
		self.config.Save(self.frame)
		del self.locale
	
	def CloseFrame(self):
		self.frame.Destroy()
		self.ExitMainLoop()

def main():
	sys.excepthook = debug.OnError
	app = Berean()
	app.MainLoop()

if __name__ == "__main__":
	main()