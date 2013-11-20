"""
debug.py - error handling functions for Berean
Copyright (C) 2013 Timothy Johnson <timothysw@objectmail.com>
NOTE: Parts of this file are based on code from GUI2Exe
"""

import platform
import sys
import traceback
import urllib2
import webbrowser
import wx

_ = wx.GetTranslation

def OnError(*exception):
	wx.CallAfter(LogError, exception)

def LogError(exception):
	global error
	if error:
		return
	error = True
	details = "".join(traceback.format_exception(*exception))
	dialog = wx.MessageDialog(None, _("An error has occurred in the application."), _("Error"), wx.ICON_ERROR | wx.YES_NO | wx.CANCEL)
	dialog.SetExtendedMessage(details)
	dialog.SetYesNoCancelLabels(_("Report"), _("Ignore"), _("Abort"))
	button = dialog.ShowModal()
	if button == wx.ID_YES:
		mac = ""
		if sys.platform == "darwin":
			mac = "\n    Mac version: " + platform.mac_ver()[0]
		message = text % ("*" * 40, "*" * 40, details, "*" * 40,
						  wx.GetOsDescription(), mac, platform.architecture()[0], platform.machine(), sys.byteorder,
						  sys.version, sys.getdefaultencoding(), sys.getfilesystemencoding(),
						  wx.VERSION_STRING, ", ".join(wx.PlatformInfo), wx.GetDefaultPyEncoding(),
						  _version, hasattr(sys, "frozen"))
		if wx.Platform != "__WXMAC__":
			message = urllib2.quote(message)
		webbrowser.open("mailto:timothysw@objectmail.com?subject=Berean Error Report&body=%s" % message.replace("'", ""))
	elif button == wx.ID_CANCEL:
		sys.exit(1)
	dialog.Destroy()
	error = False

error = False
text = """Please explain what you were doing in Berean when the error occurred.

%s
DO NOT EDIT ANYTHING BELOW THIS LINE.
%s

%s
%s

%s%s
    architecture: %s
    machine: %s
    byte order: %s
Python %s
    default encoding: %s
    file system encoding: %s
wxPython %s
    platform info: %s
    default encoding: %s
Berean %s
    frozen: %s"""
