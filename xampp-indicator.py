#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Xampp Indicator
#
# Copyright (c) 2018 - 2019 AXeL

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, GdkPixbuf, GLib, AppIndicator3 as AppIndicator
import os, subprocess, webbrowser

class ServiceStatus:
	On, Off, Disabled = ('RUNNING', 'NOTRUNNING', 'DEACTIVATED')

class XamppIndicator():
	def __init__(self):
		# Setup Indicator Applet
		self.indicator = AppIndicator.Indicator.new('xampp-indicator', 'xampp', AppIndicator.IndicatorCategory.APPLICATION_STATUS)
		self.indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)

		# Set Attributes
		xampp_path = '/opt/lampp'
		self.xampp_bin = os.path.join(xampp_path, 'lampp')
		self.control_panel_bin = os.path.join(xampp_path, 'manager-linux-x64.run')
		if not os.path.exists(self.control_panel_bin):
			self.control_panel_bin = os.path.join(xampp_path, 'manager-linux.run')
		self.default_text_editor = 'gedit'
		self.default_service = 'APACHE'
		self.serviceMenuItems = {}
		self.services = {
			'APACHE': {
				'label': 'Apache',
				'name': 'apache',
				'status_key': 'APACHE'
			},
			'MYSQL': {
				'label': 'MySQL',
				'name': 'mysql',
				'status_key': 'APACHE' # i used APACHE status here because MYSQL status returns Off when get status command is not executed as administrator (using pkexec or sudo)
			}
			,
			'PROFTPD': {
				'label': 'FTP',
				'name': 'ftp',
				#'enabled': True,
				'status_key': 'PROFTPD'
			}
		}

		# Get Xampp Status
		self.status = self.get_xampp_status()

		# Set Indicator Icon
		self.set_icon()

		# Setup The Menu
		self.menu = Gtk.Menu()

		# Menu Item: Start
		if self.default_service in self.status and self.status[self.default_service] == ServiceStatus.On:
			label = 'Stop'
		else:
			label = 'Start'
		self.startStopItem = Gtk.MenuItem(label)
		self.startStopItem.connect('activate', self.start_stop_xampp)
		self.menu.append(self.startStopItem)

		# Menu Item: Restart
		restartItem = Gtk.MenuItem('Restart')
		restartItem.connect('activate', self.restart_xampp)
		self.menu.append(restartItem)
		self.menu.append(Gtk.SeparatorMenuItem())

		# Service Menu Items
		for service in self.services:
			self.serviceMenuItems[service] = Gtk.CheckMenuItem(self.services[service]['label'])
			if 'enabled' not in self.services[service] or not self.services[service]['enabled']:
				self.serviceMenuItems[service].set_sensitive(False) # Disable service toggle due to MYSQL get status issue
			if self.services[service]['status_key'] in self.status and self.status[self.services[service]['status_key']] == ServiceStatus.On:
				self.serviceMenuItems[service].set_active(True)
			self.serviceMenuItems[service].connect('activate', self.toggle_service, service)
			self.menu.append(self.serviceMenuItems[service])
		self.menu.append(Gtk.SeparatorMenuItem())

		# Menu Item: Open htdocs
		openHtdocsItem = Gtk.MenuItem('Open htdocs')
		openHtdocsItem.connect('activate', self.open_path, xampp_path + '/htdocs')
		self.menu.append(openHtdocsItem)

		# Menu Item: Edit php.ini
		editPhpIniItem = Gtk.MenuItem('Edit php.ini')
		editPhpIniItem.connect('activate', self.open_file_in_editor, xampp_path + '/etc/php.ini')
		self.menu.append(editPhpIniItem)

		# Menu Item: Launch phpMyAdmin
		launchPhpMyAdminItem = Gtk.MenuItem('Launch phpMyAdmin')
		launchPhpMyAdminItem.connect('activate', self.open_url, 'http://localhost/phpmyadmin/')
		self.menu.append(launchPhpMyAdminItem)

		# Menu Item: Launch Control Panel
		launchControlPanelItem = Gtk.MenuItem('Launch Control Panel')
		launchControlPanelItem.connect('activate', self.launch_control_panel)
		self.menu.append(launchControlPanelItem)
		self.menu.append(Gtk.SeparatorMenuItem())

		# Menu Item: About
		aboutItem = Gtk.MenuItem('About')
		aboutItem.connect('activate', self.about)
		self.menu.append(aboutItem)

		# Menu Item: Quit
		exitItem = Gtk.MenuItem('Quit')
		exitItem.connect('activate', self.quit)
		self.menu.append(exitItem)

		# Show All Menu Items
		self.menu.show_all()

		# Assign Menu To Indicator
		self.indicator.set_menu(self.menu)

	def get_xampp_status(self):
		print('--- Get XAMPP Status ---')
		raw_status = subprocess.getoutput('echo n | ' + self.xampp_bin + ' statusraw')
		status = {}
		for service in self.services:
			status[service] = ''
		lines = raw_status.split('\n')
		for line in lines[1:]: # Ignore first line
			service = line.split(' ')
			if service[0] in status:
				status[service[0]] = service[1]
		for service in status:
			print('%s %s' % (service, status[service]))
		print('-' * 24)

		return status

	def open_file_in_editor(self, widget, filename):
		editor = os.getenv('EDITOR')
		if editor is None:
			editor = self.default_text_editor
		subprocess.Popen(['pkexec', editor, filename])

	def open_path(self, widget, path):
		subprocess.Popen(['xdg-open', path])

	def open_url(self, widget, url):
		webbrowser.open(url)

	def launch_control_panel(self, widget):
		subprocess.Popen(['pkexec', self.control_panel_bin])

	def start_stop_xampp(self, widget):
		# Disable Widget
		widget.set_sensitive(False)
		# Change Widget Label
		label = widget.get_label()
		widget.set_label(label + '...')
		# Start or Stop Xampp
		if self.default_service in self.status and self.status[self.default_service] == ServiceStatus.On:
			self.stop_service()
		else:
			self.start_service()
		# Update Status after 10 seconds
		GLib.timeout_add_seconds(10, self.update_status, widget)

	def restart_xampp(self, widget):
		# Disable Widget
		widget.set_sensitive(False)
		# Set Indicator Icon 'Off'
		self.set_icon('xampp-dark.svg')
		# Change Widget Label
		label = widget.get_label()
		widget.set_label(label + '...')
		# Restart Xampp
		self.restart_service()
		# Update Status after 10 seconds
		GLib.timeout_add_seconds(10, self.update_status, widget, label)

	def toggle_service(self, widget, service):
		if widget.get_sensitive():
			# Change Widget Label
			label = widget.get_label()
			widget.set_label(label + '...')
			# Disable Widget
			widget.set_sensitive(False)
			# Toggle Service
			if self.status[service] == ServiceStatus.On:
				self.stop_service(self.services[service]['name'])
			else:
				self.start_service(self.services[service]['name'])
			# Update Status after 10 seconds
			GLib.timeout_add_seconds(10, self.update_status, widget, label, service)

	def update_status(self, widget, widget_label = None, service = None):
		# Update Xampp Status
		self.status = self.get_xampp_status()
		if service is not None:
			# Update Widget
			if self.services[service]['status_key'] in self.status and self.status[self.services[service]['status_key']] == ServiceStatus.On:
				widget.set_active(True)
			else:
				widget.set_active(False)
		else:
			# Update All Service Menu Items
			for service in self.services:
				service_menu_item = self.serviceMenuItems[service]
				was_sensitive = service_menu_item.get_sensitive()
				if was_sensitive:
					service_menu_item.set_sensitive(False)
				if self.services[service]['status_key'] in self.status and self.status[self.services[service]['status_key']] == ServiceStatus.On:
					service_menu_item.set_active(True)
				else:
					service_menu_item.set_active(False)
				if was_sensitive:
					service_menu_item.set_sensitive(True)
		# Change Widget Label
		if widget_label is not None:
			widget.set_label(widget_label)
		# Change Start/Stop Menu Item Label
		if self.default_service in self.status and self.status[self.default_service] == ServiceStatus.On:
			self.startStopItem.set_label('Stop')
		else:
			self.startStopItem.set_label('Start')
		# Enable Widget
		widget.set_sensitive(True)
		# Set Indicator Icon
		self.set_icon()

		return False # Do not loop

	def start_service(self, service_name = ''):
		subprocess.Popen(['pkexec', self.xampp_bin, 'start' + service_name])

	def stop_service(self, service_name = ''):
		subprocess.Popen(['pkexec', self.xampp_bin, 'stop' + service_name])

	def restart_service(self, service_name = ''):
		subprocess.Popen(['pkexec', self.xampp_bin, 'reload' + service_name])

	def set_icon(self, icon_name = None):
		if icon_name is None:
			icon_name = 'xampp-dark.svg'
			if self.default_service in self.status and self.status[self.default_service] == ServiceStatus.On:
				icon_name = 'xampp.svg'
		icon = os.path.dirname(os.path.realpath(__file__)) + '/icons/' + icon_name
		if os.path.exists(icon):
			self.indicator.set_icon(icon)
		else:
			print('ERROR: Cannot find icon %s' % icon)

	def about(self, widget):
		about_dialog = Gtk.AboutDialog()
		about_dialog.set_position(Gtk.WindowPosition.CENTER)
		logo = GdkPixbuf.Pixbuf.new_from_file(os.path.dirname(os.path.realpath(__file__)) + '/icons/xampp.svg')
		about_dialog.set_logo(logo)
		about_dialog.set_program_name('Xampp Indicator')
		about_dialog.set_version('1.0')
		about_dialog.set_comments('A simple AppIndicator for XAMPP on Linux')
		about_dialog.set_website('https://github.com/AXeL-dev/xampp-indicator')
		about_dialog.set_website_label('GitHub')
		about_dialog.set_copyright('Copyright © 2019 AXeL-dev')
		about_dialog.set_authors(['AXeL-dev <contact.axel.dev@gmail.com> (Developer)'])
		about_dialog.set_license('''Xampp Indicator, A simple AppIndicator for XAMPP on Linux.
Copyright © 2019 AXeL-dev

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.''')
		about_dialog.run()
		about_dialog.destroy()

	def quit(self, widget):
		Gtk.main_quit()

	def main(self):
		Gtk.main()

if __name__ == '__main__':
	indicator = XamppIndicator()
	indicator.main()
