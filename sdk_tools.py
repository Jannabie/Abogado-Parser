#!/usr/bin/env python3
"""
SDK Tools - Unpack/Repack Visual Novel Script Files
Untuk modding visual novel yang menggunakan format .SDK

Format file:
- .PFT: Tabel indeks scene (nama scene, index, size)
- .DSK: Archive yang berisi file .SCF (script)
- SCNDAT.TBL: Tabel data scene
"""

import struct
import os
import sys
from pathlib import Path
from typing import List, Tuple, Dict


class PFTParser:
    """Parser untuk file .PFT (Scene Index Table)"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.entries = []
        self.header = None
        
    def read(self) -> List[Tuple[str, int, int]]:
        """
        Membaca file .PFT dan mengembalikan list of (name, index, size)
        """
        with open(self.filepath, 'rb') as f:
            data = f.read()
            
        # Parse header (16 bytes)
        self.header = data[0:16]
        header_values = struct.unpack('<IIHH4x', data[0:16])
        
        # Parse entries (16 bytes per entry)
        offset = 16
        self.entries = []
        
        while offset < len(data):
            if offset + 16 > len(data):
                break
                
            # 8 bytes nama, 4 bytes index, 4 bytes size
            name_bytes = data[offset:offset+8]
            name = name_bytes.decode('ascii', errors='ignore').rstrip('\x00')
            
            if not name:
                break
                
            idx = struct.unpack('<I', data[offset+8:offset+12])[0]
            size = struct.unpack('<I', data[offset+12:offset+16])[0]
            
            self.entries.append((name, idx, size))
            offset += 16
            
        return self.entries
    
    def write(self, output_path: str, entries: List[Tuple[str, int, int]]):
        """
        Menulis file .PFT dengan entries baru
        entries: List of (name, index, size)
        """
        with open(output_path, 'wb') as f:
            # Tulis header (gunakan header yang sama atau buat baru)
            if self.header:
                # Update jumlah entry di header jika perlu
                header_data = bytearray(self.header)
                # Field kedua di header mungkin adalah count
                struct.pack_into('<I', header_data, 4, len(entries))
                f.write(header_data)
            else:
                # Buat header default
                header = struct.pack('<IIHH4x', 0x08000010, len(entries), 0, 0)
                f.write(header)
            
            # Tulis entries
            for name, idx, size in entries:
                # Nama 8 bytes (padding dengan null)
                name_bytes = name.encode('ascii')[:8].ljust(8, b'\x00')
                
                # Index dan size
                entry = name_bytes + struct.pack('<II', idx, size)
                f.write(entry)


class SDKArchive:
    """Handler untuk file .SDK/.DSK (Archive berisi .SCF files)"""
    
    # CRITICAL: DSK files use 2048-byte block alignment!
    BLOCK_SIZE = 2048  # 0x800
    
    def __init__(self, archive_path: str, index_path: str = None):
        self.archive_path = archive_path
        self.index_path = index_path or archive_path.replace('.DSK', '.PFT').replace('.SDK', '.PFT')
        self.pft = None
        
    def unpack(self, output_dir: str):
        """
        Extract semua .SCF files dari archive
        CRITICAL: Index field in PFT is the block number!
        Offset = index × BLOCK_SIZE
        """
        # Baca index file
        self.pft = PFTParser(self.index_path)
        entries = self.pft.read()
        
        print(f"[*] Membaca index: {self.index_path}")
        print(f"[*] Jumlah scene: {len(entries)}")
        print(f"[*] Block size: {self.BLOCK_SIZE} bytes")
        
        # Baca archive
        with open(self.archive_path, 'rb') as f:
            archive_data = f.read()
        
        print(f"[*] Ukuran archive: {len(archive_data)} bytes")
        
        # Buat output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract setiap entry
        # CRITICAL: offset = index × BLOCK_SIZE
        extracted = 0
        
        for name, idx, size in entries:
            # Calculate offset using the index field as block number
            offset = idx * self.BLOCK_SIZE
            
            # Extract data
            if offset + size <= len(archive_data):
                scf_data = archive_data[offset:offset+size]
                output_path = os.path.join(output_dir, f"{name}.SCF")
                
                with open(output_path, 'wb') as f:
                    f.write(scf_data)
                
                extracted += 1
                print(f"[+] Extracted: {name}.SCF (block={idx}, offset=0x{offset:08x}, size={size} bytes)")
            else:
                print(f"[!] Error: {name} offset out of range (block={idx}, offset=0x{offset:08x}, size={size}, archive_size={len(archive_data)})")
        
        print(f"\n[*] Berhasil extract {extracted}/{len(entries)} files ke {output_dir}")
        return extracted
    
    def repack(self, input_dir: str, output_archive: str = None, output_index: str = None):
        """
        Repack .SCF files kembali ke archive
        PENTING: File harus di-repack dengan urutan yang sama!
        CRITICAL: Archive menggunakan sparse blocks - index field adalah block number!
        """
        output_archive = output_archive or self.archive_path
        output_index = output_index or self.index_path
        
        # Baca index file original untuk mendapatkan urutan yang benar
        self.pft = PFTParser(self.index_path)
        original_entries = self.pft.read()
        
        print(f"[*] Membaca index original: {self.index_path}")
        print(f"[*] Jumlah scene: {len(original_entries)}")
        print(f"[*] Block size: {self.BLOCK_SIZE} bytes")
        
        # Hitung total blocks needed
        max_block = max(idx for _, idx, _ in original_entries)
        total_blocks = max_block + 1
        print(f"[*] Max block number: {max_block}")
        print(f"[*] Total blocks in archive: {total_blocks}")
        
        # Buat archive kosong dengan ukuran penuh (all blocks)
        archive_data = bytearray(total_blocks * self.BLOCK_SIZE)
        
        # Baca semua .SCF files dan tulis ke block yang sesuai
        new_entries = []
        
        for name, orig_idx, orig_size in original_entries:
            scf_path = os.path.join(input_dir, f"{name}.SCF")
            
            if not os.path.exists(scf_path):
                print(f"[!] Warning: {name}.SCF tidak ditemukan, skip...")
                continue
            
            # Baca file
            with open(scf_path, 'rb') as f:
                scf_data = f.read()
            
            new_size = len(scf_data)
            
            # PENTING: Gunakan index original (block number) untuk menjaga kompatibilitas
            new_entries.append((name, orig_idx, new_size))
            
            # CRITICAL: Write to the correct block position
            # offset = index × BLOCK_SIZE
            offset = orig_idx * self.BLOCK_SIZE
            
            # Tulis data ke archive (tanpa melampaui block boundary)
            archive_data[offset:offset+new_size] = scf_data
            
            # Sisa block tetap null (0x00)
            
            size_diff = ""
            if new_size != orig_size:
                diff_val = new_size - orig_size
                size_diff = f" (diff: {diff_val:+d})"
            
            print(f"[+] Packed: {name}.SCF (block={orig_idx}, offset=0x{offset:08x}, size={new_size}{size_diff})")
        
        # Tulis archive baru
        print(f"\n[*] Menulis archive: {output_archive}")
        with open(output_archive, 'wb') as f:
            f.write(archive_data)
        
        print(f"[*] Ukuran archive: {len(archive_data)} bytes ({len(archive_data) // 1024}KB)")
        print(f"[*] Total blocks: {len(archive_data) // self.BLOCK_SIZE}")
        
        # Tulis index baru
        print(f"[*] Menulis index: {output_index}")
        self.pft.write(output_index, new_entries)
        
        print(f"\n[*] Repack selesai! {len(new_entries)}/{len(original_entries)} files")
        print(f"[*] File output:")
        print(f"    - Archive: {output_archive}")
        print(f"    - Index:   {output_index}")
        
        return len(new_entries)


def main():
    """Main function untuk CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='SDK Tools - Unpack/Repack Visual Novel Script Files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh penggunaan:

  # Unpack
  python sdk_tools.py unpack scene.DSK scene.PFT extracted/
  
  # Repack (setelah edit)
  python sdk_tools.py repack scene.DSK scene.PFT edited/ scene_new.DSK scene_new.PFT
  
  # Atau repack langsung replace original
  python sdk_tools.py repack scene.DSK scene.PFT edited/

