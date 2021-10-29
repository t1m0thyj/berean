"""preferences.py - preferences dialog class"""

import glob
import os
import pickle
import shutil

import wx
from wx import adv

import sword
from settings import BOOK_NAMES, FONT_SIZES

_ = wx.GetTranslation
LANGUAGES = {"en_GB": "English (Great Britain)", "en_US": "English (United States)"}


def import_version(infile, outdir):
    dialog = wx.ProgressDialog(_("Importing %s") % os.path.splitext(os.path.basename(infile))[0], "", 70)
    sword_bible = sword.Bible(infile)
    ber_bible = sword.osis2bbl(sword_bible,
        lambda idx, name: dialog.Update(idx + 1, _("Processing %s...") % BOOK_NAMES[idx - 1]))
    dialog.Update(68, _("Saving Bible..."))
    with open(os.path.join(outdir, os.path.splitext(infile)[0] + ".bbl"), 'wb') as fileobj:
        pickle.dump(ber_bible[0], fileobj)
        ber_bible[0] = None
        pickle.dump(ber_bible, fileobj)
    dialog.Update(70)
    dialog.Destroy()


class PreferencesDialog(wx.Dialog):
    def __init__(self, parent):
        super(PreferencesDialog, self).__init__(parent, title=_("Preferences"),
                                                style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self._parent = parent
        self.notebook = wx.Notebook(self, style=wx.NB_MULTILINE)

        self.general = wx.Panel(self.notebook)
        self.language = adv.BitmapComboBox(self.general, size=(200, -1),
                                           style=wx.CB_READONLY | wx.CB_SORT)
        for language in LANGUAGES:
            bitmap = parent.get_bitmap(os.path.join("flags", language[3:].lower()))
            self.language.Append(LANGUAGES[language], bitmap, language)
        self.language.SetStringSelection(LANGUAGES[parent._app.language])
        self.font_face = wx.Choice(self.general, choices=parent.facenames)
        self.font_face.SetStringSelection(parent.default_font["normal_face"])
        self.font_size = wx.ComboBox(self.general, choices=FONT_SIZES)
        self.font_size.SetStringSelection(str(parent.default_font["size"]))
        self.single_instance = wx.CheckBox(self.general, label=_("Allow single instance only"))
        self.single_instance.SetValue(parent._app.single_instance)
        self.minimize_to_tray = wx.CheckBox(self.general, label=_("Minimize to system tray"))
        self.minimize_to_tray.SetValue(parent.minimize_to_tray)
        self.autocomp_books = wx.CheckBox(self.general,
                                          label=_("Auto-complete book names in reference textbox"))
        self.autocomp_books.SetValue(parent.toolbar.autocomp_books)
        self.abbrev_results = wx.CheckBox(self.general, label=_("Abbreviate search results when "
                                                                "there are more than"))
        self.abbrev_results.SetValue(parent.search.abbrev_results != -1)
        self.abbrev_results.Bind(wx.EVT_CHECKBOX, self.OnAbbrevResults)
        if parent.search.abbrev_results != -1:
            abbrev_results = parent.search.abbrev_results
        else:
            abbrev_results = 1000
        if '__WXGTK__' not in wx.PlatformInfo:
            self.abbrev_results2 = wx.SpinCtrl(self.general, value=str(abbrev_results),
                                               size=(60, -1), min=0, max=1000)
        else:
            self.abbrev_results2 = wx.SpinCtrl(self.general, value=str(abbrev_results), min=0,
                                               max=1000)
        self.abbrev_results2.Enable(parent.search.abbrev_results != -1)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(wx.StaticText(self.general, label=_("Language:")), 0, wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.language, 1, wx.ALL, 5)
        sizer.Add(sizer2, 0, wx.ALL ^ wx.BOTTOM | wx.EXPAND, 5)
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3.Add(wx.StaticText(self.general, label=_("Default font:")), 0,
                   wx.ALIGN_CENTER_VERTICAL)
        sizer3.Add(self.font_face, 1, wx.ALL, 5)
        sizer3.Add(wx.StaticText(self.general, label=_("Size:")), 0,
                   wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
        sizer3.Add(self.font_size, 0, wx.ALL, 5)
        sizer.Add(sizer3, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
        sizer.Add(self.single_instance, 0, wx.ALL ^ wx.BOTTOM, 5)
        sizer.Add(self.minimize_to_tray, 0, wx.ALL ^ wx.BOTTOM, 5)
        sizer.Add(self.autocomp_books, 0, wx.ALL ^ wx.BOTTOM, 5)
        sizer4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer4.Add(self.abbrev_results, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer4.Add(self.abbrev_results2, 0, wx.ALL ^ wx.LEFT, 5)
        sizer.Add(sizer4, 0, wx.ALL ^ wx.TOP, 5)
        self.general.SetSizer(sizer)
        self.notebook.AddPage(self.general, _("General"))

        self.versions = wx.Panel(self.notebook)
        self.version_listbox = wx.CheckListBox(self.versions)
        self.LoadVersions(False)
        self.version_listbox.Bind(wx.EVT_LISTBOX, self.OnVersionListbox)
        self.add_versions = adv.HyperlinkCtrl(self.versions, wx.ID_ANY, label=_("Add versions..."),
                                             url="", style=wx.NO_BORDER | adv.HL_ALIGN_LEFT)
        self.add_versions.Bind(adv.EVT_HYPERLINK, self.OnAddVersions)
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
        version_files = glob.glob(os.path.join(self._parent._app.cwd, "versions", "*.bbl"))
        if self._parent._app.userdatadir != self._parent._app.cwd:
            version_files.extend(glob.glob("%s\\*.bbl" % self._parent.versiondir))
        version_files.sort(key=os.path.basename)
        self.version_names = []
        for i in range(len(version_files)):
            self.version_names.append(os.path.basename(version_files[i])[:-4])
            with open(version_files[i], 'rb') as fileobj:
                version_description = pickle.load(fileobj)["description"]
            self.version_listbox.Append("%s - %s" % (self.version_names[i], version_description), version_files[i])
            if self.version_names[i] in self._parent.version_list:
                self.version_listbox.Check(i)

    def OnAbbrevResults(self, event):
        self.abbrev_results2.Enable(event.IsChecked())

    def OnVersionListbox(self, event):
        version_file = event.GetClientObject()
        if version_file:
            self.remove_version.Enable(os.access(version_file, os.W_OK))

    def OnAddVersions(self, event):
        dialog = wx.FileDialog(self, _("Add versions"), self._parent.versiondir,
                               wildcard=_("Bible files (*.bbl;*.zip)|*.bbl;*.zip"),
                               style=wx.FD_OPEN | wx.FD_MULTIPLE)
        if dialog.ShowModal() == wx.ID_OK:
            for path in dialog.GetPaths():
                if not path.endswith(".zip"):
                    shutil.copy(path, self._parent.versiondir)
                else:
                    import_version(path, self._parent.versiondir)
            self.LoadVersions()
        dialog.Destroy()

    def OnRemoveVersion(self, event):
        delete = wx.MessageBox(_("Are you sure you want to permanently delete this version?"),
                               "Berean", wx.ICON_WARNING | wx.YES_NO)
        if delete == wx.YES:
            selection = self.version_listbox.GetSelection()
            os.remove(self.version_listbox.GetClientData(selection))
            self.version_listbox.Delete(selection)
            version_name = self.version_names.pop(selection)
            if version_name in self._parent.version_list:
                self._parent.version_list.remove(version_name)
            if version_name not in self._parent.old_versions:
                self._parent.old_versions.append(version_name)

    def OnOk(self, event):
        version_list = [version for i, version in enumerate(self.version_names)
                        if self.version_listbox.IsChecked(i)]
        if not version_list:
            wx.MessageBox(_("You must have at least one version selected."), "Berean",
                          wx.ICON_EXCLAMATION | wx.OK)
            return
        language = self.language.GetClientData(self.language.GetSelection())
        if language != self._parent._app.language or version_list != self._parent.version_list:
            wx.MessageBox(_("Changes to language and version settings will take effect after you "
                            "restart Berean."), "Berean", wx.ICON_INFORMATION | wx.OK)
        self._parent._app.language = language
        default_font = {"size": int(self.font_size.GetValue()),
                        "normal_face": self.font_face.GetStringSelection()}
        if default_font != self._parent.default_font:
            for i in range(self._parent.notebook.GetPageCount()):
                self._parent.get_htmlwindow(i).SetStandardFonts(**default_font)
            for htmlwindow in (self._parent.search.htmlwindow, self._parent.printing):
                htmlwindow.SetStandardFonts(**default_font)
            self._parent.default_font = default_font
        if version_list != self._parent.version_list:
            for version in set(sorted(self._parent.version_list + version_list)):
                if version in self._parent.version_list and version not in version_list:
                    self._parent.old_versions.append(version)
                elif version in version_list and version in self._parent.old_versions:
                    self._parent.old_versions.remove(version)
            self._parent.version_list = version_list
        self._parent._app.single_instance = self.single_instance.GetValue()
        self._parent._app.SetSingleInstance(self._parent._app.single_instance)
        self._parent.minimize_to_tray = self.minimize_to_tray.GetValue()
        autocomp_books = self.autocomp_books.GetValue()
        self._parent.toolbar.autocomp_books = autocomp_books
        self._parent.toolbar.verse_entry.AutoComplete(BOOK_NAMES if autocomp_books else [])
        if self.abbrev_results.GetValue():
            self._parent.search.abbrev_results = self.abbrev_results2.GetValue()
        else:
            self._parent.search.abbrev_results = -1
        self.Destroy()

    def OnCancel(self, event):
        self.Destroy()
