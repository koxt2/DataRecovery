# smart_dialog_columnview.py
#
# Copyright 2025 koxt2
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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# SPDX-License-Identifier: GPL-2.0-or-later

from gi.repository import GObject, Gtk

class SmartAttribute(GObject.Object):
    __gtype_name__ = 'SmartAttribute'
    
    def __init__(self, attr_id, name, value, worst, thresh, raw):
        super().__init__()
        self._id = attr_id
        self._name = name
        self._value = value
        self._worst = worst
        self._thresh = thresh
        self._raw = raw
    
    @GObject.Property(type=str)
    def id(self):
        return str(self._id) if self._id is not None else ""
    
    @GObject.Property(type=str)
    def name(self):
        return self._name
    
    @GObject.Property(type=str)
    def value(self):
        return str(self._value) if self._value is not None else ""
    
    @GObject.Property(type=str)
    def worst(self):
        return str(self._worst) if self._worst is not None else ""
    
    @GObject.Property(type=str)
    def thresh(self):
        return str(self._thresh) if self._thresh is not None else ""
    
    @GObject.Property(type=str)
    def raw(self):
        return str(self._raw)

class SmartDialogColumnView:
    def __init__(self, dialog):
        self.dialog = dialog
        self.setup_factories()
    
    def setup_factories(self):
        self.dialog.id_factory.connect("setup", self._label_factory_setup)
        self.dialog.id_factory.connect("bind", self._label_factory_bind('id'))
        self.dialog.name_factory.connect("setup", self._label_factory_setup)
        self.dialog.name_factory.connect("bind", self._label_factory_bind('name'))
        self.dialog.value_factory.connect("setup", self._label_factory_setup)
        self.dialog.value_factory.connect("bind", self._label_factory_bind('value'))
        self.dialog.worst_factory.connect("setup", self._label_factory_setup)
        self.dialog.worst_factory.connect("bind", self._label_factory_bind('worst'))
        self.dialog.thresh_factory.connect("setup", self._label_factory_setup)
        self.dialog.thresh_factory.connect("bind", self._label_factory_bind('thresh'))
        self.dialog.raw_factory.connect("setup", self._label_factory_setup)
        self.dialog.raw_factory.connect("bind", self._label_factory_bind('raw'))
    
    def _label_factory_setup(self, factory, list_item):
        label = Gtk.Label()
        label.set_halign(Gtk.Align.START)
        list_item.set_child(label)
    
    def _label_factory_bind(self, prop_name):
        def bind_func(factory, list_item):
            label = list_item.get_child()
            item = list_item.get_item()
            text = item.get_property(prop_name)
            label.set_text(text if text else "")
        return bind_func
    
    def populate_attributes(self, attributes):
        self.dialog.attributes_liststore.remove_all()
        
        if attributes:
            self.dialog.attributes_label.set_visible(True)
            for attr in attributes:
                self.dialog.attributes_liststore.append(SmartAttribute(
                    attr['id'], attr['name'], attr['value'], 
                    attr['worst'], attr['thresh'], attr['raw']
                ))
        else:
            self.dialog.attributes_label.set_visible(False)
