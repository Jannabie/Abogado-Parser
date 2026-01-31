#!/usr/bin/env python3
"""
Translation Workflow - Tool lengkap untuk modding Shuumatsu no Sugoshikata

Workflow:
1. Extract scene.DSK → SCF files
2. Parse SCF files → JSON + TXT (untuk translate)
3. Edit TXT files dengan translation
4. Rebuild SCF files dari JSON + TXT
5. Repack SCF files → scene.DSK baru

All-in-one solution!
"""

import os
import sys
import shutil
from pathlib import Path


def print_header(text):
    """Print fancy header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


def print_step(num, text):
    """Print step"""
    print(f"\n🔸 STEP {num}: {text}")
    print("-"*70)


def check_files(*files):
    """Check if files exist"""
    for f in files:
        if not os.path.exists(f):
            print(f"❌ Error: File tidak ditemukan: {f}")
            return False
    return True


def run_command(cmd):
    """Run shell command and capture output"""
    import subprocess
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error running command:")
        print(f"   {cmd}")
        print(f"   {result.stderr}")
        return False
    return True


class TranslationWorkflow:
    """Main workflow manager"""
    
    def __init__(self, workspace="translation_workspace"):
        self.workspace = Path(workspace)
        self.extracted_dir = self.workspace / "extracted_scf"
        self.parsed_dir = self.workspace / "parsed"
        self.translated_dir = self.workspace / "translated"
        self.rebuilt_dir = self.workspace / "rebuilt_scf"
        
    def setup_workspace(self):
        """Create workspace directories"""
        print_step(0, "Setup Workspace")
        
        dirs = [
            self.workspace,
            self.extracted_dir,
            self.parsed_dir,
            self.translated_dir,
            self.rebuilt_dir
        ]
        
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created: {d}")
        
        print("\n📁 Workspace structure:")
        print(f"   {self.workspace}/")
        print(f"   ├── extracted_scf/    (SCF files dari DSK)")
        print(f"   ├── parsed/           (JSON + TXT untuk translate)")
        print(f"   ├── translated/       (TXT yang sudah ditranslate)")
        print(f"   └── rebuilt_scf/      (SCF files hasil rebuild)")
    
    def extract_dsk(self, dsk_file, pft_file):
        """Extract DSK archive"""
        print_step(1, "Extract DSK Archive")
        
        if not check_files(dsk_file, pft_file):
            return False
        
        print(f"📦 Extracting: {dsk_file}")
        cmd = f"python3 sdk_tools.py unpack {dsk_file} {pft_file} {self.extracted_dir}"
        
        if not run_command(cmd):
            return False
        
        scf_files = list(self.extracted_dir.glob('*.SCF'))
        print(f"✅ Extracted {len(scf_files)} SCF files to: {self.extracted_dir}")
        return True
    
    def parse_scf_files(self):
        """Parse all SCF files"""
        print_step(2, "Parse SCF Files untuk Translation")
        
        scf_files = list(self.extracted_dir.glob('*.SCF'))
        if not scf_files:
            print("❌ Error: Tidak ada file SCF ditemukan")
            return False
        
        print(f"📋 Processing {len(scf_files)} files...")
        
        cmd = f"python3 scf_parser.py batch-extract {self.extracted_dir} {self.parsed_dir}"
        if not run_command(cmd):
            return False
        
        txt_files = list(self.parsed_dir.glob('*.txt'))
        print(f"\n✅ Parsed {len(txt_files)} files")
        print(f"📁 Output: {self.parsed_dir}")
        print(f"\n💡 Files yang dibuat:")
        print(f"   - *.json : Binary structure (JANGAN EDIT!)")
        print(f"   - *.txt  : Text untuk translate")
        
        return True
    
    def prepare_for_translation(self):
        """Copy TXT files to translation folder"""
        print_step(3, "Prepare Files untuk Translation")
        
        txt_files = list(self.parsed_dir.glob('*.txt'))
        if not txt_files:
            print("❌ Error: Tidak ada file TXT ditemukan")
            return False
        
        print(f"📋 Copying {len(txt_files)} TXT files...")
        
        for txt_file in txt_files:
            dst = self.translated_dir / txt_file.name
            shutil.copy2(txt_file, dst)
        
        print(f"✅ Files copied to: {self.translated_dir}")
        print(f"\n🌍 SEKARANG WAKTUNYA TRANSLATE!")
        print(f"   1. Buka folder: {self.translated_dir}")
        print(f"   2. Edit file *.txt dengan translation")
        print(f"   3. Save file dengan encoding UTF-8")
        print(f"   4. Jalankan lagi script dengan command 'rebuild'")
        
        return True
    
    def rebuild_scf_files(self):
        """Rebuild SCF files from JSON + translated TXT"""
        print_step(4, "Rebuild SCF Files")
        
        json_files = list(self.parsed_dir.glob('*.json'))
        if not json_files:
            print("❌ Error: Tidak ada file JSON ditemukan")
            return False
        
        print(f"🔨 Rebuilding {len(json_files)} files...")
        
        rebuilt_count = 0
        for json_file in json_files:
            base_name = json_file.stem
            txt_file = self.translated_dir / f"{base_name}.txt"
            output_file = self.rebuilt_dir / f"{base_name}.SCF"
            
            # Check if translation exists
            if not txt_file.exists():
                print(f"⚠️  Warning: {txt_file.name} tidak ditemukan, skip...")
                continue
            
            cmd = f"python3 scf_parser.py rebuild {json_file} {txt_file} {output_file}"
            if run_command(cmd):
                rebuilt_count += 1
            else:
                print(f"❌ Failed to rebuild: {base_name}")
        
        print(f"\n✅ Rebuilt {rebuilt_count}/{len(json_files)} files")
        print(f"📁 Output: {self.rebuilt_dir}")
        
        return rebuilt_count > 0
    
    def repack_dsk(self, original_dsk, original_pft, output_dsk=None, output_pft=None):
        """Repack DSK archive"""
        print_step(5, "Repack DSK Archive")
        
        if not check_files(original_dsk, original_pft):
            return False
        
        # Set output filenames
        if not output_dsk:
            output_dsk = self.workspace / "scene_translated.DSK"
        if not output_pft:
            output_pft = self.workspace / "scene_translated.PFT"
        
        print(f"📦 Repacking to: {output_dsk}")
        
        cmd = f"python3 sdk_tools.py repack {original_dsk} {original_pft} {self.rebuilt_dir} --output-archive {output_dsk} --output-index {output_pft}"
        
        if not run_command(cmd):
            return False
        
        print(f"\n✅ Repack complete!")
        print(f"📁 Output files:")
        print(f"   - {output_dsk}")
        print(f"   - {output_pft}")
        print(f"\n🎮 Untuk menggunakan mod:")
        print(f"   1. Backup original scene.DSK dan scene.PFT")
        print(f"   2. Copy {output_dsk.name} → scene.DSK")
        print(f"   3. Copy {output_pft.name} → scene.PFT")
        print(f"   4. Jalankan game!")
        
        return True
    
    def verify_files(self, dsk_file, pft_file):
        """Verify DSK/PFT integrity"""
        print_step("V", "Verify Files")
        
        if not check_files(dsk_file, pft_file):
            return False
        
        cmd = f"python3 sdk_verify.py verify {pft_file} {dsk_file}"
        return run_command(cmd)


def main():
    """Main CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Translation Workflow - Complete modding solution',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
