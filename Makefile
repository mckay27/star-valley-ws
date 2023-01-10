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
	@echo "Available commands are: backup, driver, schema, conf, and skin"
	@echo "    backup copies files to ./piconfig/"
	@echo "    driver copies the svws.py driver to the weewx user directory"
	@echo "    schema copies the svws_schema.py scheam to the weewx user directory"
	@echo "    conf copies the weewx.conf to the appropriate directory"
	@echo "    graphs copies the graphs.conf file to the appropriate belchertown directory"

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

graphs: ./pi-config/graphs.conf
	@echo "Copying $< to $(belchertown_conf_path)"
	sudo chown root:root $<
	sudo cp $< $(belchertown_conf_path)
	sudo chown brian:brian $<

belchertown: ./pi-config/belchertown.py
	@echo "Copying $< to $(weewx_user_path)"
	sudo chown root:root $<
	sudo cp $< $(weewx_user_path)
	sudo chown brian:brian $<