import os

def kalibrasi_visual_final_banget(file_path, output_path):
    # Mapping Terjemahan - Menyamakan Garis Tengah (Center-Axis)
    # Memulai: 14 byte | Memuat: 10 byte | CGs: 10 byte | Staff Credit: 12 byte
    translations = {
        "最初から始める": "   Memulai    ", # 3 spasi depan (Total 14)
        "ロードする":     "  Arsip  ",     # 2 spasi depan (Total 10)
        "ＣＧモード":     " CG List    ",     # 3 spasi depan agar huruf C di tengah (Total 10)
        "サウンドモード": " Staff Credit",  # 1 spasi depan (Total 12)
        "シーン回想":     "  Adegan    ",     # 2 spasi depan (Total 10)
    }

    try:
        with open(file_path, 'rb') as f:
            data = bytearray(f.read())
            orig_size = len(data) # Harus 604 bytes

        for original, replacement in translations.items():
            orig_bytes = original.encode('shift_jis')
            target_len = len(orig_bytes)
            
            # Encode dan kunci panjang byte agar file tidak rusak
            repl_bytes = replacement.encode('shift_jis')
            
            if len(repl_bytes) < target_len:
                repl_bytes = repl_bytes.ljust(target_len, b'\x20')
            elif len(repl_bytes) > target_len:
                repl_bytes = repl_bytes[:target_len]

            idx = data.find(orig_bytes)
            if idx != -1:
                data[idx:idx+target_len] = repl_bytes
                print(f"Centering: [{replacement}]")

        with open(output_path, 'wb') as f:
            f.write(data)
            
        if orig_size == os.path.getsize(output_path):
            print(f"\nSTATUS: SEMPURNA! Ukuran tetap {orig_size} bytes.")
        else:
            print("\nSTATUS: GAGAL! Ukuran file berubah.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # RENAME 'SCN002_FINAL.SCF' jadi 'SCN002.SCF' sebelum repack
    kalibrasi_visual_final_banget('SCN002.SCF', 'SCN002_FINAL.SCF')