WORKFLOW LENGKAP:

1. EXTRACT - Extract DSK dan parse SCF:
   python workflow.py extract scene.DSK scene.PFT

2. TRANSLATE - Edit file TXT di folder translated/

3. REBUILD - Rebuild SCF dan repack DSK:
   python workflow.py rebuild scene.DSK scene.PFT

4. VERIFY - Verify hasil (optional):
   python workflow.py verify scene_translated.DSK scene_translated.PFT

5. Test di game!

QUICK START:
   python workflow.py quick scene.DSK scene.PFT
   (Otomatis extract dan setup untuk translation)
        """
    )
    
    parser.add_argument('command', choices=['extract', 'rebuild', 'verify', 'quick'],
                       help='Command to run')
    parser.add_argument('dsk', help='DSK file path')
    parser.add_argument('pft', help='PFT file path')
    parser.add_argument('--workspace', default='translation_workspace',
                       help='Workspace directory (default: translation_workspace)')
    
    args = parser.parse_args()
    
    print_header("Shuumatsu no Sugoshikata - Translation Workflow")
    
    wf = TranslationWorkflow(workspace=args.workspace)
    
    try:
        if args.command == 'extract' or args.command == 'quick':
            wf.setup_workspace()
            if not wf.extract_dsk(args.dsk, args.pft):
                return 1
            if not wf.parse_scf_files():
                return 1
            if not wf.prepare_for_translation():
                return 1
            
            print_header("EXTRACT SELESAI!")
            print("📝 Langkah selanjutnya:")
            print("   1. Buka folder: translation_workspace/translated/")
            print("   2. Edit file *.txt dengan translation")
            print("   3. Save dengan UTF-8 encoding")
            print(f"   4. Run: python workflow.py rebuild {args.dsk} {args.pft}")
            
        elif args.command == 'rebuild':
            if not wf.rebuild_scf_files():
                return 1
            if not wf.repack_dsk(args.dsk, args.pft):
                return 1
            
            print_header("REBUILD SELESAI!")
            print("🎮 File siap digunakan!")
            print(f"   Location: {wf.workspace}/scene_translated.DSK")
            
        elif args.command == 'verify':
            if not wf.verify_files(args.dsk, args.pft):
                return 1
            
            print_header("VERIFY SELESAI!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
