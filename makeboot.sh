#!/bin/bash
west build -p -b xiao_ble --no-sysbuild -s $PWD/../bootloader/mcuboot/boot/zephyr -- -DDTC_OVERLAY_FILE=$PWD/boards/xiao_ble.overlay -DCONF_FILE=$PWD/boot.conf