PENTING:
- Jangan ubah nama file .SCF
- Jangan hapus atau tambah file .SCF
- Urutan file harus sama dengan original
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # Unpack command
    unpack_parser = subparsers.add_parser('unpack', help='Extract .SCF files dari archive')
    unpack_parser.add_argument('archive', help='Path ke file .DSK/.SDK')
    unpack_parser.add_argument('index', help='Path ke file .PFT')
    unpack_parser.add_argument('output', help='Output directory')
    
    # Repack command
    repack_parser = subparsers.add_parser('repack', help='Repack .SCF files ke archive')
    repack_parser.add_argument('archive', help='Path ke file .DSK/.SDK original')
    repack_parser.add_argument('index', help='Path ke file .PFT original')
    repack_parser.add_argument('input', help='Input directory dengan .SCF files')
    repack_parser.add_argument('--output-archive', help='Output archive path (default: overwrite original)')
    repack_parser.add_argument('--output-index', help='Output index path (default: overwrite original)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'unpack':
            sdk = SDKArchive(args.archive, args.index)
            sdk.unpack(args.output)
            
        elif args.command == 'repack':
            sdk = SDKArchive(args.archive, args.index)
            sdk.repack(args.input, args.output_archive, args.output_index)
            
    except Exception as e:
        print(f"\n[!] Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
