#!/bin/bash
# Sysbuild with overlay file - specify the overlay for main application
#west build -p -b xiao_ble --sysbuild -s . -- -DDTC_OVERLAY_FILE=$PWD/app.overlay

#rm -r build
#west -v build -b xiao_ble --sysbuild -- -DDTC_OVERLAY_FILE=$(realpath app.overlay)
#west -v build -b xiao_ble --sysbuild


rm -r build
west -v build -b xiao_ble --sysbuild -- \
  -DCONFIG_SIZE_OPTIMIZATIONS=y \
  -DCONFIG_COMPILER_OPT="\"-Os\"" \
  -DCONFIG_DEBUG=n \
  -DCONFIG_DEBUG_INFO=n