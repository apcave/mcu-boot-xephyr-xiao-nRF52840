openocd -f interface/cmsis-dap.cfg -f target/nrf52.cfg -c "init; dump_image flash_start.bin 0x0000 0x1000; exit"
hexdump -C flash_start.bin | head