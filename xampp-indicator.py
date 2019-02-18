#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Xampp Indicator
#
# Copyright (c) 2018 - 2019 AXeL

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, GLib, AppIndicator3 as AI
import os, sys, subprocess

class ServiceStatus:
	On, Off, Disabled = ("RUNNING", "NOTRUNNING", "DEACTIVATED")

class XamppIndicator():
	def __init__(self):
		# Setup Indicator Applet
		self.indicator = AI.Indicator.new("xampp-indicator", "xampp", AI.IndicatorCategory.APPLICATION_STATUS)
		self.indicator.set_status(AI.IndicatorStatus.ACTIVE)
		self.indicator.set_icon(self.get_icon())

		# Set Attributes
		xampp_path = "/opt/lampp"
		self.xampp_bin = os.path.join(xampp_path, "lampp")
		self.control_panel_bin = os.path.join(xampp_path, "manager-linux-x64.run")
		if not os.path.exists(self.control_panel_bin):
			self.control_panel_bin = os.path.join(xampp_path, "manager-linux.run")
		self.services = {
			"APACHE": "apache",
			"MYSQL": "mysql",
			"PROFTPD": "ftp"
		}

		# Get Xampp Status
		self.status = self.get_xampp_status()

		# Setup The Menu
		self.menu = Gtk.Menu()

		# Menu Item: Apache
		service_name = "APACHE"
		self.apacheItem = Gtk.CheckMenuItem("Apache")
		if service_name in self.status and self.status[service_name] == ServiceStatus.On:
			self.apacheItem.set_active(True)
		self.apacheItem.connect("activate", self.toggle_service, service_name)
		self.menu.append(self.apacheItem)

		# Menu Item: MySQL
		service_name = "MYSQL"
		self.mySqlItem = Gtk.CheckMenuItem("MySQL")
		if service_name in self.status and self.status[service_name] == ServiceStatus.On:
			self.mySqlItem.set_active(True)
		self.mySqlItem.connect("activate", self.toggle_service, service_name)
		self.menu.append(self.mySqlItem)

		# Menu Item: FTP
		service_name = "PROFTPD"
		self.mySqlItem = Gtk.CheckMenuItem("FTP")
		if service_name in self.status and self.status[service_name] == ServiceStatus.On:
			self.mySqlItem.set_active(True)
		self.mySqlItem.connect("activate", self.toggle_service, service_name)
		self.menu.append(self.mySqlItem)
		self.menu.append(Gtk.SeparatorMenuItem())

		# Menu Item: Control Panel
		controlPanelItem = Gtk.MenuItem("Control Panel")
		controlPanelItem.connect("activate", self.launch_control_panel)
		self.menu.append(controlPanelItem)
		self.menu.append(Gtk.SeparatorMenuItem())

		# Menu Item: Quit
		exitItem = Gtk.MenuItem("Quit")
		exitItem.connect("activate", self.quit)
		self.menu.append(exitItem)

		# Show All Menu Items
		self.menu.show_all()

		# Assign Menu To Indicator
		self.indicator.set_menu(self.menu)

	def get_xampp_status(self):
		print("--- Get XAMPP Status ---")
		raw_status = subprocess.getoutput("echo n | " + self.xampp_bin + " statusraw")
		status = {}
		for service in self.services:
			status[service] = ""
		lines = raw_status.split("\n")
		for line in lines[1:]: # Ignore first line
			service = line.split(" ")
			if service[0] in status:
				status[service[0]] = service[1]
		for service in status:
			print("%s %s" % (service, status[service]))
		print("-" * 24)

		return status

	def launch_control_panel(self, widget):
		subprocess.Popen(["pkexec", self.control_panel_bin])

	def toggle_service(self, widget, service_name):
		if widget.get_sensitive():
			# Change Widget Label
			label = widget.get_label()
			widget.set_label(label + "...")
			# Disable Widget
			widget.set_sensitive(False)
			# Toggle Service
			if self.status[service_name] == ServiceStatus.On:
				self.stop_service(self.services[service_name])
			else:
				self.start_service(self.services[service_name])
			# Update Status after 10 seconds
			GLib.timeout_add_seconds(10, self.update_status, widget, service_name)

	def update_status(self, widget, service_name):
		# Update Xampp Status
		self.status = self.get_xampp_status()
		if service_name in self.status and self.status[service_name] == ServiceStatus.On:
			widget.set_active(True)
		else:
			widget.set_active(False)
		# Change Widget Label
		label = widget.get_label().replace("...", "")
		widget.set_label(label)
		# Enable Widget
		widget.set_sensitive(True)

		return False # Do not loop

	def start_service(self, service):
		p = subprocess.Popen(["pkexec", self.xampp_bin, "start" + service])

	def stop_service(self, service):
		p = subprocess.Popen(["pkexec", self.xampp_bin, "stop" + service])

	def get_icon(self):
		# Get Icon
		icon = os.path.dirname(os.path.realpath(__file__)) + "/xampp.svg"
		if os.path.exists(icon):
			return icon
		else:
			print("ERROR: Cannot find icon : %s" % icon)
			sys.exit(1)

	def quit(self, widget):
		Gtk.main_quit()

	def main(self):
		Gtk.main()

if __name__ == "__main__":
	indicator = XamppIndicator()
	indicator.main()
