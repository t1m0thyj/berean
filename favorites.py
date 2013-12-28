"""favorites.py - favorites system for Berean"""

import wx
from wx import gizmos

from panes.search import refalize

_ = wx.GetTranslation

class FavoritesMenu(wx.Menu):
    def __init__(self, frame):
        wx.Menu.__init__(self)
        self._frame = frame

        self.favorites = frame._app.settings["FavoritesList"]
        self.ids = {}

        self.ID_ADD = wx.NewId()
        self.Append(self.ID_ADD, _("&Add to Favorites\tCtrl+D"))
        frame.Bind(wx.EVT_MENU, self.OnAdd, id=self.ID_ADD)
        self.ID_MANAGE = wx.NewId()
        self.Append(self.ID_MANAGE, _("&Manage Favorites..."))
        frame.Bind(wx.EVT_MENU, self.OnManage, id=self.ID_MANAGE)
        self.AppendSeparator()
        self.AppendSeparator()
        self.ID_VIEW_ALL = wx.NewId()
        self.Append(self.ID_VIEW_ALL, _("View All"))
        frame.Bind(wx.EVT_MENU, self.OnViewAll, id=self.ID_VIEW_ALL)

        self.UpdateFavorites()

    def HasFavorite(self, info, favorites=None):
        if not favorites:
            favorites = self.favorites
        for i in range(len(favorites)):
            if refalize(favorites[i]) == info:
                return i
        return -1

    def UpdateFavorites(self):
        for id in self.ids:
            self.Remove(id)
        self.ids = {}
        if len(self.favorites):
            for i in range(len(self.favorites)):
                id = wx.NewId()
                self.Insert(i + 3, id, self.favorites[i])
                self.ids[id] = self.favorites[i]
                self._frame.Bind(wx.EVT_MENU, self.OnFavorite, id=id)
        else:
            id = wx.NewId()
            self.Insert(3, id, _("(Empty)"))
            self.ids[id] = None
            self.Enable(id, False)

    def OnAdd(self, event):
        if self._frame.reference[2] == -1:
            favorite = "%s %s" % (self._frame.books[self._frame.reference[0] - 1], self._frame.reference[1])
        else:
            favorite = "%s %s:%s" % (self._frame.books[self._frame.reference[0] - 1], self._frame.reference[1], self._frame.reference[2])
        if self.HasFavorite(refalize(favorite)) == -1:
            self.favorites.append(favorite)
            self.UpdateFavorites()
        else:
            wx.MessageBox(_("%s is already in the favorites list.") % favorite, "Berean", wx.ICON_EXCLAMATION | wx.OK)

    def OnManage(self, event):
        dialog = FavoritesManager(self._frame)
        dialog.Show()

    def OnFavorite(self, event):
        reference = self.ids[event.GetId()]
        try:
            self._frame.LoadChapter(*refalize(reference))
        except:
            wx.MessageBox(_("Sorry, but I do not understand '%s'.\n\nIf you think that Berean should accept it,\nplease email <timothysw@objectmail.com>.") % reference, "Berean", wx.ICON_EXCLAMATION | wx.OK)

    def OnViewAll(self, event):
        self._frame.MultiverseSearch("\n".join(self.favorites))


class FavoritesManager(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, _("Manage Favorites"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self._parent = parent

        self.favorites = gizmos.EditableListBox(self, -1, _("Favorites List\n(e.g., Psa 23 (Comfort), John 3:16-17)"))
        self.favorites.SetStrings(parent.menubar.Favorites.favorites)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.favorites, 1, wx.ALL | wx.EXPAND, 2)
        sizer2 = wx.StdDialogButtonSizer()
        sizer2.AddButton(wx.Button(self, wx.ID_OK))
        sizer2.AddButton(wx.Button(self, wx.ID_CANCEL))
        sizer2.Realize()
        sizer.Add(sizer2, 0, wx.ALL | wx.EXPAND, 3)
        self.SetSizer(sizer)
        self.Layout()

        self.favorites.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.OnEndLabelEdit)
        self.Bind(wx.EVT_BUTTON, self.OnOk, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)

    def OnEndLabelEdit(self, event):
        if not event.IsEditCancelled():
            label = event.GetLabel()
            try:
                info = refalize(label)
            except:
                wx.MessageBox(_("Sorry, but I do not understand '%s'.\n\nIf you think that Berean should accept it,\nplease email <timothysw@objectmail.com>.") % label, _("Manage Favorites"), wx.ICON_EXCLAMATION | wx.OK)
                event.Veto()
            else:
                index = self._parent.menubar.Favorites.HasFavorite(info, self.favorites.GetStrings())
                if index != -1 and index != event.GetIndex():
                    if info[2] != -1:
                        wx.MessageBox(_("%s %d:%d is already in the favorites list.") % (self._parent.books[info[0] - 1], info[1], info[2]), _("Manage Favorites"), wx.ICON_EXCLAMATION | wx.OK)
                    else:
                        wx.MessageBox(_("%s %d is already in the favorites list.") % (self._parent.books[info[0] - 1], info[1]), _("Manage Favorites"), wx.ICON_EXCLAMATION | wx.OK)
                    event.Veto()
                else:
                    event.Skip()

    def OnOk(self, event):
        self._parent.menubar.Favorites.favorites = self.favorites.GetStrings()
        self._parent.menubar.Favorites.UpdateFavorites()
        self.Destroy()

    def OnCancel(self, event):
        self.Destroy()
