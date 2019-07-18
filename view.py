#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   view.py por:
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

from gi.repository import Pango
from gi.repository import GObject
from gi.repository import GtkSource


class Buffer(GtkSource.Buffer):

    __gsignals__ = {
        "language-changed": (GObject.SIGNAL_RUN_FIRST, None, [str])
    }

    def __init__(self):
        GtkSource.Buffer.__init__(self)
        self.language = None
        self.language_setted = False
        self.languages = [_("Plain text")]
        self.language_manager = GtkSource.LanguageManager()
        self.languages.extend(self.language_manager.get_language_ids())

    def set_language_from_file(self, path):
        if self.language_setted and not utils.get_language_from_file(path):
            # Maintaining the language set by the user.
            return

        self.language = utils.get_language_from_file(path)

        if self.language:
            self.set_highlight_syntax(True)
            self.set_language(self.language)
            self.emit("language-changed", self.language.get_name())

        elif not self.language:
            self.set_highlight_syntax(False)
            self.emit("language-changed", _("Plain text"))

        self.language_setted = False

    def set_language_from_string(self, language):
        if language == _("Plain text"):
            self.language = None
            self.set_highlight_syntax(False)

        else:
            self.language = self.language_manager.get_language(language)
            self.set_highlight_syntax(True)
            self.set_language(self.language)

        self.language_setted = True

    def get_language(self):
        return self.language

    def get_language_str(self):
        if self.language:
            return self.language.get_name().lower()

        return _("Plain text")

    def get_all_text(self):
        start, end = self.get_bounds()
        return self.get_text(start, end, False)


class View(GtkSource.View):

    __gsignals__ = {
        "title-changed": (GObject.SIGNAL_RUN_FIRST, None, [str]),
    }

    def __init__(self, conf):
        GtkSource.View.__init__(self)

        self.file = None
        self.conf = None
        self.style_manager = G.STYLE_MANAGER

        self.buffer = Buffer()
        self.buffer.connect("modified-changed", self.buffer_changed)
        self.set_buffer(self.buffer)

        self.tag_search = self.buffer.create_tag(
            "search", foreground="#5E82FF", background="#078D00")

        self.set_conf(conf)

    def undo(self):
        if self.buffer.can_undo():
            self.buffer.undo()

    def redo(self):
        if self.buffer.can_redo():
            self.buffer.redo()

    def buffer_changed(self, buffer):
        self.emit_title_changed()

    def set_conf(self, conf):
        self.conf = conf
        font = "%s %d" % (conf["font"], conf["font-size"])

        self.modify_font(Pango.FontDescription(font))
        self.set_tab_width(conf["tab-width"])
        self.set_insert_spaces_instead_of_tabs(conf["use-spaces"])
        self.buffer.set_style_scheme(
            self.style_manager.get_scheme(conf["theme"]))
        self.set_show_line_numbers(conf["show-line-numbers"])
        self.set_show_right_margin(conf["show-right-line"])
        self.set_right_margin_position(conf["right-line-pos"])

    def search(self, text, enter):
        start, end = self.buffer.get_bounds()
        self.buffer.remove_tag(self.tag_search, start, end)
        cursor_mark = self.buffer.get_insert()
        start_mark = self.buffer.get_iter_at_mark(cursor_mark)

        if text:
            self.search_and_mark(text, start)
            self.select_text(text, start_mark, enter)

    def replace(self, text_search, text_replace):
        if not self.buffer.get_selection_bounds():
            if text_search:
                self.search(text_search, True)

            return

        else:
            start, end = self.buffer.get_selection_bounds()
            if self.buffer.get_text(start, end, False) == text_search:
                self.buffer.delete_selection(True, True)
                self.buffer.insert_interactive_at_cursor(
                    text_replace, -1, True)

                self.search(text_search, True)

    def search_and_mark(self, text, start):
        _start, _end = self.buffer.get_bounds()

        end = self.buffer.get_end_iter()
        match = start.forward_search(text, 0, end)

        if match is not None:
            match_start, match_end = match
            self.buffer.apply_tag(self.tag_search, match_start, match_end)
            self.search_and_mark(text, match_end)

    def select_text(self, text, start, enter):
        end = self.buffer.get_end_iter()
        match = start.forward_search(text, 0, end)
        _start, _end = None, None

        if match:
            match_start, match_end = match

            if not enter:
                self.buffer.select_range(match_start, match_end)

            else:
                if self.buffer.get_selection_bounds():
                    _start, _end = self.buffer.get_selection_bounds()

                if _start is not None and _end is not None:
                    if match_end.get_offset() == _end.get_offset() and \
                            match_start.get_offset() == _start.get_offset():

                        self.select_text(text, _end, True)
                        return

                self.buffer.select_range(match_end, match_start)

            self.scroll_to_iter(match_end, 0.1, 1, 1, 1)

        else:
            start = self.buffer.get_start_iter()
            try:
                self.select_text(text, start, False)

            except RuntimeError:
                pass

    def set_file_instance(self, instance_path, path):
        if os.path.isfile(instance_path):
            with open(instance_path, "r") as file:
                modified = int(file.readline().strip())
                text = file.read()

            self.buffer.set_text(text)
            self.buffer.set_language_from_file(path)
            self.buffer.begin_not_undoable_action()
            self.buffer.end_not_undoable_action()
            self.buffer.set_modified(bool(modified))
            if path:
                self.file = path
                readable, writable = utils.get_path_access(path)
            else:
                writable = True

            self.emit_title_changed()
            self.set_editable(writable)

    def set_file(self, path, _open=True):
        if os.path.isfile(path) and _open:
            with open(path, "r") as file:
                text = file.read()

            self.buffer.set_text(text)
            self.buffer.set_language_from_file(path)
            self.buffer.begin_not_undoable_action()
            self.buffer.end_not_undoable_action()
            self.buffer.set_modified(False)

            self.file = path
            self.emit_title_changed()

            readable, writable = utils.get_path_access(path)

            self.set_editable(writable)

    def save_file_instance(self, path):
        self.buffer.set_language_from_file(path)
        with open(path, "w") as file:
            file.write(str(int(self.buffer.get_modified())) + "\n")
            file.write(self.buffer.get_all_text())

    def save_file(self, path):
        self.buffer.set_modified(False)
        self.buffer.set_language_from_file(path)

        if self.file != path:
            self.file = path

        with open(self.file, "w") as file:
            file.write(self.buffer.get_all_text())

        self.emit("title-changed", self.get_file_name())

    def get_file(self):
        return self.file

    def get_file_name(self):
        if self.file:
            return self.file.split("/")[-1]
        else:
            return _("New file")

    def emit_title_changed(self):
        self.emit("title-changed", self.get_file_name())
