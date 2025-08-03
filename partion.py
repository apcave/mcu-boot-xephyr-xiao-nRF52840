#!/usr/bin/env python3
"""
Partition Layout Calculator
Calculates partition addresses based on sizes and prints layout in hex format.
Also updates pm_static.yml and app.overlay files automatically.
"""

import os
from pathlib import Path

def calculate_partitions(flash_size, partitions):
    """
    Calculate partition layout given flash size and partition definitions.
    
    Args:
        flash_size: Total flash size in bytes
        partitions: List of tuples (name, size_in_bytes)
    
    Returns:
        List of dictionaries with partition info
    """
    current_address = 0
    partition_layout = []
    
    for name, size in partitions:
        if current_address + size > flash_size:
            raise ValueError(f"Partition '{name}' exceeds flash size!")
        
        partition_info = {
            'name': name,
            'start': current_address,
            'end': current_address + size,
            'size': size
        }
        partition_layout.append(partition_info)
        current_address += size
    
    return partition_layout

def print_partition_layout(partitions, flash_size):
    """Print partition layout in hex format."""
    print(f"Flash Size: {flash_size:#x} ({flash_size} bytes)")
    print("-" * 70)
    print(f"{'Partition':<20} {'Start':<12} {'End':<12} {'Size':<12} {'Size (KB)':<10}")
    print("-" * 70)
    
    for partition in partitions:
        size_kb = partition['size'] // 1024
        print(f"{partition['name']:<20} {partition['start']:#010x}   {partition['end']:#010x}   {partition['size']:#010x}   {size_kb}KB")
    
    # Check if we used all flash
    total_used = sum(p['size'] for p in partitions)
    remaining = flash_size - total_used
    if remaining > 0:
        print("-" * 70)
        print(f"{'UNUSED':<20} {total_used:#010x}   {flash_size:#010x}   {remaining:#010x}   {remaining//1024}KB")

def get_pm_static_name(partition_name):
    """Map partition names to Nordic Partition Manager naming conventions."""
    name_mapping = {
        'mcuboot': 'mcuboot',
        'slot0': 'mcuboot_primary',
        'slot1': 'mcuboot_secondary', 
        'scratch': 'mcuboot_scratch',
        'storage': 'settings_storage'
    }
    return name_mapping.get(partition_name, partition_name)

def get_overlay_label(partition_name):
    """Map partition names to overlay file labels."""
    label_mapping = {
        'mcuboot': 'mcuboot',
        'slot0': 'image-0',  # Standard MCUboot label for primary slot
        'slot1': 'image-1',  # Standard MCUboot label for secondary slot
        'scratch': 'image-scratch',
        'storage': 'storage'
    }
    return label_mapping.get(partition_name, partition_name)

def update_pm_static_yml(partitions):
    """Update pm_static.yml file with calculated partitions using Nordic PM naming."""
    pm_static_content = "# Auto-generated pm_static.yml from partion.py\n"
    pm_static_content += "# Nordic Partition Manager static configuration\n\n"
    
    for partition in partitions:
        pm_name = get_pm_static_name(partition['name'])
        pm_static_content += f"{pm_name}:\n"
        pm_static_content += f"  address: {partition['start']:#x}\n"
        pm_static_content += f"  end_address: {partition['end']:#x}\n"
        pm_static_content += f"  region: flash_primary\n"
        pm_static_content += f"  size: {partition['size']:#x}\n\n"
    
    # Write to pm_static.yml
    with open("pm_static.yml", "w") as f:
        f.write(pm_static_content)
    
    print(f"✓ Updated pm_static.yml")

