#!/bin/bash
west build -b xiao_ble $PWD/../bootloader/mcuboot/boot/zephyr -t menuconfig -- -DDTC_OVERLAY_FILE=$PWD/boards/xiao_ble.overlay -DCONF_FILE=$PWD/boot.conf 
