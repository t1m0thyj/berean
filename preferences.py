"""preferences.py - preferences dialog class"""

import wx

from config import *

_ = wx.GetTranslation
VERSION_ABBREVS = ("ASV", "DSV", "KJV", "LSG", "RVA", "SEV", "WEB", "Webster",
    "Wycliffe", "YLT")
VERSION_NAMES = ("American Standard Version",
    "Dutch Statenvertaling (Deutsch)", "King James Version",
    "Louis Segond (Fran\xe7ais)", "Reina-Valera Antigua (Espa\xf1ol)",
    "Las Sagradas Escrituras (Espa\xf1ol)", "World English Bible",
    "Webster's Bible", "Wycliffe New Testament", "Young's Literal Translation")


class PreferencesDialog(wx.Dialog):
    def __init__(self, parent):
        super(PreferencesDialog, self).__init__(parent, -1, _("Preferences"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self._parent = parent
        self.notebook = wx.Notebook(self, -1, style=wx.NB_MULTILINE)

        self.general = wx.Panel(self.notebook, -1)
        self.minimize_to_tray = wx.CheckBox(self.general, -1,
            _("Minimize to system tray"))
        self.minimize_to_tray.SetValue(parent.minimize_to_tray)
        self.default_font_face = wx.Choice(self.general, -1,
            choices=parent.facenames)
        self.default_font_face.SetStringSelection(
            parent.default_font["normal_face"])
        self.default_font_size = wx.ComboBox(self.general, -1,
            choices=FONT_SIZES)
        self.default_font_size.SetStringSelection(str(
            parent.default_font["size"]))
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.minimize_to_tray, 0, wx.ALL, 5)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(wx.StaticText(self.general, -1, _("Default font:")), 0,
            wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.default_font_face, 0, wx.ALL, 5)
        sizer2.Add(wx.StaticText(self.general, -1, _("Size:")), 0,
            wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
        sizer2.Add(self.default_font_size, 0, wx.ALL, 5)
        sizer.Add(sizer2, 0, wx.ALL ^ wx.TOP, 5)
        self.general.SetSizer(sizer)
        self.notebook.AddPage(self.general, _("General"))

        self.versions = wx.Panel(self.notebook, -1)
        self.version_list = wx.CheckListBox(self.versions, -1)
        for i in range(len(VERSION_ABBREVS)):
            self.version_list.Append("%s - %s" % (VERSION_ABBREVS[i],
                VERSION_NAMES[i]))
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
        self.Fit()
        self.Center()

    def OnOk(self, event):
        version_list = list(filter(lambda version: self.version_list.IsChecked(
            VERSION_ABBREVS.index(version)), VERSION_ABBREVS))
        if not len(version_list):
            wx.MessageBox(_("You must have at least one version selected."),
                _("Berean"), wx.ICON_EXCLAMATION | wx.OK)
            return
        self._parent.minimize_to_tray = self.minimize_to_tray.GetValue()
        default_font = {"size": int(self.default_font_size.GetValue()),
            "normal_face": self.default_font_face.GetStringSelection()}
        if default_font != self._parent.default_font:
            for i in range(self._parent.notebook.GetPageCount()):
                self._parent.get_htmlwindow(i).SetStandardFonts(**default_font)
            for htmlwindow in (self._parent.search.results,
                    self._parent.multiverse.verses, self._parent.printing):
                htmlwindow.SetStandardFonts(**default_font)
            for i in range(self._parent.notes.GetPageCount()):
                page = self._parent.notes.GetPage(i)
                page.editor.SetFont(wx.FFont(default_font["size"], wx.DEFAULT,
                    face=default_font["normal_face"]))
                if page.editor.IsEmpty():
                    page.update_toolbar()
            self._parent.default_font = default_font
        if version_list != self._parent.version_list:
            if not hasattr(self._parent, "old_versions"):
                self._parent.old_versions = []
            for version in VERSION_ABBREVS:
                if (version in self._parent.version_list and
                        version not in version_list):
                    self._parent.old_versions.append(version)
                elif (version in version_list and
                        version in self._parent.old_versions):
                    self._parent.old_versions.remove(version)
            self._parent.version_list = version_list
            wx.MessageBox(_("Changes to version settings will not take " \
                "effect until Berean is restarted."), _("Berean"),
                wx.ICON_INFORMATION | wx.OK)
        self.Destroy()

    def OnCancel(self, event):
        self.Destroy()
