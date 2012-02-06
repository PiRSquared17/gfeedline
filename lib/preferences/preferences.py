#
# gfeedline - Gnome Social Feed Reader
#
# Copyright (c) 2012, Yoshizumi Endo.
# Licence: GPL3

import os

from gi.repository import Gtk, Gdk

from ..plugins.twitter.assistant import TwitterAuthAssistant
from ..utils.settings import SETTINGS, SETTINGS_TWITTER
from ..utils.autostart import AutoStart
from ..constants import SHARED_DATA_DIR, Column
from feedsource import FeedSourceDialog

class Preferences(object):

    def __init__(self, mainwindow):
        self.liststore = mainwindow.liststore

        gui = Gtk.Builder()
        gui.add_from_file(os.path.join(SHARED_DATA_DIR, 'preferences.glade'))
        self.preferences = gui.get_object('preferences')
        self.preferences.show_all()

        notebook = gui.get_object('notebook1')
        notebook.remove_page(1)
        recent_page = SETTINGS.get_int('preferences-recent-page')
        notebook.set_current_page(recent_page)

        frame = gui.get_object('frame5')
        frame.hide()

        self.label_username = gui.get_object('label_confirm_username')
        self.on_setting_username_changed()
        SETTINGS_TWITTER.connect("changed::user-name", 
                                 self.on_setting_username_changed)

        self.feedsource_treeview = treeview = gui.get_object('feedsourcetreeview')
        treeview.set_model(self.liststore)
        treeview.set_headers_clickable(False) # Builder bug?
        treeview.connect("drag-begin", self.on_drag_begin)
        treeview.connect("drag-end", self.on_drag_end, mainwindow)

        self.button_prefs = gui.get_object('button_feed_prefs')
        self.button_prefs.set_sensitive(False)

        self.button_del = gui.get_object('button_feed_del')
        self.button_del.set_sensitive(False)

        self.autostart = AutoStart('gfeedline')
        checkbutton_autostart = gui.get_object('checkbutton_autostart')
        checkbutton_autostart.set_sensitive(self.autostart.check_enable())
        checkbutton_autostart.set_active(self.autostart.get())

        SETTINGS.connect("changed::window-sticky", self.on_settings_sticky_change)
        self.on_settings_sticky_change(SETTINGS, 'window-sticky')
        sticky = SETTINGS.get_boolean('window-sticky')
        checkbutton_sticky = gui.get_object('checkbutton_sticky')
        checkbutton_sticky.set_active(sticky)

        gui.connect_signals(self)

    def on_drag_begin(self, treeview, dragcontext):
        treeselection = treeview.get_selection()
        model, iter = treeselection.get_selected()

        self.api_obj = model.get_value(iter, Column.API)
        self.group = model.get_value(iter, Column.GROUP).decode('utf-8')
        self.old_page = model.get_group_page(model, self.group)

    def on_drag_end(self, treeview, dragcontext, mainwindow):
        model = treeview.get_model()

        all_obj = [x[Column.API] for x in model 
                   if x[Column.GROUP].decode('utf-8') == self.group]
        page = all_obj.index(self.api_obj)

        notebook = mainwindow.column[self.group]
        notebook.reorder_child(self.api_obj.view, page) # FIXME

        new_page = model.get_group_page(model, self.group)

        if self.old_page != new_page:
            mainwindow.hbox.reorder_child(notebook, new_page)

    def on_setting_username_changed(self, *args):
        user_name = SETTINGS_TWITTER.get_string('user-name') or 'none'
        self.label_username.set_text(user_name)

    def on_settings_sticky_change(self, settings, key):
        if settings.get_boolean(key):
            self.preferences.stick()
        else:
            self.preferences.unstick()

    def on_button_twitter_auth_clicked(self, button):
        assistant = TwitterAuthAssistant(self.preferences) 

    def on_button_close_clicked(self, notebook):
        page = notebook.get_current_page()
        SETTINGS.set_int('preferences-recent-page', page)

        self.liststore.save_settings()
        self.preferences.destroy()

    def on_checkbutton_sticky_toggled(self, button):
        sticky = button.get_active()
        SETTINGS.set_boolean('window-sticky', sticky)

    def on_checkbutton_autostart_toggled(self, button):
        state = button.get_active()
        self.autostart.set(state)

    def on_button_feed_new_clicked(self, button):
        dialog = FeedSourceDialog(self.preferences)
        (response_id, v) = dialog.run()

        if response_id == Gtk.ResponseType.OK:
            new_iter = self.liststore.append(v)
            self._set_cursor_to(self.feedsource_treeview, new_iter)

    def on_button_feed_prefs_clicked(self, button):
        treeselection = self.feedsource_treeview.get_selection()
        (model, iter) = treeselection.get_selected()

        dialog = FeedSourceDialog(self.preferences, model[iter])
        (response_id, v) = dialog.run()

        if response_id == Gtk.ResponseType.OK:
            new_iter = self.liststore.update(v, iter)
            self._set_cursor_to(self.feedsource_treeview, new_iter)

    def on_button_feed_del_clicked(self, button):
        treeselection = self.feedsource_treeview.get_selection()
        (model, iter) = treeselection.get_selected()
        self.liststore.remove(iter)

        self.button_prefs.set_sensitive(False)
        self.button_del.set_sensitive(False)

    def on_feedsource_treeview_query_tooltip(self, treeview, *args):
        pass

    def on_feedsource_treeview_cursor_changed(self, treeview):
        self.button_prefs.set_sensitive(True)
        self.button_del.set_sensitive(True)

    def on_feedsource_treeview_button_press_event(self, treeview):
        pass

    def on_plugin_treeview_cursor_changed(self, treeview):
        pass

    def _set_cursor_to(self, feedsource_treeview, iter):
        model = feedsource_treeview.get_model()
        row = model.get_path(iter)
        feedsource_treeview.set_cursor(row, None, False)
