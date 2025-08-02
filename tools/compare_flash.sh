#!/bin/bash
echo "=== Flash dump (first 64 bytes) ==="
hexdump -C flash_start.bin | head -4

echo -e "\n=== Built binary (first 64 bytes) ==="
hexdump -C build/zephyr/zephyr.bin | head -4

echo -e "\n=== Looking for custom banner in flash dump ==="
strings flash_start.bin | grep -i "custom\|mcuboot\|xiao"

echo -e "\n=== Looking for custom banner in built binary ==="
strings build/zephyr/zephyr.bin | grep -i "custom\|mcuboot\|xiao"
