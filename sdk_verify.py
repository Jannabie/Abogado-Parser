#!/usr/bin/env python3
"""
SDK Verify - Tool untuk verifikasi file .SDK/.DSK dan .PFT
Berguna untuk debug ketika repack menghasilkan error
"""

import struct
import sys
import hashlib
from pathlib import Path


def analyze_pft(pft_path: str):
    """Analisis file .PFT"""
    print(f"\n{'='*60}")
    print(f"Analyzing: {pft_path}")
    print(f"{'='*60}")
    
    with open(pft_path, 'rb') as f:
        data = f.read()
    
    print(f"File size: {len(data)} bytes")
    
    # Parse header
    header = struct.unpack('<IIHH4x', data[0:16])
    print(f"\nHeader:")
    print(f"  Field 1: 0x{header[0]:08x}")
    print(f"  Field 2: {header[1]} (0x{header[1]:08x})")
    print(f"  Field 3: {header[2]} (0x{header[2]:04x})")
    print(f"  Field 4: {header[3]} (0x{header[3]:04x})")
    
    # Parse entries
    offset = 16
    entries = []
    while offset < len(data) and offset + 16 <= len(data):
        name = data[offset:offset+8].decode('ascii', errors='ignore').rstrip('\x00')
        if not name:
            break
        
        idx = struct.unpack('<I', data[offset+8:offset+12])[0]
        size = struct.unpack('<I', data[offset+12:offset+16])[0]
        
        entries.append((name, idx, size))
        offset += 16
    
    print(f"\nEntries: {len(entries)}")
    print(f"\n{'Name':<10} {'Index':<8} {'Size':<10} {'Cumulative':<12} {'Hex Size'}")
    print("-" * 62)
    
    cumulative = 0
    for name, idx, size in entries:
        print(f"{name:<10} {idx:<8} {size:<10} {cumulative:<12} 0x{size:08x}")
        cumulative += size
    
    print(f"\nTotal expected archive size: {cumulative} bytes (0x{cumulative:08x})")
    
    return entries, cumulative


def analyze_archive(archive_path: str):
    """Analisis file archive .DSK/.SDK"""
    print(f"\n{'='*60}")
    print(f"Analyzing: {archive_path}")
    print(f"{'='*60}")
    
    with open(archive_path, 'rb') as f:
        data = f.read()
    
    print(f"File size: {len(data)} bytes (0x{len(data):08x})")
    
    # Hitung hash
    md5 = hashlib.md5(data).hexdigest()
    print(f"MD5: {md5}")
    
    # Tampilkan header
    print(f"\nFirst 256 bytes:")
    for i in range(0, min(len(data), 256), 16):
        hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"{i:08x}: {hex_str:<48} {ascii_str}")
    
    return data


def verify_integrity(pft_path: str, archive_path: str):
    """Verifikasi integritas antara .PFT dan archive"""
    print(f"\n{'='*60}")
    print(f"Integrity Check")
    print(f"{'='*60}")
    
    entries, expected_size = analyze_pft(pft_path)
    archive_data = analyze_archive(archive_path)
    
    actual_size = len(archive_data)
    
    print(f"\n{'='*60}")
    print(f"Comparison")
    print(f"{'='*60}")
    print(f"Expected archive size (from .PFT): {expected_size} bytes")
    print(f"Actual archive size:                {actual_size} bytes")
    
    if expected_size == actual_size:
        print(f"✓ Size match!")
    else:
        diff = actual_size - expected_size
        print(f"✗ Size mismatch! Difference: {diff:+d} bytes")
        
        if diff > 0:
            print(f"  Archive is {abs(diff)} bytes LARGER than expected")
        else:
            print(f"  Archive is {abs(diff)} bytes SMALLER than expected")
    
    # Verifikasi setiap entry bisa di-extract
    print(f"\n{'='*60}")
    print(f"Entry Verification")
    print(f"{'='*60}")
    
    offset = 0
    errors = 0
    
    for name, idx, size in entries:
        if offset + size > actual_size:
            print(f"✗ {name}: OUT OF RANGE (offset={offset}, size={size})")
            errors += 1
        else:
            # Extract dan verifikasi
            chunk = archive_data[offset:offset+size]
            print(f"✓ {name}: OK (offset=0x{offset:08x}, size={size})")
        
        offset += size
    
    print(f"\n{'='*60}")
    print(f"Summary")
    print(f"{'='*60}")
    print(f"Total entries: {len(entries)}")
    print(f"Errors: {errors}")
    
    if errors == 0 and expected_size == actual_size:
        print(f"\n✓ All checks passed! Files are valid.")
        return True
    else:
        print(f"\n✗ Verification failed!")
        return False


