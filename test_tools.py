#!/usr/bin/env python3
"""
Test Script - Verify semua tools bekerja dengan benar
Run script ini untuk memastikan tools working perfectly!
"""

import os
import sys
import subprocess
import hashlib
from pathlib import Path


def print_header(text):
    """Print header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def print_test(text):
    """Print test name"""
    print(f"\n🧪 TEST: {text}")
    print("-"*70)


def get_md5(filepath):
    """Get MD5 hash of file"""
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def run_command(cmd):
    """Run command"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr


def test_sdk_tools(dsk_file, pft_file):
    """Test sdk_tools.py"""
    print_test("SDK Tools - DSK Extract & Repack")
    
    test_dir = Path("test_sdk")
    test_dir.mkdir(exist_ok=True)
    
    # Extract
    print("  1. Extracting DSK...")
    extract_dir = test_dir / "extracted"
    success, stdout, stderr = run_command(
        f"python3 sdk_tools.py unpack {dsk_file} {pft_file} {extract_dir}"
    )
    
    if not success:
        print(f"  ❌ Extract failed: {stderr}")
        return False
    
    scf_count = len(list(extract_dir.glob('*.SCF')))
    print(f"  ✅ Extracted {scf_count} SCF files")
    
    # Repack
    print("  2. Repacking DSK...")
    test_dsk = test_dir / "test.DSK"
    test_pft = test_dir / "test.PFT"
    
    success, stdout, stderr = run_command(
        f"python3 sdk_tools.py repack {dsk_file} {pft_file} {extract_dir} "
        f"--output-archive {test_dsk} --output-index {test_pft}"
    )
    
    if not success:
        print(f"  ❌ Repack failed: {stderr}")
        return False
    
    print(f"  ✅ Repacked successfully")
    
    # Verify
    print("  3. Verifying MD5...")
    original_md5 = get_md5(dsk_file)
    test_md5 = get_md5(test_dsk)
    
    if original_md5 == test_md5:
        print(f"  ✅ MD5 MATCH! {original_md5}")
        print(f"  ✅ SDK TOOLS WORKING PERFECTLY!")
        return True
    else:
        print(f"  ❌ MD5 MISMATCH!")
        print(f"     Original: {original_md5}")
        print(f"     Test:     {test_md5}")
        return False


def test_scf_parser(scf_file):
    """Test scf_parser_v2.py"""
    print_test("SCF Parser - Extract & Rebuild")
    
    test_dir = Path("test_scf")
    test_dir.mkdir(exist_ok=True)
    
    # Extract
    print("  1. Extracting SCF...")
    parse_dir = test_dir / "parsed"
    success, stdout, stderr = run_command(
        f"python3 scf_parser_v2.py extract {scf_file} {parse_dir}"
    )
    
    if not success:
        print(f"  ❌ Extract failed: {stderr}")
        return False
    
    json_file = parse_dir / f"{Path(scf_file).stem}.json"
    txt_file = parse_dir / f"{Path(scf_file).stem}.txt"
    
    if not json_file.exists() or not txt_file.exists():
        print(f"  ❌ Output files not created")
        return False
    
    print(f"  ✅ Extracted to JSON + TXT")
    
    # Rebuild
    print("  2. Rebuilding SCF...")
    rebuilt_file = test_dir / "rebuilt.SCF"
    
    success, stdout, stderr = run_command(
        f"python3 scf_parser_v2.py rebuild {json_file} {txt_file} {rebuilt_file}"
    )
    
    if not success:
        print(f"  ❌ Rebuild failed: {stderr}")
        return False
    
    print(f"  ✅ Rebuilt successfully")
    
    # Verify
    print("  3. Verifying MD5...")
    original_md5 = get_md5(scf_file)
    rebuilt_md5 = get_md5(rebuilt_file)
    
    if original_md5 == rebuilt_md5:
        print(f"  ✅ MD5 MATCH! {original_md5}")
        print(f"  ✅ SCF PARSER WORKING PERFECTLY!")
        return True
    else:
        print(f"  ❌ MD5 MISMATCH!")
        print(f"     Original: {original_md5}")
        print(f"     Rebuilt:  {rebuilt_md5}")
        return False


