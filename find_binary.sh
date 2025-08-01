#!/bin/bash
echo "=== Searching for binary patterns in flash ==="
echo "Flash size: $(stat -c%s complete_flash.bin) bytes"
echo ""

echo "=== ARM Vector Table candidates (stack pointer in RAM) ==="
hexdump -C complete_flash.bin | grep -E "00 00 00 20|00 10 00 20|00 20 00 20"

echo ""
echo "=== String search results ==="
strings -t x complete_flash.bin | grep -i -E "mcuboot|custom|xiao|boot"

echo ""
echo "=== Looking for code sections (non-FF patterns) ==="
hexdump -C complete_flash.bin | grep -v "ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff" | head -20
