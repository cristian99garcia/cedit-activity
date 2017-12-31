#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   font.py por:
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

import globals as G

import os
import shutil
from gettext import gettext as _

from gi.repository import Gtk
from gi.repository import Gio
from gi.repository import GObject

from sugar3.graphics import style
from sugar3.graphics.icon import Icon
from sugar3.graphics.palette import Palette
from sugar3.graphics.palette import ToolInvoker
from sugar3.graphics.palettemenu import PaletteMenuBox
from sugar3.graphics.palettemenu import PaletteMenuItem


class FontLabel(Gtk.Label):

    def __init__(self, default_font="Monospace"):
        Gtk.Label.__init__(self)

        self._font = None
        self.set_font(default_font)

    def set_font(self, font):
        if self._font != font:
            self.set_markup('<span font="%s">%s</span>' % (font, font))


class FontComboBox(Gtk.ToolItem):

    __gsignals__ = {
        "changed": (GObject.SignalFlags.RUN_LAST, None, [str]),
    }

    def __init__(self, font_name):
        Gtk.ToolItem.__init__(self)

        self._palette_invoker = ToolInvoker()
        self._font_label = FontLabel(font_name)
        self._font_name = font_name

        bt = Gtk.Button("")
        bt.set_can_focus(False)
        bt.remove(bt.get_children()[0])

        box = Gtk.HBox()
        icon = Icon(icon_name="font-text")
        box.pack_start(icon, False, False, 10)
        box.pack_start(self._font_label, False, False, 10)
        bt.add(box)

        self.add(bt)
        self.show_all()

        if style.zoom(100) == 100:
            subcell_size = 15

        else:
            subcell_size = 11

        radius = 2 * subcell_size
        theme = "GtkButton { border-radius: %dpx; }" % radius
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(theme)
        style_context = bt.get_style_context()
        style_context.add_provider(
            css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

        self._hide_tooltip_on_click = True
        self._palette_invoker.attach_tool(self)
        self._palette_invoker.props.toggle_palette = True

        self.palette = Palette(_("Select font"))
        self.palette.set_invoker(self._palette_invoker)

        self._menu_box = PaletteMenuBox()
        self.props.palette.set_content(self._menu_box)
        self._menu_box.show()

        context = self.get_pango_context()

        self._init_font_list()

        tmp_list = []
        for family in context.list_families():
            name = family.get_name()
            if name in self._font_white_list:
                tmp_list.append(name)

        for name in sorted(tmp_list):
            self._add_menu(name, self.__font_selected_cb)

        self._font_label.set_font(self._font_name)

    def _init_font_list(self):
        self._font_white_list = []
        self._font_white_list.extend(G.DEFAULT_FONTS)

        if not os.path.exists(G.USER_FONTS_FILE_PATH):
            if os.path.exists(G.GLOBAL_FONTS_FILE_PATH):
                shutil.copy(G.GLOBAL_FONTS_FILE_PATH, G.USER_FONTS_FILE_PATH)

        if os.path.exists(G.USER_FONTS_FILE_PATH):
            fonts_file = open(G.USER_FONTS_FILE_PATH)
            for line in fonts_file:
                self._font_white_list.append(line.strip())

            gio_fonts_file = Gio.File.new_for_path(G.USER_FONTS_FILE_PATH)
            self.monitor = gio_fonts_file.monitor_file(
                Gio.FileMonitorFlags.NONE, None)
            self.monitor.set_rate_limit(5000)
            self.monitor.connect("changed", self._reload_fonts)

    def _reload_fonts(self, monitor, gio_file, other_file, event):
        if event != Gio.FileMonitorEvent.CHANGES_DONE_HINT:
            return

        self._font_white_list = []
        self._font_white_list.extend(G.DEFAULT_FONTS)
        fonts_file = open(G.USER_FONTS_FILE_PATH)

        for line in fonts_file:
            self._font_white_list.append(line.strip())

        for child in self._menu_box.get_children():
            self._menu_box.remove(child)
            child = None

        context = self.get_pango_context()
        tmp_list = []

        for family in context.list_families():
            name = family.get_name()
            if name in self._font_white_list:
                tmp_list.append(name)

        for name in sorted(tmp_list):
            self._add_menu(name, self.__font_selected_cb)

        return False

    def __font_selected_cb(self, menu, font_name):
        self._font_name = font_name
        self._font_label.set_font(font_name)
        self.emit("changed", self._font_name)

    def _add_menu(self, font_name, activate_cb):
        label = '<span font="%s">%s</span>' % (font_name, font_name)
        menu_item = PaletteMenuItem()
        menu_item.set_label(label)
        menu_item.connect("activate", activate_cb, font_name)
        self._menu_box.append_item(menu_item)
        menu_item.show()

    def __destroy_cb(self, icon):
        if self._palette_invoker is not None:
            self._palette_invoker.detach()

    def create_palette(self):
        return None

    def get_palette(self):
        return self._palette_invoker.palette

    def set_palette(self, palette):
        self._palette_invoker.palette = palette

    palette = GObject.property(
        type=object, setter=set_palette, getter=get_palette)

    def get_palette_invoker(self):
        return self._palette_invoker

    def set_palette_invoker(self, palette_invoker):
        self._palette_invoker.detach()
        self._palette_invoker = palette_invoker

    palette_invoker = GObject.property(
        type=object, setter=set_palette_invoker, getter=get_palette_invoker)

    def set_font_name(self, font_name):
        self._font_label.set_font(font_name)

    def get_font_name(self):
        return self._font_name


class FontSize(Gtk.ToolItem):

    __gsignals__ = {
        "changed": (GObject.SignalFlags.RUN_LAST, None, [int]),
    }

    def __init__(self):

        Gtk.ToolItem.__init__(self)

        self._font_sizes = [
            8, 9, 10, 11, 12, 14, 16, 20, 22, 24, 26, 28, 36, 48, 72]

        if style.zoom(100) == 100:
            subcell_size = 15
            default_padding = 6

        else:
            subcell_size = 11
            default_padding = 4

        vbox = Gtk.VBox()
        self.add(vbox)

        hbox = Gtk.HBox()
        vbox.pack_start(hbox, True, True, default_padding)

        self._size_down = Gtk.Button()
        self._size_down.set_can_focus(False)
        self._size_down.set_image(Icon(icon_name="resize-"))
        self._size_down.connect("clicked", self.__font_sizes_cb, False)
        hbox.pack_start(self._size_down, False, False, 5)

        self._default_size = 14
        self._font_size = self._default_size

        self._size_entry = Gtk.Entry()
        self._size_entry.set_text(str(self._font_size))
        self._size_entry.set_width_chars(3)
        self._size_entry.connect('activate', self.__entry_cb)
        hbox.pack_start(self._size_entry, False, False, 5)

        self._size_up = Gtk.Button()
        self._size_up.set_can_focus(False)
        self._size_up.set_image(Icon(icon_name="resize+"))
        self._size_up.connect("clicked", self.__font_sizes_cb, True)
        hbox.pack_start(self._size_up, False, False, 5)

        radius = 2 * subcell_size
        theme_up = \
            "GtkButton {border-radius:0px %dpx %dpx 0px;}" % (radius, radius)
        css_provider_up = Gtk.CssProvider()
        css_provider_up.load_from_data(theme_up)

        style_context = self._size_up.get_style_context()
        style_context.add_provider(
            css_provider_up, Gtk.STYLE_PROVIDER_PRIORITY_USER)

        theme_down = \
            "GtkButton {border-radius: %dpx 0px 0px %dpx;}" % (radius, radius)
        css_provider_down = Gtk.CssProvider()
        css_provider_down.load_from_data(theme_down)
        style_context = self._size_down.get_style_context()
        style_context.add_provider(
                css_provider_down, Gtk.STYLE_PROVIDER_PRIORITY_USER)

        self.show_all()
    def __entry_cb(self, entry):
        try:
            self._font_size = int(entry.get_text())
            if self._font_size > self._font_sizes[-1]:
                self._font_size = self._font_sizes[-1]
                entry.set_text(str(self._font_sizes[-1]))
            elif self._font_size < self._font_sizes[0]:
                self._font_size = self._font_sizes[0]
                entry.set_text(str(self._font_sizes[0]))
        except ValueError:
            entry.set_text(str(self._font_size))
        self._size_down.set_sensitive(self._font_size != self._font_sizes[0])
        self._size_up.set_sensitive(self._font_size != self._font_sizes[-1])
        self.emit("changed", self._font_size)

    def __font_sizes_cb(self, button, increase):
        if self._font_size in self._font_sizes:
            i = self._font_sizes.index(self._font_size)
            if increase:
                if i < len(self._font_sizes) - 1:
                    i += 1

            else:
                if i > 0:
                    i -= 1

        else:
            for font_size in self._font_sizes:
                if self._font_size < font_size:
                    i = self._font_sizes.index(font_size)
                    break

        self._font_size = self._font_sizes[i]
        self._size_entry.set_text(str(self._font_size))
        self._size_down.set_sensitive(i != 0)
        self._size_up.set_sensitive(i < len(self._font_sizes) - 1)
        self.emit("changed", self._font_size)

    def set_font_size(self, size):
        if size not in self._font_sizes:
            for font_size in self._font_sizes:
                if font_size > size:
                    size = font_size
                    break

            if size > self._font_sizes[-1]:
                size = self._font_sizes[-1]

        self._font_size = size
        self._size_entry.set_text(str(self._font_size))

        i = self._font_sizes.index(self._font_size)
        self._size_down.set_sensitive(i != 0)
        self._size_up.set_sensitive(i < len(self._font_sizes) - 1)
        self.emit("changed", self._font_size)

    def get_font_size(self):
        return self._font_size
