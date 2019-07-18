#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   CEdit.py por:
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
from os.path import join
from gettext import gettext as _

import utils
import globals as G

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Pango
from gi.repository import GtkSource

from view import View
from infobar import InfoBar
from filechooser import FileChooserOpen
from filechooser import FileChooserSave
from toolbars import ToolbarBox

from sugar3.activity import activity
from sugar3.graphics.alert import Alert
from sugar3.graphics.alert import TimeoutAlert


class CEdit(activity.Activity):

    def __init__(self, handle):
        activity.Activity.__init__(self, handle)
        self.instance_path = join(activity.get_activity_root(), 'instance')
        self.index_file = join(self.instance_path, 'index')

        self.get_conf()

        self.reopen = True
        self.vbox = Gtk.VBox()
        self.infobar = InfoBar()

        self.toolbar_box = ToolbarBox(self)
        self.toolbar_box.connect("new-page", lambda toolbar: self.new_page())
        self.toolbar_box.connect("chooser-open", self.file_chooser_open)
        self.toolbar_box.connect("chooser-save", self.file_chooser_save)
        self.toolbar_box.connect("print-file", self.print_file)
        self.toolbar_box.connect("undo", self.undo)
        self.toolbar_box.connect("redo", self.redo)
        self.toolbar_box.connect("search-text", self.search_text)
        self.toolbar_box.connect("replace-text", self.replace_text)
        self.toolbar_box.connect("font-size-changed", self.font_size_changed)
        self.toolbar_box.connect(
            "font-family-changed", self.font_family_changed)
        self.toolbar_box.connect(
            "show-line-numbers-changed", self.show_line_numbers_changed)
        self.toolbar_box.connect(
            "show-right-line-changed", self.show_right_line_changed)
        self.toolbar_box.connect(
            "right-line-pos-changed", self.right_line_pos_changed)
        self.toolbar_box.connect("theme-changed", self.theme_changed)
        self.set_toolbar_box(self.toolbar_box)

        self.make_notebook()

        self.infobar.connect("language-changed", self.set_language)

        self.vbox.pack_end(self.infobar, False, False, 0)
        self.set_canvas(self.vbox)
        self.show_all()

    def get_conf(self):
        if "saved" in self.metadata:
            self.conf = {}
            self.conf["font"] = str(self.metadata["font"])
            self.conf["font-size"] = int(self.metadata["font-size"])
            self.conf["show-line-numbers"] = \
                bool(int(self.metadata["show-line-numbers"]))
            self.conf["tab-width"] = int(self.metadata["tab-width"])
            self.conf["use-spaces"] = bool(int(self.metadata["use-spaces"]))
            self.conf["theme"] = str(self.metadata["theme"])
            self.conf["right-line-pos"] = int(self.metadata["right-line-pos"])
            self.conf["show-right-line"] = \
                bool(int(self.metadata["show-right-line"]))

        else:
            self.conf = {
                "font": "Monospace",
                "font-size": 14,
                "show-line-numbers": True,
                "tab-width": 4,
                "use-spaces": True,
                "theme": "classic",
                "right-line-pos": 80,
                "show-right-line": False,
            }

    def make_notebook(self):
        self.notebook = Gtk.Notebook()
        button_add = Gtk.ToolButton.new_from_stock(Gtk.STOCK_ADD)
        button_add.connect("clicked", lambda w: self.new_page())

        self.notebook.set_scrollable(True)
        self.notebook.set_show_tabs(True)
        self.notebook.set_action_widget(button_add, Gtk.PackType.END)

        self.notebook.add_events(Gdk.EventMask.SCROLL_MASK |
                                 Gdk.EventMask.SMOOTH_SCROLL_MASK)

        self.notebook.connect("switch-page", self.update_buttons)
        self.notebook.connect("scroll-event", self.notebook_scrolled)
        self.notebook.connect("page-removed", self.page_removed)

        self.vbox.pack_start(self.notebook, True, True, 2)
        if os.path.exists(self.index_file):
            self.instance_wake()
        else:
            self.new_page()
        button_add.show()
        self.show_all()

    def page_removed(self, notebook, scroll, page):
        if not self.reopen:
            return

        if len(self.notebook.get_children()) == 0:
            self.new_page()

    def set_language(self, infobar, language):
        buffer = self.get_view().buffer
        buffer.set_language_from_string(language)

    def set_language_from_buffer(self, buffer, language):
        self.infobar.set_language(language)

    def notebook_scrolled(self, widget, event):
        if event.get_scroll_direction()[1] == Gdk.ScrollDirection.UP:
            self.notebook.prev_page()
        elif event.get_scroll_direction()[1] == Gdk.ScrollDirection.DOWN:
            self.notebook.next_page()

    def update_buttons(self, notebook=None, scrolled=None, *args):
        if not isinstance(scrolled, Gtk.ScrolledWindow):
            view = self.get_view()

        else:
            view = scrolled.get_children()[0]

        buffer = view.get_buffer()

        self.toolbar_box.button_undo.set_sensitive(buffer.can_undo())
        self.toolbar_box.button_redo.set_sensitive(buffer.can_redo())
        self.toolbar_box.button_save.set_sensitive(buffer.get_modified())
        self.toolbar_box.entry_search.set_sensitive(
            bool(buffer.get_all_text()))
        self.toolbar_box.entry_replace.set_sensitive(
            bool(buffer.get_all_text()))
        self.toolbar_box.spinner_right_line.set_sensitive(
            self.conf["show-right-line"])
        self.infobar.set_language(buffer.get_language_str())
        self.update_cursor_position(buffer)

    def new_page(self, view=None, label=None):
        if not view:
            view = View(self.conf)
            view.buffer.connect("changed", self.update_buttons)
            view.buffer.connect("mark-set", self.update_cursor_position)
            view.buffer.connect(
                "language-changed", self.set_language_from_buffer)

        if not label:
            label = view.get_file_name()

        if isinstance(label, str):
            label = Gtk.Label(label)
            label.modify_font(Pango.FontDescription("15 bold"))

        view.connect("title-changed", self.change_title_from_view)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        scrolled.add(view)

        hbox = Gtk.HBox()
        hbox.set_size_request(-1, 20)

        hbox.pack_start(label, False, False, 0)

        button = Gtk.Button()
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.set_size_request(12, 12)
        button.set_image(
            Gtk.Image.new_from_stock(Gtk.STOCK_CLOSE, Gtk.IconSize.MENU))
        button.connect("clicked", self.remove_page_from_widget, scrolled)
        hbox.pack_start(button, False, False, 0)

        self.notebook.append_page(scrolled, hbox)
        self.notebook.set_tab_reorderable(scrolled, True)

        view.grab_focus()
        hbox.show_all()
        self.show_all()

        self.notebook.set_current_page(self.notebook.get_n_pages() - 1)
        return view

    def update_cursor_position(self, buffer, *args):
        iter = buffer.get_iter_at_mark(buffer.get_insert())
        line = iter.get_line() + 1
        column = iter.get_line_offset() + 1
        self.infobar.set_pos(line, column)

    def file_chooser_open(self, widget):
        path = self.get_view().get_file()
        file_chooser = FileChooserOpen(path)
        file_chooser.connect("open-file", self._open_file_from_chooser)
        file_chooser.show_all()

    def instance_wake(self):
        with open(self.index_file, 'r') as f:
            path_list = [path.strip() for path in f.readlines()]

        os.remove(self.index_file)
        for x in range(len(path_list)):
            file_path = join(self.instance_path, str(x))
            self._open_file_from_instance(file_path, path_list[x])
            os.remove(file_path)

    def file_chooser_save(self, widget, force=False, close=False):
        # Force is for "save as"

        idx = self.notebook.get_current_page()
        view = self.get_view()

        if view.get_file() and not force:
            self.save_file(idx=idx, path=view.get_file())
            return

        file_chooser = FileChooserSave()
        file_chooser.connect("save-file", self._save_file_from_chooser, close)
        file_chooser.show_all()

    def begin_print(self, operation, context, compositor):
        while not compositor.paginate(context):
            pass

        n_pages = compositor.get_n_pages()
        operation.set_n_pages(n_pages)

    def draw_page(self, operation, context, page_nr, compositor):
        compositor.draw_page(context, page_nr)

    def print_file(self, widget):
        def _alert_response(alert, response):
            self.vbox.remove(alert)

        view = self.get_view()
        buffer = view.get_buffer()
        path = view.get_file()

        if not path:
            alert = TimeoutAlert(10)
            alert.props.title = G.TEXT_FILE_NOT_SAVED
            alert.props.msg = G.TEXT_MUST_SAVE
            hbox = alert.get_children()[0]
            buttonbox = hbox.get_children()[1]
            button = buttonbox.get_children()[0]
            buttonbox.remove(button)

            alert.connect("response", _alert_response)

            self.vbox.pack_start(alert, False, False, 0)
            self.vbox.reorder_child(alert, 0)

            return

        compositor = GtkSource.PrintCompositor.new_from_view(view)
        compositor.set_highlight_syntax(buffer.get_highlight_syntax())
        compositor.set_print_line_numbers(self.conf["show-line-numbers"])

        if view.buffer.language:
            compositor.set_header_format(False, "%s - %s" % (
                view.buffer.get_language_str(), view.get_file()), None, None)

        compositor.set_footer_format(True, "%T", path, "Page %N/%Q")
        compositor.set_print_header(True)
        compositor.set_print_footer(True)

        operation = Gtk.PrintOperation()
        operation.set_job_name(path)

        operation.connect("begin-print", self.begin_print, compositor)
        operation.connect("draw-page", self.draw_page, compositor)

        res = operation.run(Gtk.PrintOperationAction.PRINT_DIALOG, None)
        if res == Gtk.PrintOperationResult.ERROR:
            dialog = Gtk.MessageDialog(
                self,
                Gtk.DialogFlags.DESTROY_WITH_PARENT,
                Gtk.MessageType.ERROR,
                Gtk.ButtonsType.OK,
                "Error to print the file: %s" % path)

            dialog.run()
            dialog.destroy()

    def _open_file_from_instance(self, path, path_set):
        self.new_page(label=path_set.split('/')[-1])
        view = self.get_view(idx=-1)
        view.set_file_instance(path, path_set)

    def _open_file_from_chooser(self, widget, path):
        children = self.notebook.get_children()
        for scrolled in children:
            view = scrolled.get_children()[0]
            if view.get_file() == path:
                idx = children.index(scrolled)
                self.notebook.set_current_page(idx)
                return

        view = self.get_view()

        if view.get_file():
            self.new_page(label=view.get_file_name())
            view = self.get_view(idx=-1)

        view.set_file(path)

    def _save_file_from_chooser(self, widget, path, close=False):
        view = self.get_view()
        view.save_file(path)

        if close:
            view = self.get_view()
            scrolled = view.get_parent()
            idx = self.notebook.get_children().index(scrolled)
            self.notebook.remove_page(idx)

    def save_file(self, widget=None, idx=None, path=None):
        if idx is not None:
            idx = self.notebook.get_current_page()

        scrolled = self.notebook.get_children()[idx]
        view = scrolled.get_children()[0]
        view.save_file(view.get_file())

    def remove_page_from_widget(self, widget, scrolled, force=False):
        view = scrolled.get_children()[0]
        buffer = view.get_buffer()
        idx = self.notebook.get_children().index(scrolled)

        if not buffer.get_modified() or force:
            self.notebook.remove_page(idx)

        else:
            name = view.get_file_name()
            title = G.TEXT_SAVE_FILE.replace("****", name)
            msg = G.TEXT_IF_NOT_SAVE
            cancel = Gtk.Image.new_from_icon_name(
                "dialog-cancel", Gtk.IconSize.MENU)
            no = Gtk.Image.new_from_icon_name(
                "activity-stop", Gtk.IconSize.MENU)
            save = Gtk.Image.new_from_icon_name("filesave", Gtk.IconSize.MENU)

            self.alert = Alert()
            self.alert.props.title = title
            self.alert.props.msg = msg

            self.alert.add_button(
                Gtk.ResponseType.CANCEL, _("Cancel"), icon=cancel)
            self.alert.add_button(Gtk.ResponseType.NO, _("No save"), icon=no)
            self.alert.add_button(Gtk.ResponseType.YES, _("Save"), icon=save)

            self.alert.connect("response", self._alert_response, scrolled)

            self.vbox.pack_start(self.alert, False, False, 0)
            self.vbox.reorder_child(self.alert, 0)
            self.vbox.show_all()

    def change_title_from_view(self, view=None, label=None):
        if not view:
            view = self.get_view()

        if not label:
            label = view.get_file_name()

        scrolled = view.get_parent()
        hbox = self.notebook.get_tab_label(scrolled)
        widget = hbox.get_children()[0]
        changed = view.get_buffer().get_modified()

        widget.set_label(label)

        color = "#FF0000" if changed else "#FFFFFF"
        if view.get_file():
            readable, writable = utils.get_path_access(view.get_file())
            color = "#4A90D9" if not writable else color
            widget.set_tooltip_text(G.TEXT_HAVE_NOT_PERMISSIONS)

        widget.modify_fg(Gtk.StateType.NORMAL, Gdk.color_parse(color))
        self.update_buttons()

    def get_view(self, idx=None):
        if idx is None:
            idx = self.notebook.get_current_page()

        scrolled = self.notebook.get_children()[idx]
        return scrolled.get_children()[0]

    def undo(self, widget):
        self.get_view().undo()
        self.change_title_from_view()

    def redo(self, widget):
        self.get_view().redo()
        self.change_title_from_view()

    def search_text(self, toolbarbox, enter=False):
        text = self.toolbar_box.entry_search.get_text()
        self.get_view().search(text, enter)

    def replace_text(self, widget):
        text_search = self.toolbar_box.entry_search.get_text()
        text_replace = self.toolbar_box.entry_replace.get_text()
        self.get_view().replace(text_search, text_replace)

    def font_size_changed(self, widget, font_size):
        self.conf["font-size"] = font_size
        self.set_conf_to_views()

    def font_family_changed(self, widget, font):
        self.conf["font"] = font
        self.set_conf_to_views()

    def show_line_numbers_changed(self, widget, show):
        self.conf["show-line-numbers"] = show
        self.set_conf_to_views()

    def show_right_line_changed(self, widget, show):
        self.conf["show-right-line"] = show
        self.update_buttons()
        self.set_conf_to_views()

    def right_line_pos_changed(self, widget, value):
        self.conf["right-line-pos"] = value
        self.set_conf_to_views()

    def theme_changed(self, widget, theme):
        self.conf["theme"] = theme
        self.set_conf_to_views()

    def tab_width_changed(self, widget, tab_width):
        self.conf["tab-width"] = tab_width
        self.set_conf_to_views()

    def set_conf_to_views(self):
        for scrolled in self.notebook.get_children():
            view = scrolled.get_children()[0]
            view.set_conf(self.conf)

    def _alert_response(self, widget, response, scrolled):
        if response == Gtk.ResponseType.NO:
            self.remove_page_from_widget(None, scrolled, force=True)

        elif response == Gtk.ResponseType.YES:
            self.file_chooser_save(None, False, True)

        self.vbox.remove(self.alert)

    def write_file(self, file_path):
        x = 0
        views = self.notebook.get_children()

        with open(self.index_file, 'w') as f:
            for scrolled in views:
                view = scrolled.get_children()[0]
                name = view.get_file()
                if not name:
                    name = ''
                path = join(self.instance_path, str(x))
                f.write(name)
                view.save_file_instance(path)
                if not name or x != len(views) - 1:
                    f.write('\n')
                x += 1

        files = []
        for scrolled in views:
            view = scrolled.get_children()[0]
            if view.get_file():
                files.append(view.get_file)

        self.metadata["saved"] = True
        self.metadata["font"] = self.conf["font"]
        self.metadata["font-size"] = self.conf["font-size"]
        self.metadata["show-line-numbers"] = self.conf["show-line-numbers"]
        self.metadata["tab-width"] = self.conf["tab-width"]
        self.metadata["use-spaces"] = self.conf["use-spaces"]
        self.metadata["theme"] = self.conf["theme"]
        self.metadata["right-line-pos"] = self.conf["right-line-pos"]
        self.metadata["show-right-line"] = self.conf["show-right-line"]

    def _exit(self, *args):
        def _remove_page(widget, scrolled):
            if scrolled in self.notebook.get_children():
                idx = self.notebook.get_children().index(scrolled)
                self.notebook.remove_page(idx)

            check_modified()

        def _alert_response(alert, response, scrolled):
            self.vbox.remove(alert)

            if response == Gtk.ResponseType.YES:
                view = scrolled.get_children()[0]

                if view.get_file():
                    idx = self.notebook.get_children()
                    self.save_file(idx=idx, path=view.get_file())
                    self.remove_page_from_widget(None, scrolled, force=True)
                    return

                file_chooser = FileChooserSave()
                file_chooser.connect(
                    "save-file", self._save_file_from_chooser, True)
                file_chooser.connect("destroy", _remove_page, scrolled)
                file_chooser.show_all()

            else:
                self.remove_page_from_widget(None, scrolled, force=True)
                check_modified()

        def _create_alert(name, scrolled):
            title = G.TEXT_SAVE_CHANGES_QUESTION.replace("****", name)
            msg = G.TEXT_IF_NOT_SAVE

            no = Gtk.Image.new_from_icon_name(
                "activity-stop", Gtk.IconSize.MENU)

            save = Gtk.Image.new_from_icon_name("filesave", Gtk.IconSize.MENU)

            alert = Alert()
            alert.props.title = title
            alert.props.msg = msg

            alert.add_button(Gtk.ResponseType.NO, _("No save"), icon=no)
            alert.add_button(Gtk.ResponseType.YES, _("Save"), icon=save)

            alert.connect("response", _alert_response, scrolled)

            self.vbox.pack_start(alert, False, False, 0)
            self.vbox.reorder_child(alert, 0)
            self.vbox.show_all()

        def check_modified():
            if not self.notebook.get_children():
                _close()
                return

            self.notebook.set_current_page(self.notebook.get_n_pages() - 1)
            scrolled = self.notebook.get_children()[-1]
            view = scrolled.get_children()[0]
            buffer = view.get_buffer()

            if buffer.get_modified():
                name = view.get_file_name()
                _create_alert(name, scrolled)

            else:
                self.remove_page_from_widget(None, scrolled, force=True)
                check_modified()

        def _close():
            self.close()

        self.reopen = False
        check_modified()
