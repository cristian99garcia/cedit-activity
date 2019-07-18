#!/usr/bin/env python

import os
from gettext import gettext as _
import gi
gi.require_version('Gdk', '3.0')
gi.require_version('GtkSource', '3.0')

from gi.repository import Gdk
from gi.repository import GtkSource

from sugar3 import env


TEXT_FILE_NOT_SAVED = _("This file has not saved.")
TEXT_MUST_SAVE = _("You must save this file to print it.")
TEXT_SAVE_FILE = _("Save changes to document **** before closing?")
TEXT_IF_NOT_SAVE = \
    _("If you do not save this file, changes will be lost forever.")
TEXT_HAVE_NOT_PERMISSIONS = \
    _("You do not have sufficient permissions to write this file.")
TEXT_SAVE_CHANGES_QUESTION = \
    _("Save changes to document **** before closing?")
TEXT_FILE_NOT_EXISTS1 = _("This file not exists.")
TEXT_FILE_NOT_EXISTS2 = \
    _("Apparently you've selected a file that does not exist.")
TEXT_ERROR_CREATING_FOLDER = _("Error creating the folder.")
TEXT_FILE_ALREADY_EXISTS = _("This file is already exists.")
TEXT_OVERWRITE_QUESTION = _("**** already exists. Overwrite it?")

ICONS = os.path.join(os.path.dirname(__file__), "icons/")

GENERIC_FOLDER = os.path.join(ICONS, "folder.svg")
HOME_DIR = os.path.join(ICONS, "folder-home.svg")
DESKTOP_DIR = os.path.join(ICONS, "folder-desktop.svg")
DOCUMENTS_DIR = os.path.join(ICONS, "folder-documents.svg")
DOWNLOADS_DIR = os.path.join(ICONS, "folder-download.svg")
PICTURES_DIR = os.path.join(ICONS, "folder-pictures.svg")
MUSIC_DIR = os.path.join(ICONS, "folder-music.svg")
VIDEOS_DIR = os.path.join(ICONS, "folder-video.svg")
MOUNT = os.path.join(ICONS, "pendrive.svg")

PDF = os.path.join(ICONS, "pdf.svg")
TEXT = os.path.join(ICONS, "plain.svg")
VIDEO = os.path.join(ICONS, "video.svg")
PYTHON = os.path.join(ICONS, "python.svg")
UNKNOWN = os.path.join(ICONS, "unknown.svg")
EXECUTABLE = os.path.join(ICONS, "executable.svg")
COMPRESSED = os.path.join(ICONS, "compressed.svg")
FOLDER_LINK = os.path.join(ICONS, "inode-symlink.svg")

IMAGES = {
    "user-home": HOME_DIR,
    "user-desktop": DESKTOP_DIR,
    "folder-documents": DOCUMENTS_DIR,
    "folder-download": DOWNLOADS_DIR,
    "folder-pictures": PICTURES_DIR,
    "folder-music": MUSIC_DIR,
    "folder-videos": VIDEOS_DIR,
    "folder": GENERIC_FOLDER,

    "text-x-generic": TEXT,
    "text-x-python": PYTHON,
    "application-x-python-bytecode": PYTHON,
    "application-x-executable": EXECUTABLE,
    "application-x-shellscript": EXECUTABLE,
    "application-x-m4": EXECUTABLE,
    "text-x-script": EXECUTABLE,
    "package-x-generic": COMPRESSED,
    "inode-symlink": FOLDER_LINK,
    "application-pdf": PDF,
    "video-mp4": VIDEO,
}

LANGUAGE_MANAGER = GtkSource.LanguageManager()
LANGUAGES = LANGUAGE_MANAGER.get_language_ids()
STYLE_MANAGER = GtkSource.StyleSchemeManager()
STYLES = STYLE_MANAGER.get_scheme_ids()

STYLES_PATH = os.path.join(os.path.dirname(__file__), "styles/")
STYLE_MANAGER = GtkSource.StyleSchemeManager()
STYLE_MANAGER.append_search_path(STYLES_PATH)
STYLES = STYLE_MANAGER.get_scheme_ids()

# FIXME: Maybe there are many more exceptions.
BAD_LANGUAGES = {
    "c++": "cpp",
    ".desktop": "desktop",
    "marcar": "markdown",
    "javascript": "js",
}

screen = Gdk.Screen().get_default()
WIDTH = (screen.get_width() / 6) * 5
HEIGHT = (screen.get_height() / 6) * 5

DEFAULT_FONTS = ["Sans", "Serif", "Monospace"]
USER_FONTS_FILE_PATH = env.get_profile_path("fonts")
GLOBAL_FONTS_FILE_PATH = "/etc/sugar_fonts"
