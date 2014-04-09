"""debug.py - error handling code"""

import platform
import sys
import traceback
import urllib2

import wx

from config import VERSION

_ = wx.GetTranslation


def OnError(*exception):
    exc_info = "".join(traceback.format_exception(*exception))
    print exc_info
    if not ErrorDialog.ACTIVE:
        dialog = ErrorDialog(exc_info)
        dialog.ShowModal()
        dialog.Destroy()


class ErrorDialog(wx.Dialog):
    ACTIVE = False

    def __init__(self, exc_info):
        ErrorDialog.ACTIVE = True
        super(ErrorDialog, self).__init__(None, -1, _("Error"))
        bitmap = wx.StaticBitmap(self, -1, wx.ArtProvider.GetBitmap(
            wx.ART_ERROR))
        label = wx.StaticText(self, -1,
            _("An error occurred in the application."))
        mac_ver = ""
        if sys.platform == "darwin":
            mac_ver = "\nmac_ver: %s" % platform.mac_ver()[0]
        self.send = wx.Button(self, -1, _("send bug report"))
        self.show = wx.Button(self, -1, _("show bug report"))
        self.continue_button = wx.Button(self, -1, _("continue application"))
        self.restart = wx.Button(self, -1, _("restart application"))
        self.restart.Disable()
        self.close = wx.Button(self, -1, _("close application"))
        self.textctrl = wx.TextCtrl(self, -1, REPORT % (wx.GetOsDescription(),
            mac_ver, platform.architecture()[0], platform.machine(),
            sys.byteorder, sys.version, sys.getdefaultencoding(),
            sys.getfilesystemencoding(), wx.version(), wx.PlatformInfo,
            wx.GetDefaultPyEncoding(), VERSION, hasattr(sys, "frozen"),
            exc_info.rstrip()), style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.textctrl.Hide()
        self.Bind(wx.EVT_BUTTON, self.OnSend, self.send)
        self.Bind(wx.EVT_BUTTON, self.OnShow, self.show)
        self.Bind(wx.EVT_BUTTON, self.OnContinue, self.continue_button)
        self.Bind(wx.EVT_BUTTON, self.OnRestart, self.restart)
        self.Bind(wx.EVT_BUTTON, self.OnCloseButton, self.close)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3 = wx.BoxSizer(wx.VERTICAL)
        sizer4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer4.Add(bitmap, 0, wx.ALL | wx.CENTER, 10)
        sizer4.Add(label, 1, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10)
        sizer3.Add(sizer4, 0, wx.EXPAND)
        sizer3.AddStretchSpacer(1)
        sizer5 = wx.BoxSizer(wx.HORIZONTAL)
        sizer5.Add(self.send, 0, wx.EXPAND)
        sizer5.Add(self.show, 0,
            wx.LEFT | wx.EXPAND | wx.RESERVE_SPACE_EVEN_IF_HIDDEN, 5)
        sizer3.Add(sizer5, 0, wx.ALL | wx.EXPAND, 5)
        sizer2.Add(sizer3, 1, wx.EXPAND)
        sizer6 = wx.BoxSizer(wx.VERTICAL)
        sizer6.Add(self.continue_button, 0, wx.EXPAND)
        sizer6.Add(self.restart, 0, wx.TOP | wx.EXPAND, 5)
        sizer6.Add(self.close, 0, wx.TOP | wx.EXPAND, 5)
        sizer2.Add(sizer6, 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(sizer2, 0, wx.EXPAND)
        sizer.Add(self.textctrl, 1, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(sizer)
        self.Fit()
        self.Center()

    def OnSend(self, event):
        body = self.textctrl.GetValue()
        if '__WXMAC__' not in wx.PlatformInfo:
            body = urllib2.quote(body)
        wx.LaunchDefaultBrowser("mailto:berean_bugs@snapunit.com?subject=" \
            "Berean Bug Report&body=%s" % body.replace("'", ""))

    def OnShow(self, event):
        self.textctrl.Show()
        self.show.Hide()
        self.Fit()

    def OnContinue(self, event):
        self.Close()

    def OnRestart(self, event):
        app = wx.GetApp()
        app.GetTopWindow().Destroy()
        app.OnInit()

    def OnCloseButton(self, event):
        sys.exit(1)

    def OnClose(self, event):
        ErrorDialog.ACTIVE = False
        event.Skip()


REPORT = """OSDescription: %s%s
architecture: %s
machine: %s
byteorder: %s
Python version: %s
defaultencoding: %s
filesystemencoding: %s
wxPython version: %s
PlatformInfo: %s
DefaultPyEncoding: %s
Berean version: %s
frozen: %s
------------------------------------------------------------------------------
%s
------------------------------------------------------------------------------
"""
