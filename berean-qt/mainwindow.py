"""mainwindow.py - main window class"""

import os.path

from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtPrintSupport import (QAbstractPrintDialog, QPageSetupDialog,
    QPrintDialog, QPrinter, QPrintPreviewDialog)
from PyQt5.QtWebKitWidgets import QWebPage
from PyQt5.QtWidgets import (QAction, QDialog, QLabel, QMainWindow, QMenu,
    QMessageBox, QTabWidget)

import dockwindows
import webview
import toolbar
from config import *


class MainWindow(QMainWindow):
    def __init__(self, app):
        super(MainWindow, self).__init__()
        self._app = app
        self.printer = QPrinter()
        self.reference = (1, 1, -1)
        self.zoom = 3

        self.tabwidget = QTabWidget()
        version_list = ("KJV", "WEB")
        for i in range(len(version_list)):
            self.tabwidget.addTab(webview.ChapterWebView(
                self, version_list[i]), version_list[i])
            self.tabwidget.setTabIcon(i, self.get_icon(
                os.path.join("flags", FLAG_NAMES[version_list[i]])))
            self.tabwidget.setTabToolTip(i,
                VERSION_DESCRIPTIONS[version_list[i]])
        self.setCentralWidget(self.tabwidget)
        self.create_actions()
        self.create_menus()
        self.create_toolbars()
        self.create_statusbar()
        self.create_dockwindows()
        rect = app.desktop().availableGeometry(self)
        self.resize(int(rect.width() * 0.8), int(rect.height() * 0.8))
        self.setWindowIcon(QIcon(os.path.join(app.cwd, "berean.ico")))
        self.retranslateUi()

    def get_icon(self, name):
        return QIcon(os.path.join(self._app.cwd, "images", "%s.png" % name))

    def create_actions(self):
        self.action_print = QAction(self, triggered=self.print_)
        self.action_print.setIcon(self.get_icon("print"))
        self.action_page_setup = QAction(self, triggered=self.page_setup)
        self.action_print_preview = QAction(self, triggered=self.print_preview)
        self.action_exit = QAction(self, triggered=self.close)
        self.action_exit.setMenuRole(QAction.QuitRole)
        self.action_copy = QAction(self, triggered=self.copy)
        self.action_copy.setIcon(self.get_icon("copy"))
        self.action_preferences = QAction(self)
        self.action_preferences.setMenuRole(QAction.PreferencesRole)
        self.action_go_to_verse = QAction(self, triggered=self.go_to_verse)
        self.action_go_to_verse.setIcon(self.get_icon("goto-verse"))
        self.action_go_back = QAction(self)
        self.action_go_back.setEnabled(True)
        self.action_go_back.setIcon(self.get_icon("go-back"))
        self.action_go_forward = QAction(self)
        self.action_go_forward.setEnabled(False)
        self.action_go_forward.setIcon(self.get_icon("go-forward"))
        self.action_zoom_in = QAction(self)
        self.action_zoom_in.setIcon(self.get_icon("zoom-in"))
        self.action_zoom_out = QAction(self)
        self.action_zoom_out.setIcon(self.get_icon("zoom-out"))
        self.action_reset_zoom = QAction(self)
        self.action_add_to_favorites = QAction(self)
        self.action_add_to_favorites.setIcon(self.get_icon("add-favorite"))
        self.action_manage_favorites = QAction(self)
        self.action_manage_favorites.setIcon(self.get_icon("manage-favorites"))
        self.action_empty = QAction(self)
        self.action_empty.setEnabled(False)
        self.action_view_all = QAction(self)
        self.action_view_all.setEnabled(False)
        self.action_contents = QAction(self)
        self.action_about = QAction(self, triggered=self.about)
        self.action_about.setMenuRole(QAction.AboutRole)

    def print_(self):
        self.printer.setDocName("%s %d (%s)" %
            (BOOK_NAMES[self.reference[0] - 1], self.reference[1],
            self.tabwidget.tabText(self.tabwidget.currentIndex())))
        dialog = QPrintDialog(self.printer, self)
        if len(self.tabwidget.currentWidget().selectedText()):
            dialog.setOption(QAbstractPrintDialog.PrintSelection, True)
        if dialog.exec_() == QDialog.Accepted:
            self.tabwidget.currentWidget().print_(self.printer)

    def page_setup(self):
        dialog = QPageSetupDialog(self.printer)
        dialog.exec_()

    def print_preview(self):
        self.printer.setDocName("%s %d (%s)" %
            (BOOK_NAMES[self.reference[0] - 1], self.reference[1],
            self.tabwidget.tabText(self.tabwidget.currentIndex())))
        dialog = QPrintPreviewDialog(self.printer)
        dialog.paintRequested.connect(self.tabwidget.currentWidget().print_)
        dialog.exec_()

    def copy(self):
        self.tabwidget.currentWidget().triggerPageAction(QWebPage.Copy)

    def go_to_verse(self):
        pass

    def about(self):
        QMessageBox.about(self, "About Berean", "<div align=\"center\">"
            "<font size=\"+1\"><b>Berean %s</b></font><br />Copyright &copy; "
            "2011-2014 Timothy Johnson<br />An open source, cross-platform "
            "Bible study tool</div>" % VERSION)

    def create_menus(self):
        self.menubar = self.menuBar()
        self.menu_file = QMenu(self.menubar)
        self.menu_file.addAction(self.action_print)
        self.menu_file.addAction(self.action_page_setup)
        self.menu_file.addAction(self.action_print_preview)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_exit)
        self.menubar.addAction(self.menu_file.menuAction())
        self.menu_edit = QMenu(self.menubar)
        self.menu_edit.addAction(self.action_copy)
        self.menu_edit.addSeparator()
        self.menu_edit.addAction(self.action_preferences)
        self.menubar.addAction(self.menu_edit.menuAction())
        self.menu_view = QMenu(self.menubar)
        self.menu_view.addAction(self.action_go_to_verse)
        self.menu_view.addAction(self.action_go_back)
        self.menu_view.addAction(self.action_go_forward)
        self.menu_view.addSeparator()
        self.menu_view.addAction(self.action_zoom_in)
        self.menu_view.addAction(self.action_zoom_out)
        self.menu_view.addAction(self.action_reset_zoom)
        self.menu_view.addSeparator()
        self.menubar.addAction(self.menu_view.menuAction())
        self.menu_favorites = QMenu(self.menubar)
        self.menu_favorites.addAction(self.action_add_to_favorites)
        self.menu_favorites.addAction(self.action_manage_favorites)
        self.menu_favorites.addSeparator()
        self.menu_favorites.addAction(self.action_empty)
        self.menu_favorites.addSeparator()
        self.menu_favorites.addAction(self.action_view_all)
        self.menubar.addAction(self.menu_favorites.menuAction())
        self.menu_help = QMenu(self.menubar)
        self.menu_help.addAction(self.action_contents)
        self.menu_help.addAction(self.action_about)
        self.menubar.addAction(self.menu_help.menuAction())

    def create_toolbars(self):
        self.toolbar = toolbar.ToolBar(self)
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)
        self.action_toolbar = self.toolbar.toggleViewAction()
        self.menu_view.addAction(self.action_toolbar)

    def create_statusbar(self):
        self.statusBar().addWidget(QLabel("%s %d" %
            (BOOK_NAMES[self.reference[0] - 1], self.reference[1])), 1)
        self.statusBar().addPermanentWidget(QLabel(VERSION_DESCRIPTIONS[
            self.tabwidget.tabText(self.tabwidget.currentIndex())]), 1)
        self.zoombar = toolbar.ZoomBar(self)
        self.statusBar().addPermanentWidget(self.zoombar)

    def create_dockwindows(self):
        self.tree = dockwindows.TreeDockWindow()
        self.addDockWidget(Qt.LeftDockWidgetArea, self.tree)
        self.setCorner(Qt.BottomLeftCorner, Qt.LeftDockWidgetArea)
        self.action_tree_pane = self.tree.toggleViewAction()
        self.menu_view.addSeparator()
        self.menu_view.addAction(self.action_tree_pane)
        self.search = dockwindows.SearchDockWindow()
        self.addDockWidget(Qt.RightDockWidgetArea, self.search)
        self.setCorner(Qt.BottomRightCorner, Qt.RightDockWidgetArea)
        self.action_search_pane = self.search.toggleViewAction()
        self.menu_view.addAction(self.action_search_pane)
        self.notes = dockwindows.NotesDockWindow()
        self.addDockWidget(Qt.BottomDockWidgetArea, self.notes)
        self.action_notes_pane = self.notes.toggleViewAction()
        self.menu_view.addAction(self.action_notes_pane)
        self.multiverse = dockwindows.MultiverseDockWindow()
        self.multiverse.setFloating(True)
        self.action_multiverse_pane = self.multiverse.toggleViewAction()
        self.menu_view.addAction(self.action_multiverse_pane)

    def retranslateUi(self):
        _translate = QCoreApplication.translate
        self.setWindowTitle(_translate("MainWindow", "Berean - %s %d (%s)" %
            (BOOK_NAMES[self.reference[0] - 1], self.reference[1],
            self.tabwidget.tabText(self.tabwidget.currentIndex()))))
        self.menu_file.setTitle(_translate("MainWindow", "&File"))
        self.menu_edit.setTitle(_translate("MainWindow", "&Edit"))
        self.menu_view.setTitle(_translate("MainWindow", "&View"))
        self.menu_favorites.setTitle(_translate("MainWindow", "F&avorites"))
        self.menu_help.setTitle(_translate("MainWindow", "&Help"))
        self.toolbar.setWindowTitle(_translate("MainWindow", "Toolbar"))
        self.tree.setWindowTitle(_translate("MainWindow", "Tree"))
        self.search.setWindowTitle(_translate("MainWindow", "Search"))
        self.notes.setWindowTitle(_translate("MainWindow", "Notes"))
        self.multiverse.setWindowTitle(
            _translate("MainWindow", "Multi-Verse Retrieval"))
        self.action_print.setText(_translate("MainWindow", "&Print..."))
        self.action_print.setShortcut(_translate("MainWindow", "Ctrl+P"))
        self.action_page_setup.setText(
            _translate("MainWindow", "Page &Setup..."))
        self.action_print_preview.setText(
            _translate("MainWindow", "P&rint Preview..."))
        self.action_exit.setText(_translate("MainWindow", "E&xit"))
        self.action_exit.setShortcut(_translate("MainWindow", "Alt+F4"))
        self.action_copy.setText(_translate("MainWindow", "&Copy"))
        self.action_copy.setShortcut(_translate("MainWindow", "Ctrl+C"))
        self.action_preferences.setText(
            _translate("MainWindow", "&Preferences..."))
        self.action_go_to_verse.setText(
            _translate("MainWindow", "&Go to Verse"))
        self.action_go_back.setText(_translate("MainWindow", "Go &Back"))
        self.action_go_back.setIconText(_translate("MainWindow", "Back"))
        self.action_go_back.setShortcut(_translate("MainWindow", "Alt+Left"))
        self.action_go_forward.setText(_translate("MainWindow", "Go &Forward"))
        self.action_go_forward.setIconText(_translate("MainWindow", "Forward"))
        self.action_go_forward.setShortcut(_translate("MainWindow",
            "Alt+Right"))
        self.action_zoom_in.setText(_translate("MainWindow", "Zoom &In"))
        self.action_zoom_in.setShortcut(_translate("MainWindow", "Ctrl++"))
        self.action_zoom_out.setText(_translate("MainWindow", "Zoom &Out"))
        self.action_zoom_out.setShortcut(_translate("MainWindow", "Ctrl+-"))
        self.action_reset_zoom.setText(_translate("MainWindow", "Reset Zoom"))
        self.action_reset_zoom.setShortcut(_translate("MainWindow", "Ctrl+0"))
        self.action_toolbar.setText(_translate("MainWindow", "&Toolbar"))
        self.action_tree_pane.setText(_translate("MainWindow", "T&ree Pane"))
        self.action_tree_pane.setShortcut(
            _translate("MainWindow", "Ctrl+Shift+T"))
        self.action_search_pane.setText(
            _translate("MainWindow", "&Search Pane"))
        self.action_search_pane.setShortcut(
            _translate("MainWindow", "Ctrl+Shift+S"))
        self.action_notes_pane.setText(_translate("MainWindow", "&Notes Pane"))
        self.action_notes_pane.setShortcut(
            _translate("MainWindow", "Ctrl+Shift+N"))
        self.action_multiverse_pane.setText(
            _translate("MainWindow", "&Multi-Verse Retrieval"))
        self.action_multiverse_pane.setShortcut(
            _translate("MainWindow", "Ctrl+M"))
        self.action_add_to_favorites.setText(
            _translate("MainWindow", "&Add to Favorites"))
        self.action_add_to_favorites.setShortcut(
            _translate("MainWindow", "Ctrl+D"))
        self.action_manage_favorites.setText(
            _translate("MainWindow", "&Manage Favorites..."))
        self.action_empty.setText(_translate("MainWindow", "(Empty)"))
        self.action_view_all.setText(_translate("MainWindow", "View All"))
        self.action_contents.setText(_translate("MainWindow", "&Help..."))
        self.action_contents.setShortcut(_translate("MainWindow", "F1"))
        self.action_about.setText(_translate("MainWindow", "&About Berean..."))