def compare_archives(original_archive: str, new_archive: str, original_pft: str = None, new_pft: str = None):
    """Bandingkan dua archive"""
    print(f"\n{'='*60}")
    print(f"Comparing Archives")
    print(f"{'='*60}")
    
    with open(original_archive, 'rb') as f:
        orig_data = f.read()
    
    with open(new_archive, 'rb') as f:
        new_data = f.read()
    
    print(f"Original: {len(orig_data)} bytes")
    print(f"New:      {len(new_data)} bytes")
    print(f"Diff:     {len(new_data) - len(orig_data):+d} bytes")
    
    # MD5 comparison
    orig_md5 = hashlib.md5(orig_data).hexdigest()
    new_md5 = hashlib.md5(new_data).hexdigest()
    
    print(f"\nOriginal MD5: {orig_md5}")
    print(f"New MD5:      {new_md5}")
    
    if orig_md5 == new_md5:
        print(f"✓ Files are identical!")
    else:
        print(f"✗ Files are different")
        
        # Find first difference
        for i, (a, b) in enumerate(zip(orig_data, new_data)):
            if a != b:
                print(f"\nFirst difference at offset 0x{i:08x}:")
                print(f"  Original: 0x{a:02x}")
                print(f"  New:      0x{b:02x}")
                
                # Show context
                start = max(0, i - 16)
                end = min(len(orig_data), i + 16)
                
                print(f"\n  Context (original):")
                print(f"    {orig_data[start:end].hex()}")
                print(f"\n  Context (new):")
                print(f"    {new_data[start:end].hex()}")
                break
    
    # Compare PFT if provided
    if original_pft and new_pft:
        print(f"\n{'='*60}")
        print(f"Comparing PFT Files")
        print(f"{'='*60}")
        
        orig_entries, _ = analyze_pft(original_pft)
        new_entries, _ = analyze_pft(new_pft)
        
        if len(orig_entries) != len(new_entries):
            print(f"✗ Entry count mismatch: {len(orig_entries)} vs {len(new_entries)}")
        else:
            print(f"✓ Entry count: {len(orig_entries)}")
            
            diff_count = 0
            for i, ((oname, oidx, osize), (nname, nidx, nsize)) in enumerate(zip(orig_entries, new_entries)):
                if oname != nname or oidx != nidx or osize != nsize:
                    print(f"\n  Entry {i} differs:")
                    print(f"    Original: {oname:<10} idx={oidx:<8} size={osize}")
                    print(f"    New:      {nname:<10} idx={nidx:<8} size={nsize}")
                    diff_count += 1
            
            if diff_count == 0:
                print(f"✓ All entries match!")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='SDK Verify - Verifikasi dan analisis file SDK',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # Analyze PFT
    pft_parser = subparsers.add_parser('pft', help='Analisis file .PFT')
    pft_parser.add_argument('file', help='Path ke file .PFT')
    
    # Analyze archive
    archive_parser = subparsers.add_parser('archive', help='Analisis file archive')
    archive_parser.add_argument('file', help='Path ke file .DSK/.SDK')
    
    # Verify integrity
    verify_parser = subparsers.add_parser('verify', help='Verifikasi integritas')
    verify_parser.add_argument('pft', help='Path ke file .PFT')
    verify_parser.add_argument('archive', help='Path ke file .DSK/.SDK')
    
    # Compare archives
    compare_parser = subparsers.add_parser('compare', help='Bandingkan dua archive')
    compare_parser.add_argument('original_archive', help='Archive original')
    compare_parser.add_argument('new_archive', help='Archive baru')
    compare_parser.add_argument('--original-pft', help='PFT original (optional)')
    compare_parser.add_argument('--new-pft', help='PFT baru (optional)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'pft':
            analyze_pft(args.file)
            
        elif args.command == 'archive':
            analyze_archive(args.file)
            
        elif args.command == 'verify':
            result = verify_integrity(args.pft, args.archive)
            return 0 if result else 1
            
        elif args.command == 'compare':
            compare_archives(
                args.original_archive,
                args.new_archive,
                args.original_pft,
                args.new_pft
            )
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
