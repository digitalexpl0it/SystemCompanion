"""
Security widget for System Companion.

This module provides the security widget that displays
security monitoring, vulnerability checks, and security recommendations.
"""

import logging
import subprocess
import json
import os
import threading
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import shutil

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio

from ...core.system_monitor import SystemMonitor
from ...utils.exceptions import MonitoringError


class SecurityIssue:
    """Represents a security issue."""
    def __init__(self, severity: str, title: str, description: str, recommendation: str, component: str):
        self.severity = severity
        self.title = title
        self.description = description
        self.recommendation = recommendation
        self.component = component


class SecurityWidget(Gtk.Box):
    """Security widget displaying security monitoring and recommendations."""
    
    # State file for persistent firewall status
    STATE_FILE = os.path.expanduser("~/.config/system-companion/security_state.json")
    
    def __init__(self, system_monitor: SystemMonitor) -> None:
        """Initialize the security widget."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        self.logger = logging.getLogger("system_companion.ui.security_widget")
        self.system_monitor = system_monitor
        
        # Security issues
        self.security_issues = []
        
        # Firewall state
        self.ufw_installed = False
        self.ufw_enabled = False
        self.gufw_installed = False
        
        # Load persistent state
        self._load_firewall_state()
        
        # Setup UI
        self._setup_ui()
        self._setup_update_timer()
        
        self.logger.info("Security widget initialized")
    
    def _load_firewall_state(self) -> None:
        """Load firewall state from persistent storage."""
        try:
            if os.path.exists(self.STATE_FILE):
                with open(self.STATE_FILE, 'r') as f:
                    state = json.load(f)
                    self.ufw_installed = state.get('ufw_installed', False)
                    self.ufw_enabled = state.get('ufw_enabled', False)
                    self.gufw_installed = state.get('gufw_installed', False)
            else:
                # Initialize with current system state
                self._update_firewall_state()
        except Exception as e:
            self.logger.error(f"Failed to load firewall state: {e}")
            self._update_firewall_state()
    
    def _save_firewall_state(self) -> None:
        """Save firewall state to persistent storage."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.STATE_FILE), exist_ok=True)
            
            state = {
                'ufw_installed': self.ufw_installed,
                'ufw_enabled': self.ufw_enabled,
                'gufw_installed': self.gufw_installed,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.STATE_FILE, 'w') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save firewall state: {e}")
    
    def _update_firewall_state(self) -> None:
        """Update firewall state from system."""
        try:
            # Check UFW installation
            self.ufw_installed = shutil.which('ufw') is not None
            
            # Check UFW status
            self.ufw_enabled = False
            if self.ufw_installed:
                try:
                    result = subprocess.run(['pkexec', 'ufw', 'status'], capture_output=True, text=True, timeout=10)
                    if result.returncode == 0 and 'active' in result.stdout.lower():
                        self.ufw_enabled = True
                except Exception:
                    pass
            
            # Check GUFW installation
            self.gufw_installed = shutil.which('gufw') is not None
            
            # Save updated state
            self._save_firewall_state()
            
        except Exception as e:
            self.logger.error(f"Failed to update firewall state: {e}")
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        # Main container with scrolling
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_hexpand(True)
        
        # Main content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_margin_start(16)
        content_box.set_margin_end(16)
        content_box.set_margin_top(16)
        content_box.set_margin_bottom(16)
        content_box.set_spacing(16)
        
        # Header
        header = self._create_header()
        content_box.append(header)
        
        # Security overview
        security_overview = self._create_security_overview()
        content_box.append(security_overview)
        
        # Security issues
        issues_section = self._create_issues_section()
        content_box.append(issues_section)
        
        # Security recommendations
        recommendations_section = self._create_recommendations_section()
        content_box.append(recommendations_section)
        
        # System security status
        security_status = self._create_security_status()
        content_box.append(security_status)
        
        scrolled_window.set_child(content_box)
        self.append(scrolled_window)
    
    def _create_header(self) -> Gtk.Box:
        """Create the security header."""
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header_box.add_css_class("security-header")
        header_box.set_hexpand(True)

        # Title
        title_label = Gtk.Label(label="Security Monitor")
        title_label.add_css_class("title-1")
        title_label.set_xalign(0)
        header_box.append(title_label)

        # Spacer to push button to the right
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        header_box.append(spacer)

        # Scan button
        self.scan_button = Gtk.Button(label="Run Security Scan")
        self.scan_button.add_css_class("suggested-action")
        self.scan_button.set_hexpand(False)
        self.scan_button.connect("clicked", self._on_security_scan)
        header_box.append(self.scan_button)

        return header_box
    
    def _create_security_overview(self) -> Gtk.Box:
        """Create the security overview section."""
        overview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        overview_box.add_css_class("dashboard-card")
        
        # Title
        title_label = Gtk.Label(label="Security Overview")
        title_label.add_css_class("title-2")
        overview_box.append(title_label)
        
        # Security score
        self.security_score_label = Gtk.Label(label="Security Score: Loading...")
        self.security_score_label.add_css_class("title-3")
        overview_box.append(self.security_score_label)
        
        # Security bar
        self.security_bar = Gtk.ProgressBar()
        self.security_bar.set_show_text(True)
        self.security_bar.set_fraction(0.0)
        overview_box.append(self.security_bar)
        
        # Security stats grid
        stats_grid = Gtk.Grid()
        stats_grid.set_row_spacing(8)
        stats_grid.set_column_spacing(16)
        
        # Critical issues
        critical_label = Gtk.Label(label="Critical Issues:")
        critical_label.set_xalign(0)
        stats_grid.attach(critical_label, 0, 0, 1, 1)
        
        self.critical_issues_label = Gtk.Label(label="0")
        self.critical_issues_label.add_css_class("security-critical")
        stats_grid.attach(self.critical_issues_label, 1, 0, 1, 1)
        
        # High issues
        high_label = Gtk.Label(label="High Issues:")
        high_label.set_xalign(0)
        stats_grid.attach(high_label, 0, 1, 1, 1)
        
        self.high_issues_label = Gtk.Label(label="0")
        self.high_issues_label.add_css_class("security-high")
        stats_grid.attach(self.high_issues_label, 1, 1, 1, 1)
        
        # Medium issues
        medium_label = Gtk.Label(label="Medium Issues:")
        medium_label.set_xalign(0)
        stats_grid.attach(medium_label, 0, 2, 1, 1)
        
        self.medium_issues_label = Gtk.Label(label="0")
        self.medium_issues_label.add_css_class("security-medium")
        stats_grid.attach(self.medium_issues_label, 1, 2, 1, 1)
        
        # Low issues
        low_label = Gtk.Label(label="Low Issues:")
        low_label.set_xalign(0)
        stats_grid.attach(low_label, 0, 3, 1, 1)
        
        self.low_issues_label = Gtk.Label(label="0")
        self.low_issues_label.add_css_class("security-low")
        stats_grid.attach(self.low_issues_label, 1, 3, 1, 1)
        
        overview_box.append(stats_grid)
        
        return overview_box
    
    def _create_issues_section(self) -> Gtk.Box:
        """Create the security issues section."""
        issues_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        issues_box.add_css_class("dashboard-card")
        
        # Title
        title_label = Gtk.Label(label="Security Issues")
        title_label.add_css_class("title-2")
        issues_box.append(title_label)
        
        # Issues list
        self.issues_listbox = Gtk.ListBox()
        self.issues_listbox.add_css_class("security-issues-list")
        issues_box.append(self.issues_listbox)
        
        # No issues message
        self.no_issues_label = Gtk.Label(label="No security issues detected")
        self.no_issues_label.add_css_class("caption")
        self.no_issues_label.add_css_class("dim-label")
        issues_box.append(self.no_issues_label)
        
        return issues_box
    
    def _create_recommendations_section(self) -> Gtk.Box:
        """Create the security recommendations section."""
        recommendations_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        recommendations_box.add_css_class("dashboard-card")
        
        # Title
        title_label = Gtk.Label(label="Security Recommendations")
        title_label.add_css_class("title-2")
        recommendations_box.append(title_label)
        
        # Two-column grid for recommendations
        self.recommendations_grid = Gtk.Grid()
        self.recommendations_grid.set_row_spacing(16)
        self.recommendations_grid.set_column_spacing(16)
        recommendations_box.append(self.recommendations_grid)
        
        return recommendations_box
    
    def _create_security_status(self) -> Gtk.Frame:
        """Create the system security status section as a card."""
        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        status_box.set_margin_start(16)
        status_box.set_margin_end(16)
        status_box.set_margin_top(16)
        status_box.set_margin_bottom(16)
        status_box.set_spacing(8)
        
        # Title
        title_label = Gtk.Label(label="System Security Status")
        title_label.add_css_class("title-2")
        status_box.append(title_label)
        
        # Status grid
        self.status_grid = Gtk.Grid()
        self.status_grid.set_row_spacing(8)
        self.status_grid.set_column_spacing(16)
        
        status_box.append(self.status_grid)
        
        # Frame for card styling
        frame = Gtk.Frame()
        frame.set_child(status_box)
        frame.add_css_class("task-card")
        frame.set_margin_start(4)
        frame.set_margin_end(4)
        frame.set_margin_top(4)
        frame.set_margin_bottom(4)
        return frame
    
    def _setup_update_timer(self) -> None:
        """Setup the update timer for security monitoring."""
        # Update immediately
        self._update_security_status()
        
        # Set up timer for periodic updates (every 60 seconds)
        GLib.timeout_add_seconds(60, self._update_security_status)
    
    def _update_security_status(self) -> bool:
        """Update security status and return True to continue the timer."""
        try:
            # Update security overview
            self._update_security_overview()
            
            # Update security issues
            self._update_security_issues()
            
            # Update security recommendations
            self._update_security_recommendations()
            
            # Update system security status
            self._update_system_security_status()
            
            return True  # Continue the timer
            
        except Exception as e:
            self.logger.error(f"Failed to update security status: {e}")
            return True  # Continue the timer even on error
    
    def _update_security_overview(self) -> None:
        """Update the security overview."""
        try:
            # Calculate security score based on issues
            critical_count = len([i for i in self.security_issues if i.severity == "critical"])
            high_count = len([i for i in self.security_issues if i.severity == "high"])
            medium_count = len([i for i in self.security_issues if i.severity == "medium"])
            low_count = len([i for i in self.security_issues if i.severity == "low"])
            
            # Update issue counts
            self.critical_issues_label.set_label(str(critical_count))
            self.high_issues_label.set_label(str(high_count))
            self.medium_issues_label.set_label(str(medium_count))
            self.low_issues_label.set_label(str(low_count))
            
            # Calculate security score (100 - weighted issue count)
            security_score = 100 - (critical_count * 20 + high_count * 10 + medium_count * 5 + low_count * 2)
            security_score = max(0, security_score)
            
            # Update security score
            if security_score >= 80:
                status = "Excellent"
                css_class = "security-excellent"
            elif security_score >= 60:
                status = "Good"
                css_class = "security-good"
            elif security_score >= 40:
                status = "Fair"
                css_class = "security-fair"
            else:
                status = "Poor"
                css_class = "security-poor"
            
            self.security_score_label.set_label(f"Security Score: {status} ({security_score:.0f}/100)")
            
            # Update progress bar
            self.security_bar.set_fraction(security_score / 100.0)
            
            # Update CSS class
            self.security_score_label.remove_css_class("security-excellent")
            self.security_score_label.remove_css_class("security-good")
            self.security_score_label.remove_css_class("security-fair")
            self.security_score_label.remove_css_class("security-poor")
            self.security_score_label.add_css_class(css_class)
            
        except Exception as e:
            self.logger.error(f"Failed to update security overview: {e}")
    
    def _update_security_issues(self) -> None:
        """Update the security issues list."""
        try:
            # Clear existing issues
            while self.issues_listbox.get_first_child():
                self.issues_listbox.remove(self.issues_listbox.get_first_child())
            
            if not self.security_issues:
                # Show no issues message
                self.no_issues_label.set_visible(True)
                return
            
            # Hide no issues message
            self.no_issues_label.set_visible(False)
            
            for issue in self.security_issues:
                # Create issue row
                row = Gtk.ListBoxRow()
                
                # Issue content
                issue_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                issue_box.set_margin_start(8)
                issue_box.set_margin_end(8)
                issue_box.set_margin_top(8)
                issue_box.set_margin_bottom(8)
                issue_box.set_spacing(4)
                
                # Issue header
                header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                
                # Title
                title_label = Gtk.Label(label=issue.title)
                title_label.add_css_class("title-4")
                title_label.set_xalign(0)
                title_label.set_hexpand(True)
                header_box.append(title_label)
                
                # Severity pill
                severity_label = Gtk.Label(label=issue.severity.upper())
                severity_label.add_css_class("pill")
                severity_label.add_css_class(f"pill-{issue.severity}")
                header_box.append(severity_label)
                
                issue_box.append(header_box)
                
                # Description
                desc_label = Gtk.Label(label=issue.description)
                desc_label.set_xalign(0)
                desc_label.set_wrap(True)
                issue_box.append(desc_label)
                
                # Recommendation
                rec_label = Gtk.Label(label=f"Recommendation: {issue.recommendation}")
                rec_label.add_css_class("caption")
                rec_label.set_xalign(0)
                rec_label.set_wrap(True)
                issue_box.append(rec_label)
                
                # Fix/Review button
                button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                button_box.set_spacing(8)
                if issue.title.lower() == "outdated packages":
                    fix_btn = Gtk.Button(label="Fix")
                    fix_btn.add_css_class("suggested-action")
                    fix_btn.connect("clicked", self._on_fix_outdated_packages)
                    # Spinner for loading state
                    fix_spinner = Gtk.Spinner()
                    fix_spinner.set_margin_start(8)
                    fix_spinner.set_visible(False)
                    button_box.append(fix_btn)
                    button_box.append(fix_spinner)
                    # Store references for later use
                    self._fix_btn = fix_btn
                    self._fix_spinner = fix_spinner
                elif issue.title.lower() == "multiple open ports":
                    review_btn = Gtk.Button(label="Review")
                    review_btn.add_css_class("suggested-action")
                    review_btn.connect("clicked", self._on_review_open_ports)
                    button_box.append(review_btn)
                else:
                    review_btn = Gtk.Button(label="Review")
                    review_btn.add_css_class("suggested-action")
                    review_btn.connect("clicked", self._on_review_issue, issue)
                    button_box.append(review_btn)
                issue_box.append(button_box)
                
                row.set_child(issue_box)
                self.issues_listbox.append(row)
        
        except Exception as e:
            self.logger.error(f"Failed to update security issues: {e}")

    def _on_fix_outdated_packages(self, button: Gtk.Button) -> None:
        """Fix outdated packages by running apt update/upgrade."""
        # Show spinner and disable button
        if hasattr(self, '_fix_btn') and hasattr(self, '_fix_spinner'):
            self._fix_btn.set_sensitive(False)
            self._fix_spinner.set_visible(True)
            self._fix_spinner.start()
        def on_complete(success: bool):
            if hasattr(self, '_fix_btn') and hasattr(self, '_fix_spinner'):
                self._fix_btn.set_sensitive(True)
                self._fix_spinner.set_visible(False)
                self._fix_spinner.stop()
            if success:
                self._show_notification("Success", "System packages updated successfully.")
                # Re-run security scan to check if the issue is resolved
                self._perform_security_scan_async()
            else:
                self._show_notification("Error", "Failed to update system packages.")
        self._run_privileged_command(
            ['sh', '-c', 'apt update && apt upgrade -y && apt autoremove -y'],
            on_complete
        )

    def _on_review_open_ports(self, button: Gtk.Button) -> None:
        """Show a dialog listing open network ports using ss in a grid view with export option."""
        import subprocess
        import csv
        import tempfile
        import os
        
        try:
            # Run ss to get open ports
            result = subprocess.run(["ss", "-tuln"], capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception("Failed to get open ports: ss command failed")
            
            lines = result.stdout.strip().split('\n')
            if len(lines) <= 1:  # Only header or empty
                ports_data = []
            else:
                # Parse ss output, skip the first header line
                ports_data = []
                for line in lines[1:]:
                    parts = line.split()
                    if len(parts) >= 6:
                        netid = parts[0]
                        state = parts[1]
                        local_address = parts[4]
                        peer_address = parts[5]
                        ports_data.append([
                            netid,
                            state,
                            local_address,
                            peer_address
                        ])
            
            # Create dialog
            dialog = Gtk.Dialog(
                title="Open Network Ports (ss)",
                transient_for=self.get_root(),
                modal=True
            )
            dialog.set_default_size(900, 600)
            
            # Content area
            content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            content_box.set_margin_start(16)
            content_box.set_margin_end(16)
            content_box.set_margin_top(16)
            content_box.set_margin_bottom(16)
            content_box.set_spacing(16)
            
            # Header with export button
            header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            header_box.set_spacing(8)
            
            title_label = Gtk.Label(label=f"Found {len(ports_data)} open ports")
            title_label.add_css_class("title-3")
            title_label.set_xalign(0)
            title_label.set_hexpand(True)
            header_box.append(title_label)
            
            export_btn = Gtk.Button(label="Export to CSV")
            export_btn.add_css_class("suggested-action")
            export_btn.connect("clicked", self._export_ports_to_csv, ports_data)
            header_box.append(export_btn)
            
            content_box.append(header_box)
            
            # Create tree view
            tree_view = Gtk.TreeView()
            tree_view.set_vexpand(True)
            tree_view.set_hexpand(True)
            
            # Create list store
            list_store = Gtk.ListStore(str, str, str, str)  # Netid, State, Local Address:Port, Peer Address:Port
            
            # Add columns
            columns = [
                ("Netid", 0, 80),
                ("State", 1, 100),
                ("Local Address:Port", 2, 220),
                ("Peer Address:Port", 3, 220)
            ]
            for col_title, col_idx, col_width in columns:
                renderer = Gtk.CellRendererText()
                column = Gtk.TreeViewColumn(col_title, renderer, text=col_idx)
                column.set_min_width(col_width)
                tree_view.append_column(column)
            
            # Populate list store
            for row in ports_data:
                list_store.append(row)
            tree_view.set_model(list_store)
            
            content_box.append(tree_view)
            
            dialog.get_content_area().append(content_box)
            dialog.add_button("Close", Gtk.ResponseType.CLOSE)
            dialog.connect("response", lambda d, r: d.destroy())
            dialog.show()
            
        except FileNotFoundError:
            self._show_notification("ss Not Found", "The 'ss' command is not available on this system. Please install the 'iproute2' package.")
        except Exception as e:
            self._show_notification("Open Ports Error", f"Failed to list open ports: {e}")

    def _export_ports_to_csv(self, button: Gtk.Button, ports_data: list) -> None:
        """Export open ports data to a CSV file."""
        import tempfile
        import csv
        import os
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix="_open_ports.csv", mode="w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Netid", "State", "Local Address:Port", "Peer Address:Port"])
                for row in ports_data:
                    writer.writerow(row)
                file_path = f.name
            os.system(f'xdg-open "{file_path}"')
        except Exception as e:
            self._show_notification("Export Error", f"Failed to export open ports: {e}")
    
    def _on_review_issue(self, button: Gtk.Button, issue) -> None:
        """Show a dialog with more information about the issue."""
        dialog = Adw.MessageDialog(
            transient_for=self.get_root(),
            modal=True,
            heading=issue.title,
            body=issue.description + "\n\nRecommendation: " + issue.recommendation
        )
        dialog.add_response("close", "Close")
        dialog.set_default_response("close")
        dialog.connect("response", lambda d, r: d.destroy())
        dialog.show()
    
    def _update_security_recommendations(self) -> None:
        """Update the security recommendations grid."""
        try:
            # Clear existing recommendations
            while self.recommendations_grid.get_first_child():
                self.recommendations_grid.remove(self.recommendations_grid.get_first_child())
            
            # Get security recommendations
            recommendations = self._get_security_recommendations()
            
            for i, recommendation in enumerate(recommendations):
                # Create recommendation card
                card = self._create_recommendation_card(recommendation)
                
                # Add to grid (2 columns)
                row = i // 2
                col = i % 2
                self.recommendations_grid.attach(card, col, row, 1, 1)
            
        except Exception as e:
            self.logger.error(f"Failed to update security recommendations: {e}")
    
    def _create_recommendation_card(self, recommendation: Dict) -> Gtk.Frame:
        """Create a recommendation card as a Gtk.Frame for proper CSS styling."""
        # Card content
        card_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        card_box.set_margin_start(16)
        card_box.set_margin_end(16)
        card_box.set_margin_top(16)
        card_box.set_margin_bottom(16)
        card_box.set_spacing(12)
        
        # Header with title and priority
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header_box.set_spacing(8)
        
        # Title
        title_label = Gtk.Label(label=recommendation['title'])
        title_label.add_css_class("title-4")
        title_label.set_xalign(0)
        title_label.set_hexpand(True)
        header_box.append(title_label)
        
        # Priority pill
        priority_pill = Gtk.Label(label=recommendation['priority'])
        priority_pill.add_css_class("pill")
        priority_pill.add_css_class(f"pill-{recommendation['priority'].lower()}")
        header_box.append(priority_pill)
        
        card_box.append(header_box)
        
        # Description
        desc_label = Gtk.Label(label=recommendation['description'])
        desc_label.set_xalign(0)
        desc_label.set_wrap(True)
        desc_label.set_max_width_chars(40)
        card_box.append(desc_label)
        
        # Action buttons for specific recommendations
        if recommendation['title'] == 'Enable Firewall':
            button_box = self._create_firewall_buttons()
            if button_box:
                card_box.append(button_box)
        
        # Frame for card styling
        frame = Gtk.Frame()
        frame.set_child(card_box)
        frame.add_css_class("task-card")
        frame.set_margin_start(4)
        frame.set_margin_end(4)
        frame.set_margin_top(4)
        frame.set_margin_bottom(4)
        return frame
    
    def _create_firewall_buttons(self) -> Optional[Gtk.Box]:
        """Create firewall action buttons using persistent state."""
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_spacing(8)
        
        if not self.ufw_installed:
            install_ufw_btn = Gtk.Button(label="Install UFW")
            install_ufw_btn.add_css_class("suggested-action")
            install_ufw_btn.connect("clicked", self._on_install_ufw)
            button_box.append(install_ufw_btn)
        elif not self.ufw_enabled:
            enable_ufw_btn = Gtk.Button(label="Enable UFW")
            enable_ufw_btn.add_css_class("suggested-action")
            enable_ufw_btn.connect("clicked", self._on_enable_ufw)
            button_box.append(enable_ufw_btn)
        elif not self.gufw_installed:
            install_gufw_btn = Gtk.Button(label="Install GUFW")
            install_gufw_btn.add_css_class("suggested-action")
            install_gufw_btn.connect("clicked", self._on_install_gufw)
            button_box.append(install_gufw_btn)
        else:
            open_gufw_btn = Gtk.Button(label="Open GUFW")
            open_gufw_btn.add_css_class("suggested-action")
            open_gufw_btn.connect("clicked", self._on_open_gufw)
            button_box.append(open_gufw_btn)
        
        return button_box

    def _get_security_recommendations(self) -> List[Dict]:
        """Get security recommendations."""
        recommendations = []
        
        # Basic security recommendations
        recommendations.append({
            'title': 'Keep System Updated',
            'description': 'Regularly update your system packages to patch security vulnerabilities.',
            'priority': 'High'
        })
        
        recommendations.append({
            'title': 'Enable Firewall',
            'description': 'Ensure UFW firewall is enabled and properly configured.',
            'priority': 'High'
        })
        
        recommendations.append({
            'title': 'Use Strong Passwords',
            'description': 'Use strong, unique passwords for all user accounts.',
            'priority': 'Medium'
        })
        
        recommendations.append({
            'title': 'Enable Automatic Security Updates',
            'description': 'Configure unattended-upgrades for automatic security updates.',
            'priority': 'Medium'
        })
        
        recommendations.append({
            'title': 'Regular Security Audits',
            'description': 'Perform regular security audits using tools like Lynis.',
            'priority': 'Low'
        })
        
        return recommendations
    
    def _update_system_security_status(self) -> None:
        """Update system security status."""
        try:
            # Clear existing status
            while self.status_grid.get_first_child():
                self.status_grid.remove(self.status_grid.get_first_child())
            
            # Get security status
            security_status = self._get_system_security_status()
            
            # Add status rows
            for i, (component, status) in enumerate(security_status.items()):
                # Component name
                name_label = Gtk.Label(label=component)
                name_label.set_xalign(0)
                self.status_grid.attach(name_label, 0, i, 1, 1)
                
                # Status as pill
                status_label = Gtk.Label(label=status['status'])
                status_label.add_css_class("pill")
                status_label.add_css_class(f"pill-{status['status'].lower()}")
                self.status_grid.attach(status_label, 1, i, 1, 1)
                
                # Details
                details_label = Gtk.Label(label=status['details'])
                details_label.set_xalign(0)
                details_label.set_hexpand(True)
                self.status_grid.attach(details_label, 2, i, 1, 1)
            
                # Add Verify button for Firewall status
                if component == 'Firewall':
                    verify_btn = Gtk.Button(label="Verify")
                    verify_btn.add_css_class("suggested-action")
                    verify_btn.set_hexpand(False)
                    verify_btn.set_margin_start(16)
                    verify_btn.connect("clicked", self._on_verify_firewall_status)
                    self.status_grid.attach(verify_btn, 3, i, 1, 1)

        except Exception as e:
            self.logger.error(f"Failed to update system security status: {e}")

    def _on_verify_firewall_status(self, button: Gtk.Button) -> None:
        """Verify firewall status with privileged access."""
        # Disable button and show loading state
        button.set_sensitive(False)
        button.set_label("Verifying...")

        def on_complete(success: bool, output: str = "", error: str = ""):
            # Re-enable button
            button.set_sensitive(True)
            button.set_label("Verify")

            if success:
                if 'active' in output.lower():
                    self._show_notification("Firewall Status", "UFW firewall is active and running.")
                    self.ufw_enabled = True
                    self._save_firewall_state()
                    self._update_firewall_status_row("ok", "UFW firewall is active")
                else:
                    self._show_notification("Firewall Status", "UFW firewall is not active.")
                    self.ufw_enabled = False
                    self._save_firewall_state()
                    self._update_firewall_status_row("warning", "UFW firewall is not active")
            else:
                self._show_notification("Verification Failed", f"Could not verify firewall status: {error}")

        # Run the privileged command
        self._run_privileged_command_with_output(['ufw', 'status'], on_complete)

    def _update_firewall_status_row(self, status, details):
        """Update the firewall row in the status grid with new status and details."""
        # Find the row index for Firewall
        for i, (component, _) in enumerate(self._get_system_security_status().items()):
            if component == 'Firewall':
                # Update status label
                status_label = self.status_grid.get_child_at(1, i)
                if status_label:
                    status_label.set_label(status)
                    # Remove old status classes and add new one
                    for s in ["ok", "warning", "unknown"]:
                        status_label.remove_css_class(f"pill-{s}")
                    status_label.add_css_class(f"pill-{status}")
                # Update details label
                details_label = self.status_grid.get_child_at(2, i)
                if details_label:
                    details_label.set_label(details)
                break
    
    def _run_privileged_command_with_output(self, command, on_complete=None):
        """Run a privileged command with output callback."""
        import subprocess
        import threading

        def run_cmd():
            try:
                full_cmd = ['pkexec'] + command
                result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=30)
                success = result.returncode == 0
                output = result.stdout
                error = result.stderr

                if on_complete:
                    GLib.idle_add(on_complete, success, output, error)

            except subprocess.TimeoutExpired:
                if on_complete:
                    GLib.idle_add(on_complete, False, "", "Command timed out")
            except Exception as e:
                if on_complete:
                    GLib.idle_add(on_complete, False, "", str(e))

        thread = threading.Thread(target=run_cmd)
        thread.daemon = True
        thread.start()
    
    def _get_system_security_status(self) -> Dict[str, Dict]:
        """Get system security status."""
        try:
            status = {}
            
            # Check firewall status
            try:
                result = subprocess.run(['ufw', 'status'], capture_output=True, text=True)
                if result.returncode == 0 and 'active' in result.stdout.lower():
                    firewall_status = "ok"
                    firewall_details = "UFW firewall is active"
                else:
                    firewall_status = "warning"
                    firewall_details = "UFW firewall is not active"
            except Exception:
                firewall_status = "unknown"
                firewall_details = "Could not check firewall status"
            
            status['Firewall'] = {
                'status': firewall_status,
                'details': firewall_details
            }
            
            # Check for root login
            try:
                with open('/etc/ssh/sshd_config', 'r') as f:
                    ssh_config = f.read()
                if 'PermitRootLogin no' in ssh_config:
                    ssh_status = "ok"
                    ssh_details = "Root login disabled"
                else:
                    ssh_status = "warning"
                    ssh_details = "Root login may be enabled"
            except Exception:
                ssh_status = "unknown"
                ssh_details = "Could not check SSH configuration"
            
            status['SSH Security'] = {
                'status': ssh_status,
                'details': ssh_details
            }
            
            # Check for automatic updates
            try:
                result = subprocess.run(['systemctl', 'is-active', 'unattended-upgrades'], 
                                      capture_output=True, text=True)
                if result.returncode == 0 and 'active' in result.stdout:
                    updates_status = "ok"
                    updates_details = "Automatic updates enabled"
                else:
                    updates_status = "warning"
                    updates_details = "Automatic updates not enabled"
            except Exception:
                updates_status = "unknown"
                updates_details = "Could not check automatic updates"
            
            status['Automatic Updates'] = {
                'status': updates_status,
                'details': updates_details
            }
            
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to get system security status: {e}")
            return {}
    
    def _on_security_scan(self, button: Gtk.Button) -> None:
        """Handle security scan button click."""
        try:
            # Disable button during scan
            button.set_sensitive(False)
            button.set_label("Scanning...")
            
            # Run security scan in background
            def run_scan():
                try:
                    # Perform security scan
                    issues = self._perform_security_scan()
                    
                    # Update UI in main thread
                    GLib.idle_add(self._scan_completed, issues)
                    
                except Exception as e:
                    self.logger.error(f"Security scan failed: {e}")
                    GLib.idle_add(self._scan_failed, str(e))
            
            # Start scan thread
            import threading
            thread = threading.Thread(target=run_scan)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            self.logger.error(f"Failed to start security scan: {e}")
            button.set_sensitive(True)
            button.set_label("Run Security Scan")
    
    def _perform_security_scan(self) -> List[SecurityIssue]:
        """Perform a security scan."""
        issues = []
        
        try:
            # Check for outdated packages
            try:
                # First check for security updates specifically
                result = subprocess.run(['apt', 'list', '--upgradable'], 
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:  # More than just the header
                        # Count upgradable packages
                        upgradable_count = len([line for line in lines[1:] if line.strip()])
                        
                        # Check if there are security-related packages
                        security_packages = []
                        for line in lines[1:]:
                            if line.strip() and any(security_keyword in line.lower() for security_keyword in 
                                                  ['security', 'kernel', 'openssl', 'libssl', 'firefox', 'chromium', 'thunderbird']):
                                security_packages.append(line.split('/')[0])
                        
                        if security_packages or upgradable_count > 10:  # Show if security packages or many updates
                            description = f"System has {upgradable_count} outdated packages"
                            if security_packages:
                                description += f" including security updates: {', '.join(security_packages[:3])}"
                                if len(security_packages) > 3:
                                    description += f" and {len(security_packages) - 3} more"
                            
                            # Log what we found for debugging
                            self.logger.info(f"Found {upgradable_count} upgradable packages, {len(security_packages)} security-related")
                            if security_packages:
                                self.logger.info(f"Security packages: {security_packages}")
                            
                            issues.append(SecurityIssue(
                                severity="medium",
                                title="Outdated Packages",
                                description=description,
                                recommendation="Run 'pkexec apt update && pkexec apt upgrade' to update packages.",
                                component="Package Management"
                            ))
            except Exception as e:
                self.logger.error(f"Failed to check for outdated packages: {e}")
                pass
            
            # Check for weak file permissions
            try:
                result = subprocess.run(['find', '/etc', '-perm', '-o+w'], 
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0 and result.stdout.strip():
                    issues.append(SecurityIssue(
                        severity="high",
                        title="Weak File Permissions",
                        description="Some system files have overly permissive permissions.",
                        recommendation="Review and fix file permissions in /etc directory.",
                        component="File System"
                    ))
            except Exception:
                pass
            
            # Check for open ports
            try:
                result = subprocess.run(['ss', '-tuln'], capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    open_ports = result.stdout.strip().split('\n')[1:]  # Skip header
                    if len(open_ports) > 5:  # Arbitrary threshold
                        issues.append(SecurityIssue(
                            severity="medium",
                            title="Multiple Open Ports",
                            description="System has many open network ports.",
                            recommendation="Review and close unnecessary network ports.",
                            component="Network"
                        ))
            except Exception:
                pass
            
        except Exception as e:
            self.logger.error(f"Security scan error: {e}")
        
        return issues
    
    def _scan_completed(self, issues: List[SecurityIssue]) -> None:
        """Handle security scan completion."""
        try:
            # Re-enable button
            self.scan_button.set_sensitive(True)
            self.scan_button.set_label("Run Security Scan")
            
            # Update security issues
            self.security_issues = issues
            
            # Update security status
            self._update_security_status()
            
            # Show completion message
            self._show_notification("Security Scan Completed", f"Found {len(issues)} security issues")
            
        except Exception as e:
            self.logger.error(f"Failed to handle scan completion: {e}")
    
    def _perform_security_scan_async(self) -> None:
        """Perform security scan asynchronously and update UI."""
        def run_scan():
            try:
                issues = self._perform_security_scan()
                GLib.idle_add(self._scan_completed, issues)
            except Exception as e:
                error_message = f"Security scan failed: {e}"
                GLib.idle_add(self._scan_failed, error_message)
        
        # Run scan in background thread
        threading.Thread(target=run_scan, daemon=True).start()

    def _scan_failed(self, error_message: str) -> None:
        """Handle security scan failure."""
        try:
            # Re-enable button
            self.scan_button.set_sensitive(True)
            self.scan_button.set_label("Run Security Scan")
            
            # Show error message
            self._show_notification("Security Scan Failed", error_message)
            
        except Exception as e:
            self.logger.error(f"Failed to handle scan failure: {e}")
    
    def _show_notification(self, title: str, message: str) -> None:
        """Show a notification message."""
        try:
            # Create a simple notification dialog
            dialog = Gtk.MessageDialog(
                transient_for=self.get_root(),
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text=title,
                secondary_text=message
            )
            
            dialog.connect("response", lambda dialog, response: dialog.destroy())
            dialog.present()
            
        except Exception as e:
            self.logger.error(f"Failed to show notification: {e}")
    
    def _on_install_ufw(self, button: Gtk.Button) -> None:
        """Install UFW and update state."""
        def on_complete(success: bool):
            if success:
                self.ufw_installed = True
                self._save_firewall_state()
                self._update_security_recommendations()  # Refresh UI
                self._show_notification("Success", "UFW installed successfully.")
            else:
                self._show_notification("Error", "Failed to install UFW.")
        
        self._run_privileged_command(['apt', 'install', '-y', 'ufw'], on_complete)

    def _on_enable_ufw(self, button: Gtk.Button) -> None:
        """Enable UFW and update state."""
        def on_complete(success: bool):
            if success:
                self.ufw_enabled = True
                self._save_firewall_state()
                self._update_security_recommendations()  # Refresh UI
                self._show_notification("Success", "UFW enabled successfully.")
            else:
                self._show_notification("Error", "Failed to enable UFW.")
        
        self._run_privileged_command(['ufw', 'enable'], on_complete)

    def _on_install_gufw(self, button: Gtk.Button) -> None:
        """Install GUFW and update state."""
        def on_complete(success: bool):
            if success:
                self.gufw_installed = True
                self._save_firewall_state()
                self._update_security_recommendations()  # Refresh UI
                self._show_notification("Success", "GUFW installed successfully.")
            else:
                self._show_notification("Error", "Failed to install GUFW.")
        
        self._run_privileged_command(['apt', 'install', '-y', 'gufw'], on_complete)

    def _on_open_gufw(self, button: Gtk.Button) -> None:
        """Open GUFW."""
        import subprocess
        try:
            subprocess.Popen(['gufw'])
            self._show_notification("GUFW", "GUFW opened successfully.")
        except Exception as e:
            self._show_notification("Error", f"Failed to open GUFW: {e}")

    def _run_privileged_command(self, command, on_complete=None):
        """Run a privileged command with callback."""
        import subprocess
        import threading
        
        def run_cmd():
            try:
                full_cmd = ['pkexec'] + command
                result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=60)
                success = result.returncode == 0
                
                if on_complete:
                    GLib.idle_add(on_complete, success)
                else:
                    if success:
                        GLib.idle_add(self._show_notification, "Success", "Command completed successfully.")
                    else:
                        GLib.idle_add(self._show_notification, "Error", f"Command failed: {result.stderr}")
                        
            except Exception as e:
                if on_complete:
                    GLib.idle_add(on_complete, False)
                else:
                    GLib.idle_add(self._show_notification, "Error", f"Command failed: {e}")
        
        thread = threading.Thread(target=run_cmd)
        thread.daemon = True
        thread.start()
    
    def cleanup(self) -> None:
        """Clean up resources when the widget is destroyed."""
        self.logger.info("Cleaning up security widget")
        # Any cleanup code would go here 