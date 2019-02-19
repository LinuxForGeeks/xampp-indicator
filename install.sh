#!/bin/bash

if [ "$(id -u)" != "0" ]; then
echo “This script must be run as root” 2>&1
exit 1
fi

sh uninstall.sh

mkdir /usr/share/xampp-indicator
cp -R icons /usr/share/xampp-indicator/
cp -R *.policy /usr/share/polkit-1/actions/

cp *.py /usr/share/xampp-indicator/
chmod 755 -R /usr/share/xampp-indicator/

cp xampp-indicator.desktop /etc/xdg/autostart/
chmod 755 /etc/xdg/autostart/xampp-indicator.desktop

cp xampp-indicator.desktop /usr/share/applications/
chmod 755 /usr/share/applications/xampp-indicator.desktop

ln -s /usr/share/xampp-indicator/xampp-indicator.py /usr/local/bin/xampp-indicator
chmod 755 /usr/local/bin/xampp-indicator