def test_workflow(dsk_file, pft_file):
    """Test workflow.py"""
    print_test("Workflow - Full Pipeline")
    
    workspace = Path("test_workflow")
    
    # Clean workspace
    if workspace.exists():
        import shutil
        shutil.rmtree(workspace)
    
    print("  1. Running quick setup...")
    success, stdout, stderr = run_command(
        f"python3 workflow.py quick {dsk_file} {pft_file} --workspace {workspace}"
    )
    
    if not success:
        print(f"  ❌ Quick setup failed: {stderr}")
        return False
    
    print(f"  ✅ Workspace created")
    
    # Check structure
    expected_dirs = [
        workspace / "extracted_scf",
        workspace / "parsed",
        workspace / "translated",
        workspace / "rebuilt_scf"
    ]
    
    for d in expected_dirs:
        if not d.exists():
            print(f"  ❌ Missing directory: {d}")
            return False
    
    print(f"  ✅ All directories created")
    
    # Check files
    txt_files = list((workspace / "translated").glob("*.txt"))
    if not txt_files:
        print(f"  ❌ No TXT files created")
        return False
    
    print(f"  ✅ {len(txt_files)} TXT files ready for translation")
    
    print("  2. Running rebuild...")
    success, stdout, stderr = run_command(
        f"python3 workflow.py rebuild {dsk_file} {pft_file} --workspace {workspace}"
    )
    
    if not success:
        print(f"  ❌ Rebuild failed: {stderr}")
        return False
    
    # Check output
    output_dsk = workspace / "scene_translated.DSK"
    output_pft = workspace / "scene_translated.PFT"
    
    if not output_dsk.exists() or not output_pft.exists():
        print(f"  ❌ Output files not created")
        return False
    
    print(f"  ✅ Output files created")
    
    # Verify (should be identical since no translation done)
    print("  3. Verifying output...")
    original_md5 = get_md5(dsk_file)
    output_md5 = get_md5(output_dsk)
    
    if original_md5 == output_md5:
        print(f"  ✅ MD5 MATCH! {original_md5}")
        print(f"  ✅ WORKFLOW WORKING PERFECTLY!")
        return True
    else:
        print(f"  ❌ MD5 MISMATCH!")
        print(f"     Original: {original_md5}")
        print(f"     Output:   {output_md5}")
        return False


def cleanup():
    """Cleanup test directories"""
    import shutil
    for d in ["test_sdk", "test_scf", "test_workflow"]:
        if Path(d).exists():
            shutil.rmtree(d)


def main():
    """Main test runner"""
    print_header("Translation Tools - Test Suite")
    
    # Check if files exist
    if not Path("sdk_tools.py").exists():
        print("❌ Error: sdk_tools.py not found!")
        print("   Make sure you're in the correct directory")
        return 1
    
    if not Path("scf_parser_v2.py").exists():
        print("❌ Error: scf_parser_v2.py not found!")
        print("   Make sure you're in the correct directory")
        return 1
    
    if not Path("workflow.py").exists():
        print("❌ Error: workflow.py not found!")
        print("   Make sure you're in the correct directory")
        return 1
    
    # Check for test data
    dsk_file = None
    pft_file = None
    
    # Look for scene files
    for name in ["scene.DSK", "test.DSK"]:
        if Path(name).exists():
            dsk_file = name
            pft_file = name.replace(".DSK", ".PFT")
            break
    
    if not dsk_file or not Path(pft_file).exists():
        print("❌ Error: No test data found!")
        print("   Please provide scene.DSK and scene.PFT files")
        print("\n   Usage: python3 test_tools.py")
        print("   (Make sure scene.DSK and scene.PFT are in the same directory)")
        return 1
    
    print(f"\n📁 Using test data:")
    print(f"   DSK: {dsk_file}")
    print(f"   PFT: {pft_file}")
    
    # Run tests
    results = []
    
    # Test 1: SDK Tools
    results.append(("SDK Tools", test_sdk_tools(dsk_file, pft_file)))
    
    # Test 2: SCF Parser
    # Use first extracted SCF for testing
    scf_file = "test_sdk/extracted/SCN003.SCF"
    if Path(scf_file).exists():
        results.append(("SCF Parser", test_scf_parser(scf_file)))
    else:
        print("\n⚠️  Warning: Cannot test SCF Parser (no SCF file)")
        results.append(("SCF Parser", None))
    
    # Test 3: Workflow
    results.append(("Workflow", test_workflow(dsk_file, pft_file)))
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = 0
    failed = 0
    skipped = 0
    
    for name, result in results:
        if result is True:
            print(f"  ✅ {name}: PASSED")
            passed += 1
        elif result is False:
            print(f"  ❌ {name}: FAILED")
            failed += 1
        else:
            print(f"  ⚠️  {name}: SKIPPED")
            skipped += 1
    
    print(f"\n  Total: {passed} passed, {failed} failed, {skipped} skipped")
    
    # Cleanup
    print("\n🧹 Cleaning up test files...")
    cleanup()
    print("  ✅ Cleanup complete")
    
    # Final verdict
    if failed == 0 and passed > 0:
        print_header("✅ ALL TESTS PASSED!")
        print("\n  🎉 Tools are working perfectly!")
        print("  📝 Ready for translation work!")
        return 0
    else:
        print_header("❌ SOME TESTS FAILED")
        print("\n  Please check the errors above")
        print("  Make sure you're using the correct tool versions")
        return 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests cancelled by user")
        cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        cleanup()
        sys.exit(1)
