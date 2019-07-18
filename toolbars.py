#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   toolbars.py por:
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

import utils
from font import FontSize
from font import FontComboBox
from combo_styles import ComboStyles

from gettext import gettext as _

from gi.repository import Gtk
from gi.repository import GObject

from sugar3.graphics.iconentry import IconEntry
from sugar3.graphics.toolbutton import ToolButton
from sugar3.graphics.toolbarbox import ToolbarBox as SugarToolbarbox
from sugar3.graphics.toolbarbox import ToolbarButton
from sugar3.graphics.toggletoolbutton import ToggleToolButton

from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.activity.widgets import StopButton
from sugar3.activity.widgets import EditToolbar as SugarEditToolbar


class FileToolbar(Gtk.Toolbar):

    __gsignals__ = {
        "new-page": (GObject.SIGNAL_RUN_LAST, None, []),
        "chooser-open": (GObject.SIGNAL_RUN_LAST, None, []),
        "chooser-save": (GObject.SIGNAL_RUN_LAST, None, [bool]),
        "print-file": (GObject.SIGNAL_RUN_LAST, None, []),
    }

    def __init__(self):
        Gtk.Toolbar.__init__(self)

        self.button = ToolbarButton(page=self, icon_name="txt")

        button_new = ToolButton("new-file")
        button_new.props.accelerator = "<Ctrl>N"
        button_new.connect("clicked", lambda button: self.emit("new-page"))
        button_new.set_tooltip(_("New file"))
        self.insert(button_new, -1)

        button_open = ToolButton("fileopen")
        button_open.props.accelerator = "<Ctrl>O"
        button_open.set_tooltip(_("Open file from file system"))
        button_open.connect(
            "clicked", lambda button: self.emit("chooser-open"))
        self.insert(button_open, -1)

        self.button_save = ToolButton("filesave")
        self.button_save.props.accelerator = "<Ctrl>S"
        self.button_save.set_tooltip(_("Save file to the file system"))
        self.button_save.connect(
            "clicked", lambda button: self.emit("chooser-save", False))
        self.insert(self.button_save, -1)

        button_save_as = ToolButton("save-as")
        button_save_as.props.accelerator = "<Ctrl><Mayus>S"
        button_save_as.set_tooltip(_("Save as file to the file system"))
        button_save_as.connect(
            "clicked", lambda button: self.emit("chooser-save", True))
        self.insert(button_save_as, -1)

        self.insert(utils.make_separator(False), -1)

        button_print = ToolButton("printer")
        button_print.props.accelerator = "<Ctrl>I"
        button_print.set_tooltip(_("Print file"))
        button_print.connect("clicked", lambda widget: self.emit("print-file"))
        self.insert(button_print, -1)

        self.show_all()


class EditToolbar(SugarEditToolbar):

    __gsignals__ = {
        "undo": (GObject.SIGNAL_RUN_LAST, None, []),
        "redo": (GObject.SIGNAL_RUN_LAST, None, []),
        "search-text": (GObject.SIGNAL_RUN_LAST, None, [bool]),
        "replace-text": (GObject.SIGNAL_RUN_LAST, None, [])
    }

    def __init__(self):
        SugarEditToolbar.__init__(self)

        self.button = ToolbarButton(page=self, icon_name="toolbar-edit")

        self.undo.props.accelerator = "<Ctrl>Z"
        self.undo.set_sensitive(False)
        self.undo.connect("clicked", lambda button: self.emit("undo"))

        self.redo.props.accelerator = "<Ctrl><Mayus>Z"
        self.redo.set_sensitive(False)
        self.redo.connect("clicked", lambda button: self.emit("redo"))

        item_entry = Gtk.ToolItem()
        self.insert(item_entry, -1)

        self.entry_search = IconEntry()
        self.entry_search.set_size_request(250, -1)
        self.entry_search.set_placeholder_text("Search...")
        self.entry_search.set_margin_right(10)
        self.entry_search.set_icon_from_name(
            Gtk.EntryIconPosition.SECONDARY, "search")
        self.entry_search.connect(
            "changed", lambda entry: self.emit("search-text", False))
        self.entry_search.connect(
            "activate", lambda entry: self.emit("search-text", True))
        item_entry.add(self.entry_search)

        item_entry = Gtk.ToolItem()
        self.insert(item_entry, -1)

        self.entry_replace = IconEntry()
        self.entry_replace.set_size_request(250, -1)
        self.entry_replace.set_placeholder_text("Replace...")
        self.entry_replace.connect(
            "activate", lambda entry: self.emit("replace-text"))
        item_entry.add(self.entry_replace)

        self.copy.destroy()
        self.paste.destroy()

        self.show_all()


