#!/usr/bin/env python3
"""
Flash Footprint Analyzer
Analyzes build output to determine MCUboot and application flash usage.
"""

import os
import re
import subprocess
from pathlib import Path

def get_elf_size(elf_path):
    """Get size information from ELF file using objdump or size command."""
    if not os.path.exists(elf_path):
        return None
    
    try:
        # Use arm-none-eabi-size if available, otherwise try size
        size_cmd = ["arm-none-eabi-size", str(elf_path)]
        try:
            result = subprocess.run(size_cmd, capture_output=True, text=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to regular size command
            size_cmd = ["size", str(elf_path)]
            result = subprocess.run(size_cmd, capture_output=True, text=True, check=True)
        
        # Parse the output - format is typically:
        # text    data     bss     dec     hex filename
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 2:
            size_line = lines[1].split()
            text_size = int(size_line[0])
            data_size = int(size_line[1])
            bss_size = int(size_line[2])
            
            # Flash usage = text + data (bss is in RAM)
            flash_usage = text_size + data_size
            
            return {
                'text': text_size,
                'data': data_size,
                'bss': bss_size,
                'flash_total': flash_usage,
                'ram_total': data_size + bss_size
            }
    except Exception as e:
        print(f"Error analyzing {elf_path}: {e}")
        return None

def get_hex_size(hex_path):
    """Get size from Intel HEX file."""
    if not os.path.exists(hex_path):
        return None
    
    try:
        with open(hex_path, 'r') as f:
            total_bytes = 0
            for line in f:
                line = line.strip()
                if line.startswith(':') and len(line) >= 11:
                    # Intel HEX format: :LLAAAATT[DD...]CC
                    byte_count = int(line[1:3], 16)
                    record_type = int(line[7:9], 16)
                    if record_type == 0x00:  # Data record
                        total_bytes += byte_count
            return total_bytes
    except Exception as e:
        print(f"Error reading HEX file {hex_path}: {e}")
        return None

def analyze_partition_usage():
    """Analyze partition usage from pm_static.yml."""
    pm_static_path = Path("pm_static.yml")
    if not pm_static_path.exists():
        return None
    
    partitions = {}
    try:
        with open(pm_static_path, 'r') as f:
            current_partition = None
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if ':' in line and not line.startswith(' '):
                        current_partition = line.rstrip(':')
                        partitions[current_partition] = {}
                    elif current_partition and ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        if key in ['size', 'address', 'end_address']:
                            partitions[current_partition][key] = int(value, 16)
    except Exception as e:
        print(f"Error reading pm_static.yml: {e}")
        return None
    
    return partitions

def main():
    print("Flash Footprint Analysis")
    print("=" * 60)
    
    # Define build paths
    build_dir = Path("build")
    mcuboot_elf = build_dir / "mcuboot" / "zephyr" / "zephyr.elf"
    app_elf = build_dir / "zephyr" / "zephyr.elf"
    mcuboot_hex = build_dir / "mcuboot" / "zephyr" / "zephyr.hex"
    app_hex = build_dir / "zephyr" / "zephyr.hex"
    
    # Analyze MCUboot
    print("\nMCUboot Bootloader:")
    print("-" * 30)
    mcuboot_size = get_elf_size(mcuboot_elf)
    if mcuboot_size:
        print(f"Text (code):     {mcuboot_size['text']:8,} bytes ({mcuboot_size['text']:6.1f} KB)")
        print(f"Data (init):     {mcuboot_size['data']:8,} bytes ({mcuboot_size['data']:6.1f} KB)")
        print(f"BSS (uninit):    {mcuboot_size['bss']:8,} bytes ({mcuboot_size['bss']:6.1f} KB)")
        print(f"Flash usage:     {mcuboot_size['flash_total']:8,} bytes ({mcuboot_size['flash_total']:6.1f} KB)")
        print(f"RAM usage:       {mcuboot_size['ram_total']:8,} bytes ({mcuboot_size['ram_total']:6.1f} KB)")
    else:
        # Try HEX file
        hex_size = get_hex_size(mcuboot_hex)
        if hex_size:
            print(f"Flash usage:     {hex_size:8,} bytes ({hex_size/1024:6.1f} KB)")
        else:
            print("MCUboot size information not available")
    
    # Analyze Application
    print("\nMain Application:")
    print("-" * 30)
    app_size = get_elf_size(app_elf)
    if app_size:
        print(f"Text (code):     {app_size['text']:8,} bytes ({app_size['text']:6.1f} KB)")
        print(f"Data (init):     {app_size['data']:8,} bytes ({app_size['data']:6.1f} KB)")
        print(f"BSS (uninit):    {app_size['bss']:8,} bytes ({app_size['bss']:6.1f} KB)")
        print(f"Flash usage:     {app_size['flash_total']:8,} bytes ({app_size['flash_total']:6.1f} KB)")
        print(f"RAM usage:       {app_size['ram_total']:8,} bytes ({app_size['ram_total']:6.1f} KB)")
    else:
        # Try HEX file
        hex_size = get_hex_size(app_hex)
        if hex_size:
            print(f"Flash usage:     {hex_size:8,} bytes ({hex_size/1024:6.1f} KB)")
        else:
            print("Application size information not available")
    
    # Analyze partition usage
    print("\nPartition Usage:")
    print("-" * 30)
    partitions = analyze_partition_usage()
    if partitions:
        for name, info in partitions.items():
            if 'size' in info:
                size_bytes = info['size']
                size_kb = size_bytes / 1024
                print(f"{name:<15}: {size_bytes:8,} bytes ({size_kb:6.1f} KB)")
                
                # Show usage percentage for MCUboot and slot0
                if name == 'mcuboot' and mcuboot_size:
                    usage_pct = (mcuboot_size['flash_total'] / size_bytes) * 100
                    print(f"{'':15}  Usage: {usage_pct:5.1f}%")
                elif name == 'slot0' and app_size:
                    usage_pct = (app_size['flash_total'] / size_bytes) * 100
                    print(f"{'':15}  Usage: {usage_pct:5.1f}%")
    
    # Summary
    print("\nSummary:")
    print("-" * 30)
    total_flash = 1024 * 1024  # 1MB
    if mcuboot_size and app_size:
        total_used = mcuboot_size['flash_total'] + app_size['flash_total']
        remaining = total_flash - total_used
        print(f"Total flash:     {total_flash:8,} bytes ({total_flash/1024:6.1f} KB)")
        print(f"Used by code:    {total_used:8,} bytes ({total_used/1024:6.1f} KB)")
        print(f"Available:       {remaining:8,} bytes ({remaining/1024:6.1f} KB)")
        print(f"Usage:           {(total_used/total_flash)*100:5.1f}%")

if __name__ == "__main__":
    main()