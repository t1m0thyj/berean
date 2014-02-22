"""preferences.py - preferences dialog class"""

import os

import wx

_ = wx.GetTranslation
VERSION_ABBREVS = ("ASV", "DSV", "KJV", "LSG", "RVA", "SEV", "WEB", "Webster",
    "Wycliffe", "YLT")
VERSION_NAMES = ("American Standard Version", "Dutch Statenvertaling (Dutch)",
    "King James Version", "Louis Segond (French)",
    "Reina-Valera Antigua (Spanish)", "Las Sagradas Escrituras (Spanish)",
    "World English Bible", "Webster's Bible", "Wycliffe New Testament",
    "Young's Literal Translation")


class PreferencesDialog(wx.Dialog):
    def __init__(self, parent):
        super(PreferencesDialog, self).__init__(parent, -1, _("Preferences"),
            size=(300, 440), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self._parent = parent
        self.notebook = wx.Notebook(self, -1, style=wx.NB_MULTILINE)

        self.general = wx.Panel(self.notebook, -1)
        self.minimize_to_tray = wx.CheckBox(self.general, -1,
            _("Minimize to system tray"))
        self.minimize_to_tray.SetValue(parent.minimize_to_tray)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.minimize_to_tray, 0, wx.ALL, 5)
        self.general.SetSizer(sizer)
        self.notebook.AddPage(self.general, _("General"))

        self.versions = wx.Panel(self.notebook, -1)
        self.version_list = wx.CheckListBox(self.versions, -1)
        for i in range(len(VERSION_ABBREVS)):
            self.version_list.Append("%s - %s" % (VERSION_NAMES[i],
                VERSION_ABBREVS[i]))
            if VERSION_ABBREVS[i] in parent.version_list:
                self.version_list.Check(i)
        sizer = wx.BoxSizer()
        sizer.Add(self.version_list, 1, wx.EXPAND)
        self.versions.SetSizer(sizer)
        self.notebook.AddPage(self.versions, _("Versions"))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook, 1, wx.ALL | wx.EXPAND, 5)
        button_sizer = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        self.Bind(wx.EVT_BUTTON, self.OnOk, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)
        sizer.Add(button_sizer, 0, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(sizer)
        self.Center()

    def OnOk(self, event):
        version_list = list(filter(lambda version: self.version_list.IsChecked(
            VERSION_ABBREVS.index(version)), VERSION_ABBREVS))
        if not len(version_list):
            wx.MessageBox(_("You must have at least one version selected."),
                _("Berean"), wx.ICON_EXCLAMATION | wx.OK)
            return
        self._parent.minimize_to_tray = self.minimize_to_tray.GetValue()
        if version_list != self._parent.version_list:
            for version in self._parent.version_list:   # Delete old indexes
                filename = os.path.join(self._parent._app.userdatadir,
                    "indexes", "%s.idx" % version)
                if version not in version_list and os.path.isfile(filename):
                    wx.CallAfter(os.remove, filename)
            self._parent.version_list = version_list
            wx.MessageBox(_("Changes to version settings will not take " \
                "effect until Berean is restarted."), _("Berean"),
                wx.ICON_INFORMATION | wx.OK)
        self.Destroy()

    def OnCancel(self, event):
        self.Destroy()
