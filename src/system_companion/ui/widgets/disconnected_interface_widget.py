#!/usr/bin/env python3
"""
Widget to display disconnected network interfaces.
"""

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

class DisconnectedInterfaceWidget(Gtk.Box):
    """Widget to display a disconnected network interface."""
    
    def __init__(self, interface_name: str):
        """Initialize the disconnected interface widget."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        self.interface_name = interface_name
        
        # Set up the widget
        self.set_spacing(16)
        self.set_margin_start(16)
        self.set_margin_end(16)
        self.set_margin_top(16)
        self.set_margin_bottom(16)
        self.add_css_class("disconnected-interface-widget")
        
        # Create main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.add_css_class("dashboard-card")
        main_box.set_spacing(16)
        
        # Interface name header
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header_box.set_spacing(8)
        
        # Interface icon (network icon)
        icon = Gtk.Image()
        icon.set_from_icon_name("network-wireless-symbolic")
        icon.set_pixel_size(24)
        header_box.append(icon)
        
        # Interface name
        name_label = Gtk.Label(label=interface_name)
        name_label.add_css_class("title-2")
        name_label.set_hexpand(True)
        name_label.set_xalign(0)
        header_box.append(name_label)
        
        main_box.append(header_box)
        
        # Disconnected status
        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        status_box.set_spacing(8)
        
        # Status icon
        status_icon = Gtk.Image()
        status_icon.set_from_icon_name("network-wireless-offline-symbolic")
        status_icon.set_pixel_size(48)
        status_icon.add_css_class("disconnected-icon")
        status_box.append(status_icon)
        
        # Status text
        status_label = Gtk.Label(label="Disconnected")
        status_label.add_css_class("title-3")
        status_label.add_css_class("disconnected-text")
        status_box.append(status_label)
        
        # Description
        desc_label = Gtk.Label(label="This network interface is currently not connected or inactive.")
        desc_label.add_css_class("body")
        desc_label.add_css_class("disconnected-description")
        desc_label.set_wrap(True)
        status_box.append(desc_label)
        
        main_box.append(status_box)
        
        # Add to main container
        self.append(main_box)
        
        # Set size request for consistent layout
        self.set_size_request(600, 200) 