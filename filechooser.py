#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   filechooser.py por:
#   Cristian García <cristian99garcia@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os
from gettext import gettext as _

import utils
import globals as G

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GObject
from gi.repository import GdkPixbuf

from sugar3.graphics import style
from sugar3.graphics.alert import Alert
from sugar3.graphics.alert import TimeoutAlert
from sugar3.graphics.toolbutton import ToolButton
from sugar3.graphics.toggletoolbutton import ToggleToolButton


class FileChooser(Gtk.Window):

    def __init__(self, folder=None):
        Gtk.Window.__init__(self)

        self.entries = []
        self.model = Gtk.ListStore(str, GdkPixbuf.Pixbuf, str)

        self.folder = folder
        if folder is None or not os.path.exists(self.folder):
            self.folder = os.path.expanduser("~/")

        self.files = []
        self.show_hidden_files = False

        if os.path.isfile(self.folder):
            self.folder = self.go_up(self.folder, _return=True)

        self.set_modal(True)
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_size_request(G.WIDTH, G.HEIGHT)
        self.set_border_width(style.LINE_WIDTH)
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.modify_bg(Gtk.StateType.NORMAL, style.COLOR_WHITE.get_gdk_color())

        self.add_events(Gdk.EventMask.KEY_RELEASE_MASK)

        self.connect("key-release-event", self.__key_release_event_cb)

        self.vbox = Gtk.VBox()
        self.add(self.vbox)

        scrolled = Gtk.ScrolledWindow()
        self.vbox.pack_end(scrolled, True, True, 0)

        self.view = Gtk.IconView()
        self.view.set_model(self.model)
        self.view.set_text_column(0)
        self.view.set_pixbuf_column(1)
        self.view.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        scrolled.add(self.view)

        self.go_up_button = ToolButton(icon_name="go-up")
        self.go_up_button.props.accelerator = "<Alt>S"
        self.go_up_button.set_tooltip(_("Go to pather directory"))
        self.go_up_button.connect("clicked", self.go_up)

        self.entry = Gtk.Entry()
        self.entry.set_size_request(300, -1)
        self.entry.set_text(self.folder)
        self.entries.append(self.entry)

        self._gfile = None
        self._file_monitor = None
        self._files_changed_idx = None

        self.set_directory(self.folder)

    def __key_release_event_cb(self, widget, event):
        if event.keyval == Gdk.KEY_Return:
            self._open_path()

        elif event.keyval == Gdk.KEY_BackSpace:
            for entry in self.entries:
                if entry.has_focus():
                    return

            self.go_up()

        elif event.keyval == Gdk.KEY_Escape:
            self.close()

    def __files_changed_cb(self, monitor, file, other_file, event):
        if event == Gio.FileMonitorEvent.DELETED:
            if file.equal(Gio.File.new_for_path(self.folder)):
                self.go_up()

            else:
                self.__remove_item(file.get_path())

        elif event == Gio.FileMonitorEvent.CHANGES_DONE_HINT:
            self.__append_item(file.get_path())

    def __append_item(self, path):
        filename = os.path.basename(path)
        self.files.append(filename)

        if utils.is_hidden_filename(filename) and not self.show_hidden_files:
            return

        folders, files = utils.split_directory_content(self.folder, self.files)

        # We can't use folders.index/files.index because it always include
        # hidden directories/files
        index = 0

        # Include directories in case path is a file because all files are
        # displayed after directories
        for _path in folders:
            name = utils.get_path_name(_path)
            if utils.is_hidden_filename(name) and not self.show_hidden_files:
                continue

            if name == filename and os.path.isdir(path):
                break

            index += 1

        if os.path.isfile(path):
            for _path in files:
                name = utils.get_path_name(_path)
                if utils.is_hidden_filename(name) and \
                        not self.show_hidden_files:

                    continue

                if name == filename:
                    break

                index += 1

        self.model.insert(
            index, [filename, utils.get_pixbuf_from_path(path), path])

    def __remove_item(self, path):
        filename = os.path.basename(path)

        for row in self.model:
            if row[0] == filename:
                self.model.remove(row.iter)
                break

    def set_directory(self, path):
        if self._files_changed_idx is not None:
            self._file_monitor.disconnect(self._files_changed_idx)
            del self._gfile
            del self._file_monitor

        self.folder = path
        self.check_files()

        self._gfile = Gio.File.new_for_path(self.folder)
        self._file_monitor = Gio.File.monitor(
            self._gfile, Gio.FileMonitorFlags.NONE, None)
        self._files_changed_idx = \
            self._file_monitor.connect("changed", self.__files_changed_cb)

    def go_up(self, button=None, _return=False):
        path = "/"
        folders = []

        if self.folder == "/":
            return

        for folder in self.folder.split("/"):
            if not folder:
                continue

            folders.append(folder)

        if not folders:
            return

        for folder in folders[:-1]:
            if folder:
                path += folder + "/"

        if not _return:
            self.set_directory(path)

        else:
            return path

    def show_folder(self):
        folders, files = utils.get_directory_content(self.folder)
        self.model.clear()

        for path in folders + files:
            filename = utils.get_path_name(path)
            self.files.append(filename)

            if not self.show_hidden_files:
                if filename.endswith("~") or filename.startswith("."):
                    continue

            pixbuf = utils.get_pixbuf_from_path(path)
            self.model.append([filename, pixbuf, path])

    def check_files(self):
        files = sorted(os.listdir(self.folder))

        if files != self.files:
            self.selected_path = None

            self.entry.set_text(self.folder)
            self.go_up_button.set_sensitive(self.folder != "/")

            self.show_folder()

        return True

    def create_alert(self, path):
        pass

    def close(self, *args):
        self.destroy()