class ViewToolbar(Gtk.Toolbar):

    __gsignals__ = {
        "font-size-changed": (GObject.SIGNAL_RUN_LAST, None, [int]),
        "font-family-changed": (GObject.SIGNAL_RUN_LAST, None, [str]),
        "show-line-numbers-changed": (GObject.SIGNAL_RUN_LAST, None, [bool]),
        "show-right-line-changed": (GObject.SIGNAL_RUN_LAST, None, [bool]),
        "right-line-pos-changed": (GObject.SIGNAL_RUN_LAST, None, [int]),
        "theme-changed": (GObject.SIGNAL_RUN_LAST, None, [str]),
    }

    def __init__(self, conf):
        Gtk.Toolbar.__init__(self)

        self.button = ToolbarButton(page=self, icon_name="toolbar-view")

        combo_font = FontComboBox(conf["font"])
        combo_font.connect("changed", self.__font_changed_cb)
        self.insert(combo_font, -1)

        item_font_size = FontSize()
        item_font_size.set_font_size(conf["font-size"])
        item_font_size.connect("changed", self.__font_size_changed_cb)
        self.insert(item_font_size, -1)

        self.insert(utils.make_separator(False), -1)

        button_numbers = ToggleToolButton("show-numbers")
        button_numbers.props.accelerator = "<Ctrl><Mayus>N"
        button_numbers.set_tooltip(_("Show line numbers"))
        button_numbers.set_active(conf["show-line-numbers"])
        button_numbers.connect("toggled", self.__show_line_numbers_changed_cb)
        self.insert(button_numbers, -1)

        button_right_line = ToggleToolButton("show-right-line")
        button_right_line.props.accelerator = "<Ctrl>L"
        button_right_line.set_tooltip(_("Show a line in a specific position"))
        button_right_line.set_active(conf["show-right-line"])
        button_right_line.connect("toggled", self.__show_right_line_changed_cb)
        self.insert(button_right_line, -1)

        adjustement = Gtk.Adjustment(
            value=conf["right-line-pos"],
            lower=1,
            upper=150,
            step_increment=1,
            page_increment=5,
            page_size=0,
        )

        toolItem1 = Gtk.ToolItem()
        self.spinner_right_line = Gtk.SpinButton()
        self.spinner_right_line.set_margin_left(5)
        self.spinner_right_line.set_adjustment(adjustement)

        # Ensuring that the value is displayed when starting:
        self.spinner_right_line.set_value(conf["right-line-pos"])
        self.spinner_right_line.connect('notify::value',
                                        self.__right_line_pos_changed_cb)

        toolItem1.add(self.spinner_right_line)
        self.insert(toolItem1, -1)

        self.insert(utils.make_separator(False), -1)

        combo_styles = ComboStyles(conf["theme"])
        combo_styles.connect("theme-changed", self.__theme_changed_cb)
        self.insert(combo_styles, -1)

        self.show_all()

    def __font_size_changed_cb(self, item, size):
        self.emit("font-size-changed", size)

    def __font_changed_cb(self, combo, font):
        self.emit("font-family-changed", font)

    def __show_line_numbers_changed_cb(self, button):
        self.emit("show-line-numbers-changed", button.get_active())

    def __show_right_line_changed_cb(self, button):
        self.emit("show-right-line-changed", button.get_active())

    def __right_line_pos_changed_cb(self, spinner, user_data):
        self.emit("right-line-pos-changed", spinner.props.value)

    def __theme_changed_cb(self, combo, theme):
        self.emit("theme-changed", theme)


