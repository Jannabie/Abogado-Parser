import os

def kodingan_final_rapi(file_input, file_output):
    # Mapping terjemahan dengan spasi manual untuk Center Alignment
    # Total byte setiap baris harus SAMA dengan aslinya (Shift-JIS)
    translations = {
        "最初から始める": "  Mulai Baru   ", # Asli 14 byte -> Baru 14 byte
        "ロードする":     " Muat Data ",      # Asli 10 byte -> Baru 10 byte
        "ＣＧモード":     " Galeri CG ",      # Asli 10 byte -> Baru 10 byte
        "サウンドモード": " Mode Suara  ",     # Asli 12 byte -> Baru 12 byte
        "シーン回想":     "Ingat Adegan",    # Asli 10 byte -> Baru 10 byte
    }

    try:
        # 1. Membaca file asli
        if not os.path.exists(file_input):
            print(f"Error: File {file_input} tidak ditemukan!")
            return

        with open(file_input, 'rb') as f:
            data = bytearray(f.read())
            ukuran_asli = len(data)

        # 2. Proses Injeksi Teks
        for original, replacement in translations.items():
            orig_bytes = original.encode('shift_jis')
            repl_bytes = replacement.encode('shift_jis')
            target_len = len(orig_bytes)

            # Cari posisi byte teks asli
            idx = data.find(orig_bytes)
            
            if idx != -1:
                # Pastikan panjang pengganti tepat sama dengan target
                if len(repl_bytes) < target_len:
                    repl_bytes = repl_bytes.ljust(target_len, b'\x20')
                elif len(repl_bytes) > target_len:
                    repl_bytes = repl_bytes[:target_len]
                
                # Timpa di lokasi yang sama
                data[idx:idx+target_len] = repl_bytes
                print(f"Berhasil merapikan: [{replacement.strip()}]")

        # 3. Simpan dan Validasi
        with open(file_output, 'wb') as f:
            f.write(data)
        
        ukuran_baru = os.path.getsize(file_output)
        print(f"\n--- HASIL VALIDASI ---")
        print(f"Ukuran Asli: {ukuran_asli} bytes")
        print(f"Ukuran Baru: {ukuran_baru} bytes")
        
        if ukuran_asli == ukuran_baru:
            print("STATUS: AMAN! Ukuran file tidak berubah. Silakan tes di game.")
        else:
            print("STATUS: BAHAYA! Ukuran file berubah, game mungkin crash.")

    except Exception as e:
        print(f"Terjadi kesalahan: {e}")

if __name__ == "__main__":
    # Pastikan SCN002.SCF adalah file original Jepang
    kodingan_final_rapi('SCN002.SCF', 'SCN002_RAPI.SCF')