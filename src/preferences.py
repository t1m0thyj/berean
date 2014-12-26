"""preferences.py - preferences dialog class"""

import glob
import os
import shutil
import zipfile

import wx

from config import VERSION_NAMES, VERSION_DESCRIPTIONS, FONT_SIZES

_ = wx.GetTranslation


class PreferencesDialog(wx.Dialog):
    def __init__(self, parent):
        super(PreferencesDialog, self).__init__(parent, title=_("Preferences"),
                                                style=wx.DEFAULT_DIALOG_STYLE |
                                                wx.RESIZE_BORDER)
        self._parent = parent
        self.notebook = wx.Notebook(self, style=wx.NB_MULTILINE)

        self.general = wx.Panel(self.notebook)
        self.minimize_to_tray = wx.CheckBox(self.general,
                                            label=_("Minimize to system tray"))
        self.minimize_to_tray.SetValue(parent.minimize_to_tray)
        self.font_face = wx.Choice(self.general, choices=parent.facenames)
        self.font_face.SetStringSelection(parent.default_font["normal_face"])
        self.font_size = wx.ComboBox(self.general, choices=FONT_SIZES)
        self.font_size.SetStringSelection(str(parent.default_font["size"]))
        self.abbrev_results = wx.CheckBox(self.general,
                                          label=_("Abbreviate search results "
                                                  "when there are more than"))
        self.abbrev_results.SetValue(parent.search.abbrev_results != -1)
        self.abbrev_results.Bind(wx.EVT_CHECKBOX, self.OnAbbrevResults)
        if parent.search.abbrev_results != -1:
            abbrev_results = parent.search.abbrev_results
        else:
            abbrev_results = 1000
        self.abbrev_results2 = wx.SpinCtrl(self.general,
                                           value=str(abbrev_results),
                                           size=(60, -1), min=0, max=1000)
        self.abbrev_results2.Enable(parent.search.abbrev_results != -1)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.minimize_to_tray, 0, wx.ALL, 5)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(wx.StaticText(self.general, label=_("Default font:")), 0,
                   wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.font_face, 0, wx.ALL, 5)
        sizer2.Add(wx.StaticText(self.general, label=_("Size:")), 0,
                   wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
        sizer2.Add(self.font_size, 0, wx.ALL, 5)
        sizer.Add(sizer2, 0, wx.LEFT | wx.RIGHT, 5)
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3.Add(self.abbrev_results, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer3.Add(self.abbrev_results2, 0, wx.ALL ^ wx.LEFT, 5)
        sizer.Add(sizer3, 0, wx.ALL ^ wx.TOP, 5)
        self.general.SetSizer(sizer)
        self.notebook.AddPage(self.general, _("General"))

        self.versions = wx.Panel(self.notebook)
        self.version_listbox = wx.CheckListBox(self.versions)
        self.LoadVersions(False)
        self.version_listbox.Bind(wx.EVT_LISTBOX, self.OnVersionListbox)
        self.add_versions = wx.HyperlinkCtrl(self.versions,
                                             label=_("Add versions..."),
                                             url="",
                                             style=wx.HL_DEFAULT_STYLE ^
                                             wx.HL_CONTEXTMENU)
        self.add_versions.Bind(wx.EVT_HYPERLINK, self.OnAddVersions)
        self.remove_version = wx.Button(self.versions, label=_("Remove"))
        self.remove_version.Disable()
        self.remove_version.Bind(wx.EVT_BUTTON, self.OnRemoveVersion)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.version_listbox, 1, wx.EXPAND)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(self.add_versions, 1, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 3)
        sizer2.Add(self.remove_version, 0, wx.RIGHT | wx.EXPAND, 3)
        sizer.Add(sizer2, 0, wx.ALL | wx.EXPAND, 2)
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
    
    def LoadVersions(self, clear=True):
        if clear:
            self.version_listbox.Clear()
        version_files = glob.glob(os.path.join(self._parent._app.cwd,
                                               "versions", "*.bbl"))
        if self._parent._app.userdatadir != self._parent._app.cwd:
            version_files. \
                extend(glob.glob(os.path.join(self._parent._app.userdatadir,
                                              "versions", "*.bbl")))
        version_files.sort(key=os.path.basename)
        self.version_names = []
        for i in range(len(version_files)):
            self.version_names.append(os.path.basename(version_files[i])[:-4])
            self.version_listbox.Append("%s - %s" %
                                     (self.version_names[i],
                                      VERSION_DESCRIPTIONS[self.
                                                           version_names[i]].
                                      decode("latin_1")), version_files[i])
            if self.version_names[i] in self._parent.version_list:
                self.version_listbox.Check(i)

    def OnAbbrevResults(self, event):
        self.abbrev_results2.Enable(event.IsChecked())

    def OnVersionListbox(self, event):
        self.remove_version.Enable(os.access(event.GetClientData(), os.W_OK))

    def OnAddVersions(self, event):
        versiondir = os.path.join(self._parent._app.userdatadir, "versions")
        dialog = wx.FileDialog(self, _("Add versions"), versiondir,
                               wildcard=_("Bible Files (*.bbl;*.zip)|*.bbl;"
                                          "*.zip"),
                               style=wx.OPEN | wx.MULTIPLE)
        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath()
            if not path.endswith(".zip"):
                shutil.copy(path, versiondir)
            else:
                with zipfile.ZipFile(path) as zipobj:
                    zipobj.extractall(versiondir)
            self.LoadVersions()
        dialog.Destroy()

    def OnRemoveVersion(self, event):
        delete = wx.MessageBox(_("Are you sure you want to permanently delete "
                                 "this version?"), "Berean",
                               wx.ICON_WARNING | wx.YES_NO)
        if delete == wx.YES:
            selection = self.version_listbox.GetSelection()
            os.remove(self.version_listbox.GetClientData(selection))
            if self.version_names[selection] in self._parent.version_list:
                self._parent.version_list.remove(self.version_names[selection])
                self._parent.old_versions.append(self.version_names[selection])
            self.LoadVersions()

    def OnOk(self, event):
        version_list = [version for i, version in
                        enumerate(self.version_names) if
                        self.version_listbox.IsChecked(i)]
        if not version_list:
            wx.MessageBox(_("You must have at least one version selected."),
                          "Berean", wx.ICON_EXCLAMATION | wx.OK)
            return
        self._parent.minimize_to_tray = self.minimize_to_tray.GetValue()
        default_font = {"size": int(self.font_size.GetValue()),
                        "normal_face": self.font_face.GetStringSelection()}
        if default_font != self._parent.default_font:
            for i in range(self._parent.notebook.GetPageCount()):
                self._parent.get_htmlwindow(i).SetStandardFonts(**default_font)
            for htmlwindow in (self._parent.search.htmlwindow,
                               self._parent.multiverse.htmlwindow,
                               self._parent.printing):
                htmlwindow.SetStandardFonts(**default_font)
            for i in range(self._parent.notes.GetPageCount()):
                self._parent.notes.GetPage(i).set_default_style(default_font)
            self._parent.default_font = default_font
        if version_list != self._parent.version_list:
            for version in VERSION_NAMES:
                if (version in self._parent.version_list and
                        version not in version_list):
                    self._parent.old_versions.append(version)
                elif (version in version_list and
                        version in self._parent.old_versions):
                    self._parent.old_versions.remove(version)
            self._parent.version_list = version_list
            wx.MessageBox(_("Changes to version settings will take effect "
                            "after you restart Berean."), "Berean",
                          wx.ICON_INFORMATION | wx.OK)
        if self.abbrev_results.GetValue():
            self._parent.search.abbrev_results = \
                self.abbrev_results2.GetValue()
        else:
            self._parent.search.abbrev_results = -1
        self.Destroy()

    def OnCancel(self, event):
        self.Destroy()
