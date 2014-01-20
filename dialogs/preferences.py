"""preferences.py - preferences dialog class"""

import os

import wx

_ = wx.GetTranslation

class PreferencesDialog(wx.Dialog):
    def __init__(self, parent):
        super(PreferencesDialog, self).__init__(parent, title=_("Preferences"),
            size=(600, 440), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self._parent = parent

        self.version_abbrevs = ("ASV", "DSV", "KJV", "LSG", "RV1909",
            "WEB", "Webster", "Wycliffe", "YLT")
        self.version_names = ("American Standard Version",
            "Dutch Statenvertaling (Dutch)", "King James Version",
            "Louis Segond (French)", "Reina Valera 1909 (Spanish)",
            "Webster's Bible", "World English Bible", "Wycliffe New Testament",
            "Young's Literal Translation")

        self.notebook = wx.Notebook(self, -1)
        if '__WXMSW__' in wx.PlatformInfo:
            wx.CallAfter(self.notebook.Refresh)

        self.general = wx.Panel(self.notebook, -1)
        self.MinimizeToTray = wx.CheckBox(self.general, -1,
            _("Minimize to system tray"))
        self.MinimizeToTray.SetValue(parent._app.settings["MinimizeToTray"])
        self.AbbrevSearchResults = wx.CheckBox(self.general, -1,
            _("Abbreviate book names in search results"))
        self.AbbrevSearchResults.SetValue(
            parent._app.settings["AbbrevSearchResults"])
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.MinimizeToTray, 0, wx.ALL, 2)
        sizer.Add(self.AbbrevSearchResults, 0, wx.ALL, 2)
        self.general.SetSizer(sizer)
        self.notebook.AddPage(self.general, _("General"))

        self.versions = wx.Panel(self.notebook, -1)
        self.VersionList = wx.CheckListBox(self.versions, -1)
        for i in range(len(self.version_abbrevs)):
            self.VersionList.Append("%s - %s" % (self.version_names[i],
                self.version_abbrevs[i]))
            if self.version_abbrevs[i] in parent.versions:
                self.VersionList.Check(i)
        self.VersionList.Bind(wx.EVT_CHECKLISTBOX, self.OnVersionList)
        sizer = wx.BoxSizer()
        sizer.Add(self.VersionList, 1, wx.EXPAND)
        self.versions.SetSizer(sizer)
        self.notebook.AddPage(self.versions, _("Versions*"))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook, 1, wx.ALL | wx.EXPAND, 5)
        statictext = wx.StaticText(self, -1,
            _("*Takes effect after you restart Berean"))
        statictext.SetForegroundColour("#808080")
        sizer.Add(statictext, 0, wx.LEFT | wx.RIGHT, 5)
        button_sizer = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        sizer.Add(button_sizer, 0, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(sizer)

        self.Bind(wx.EVT_BUTTON, self.OnOk, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)

    def OnVersionList(self, event):
        item = event.GetInt()
        if not self.VersionList.IsChecked(item):
            selections = False
            for i in range(self.VersionList.GetCount()):
                if self.VersionList.IsChecked(i):
                    selections = True
                    break
            if not selections:
                self.VersionList.Check(item)
                wx.MessageBox(
                    _("You must have at least one version selected."),
                    _("Berean"), wx.ICON_EXCLAMATION | wx.OK)

    def OnOk(self, event):
        self._parent._app.settings["MinimizeToTray"] = \
            self.MinimizeToTray.GetValue()
        self._parent._app.settings["AbbrevSearchResults"] = \
            self.AbbrevSearchResults.GetValue()
        versions = []
        for i in range(len(self.version_abbrevs)):
            if self.VersionList.IsChecked(i):
                versions.append(self.version_abbrevs[i])
        if versions != self._parent.versions:
            for version in self._parent.versions:   # Delete old indexes
                if version not in versions:
                    wx.CallAfter(os.remove, os.path.join(
                        self._parent._app.userdatadir, "indexes",
                        "%s.idx" % version))
            self._parent.versions = versions
        self.Destroy()

    def OnCancel(self, event):
        self.Destroy()
