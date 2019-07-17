#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   utils.py por:
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
import globals as G

from configparser import ConfigParser

from gi.repository import Gtk
from gi.repository import Gio
from gi.repository import GdkPixbuf


def make_separator(expand=True):
    separator = Gtk.SeparatorToolItem()
    separator.props.draw = not expand
    separator.set_expand(expand)
    return separator


def get_pixbuf_from_path(path, size=62):
    icon_theme = Gtk.IconTheme()
    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(G.UNKNOWN, size, size)

    if "/" in path:
        _file = Gio.File.new_for_path(path)
        info = _file.query_info(
            "standard::icon", Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS, None)
        icon = info.get_icon()
        types = icon.get_names()

        # print path, types

        if os.path.ismount(path):
            return GdkPixbuf.Pixbuf.new_from_file_at_size(G.MOUNT, size, size)

        if "image-x-generic" in types:
            return GdkPixbuf.Pixbuf.new_from_file_at_size(path, size, size)

        for tipo in types:
            if tipo in list(G.IMAGES.keys()):
                return GdkPixbuf.Pixbuf.new_from_file_at_size(
                    G.IMAGES[tipo], size, size)

        if path.endswith(".desktop"):
            cfg = ConfigParser.ConfigParser()
            cfg.read([path])

            if cfg.has_option("Desktop Entry", "Icon"):
                if "/" in cfg.get("Desktop Entry", "Icon"):
                    d = cfg.get("Desktop Entry", "Icon")
                    return GdkPixbuf.Pixbuf.new_from_file_at_size(
                        d, size, size)

                else:
                    return icon_theme.load_icon(
                        cfg.get("Desktop Entry", "Icon"), size, 0)

            else:
                return icon_theme.load_icon(icon, size, 0)

        else:
            try:
                return icon_theme.choose_icon(types, size, 0).load_icon()

            except BaseException:
                # pixbuf = icon_theme.load_icon(icon, size, 0)
                pass

    return pixbuf


def get_language_from_file(path):
    language = G.LANGUAGE_MANAGER.guess_language(path, None)

    if not language:
        type = Gio.content_type_guess(path, [])[0]

        if "x-" in type:
            type = type.replace("x-", "")
        if "text/" in type:
            type = type.replace("text/", "")
        if type == "shellscript":
            type = "sh"

        language = G.LANGUAGE_MANAGER.get_language(type)

    return language


def get_path_access(path):
    #  R_OK = Readable, W_OK = Writable
    return os.access(path, os.R_OK), os.access(path, os.W_OK)


def is_hidden_filename(name):
    return name.startswith(".") or name.endswith("~")


def is_hidden_path(path):
    gfile = Gio.File.new_for_path(path)
    filename = os.path.basename(gfile.get_path())

    return is_hidden_filename(filename)


def split_directory_content(directory, content):
    content.sort()

    folders = []
    files = []

    for x in content:
        path = os.path.join(directory, x)
        if os.path.isdir(path):
            folders.append(path)

        elif os.path.isfile(path):
            files.append(path)

    return folders, files


def get_directory_content(directory):
    content = os.listdir(directory)
    return split_directory_content(directory, content)


def get_path_name(path):
    gfile = Gio.File.new_for_path(path)  # Standardize path
    return os.path.basename(gfile.get_path())


def set_border_radius(widget, r1=0, r2=0, r3=0, r4=0):
    name = "Gtk" + widget.__class__.__name__
    theme = "%s {border-radius: %dpx %dpx %dpx %dpx;}" % \
        (name, r1, r2, r3, r4)

    css_provider_up = Gtk.CssProvider()
    css_provider_up.load_from_data(theme.encode())

    style_context = widget.get_style_context()
    style_context.add_provider(
        css_provider_up, Gtk.STYLE_PROVIDER_PRIORITY_USER)