class FileChooserOpen(FileChooser):

    __gsignals__ = {
        "open-file": (GObject.SIGNAL_RUN_FIRST, None, [str])
    }

    def __init__(self, folder=None):
        FileChooser.__init__(self, folder)

        self.view.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
        self.view.connect("selection-changed", self.__selection_changed)
        self.view.connect("button-press-event", self.__button_press_event_cb)
        self.entry.connect("activate", self._open_path_from_entry)

        self.__make_toolbar()
        self.show_folder()

        self.show_all()

    def __make_toolbar(self):
        self.toolbar = Gtk.Toolbar()
        self.toolbar.modify_bg(
            Gtk.StateType.NORMAL, style.COLOR_TOOLBAR_GREY.get_gdk_color())

        self.toolbar.insert(self.go_up_button, -1)

        self.toolbar.insert(Gtk.SeparatorToolItem(), -1)

        self.hidden_files_button = ToggleToolButton("show-hidden-files")
        self.hidden_files_button.props.accelerator = "<Ctrl>H"
        self.hidden_files_button.set_tooltip(_("Show hidden files"))
        self.hidden_files_button.connect("clicked", self.__show_hidden_files)
        self.toolbar.insert(self.hidden_files_button, -1)

        self.toolbar.insert(Gtk.SeparatorToolItem(), -1)

        item = Gtk.ToolItem()
        item.add(self.entry)
        self.toolbar.insert(item, -1)

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        self.toolbar.insert(separator, -1)

        self.button_open = ToolButton(icon_name="fileopen")
        self.button_open.set_tooltip(_("Open selected file"))
        self.button_open.set_sensitive(False)
        self.button_open.connect("clicked", self._open_path)
        self.toolbar.insert(self.button_open, -1)

        self.close_button = ToolButton(icon_name="dialog-cancel")
        self.close_button.connect("clicked", self.close)
        self.toolbar.insert(self.close_button, -1)

        self.vbox.pack_start(self.toolbar, False, False, 0)

    def __show_hidden_files(self, button):
        self.show_hidden_files = button.get_active()
        self.show_folder()

    def __alert_response(self, alert, response):
        self.vbox.remove(alert)

    def __selection_changed(self, view):
        if self.view.get_selected_items():
            path = self.view.get_selected_items()[0]
            iter = self.model.get_iter(path)
            self.selected_path = os.path.join(
                self.folder, self.model.get_value(iter, 0))
            self.button_open.set_sensitive(True)

        else:
            self.selected_path = None
            self.button_open.set_sensitive(False)

    def __button_press_event_cb(self, view, event):
        if event.button != 1:
            return

        try:
            path = view.get_path_at_pos(int(event.x), int(event.y))
            iter = self.model.get_iter(path)
            directory = os.path.join(
                self.folder, self.model.get_value(iter, 0))

            if event.type.value_name == "GDK_2BUTTON_PRESS":
                if os.path.isdir(directory):
                    self.set_directory(directory)

                elif os.path.isfile(directory):
                    self.emit("open-file", directory)
                    self.destroy()

        except TypeError:
            self.selected_path = None
            self.button_open.set_sensitive(False)

    def create_alert(self, path):
        alert = TimeoutAlert(10)
        alert.props.title = G.TEXT_FILE_NOT_EXISTS1
        alert.props.msg = G.TEXT_FILE_NOT_EXISTS2

        hbox = alert.get_children()[0]
        buttonbox = hbox.get_children()[1]
        button = buttonbox.get_children()[0]
        buttonbox.remove(button)

        alert.connect("response", self.__alert_response)

        self.vbox.pack_start(alert, False, False, 0)
        self.vbox.reorder_child(alert, 2)

    def _open_path(self, button=None):
        files = []
        directory = None

        for item in self.view.get_selected_items():
            iter = self.model.get_iter(item)
            path = self.model.get_value(iter, 2)

            if os.path.isfile(path):
                files.append(path)

            elif os.path.isdir(path) and not directory:
                directory = path

        if files:
            for path in files:
                GObject.idle_add(self.emit, "open-file", path)
                self.emit("open-file", path)
                self.selected_path = None

            self.destroy()

        else:
            if directory:
                self.folder = directory

    def _open_path_from_entry(self, entry):
        path = self.entry.get_text()

        if not os.path.exists(path):
            self.create_alert(path)
            return

        if os.path.isdir(path):
            self.folder = path
            self.check_files()

        elif os.path.isfile(path):
            self.emit("open-file", path)
            self.destroy()