def update_app_overlay(partitions):
    """Update app.overlay file with calculated partitions using devicetree labels."""
    
    # Create devicetree overlay content
    overlay_content = "// Auto-generated app.overlay from partion.py\n"
    overlay_content += "// Device tree overlay for partition configuration\n\n"
    
    overlay_content += "/ {\n"
    overlay_content += "\tchosen {\n"
    overlay_content += "\t\tzephyr,code-partition = &slot0_partition;\n"
    overlay_content += "\t};\n"
    overlay_content += "};\n\n"
    
    overlay_content += "&flash0 {\n"
    overlay_content += "\tpartitions {\n"
    overlay_content += "\t\tcompatible = \"fixed-partitions\";\n"
    overlay_content += "\t\t#address-cells = <1>;\n"
    overlay_content += "\t\t#size-cells = <1>;\n\n"
    
    # Add each partition
    for partition in partitions:
        # Use overlay label for devicetree
        overlay_label = get_overlay_label(partition['name'])
        partition_node_name = f"{partition['name']}_partition"
        
        overlay_content += f"\t\t{partition_node_name}: partition@{partition['start']:x} {{\n"
        overlay_content += f"\t\t\tlabel = \"{overlay_label}\";\n"
        overlay_content += f"\t\t\treg = <{partition['start']:#010x} {partition['size']:#010x}>;\n"
        
        # Add special properties for known partition types
        if partition['name'] == 'mcuboot':
            overlay_content += "\t\t\tread-only;\n"
        elif partition['name'] == 'slot0':
            overlay_content += "\t\t\t// Primary application slot\n"
        elif partition['name'] == 'slot1':
            overlay_content += "\t\t\t// Secondary application slot\n"
        elif partition['name'] == 'scratch':
            overlay_content += "\t\t\t// MCUboot scratch area\n"
        elif partition['name'] == 'storage':
            overlay_content += "\t\t\t// Settings storage\n"
        
        overlay_content += "\t\t};\n\n"
    
    overlay_content += "\t};\n"
    overlay_content += "};\n"
    
    # Write to app.overlay
    with open("app.overlay", "w") as f:
        f.write(overlay_content)
    
    print(f"✓ Updated app.overlay")

def create_backup_files():
    """Create backup copies of existing files."""
    files_to_backup = ["pm_static.yml", "app.overlay"]
    
    for filename in files_to_backup:
        if Path(filename).exists():
            backup_name = f"{filename}.backup"
            # Only create backup if it doesn't exist
            if not Path(backup_name).exists():
                os.rename(filename, backup_name)
                print(f"✓ Created backup: {backup_name}")

def main():
    # nRF52840 has 1MB (1024KB) of flash
    FLASH_SIZE = 1024 * 1024  # 1MB = 0x100000
    
    # Define partitions: (name, size_in_bytes)
    # Single slot configuration - remove slot1
    mcuboot = 110 * 1024      # 100KB MCUboot bootloader
    storage = 76 * 1024       # 76KB storage for settings
    scratch = 1 * 1024       # 1KB scratch area (optional, can be 0)
    
    # Single large application slot
    slot0_partition =(FLASH_SIZE - mcuboot - storage  - scratch) // 2
    slot1_partition = slot0_partition  # For single slot, both slots are the same size

    
    partitions = [
        ("mcuboot", mcuboot),  
        ("slot0", slot0_partition),    # Single large slot
        ("slot1", slot1_partition),    # Single large slot
        ("scratch", scratch),                # No scratch needed for single slot
        ("storage", storage),   
    ]
    
    try:
        # Create backups of existing files
        print("Creating backups of existing files...")
        create_backup_files()
        print()
        
        # Calculate partition layout
        layout = calculate_partitions(FLASH_SIZE, partitions)
        
        # Print the layout
        print("Single Slot MCUboot Partition Layout for nRF52840")
        print("=" * 70)
        print_partition_layout(layout, FLASH_SIZE)
        print()
        
        # Update configuration files
        print("Updating configuration files...")
        update_pm_static_yml(layout)
        update_app_overlay(layout)
        print()
        
        print("✓ All files updated successfully!")
        print("✓ Single slot configuration with 892KB for application")
        print("✓ You can now run: ./makeboot.sh")
        print()
        print("To restore original files if needed:")
        print("  mv pm_static.yml.backup pm_static.yml")
        print("  mv app.overlay.backup app.overlay")
        
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()