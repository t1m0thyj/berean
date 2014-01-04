"""help.py - help system class"""

import os.path

import wx
from wx import html

_ = wx.GetTranslation

license = """This program is free software: you can redistribute it and/or modify
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

class HelpSystem(html.HtmlHelpController):
    def __init__(self, frame):
        html.HtmlHelpController.__init__(self, parentWindow=frame)
        self._frame = frame

        self.config = wx.FileConfig(localFilename=os.path.join(frame._app.userdatadir, "help.cfg"))

        self.SetTempDir(os.path.join(frame._app.userdatadir, ""))
        self.SetTitleFormat("%s")
        self.UseConfig(self.config)

        filename = os.path.join(frame._app.cwd, "locale", frame._app.locale.GetCanonicalName(), "help", "header.hhp")
        if not os.path.isfile(filename):
            filename = os.path.join(frame._app.cwd, "locale", "en_US", "help", "header.hhp")
        self.AddBook(filename)

    def show_help_window(self):
        self.DisplayContents()
        self.GetHelpWindow().Bind(html.EVT_HTML_LINK_CLICKED,
            self.OnHtmlLinkClicked)

    def OnHtmlLinkClicked(self, event):
        link = event.GetLinkInfo().GetHref()
        if link.startswith("http://"):
            wx.LaunchDefaultBrowser(link)
        else:
            event.Skip()

    def show_about_box(self):
        info = wx.AboutDialogInfo()
        info.SetName("Berean")
        info.SetVersion(VERSION)
        info.SetCopyright("Copyright (C) 2011-2014 Timothy Johnson")
        info.SetDescription(_("A free, cross-platform, and open-source Bible study tool"))
        info.SetWebSite("http://berean.sf.net")
        info.SetLicense(license)
        wx.AboutBox(info)
