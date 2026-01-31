#!/usr/bin/env python3
"""
SCF Parser v2 - Improved parser untuk .SCF files
Preserves complete binary structure untuk perfect rebuilds
"""

import json
import os
from pathlib import Path
from typing import List, Tuple


class SCFParserV2:
    """Parser yang preserves complete binary structure"""
    
    def __init__(self, encoding='shift_jis'):
        self.encoding = encoding
    
    def parse(self, filepath: str) -> dict:
        """
        Parse file SCF dan extract text dengan mempertahankan struktur
        
        Returns structure untuk perfect rebuild
        """
        with open(filepath, 'rb') as f:
            data = f.read()
        
        # Extract Japanese text segments with their offsets
        text_segments = []
        i = 0
        
        while i < len(data):
            # Look for null-terminated strings
            start = i
            segment = bytearray()
            
            while i < len(data) and data[i] != 0x00:
                segment.append(data[i])
                i += 1
            
            # Include null terminator if found
            if i < len(data) and data[i] == 0x00:
                segment.append(0x00)
                i += 1
            
            # Try to decode as text
            if len(segment) > 1:  # More than just null
                try:
                    text_content = bytes(segment[:-1])  # Exclude null
                    if text_content:
                        decoded = text_content.decode(self.encoding, errors='ignore')
                        # Check if contains Japanese
                        if any('\u3040' <= c <= '\u30ff' or '\u4e00' <= c <= '\u9fff' for c in decoded):
                            text_segments.append({
                                'offset': start,
                                'length': len(segment),
                                'original': list(segment),  # Convert to list for JSON
                                'text': decoded
                            })
                except:
                    pass
        
        return {
            'original_data': list(data),  # Keep complete original
            'size': len(data),
            'encoding': self.encoding,
            'text_segments': text_segments
        }
    
    def extract_texts(self, parsed_data: dict) -> List[str]:
        """Extract just the texts for translation"""
        return [seg['text'] for seg in parsed_data['text_segments']]
    
    def rebuild(self, parsed_data: dict, new_texts: List[str] = None) -> bytes:
        """
        Rebuild SCF with optional text replacement
        
        Args:
            parsed_data: Data from parse()
            new_texts: Optional list of replacement texts
        
        Returns:
            Binary data for SCF file
        """
        # Start with original data
        data = bytearray(parsed_data['original_data'])
        
        if not new_texts:
            # No replacement, return original
            return bytes(data)
        
        # Replace text segments
        # Work backwards to avoid offset issues
        segments = parsed_data['text_segments']
        
        if len(new_texts) != len(segments):
            print(f"⚠️  Warning: Text count mismatch! Expected {len(segments)}, got {len(new_texts)}")
            print(f"   Using min({len(segments)}, {len(new_texts)}) texts")
        
        # Process in reverse order to maintain offsets
        for i in range(min(len(segments), len(new_texts)) - 1, -1, -1):
            seg = segments[i]
            new_text = new_texts[i]
            
            # Encode new text
            try:
                new_bytes = new_text.encode(self.encoding)
                new_bytes += b'\x00'  # Add null terminator
                
                # Replace in data
                offset = seg['offset']
                old_length = seg['length']
                
                # Remove old bytes
                del data[offset:offset + old_length]
                
                # Insert new bytes
                for j, byte in enumerate(new_bytes):
                    data.insert(offset + j, byte)
                
            except Exception as e:
                print(f"❌ Error encoding text at offset {seg['offset']}: {e}")
                print(f"   Keeping original text")
        
        return bytes(data)
    
    def save_for_translation(self, filepath: str, output_dir: str):
        """Save files for translation workflow"""
        parsed = self.parse(filepath)
        base_name = Path(filepath).stem
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Save JSON with full structure
        json_path = os.path.join(output_dir, f"{base_name}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(parsed, f, ensure_ascii=False, indent=2)
        
        # Save TXT with texts only
        txt_path = os.path.join(output_dir, f"{base_name}.txt")
        texts = self.extract_texts(parsed)
        with open(txt_path, 'w', encoding='utf-8') as f:
            for text in texts:
                f.write(text + '\n')
        
        print(f"   JSON: {json_path}")
        print(f"   TXT:  {txt_path}")
        print(f"   Found {len(texts)} text segments")
        
        return json_path, txt_path
    
    def rebuild_from_files(self, json_path: str, txt_path: str = None) -> bytes:
        """Rebuild from JSON + optional TXT"""
        with open(json_path, 'r', encoding='utf-8') as f:
            parsed_data = json.load(f)
        
        new_texts = None
        if txt_path and os.path.exists(txt_path):
            with open(txt_path, 'r', encoding='utf-8') as f:
                new_texts = [line.rstrip('\n') for line in f]
        
        return self.rebuild(parsed_data, new_texts)


def main():
    """CLI"""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(
        description='SCF Parser v2 - Perfect rebuild preservation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
USAGE:

1. Extract untuk translation:
   python scf_parser_v2.py extract input.SCF output_dir/

2. Edit file TXT dengan translation

3. Rebuild:
   python scf_parser_v2.py rebuild input.json translated.txt output.SCF

4. Batch extract:
   python scf_parser_v2.py batch-extract scf_folder/ output_dir/
        """
    )
    
    subparsers = parser.add_subparsers(dest='command')
    
    # Extract
    extract_parser = subparsers.add_parser('extract')
    extract_parser.add_argument('input', help='Input SCF file')
    extract_parser.add_argument('output_dir', help='Output directory')
    
    # Rebuild
    rebuild_parser = subparsers.add_parser('rebuild')
    rebuild_parser.add_argument('json', help='JSON file')
    rebuild_parser.add_argument('txt', nargs='?', help='TXT file (optional)')
    rebuild_parser.add_argument('output', help='Output SCF')
    
    # Batch extract
    batch_parser = subparsers.add_parser('batch-extract')
    batch_parser.add_argument('input_dir', help='Input directory with SCF files')
    batch_parser.add_argument('output_dir', help='Output directory')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    try:
        scf = SCFParserV2()
        
        if args.command == 'extract':
            print(f"📖 Extracting: {args.input}")
            scf.save_for_translation(args.input, args.output_dir)
            print("✅ Done!")
            
        elif args.command == 'rebuild':
            print(f"🔨 Rebuilding: {args.json}")
            if args.txt:
                print(f"   With translation: {args.txt}")
            
            data = scf.rebuild_from_files(args.json, args.txt)
            
            with open(args.output, 'wb') as f:
                f.write(data)
            
            print(f"✅ Created: {args.output} ({len(data)} bytes)")
            
        elif args.command == 'batch-extract':
            scf_files = list(Path(args.input_dir).glob('*.SCF'))
            print(f"📋 Found {len(scf_files)} files")
            
            for scf_file in scf_files:
                print(f"\n📖 {scf_file.name}")
                scf.save_for_translation(str(scf_file), args.output_dir)
            
            print(f"\n✅ All done! Output: {args.output_dir}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