class ToolbarBox(SugarToolbarbox):

    __gsignals__ = {
        "new-page": (GObject.SIGNAL_RUN_LAST, None, []),
        "chooser-open": (GObject.SIGNAL_RUN_LAST, None, []),
        "chooser-save": (GObject.SIGNAL_RUN_LAST, None, [bool]),
        "print-file": (GObject.SIGNAL_RUN_LAST, None, []),
        "undo": (GObject.SIGNAL_RUN_LAST, None, []),
        "redo": (GObject.SIGNAL_RUN_LAST, None, []),
        "search-text": (GObject.SIGNAL_RUN_LAST, None, [bool]),
        "replace-text": (GObject.SIGNAL_RUN_LAST, None, []),
        "font-size-changed": (GObject.SIGNAL_RUN_LAST, None, [int]),
        "font-family-changed": (GObject.SIGNAL_RUN_LAST, None, [str]),
        "show-line-numbers-changed": (GObject.SIGNAL_RUN_LAST, None, [bool]),
        "show-right-line-changed": (GObject.SIGNAL_RUN_LAST, None, [bool]),
        "right-line-pos-changed": (GObject.SIGNAL_RUN_LAST, None, [int]),
        "theme-changed": (GObject.SIGNAL_RUN_LAST, None, [str]),
    }

    def __init__(self, activity):
        SugarToolbarbox.__init__(self)

        activity_button = ActivityToolbarButton(activity)
        self.toolbar.insert(activity_button, 0)

        self.toolbar.insert(utils.make_separator(False), -1)

        toolbar_file = FileToolbar()
        toolbar_file.connect("new-page", lambda toolbar: self.emit("new-page"))
        toolbar_file.connect(
            "chooser-open", lambda toolbar: self.emit("chooser-open"))
        toolbar_file.connect("chooser-save", self._chooser_save)
        toolbar_file.connect(
            "print-file", lambda toolbar: self.emit("print-file"))
        self.toolbar.add(toolbar_file.button)

        toolbar_edit = EditToolbar()
        toolbar_edit.connect("undo", lambda toolbar: self.emit("undo"))
        toolbar_edit.connect("redo", lambda toolbar: self.emit("redo"))
        toolbar_edit.connect("search-text", self._search_text)
        toolbar_edit.connect(
            "replace-text", lambda toolbar: self.emit("replace-text"))
        self.toolbar.insert(toolbar_edit.button, -1)

        toolbar_view = ViewToolbar(activity.conf)
        toolbar_view.connect("font-size-changed", self._font_size_changed)
        toolbar_view.connect("font-family-changed", self._font_family_changed)
        toolbar_view.connect(
            "show-line-numbers-changed", self._show_line_numbers_changed)
        toolbar_view.connect(
            "show-right-line-changed", self._show_right_line_changed)
        toolbar_view.connect(
            "right-line-pos-changed", self._right_line_pos_changed)
        toolbar_view.connect("theme-changed", self._theme_changed)
        self.toolbar.insert(toolbar_view.button, -1)

        self.toolbar.insert(utils.make_separator(True), -1)

        stop_button = StopButton(activity)
        stop_button.props.accelerator = "<Ctrl><Shift>Q"
        self.toolbar.insert(stop_button, -1)

        self.button_undo = toolbar_edit.undo
        self.button_redo = toolbar_edit.redo
        self.button_save = toolbar_file.button_save
        self.entry_search = toolbar_edit.entry_search
        self.entry_replace = toolbar_edit.entry_replace
        self.spinner_right_line = toolbar_view.spinner_right_line

    def _chooser_save(self, toolbar, force):
        self.emit("chooser-save", force)

    def _search_text(self, toolbar, force):
        self.emit("search-text", force)

    def _font_size_changed(self, toolbar, size):
        self.emit("font-size-changed", size)

    def _font_family_changed(self, toolbar, family):
        self.emit("font-family-changed", family)

    def _show_line_numbers_changed(self, toolbar, show):
        self.emit("show-line-numbers-changed", show)

    def _show_right_line_changed(self, toolbar, show):
        self.emit("show-right-line-changed", show)

    def _right_line_pos_changed(self, toolbar, pos):
        self.emit("right-line-pos-changed", pos)

    def _theme_changed(self, toolbar, theme):
        self.emit("theme-changed", theme)
