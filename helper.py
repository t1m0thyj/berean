"""
helper.py - help system for Berean
Copyright (C) 2013 Timothy Johnson <timothysw@objectmail.com>
"""

import os.path
import webbrowser
import wx
from wx import html

_ = wx.GetTranslation

class HelpSystem(html.HtmlHelpController):
	def __init__(self, frame):
		html.HtmlHelpController.__init__(self, parentWindow=frame)
		self._frame = frame
		
		self.config = wx.FileConfig(localFilename=os.path.join(frame._app.userdatadir, "help.cfg"))
		
		self.SetTempDir(os.path.join(frame._app.userdatadir, ""))
		self.SetTitleFormat("%s")
		self.UseConfig(self.config)
		
		book = os.path.join(frame._app.cwd, "locale", frame._app.locale.GetCanonicalName(), "help", "header.hhp")
		if not os.path.isfile(book):
			book = os.path.join(frame._app.cwd, "locale", "en_US", "help", "header.hhp")
		self.AddBook(book)
	
	def ShowHelpFrame(self):
		self.DisplayContents()
		self.GetHelpWindow().Bind(html.EVT_HTML_LINK_CLICKED, self.OnHelpHtmlLinkClicked)
	
	def OnHelpHtmlLinkClicked(self, event):
		href = event.GetLinkInfo().GetHref()
		if href.startswith("http:"):
			webbrowser.open(href)
		else:
			event.Skip()
	
	def ShowAboutBox(self):
		info = wx.AboutDialogInfo()
		info.SetName("Berean")
		info.SetVersion(self._frame._app.version)
		info.SetCopyright("Copyright (C) 2011-2013 Timothy Johnson. All rights reserved.")
		info.SetDescription(_("A Bible study tool that is free, cross-platform, and open-source."))
		info.SetWebSite("http://berean.sf.net")
		info.SetLicense(license)
		wx.AboutBox(info)

license = """This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>."""