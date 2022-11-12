# Makeile to configure weewx with provided schema and driver
#
# Author: McKay Humpherys
# Date: 11/10/2022
#

weewx_user_path = /usr/share/weewx/user/
weewx_conf_path = /etc/weewx
belchertown_conf_path = $(weewx_conf_path)/skins/Belchertown
backup_path = ./pi-config

help:
	@echo "Available commands are: backup, driver, schema, and conf"

backup: 
	@echo "Backing up weewx.conf"
	sudo cp $(weewx_conf_path)/weewx.conf $(backup_path)
	sudo chown brian:brian $(backup_path)/weewx.conf
	@echo "Backing up /boot/config.conf"
	sudo cp /boot/config.txt $(backup_path)
	@echo "Backing up graphs.conf"
	sudo cp $(belchertown_conf_path)/graphs.conf $(backup_path)
	sudo chown brian:brian $(backup_path)/graphs.conf

driver: svws.py
	@echo "Copying $< to $(weewx_user_path)"
	sudo cp $< $(weewx_user_path)

schema: svws_schema.py
	@echo "Copying $< to $(weewx_user_path)"
	sudo cp $< $(weewx_user_path)

conf: ./pi-config/weewx.conf
	@echo "Copying $< to $(weewx_conf_path)"
	sudo chown root:root $<
	sudo cp $< $(weewx_conf_path)
	sudo chown brian:brian $<

skin: ./pi-config/graphs.conf
	@echo "Copying $< to $(belchertown_conf_path)"
	sudo chown root:root $<
	sudo cp $< $(belchertown_conf_path)
	sudo chown brian:brian $<