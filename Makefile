# Makeile to configure weewx with provided schema and driver
#
# Author: McKay Humpherys
# Date: 11/10/2022
#

weewx_user_path = /usr/share/weewx/user/
weewx_conf_path = /etc/weewx/weewx.conf
backup_path = ./pi-config/

backup: 
	@echo "Backing up weewx.conf"
	sudo cp $(weewx_conf_path) $(backup_path)
	@echo "Backing up /boot/config.conf"
	sudo cp /boot/config.txt $(backup_path)

driver: svws.py
	@echo "Copying $< to $(weewx_user_path)"
	sudo cp $< $(weewx_user_path)

schema: svws_schema.py
	@echo "Copying $< to $(weewx_user_path)"
	sudo cp $< $(weewx_user_path)

conf: ./weewx-config/weewx.conf
	@echo "Copying $< to $(weewx_conf_path)"
	sudo cp $< $(weewx_conf_path)