#!/bin/bash
echo "Setting up for Seeed Xiao BLE board programming using OpenOCD and"
echo "Raspberry Pi Debug probe."
cp -r support ../zephyr/boards/seeed/xiao_ble/.
west flash --runner openocd