class FileChooserSave(FileChooser):

    __gsignals__ = {
        "save-file": (GObject.SIGNAL_RUN_FIRST, None, [str])
    }

    def __init__(self, folder=None):
        FileChooser.__init__(self, folder)

        self.alert = None
        self.view.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.view.connect("selection-changed", self.__selection_changed)
        self.view.connect("button-press-event", self.__button_press_event_cb)
        self.entry.connect("activate", self._save_path_from_entry)

        self.connect("key-release-event", self.__key_release_event_cb)

        self.__make_toolbar()
        self.show_folder()

        self.show_all()

    def __make_toolbar(self):
        self.toolbar = Gtk.Toolbar()
        self.toolbar.modify_bg(
            Gtk.StateType.NORMAL, style.COLOR_TOOLBAR_GREY.get_gdk_color())

        self.toolbar.insert(self.go_up_button, -1)

        self.toolbar.insert(Gtk.SeparatorToolItem(), -1)

        self.button_new_folder = ToolButton(icon_name="new-folder")
        self.button_new_folder.set_tooltip(_("Create a folder"))
        self.button_new_folder.connect("clicked", self.create_folder)
        self.toolbar.insert(self.button_new_folder, -1)

        item = Gtk.ToolItem()
        item.add(self.entry)
        self.toolbar.insert(item, -1)

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        self.toolbar.insert(separator, -1)

        item = Gtk.ToolItem()
        self.entry_name = Gtk.Entry()
        self.entry_name.set_size_request(200, -1)
        self.entry_name.set_placeholder_text("Select a name for this file.")
        self.entry_name.connect("activate", self.__name_selected)
        item.add(self.entry_name)
        self.toolbar.insert(item, -1)
        self.entries.append(self.entry_name)

        self.button_save = ToolButton(icon_name="save-as")
        self.button_save.connect("clicked", self.__save_path_from_button)
        self.toolbar.insert(self.button_save, -1)

        self.close_button = ToolButton(icon_name="dialog-cancel")
        self.close_button.connect("clicked", self.close)
        self.toolbar.insert(self.close_button, -1)

        self.vbox.pack_start(self.toolbar, False, False, 0)

    def __key_release_event_cb(self, widget, event):
        if event.keyval == Gdk.KEY_Return:
            if self.area.get_selected_items():
                self.__name_selected()

        elif event.keyval == Gdk.KEY_BackSpace:
            if not self.entry.has_focus() and not self.entry_name.has_focus():
                self.go_up()

        elif event.keyval == Gdk.KEY_Escape:
            self.close()

    def create_folder(self, widget):
        self.button_new_folder.set_sensitive(False)

        entry = Gtk.Entry()
        entry.set_placeholder_text("Select a name")
        entry.connect("activate", self.__create_new_folder)

        item = Gtk.ToolItem()
        item.add(entry)
        self.toolbar.insert(item, 4)
        self.toolbar.show_all()

    def __create_new_folder(self, entry):
        if entry.get_text():
            try:
                path = os.path.join(self.folder, entry.get_text())
                os.mkdir(path)
                self.folder = path

            except OSError as msg:
                if self.alert:
                    self.vbox.remove(self.alert)
                    self.alert = None
                self.alert = Alert()
                self.alert.props.title = G.TEXT_ERROR_CREATING_FOLDER
                self.alert.props.msg = msg
                image = Gtk.Image.new_from_stock(
                    Gtk.STOCK_OK, Gtk.IconSize.MENU)
                self.alert.add_button(Gtk.ResponseType.NO, _("Ok"), icon=image)

                self.alert.connect("response", self.__alert_response)

                self.vbox.pack_start(self.alert, False, False, 0)
                self.vbox.reorder_child(self.alert, 1)

        item = entry.get_parent()
        self.toolbar.remove(item)
        self.button_new_folder.set_sensitive(True)

    def __save_path_from_button(self, button):
        self.__name_selected()

    def __name_selected(self, entry=None):
        path = os.path.join(self.folder, self.entry_name.get_text())
        self._save_path_from_entry(path=path)

    def _save_path_from_entry(self, entry=None, path=None):
        if not path:
            path = self.entry.get_text()

        if os.path.exists(path):
            if os.path.isdir(path):
                self.folder = path

            elif os.path.isfile(path):
                self.create_alert(path)

        elif not os.path.exists(path):
            if os.path.isdir(self.go_up(path, _return=True)):
                self.emit("save-file", path)
                self.destroy()

    def create_alert(self, path):
        if self.alert:
            self.vbox.remove(self.alert)
            self.alert = None

        self.alert = Alert()
        self.alert.props.title = G.TEXT_FILE_ALREADY_EXISTS
        self.alert.props.msg = G.TEXT_OVERWRITE_QUESTION.replace("****", path)
        cancel = Gtk.Image.new_from_icon_name(
            "dialog-cancel", Gtk.IconSize.MENU)
        save = Gtk.Image.new_from_icon_name("filesave", Gtk.IconSize.MENU)
        self.alert.add_button(Gtk.ResponseType.NO, _("Cancel"), icon=cancel)
        self.alert.add_button(Gtk.ResponseType.YES, _("Save"), icon=save)

        self.alert.connect("response", self.__alert_response, path)

        self.vbox.pack_start(self.alert, False, False, 0)
        self.vbox.reorder_child(self.alert, 2)

    def __alert_response(self, alert, response, path):
        if response == Gtk.ResponseType.NO:
            self.vbox.remove(alert)

        elif response == Gtk.ResponseType.YES:
            self.emit("save-file", path)
            self.destroy()
        self.alert_status = 0
        self.alert = None

    def __selection_changed(self, view):
        if self.view.get_selected_items():
            path = self.view.get_selected_items()[0]
            iter = self.model.get_iter(path)
            name = self.model.get_value(iter, 0)
            if os.path.isfile(os.path.join(self.folder, name)):
                self.entry_name.set_text(name)

            else:
                self.entry_name.set_text("")

        else:
            self.entry_name.set_text("")

    def __button_press_event_cb(self, view, event):
        if event.button != 1:
            return

        try:
            path = view.get_path_at_pos(int(event.x), int(event.y))
            iter = self.model.get_iter(path)
            directory = os.path.join(
                self.folder, self.model.get_value(iter, 0))

            if event.type.value_name == "GDK_2BUTTON_PRESS":
                if os.path.isdir(directory):
                    self.folder = directory
                    self.selected_path = None

                elif os.path.isfile(directory):
                    self.selected_path = directory
                    self.create_alert(directory)

            elif event.type.value_name == "GDK_1BUTTON_PRESS":
                self.selected_path = directory

        except TypeError:
            self.selected_path = None
