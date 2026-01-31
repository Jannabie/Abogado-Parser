import re

def smart_parse_scf(file_path):
    print(f"Memproses file: {file_path}...\n")
    try:
        with open(file_path, 'rb') as f:
            data = f.read()

        # Dekode ke Shift-JIS, abaikan error biner
        raw_text = data.decode('shift_jis', errors='ignore')

        # Bersihkan karakter padding '@' dan spasi lebar Jepang
        clean_raw = raw_text.replace('@', '').replace('\u3000', ' ')

        # Regex untuk memisahkan teks asli dari instruksi sistem
        # Kita hanya mengambil kata yang tidak diawali karakter kontrol (!, #, _)
        lines = clean_raw.split()
        
        print("--- MENU & INSTRUKSI TERDETEKSI ---")
        for line in lines:
            # Lewati baris yang isinya instruksi sistem (pendek & diawali simbol)
            if re.match(r'^[!#_\[\]=;]', line) or len(line) < 2:
                continue
                
            # Bersihkan karakter biner acak yang tersisa di tengah kata
            clean_line = re.sub(r'[a-zA-Z0-9!#_\[\]=;]', '', line).strip()
            
            if clean_line:
                # Pemetaan manual berdasarkan data source Anda
                if "始" in clean_line: print(f"Menyambung: 最初から始める (Start)")
                elif "ロ" in clean_line and "ド" in clean_line: print(f"Menyambung: ロードする (Load)")
                elif "Ｇ" in clean_line: print(f"Menyambung: ＣＧモード (CG Mode)")
                elif "サ" in clean_line: print(f"Menyambung: サウンドモード (Sound Mode)")
                elif "回想" in clean_line: print(f"Menyambung: シーン回想 (Scene Recall)")
                else: print(f"Ditemukan: {clean_line}")
        
        # Cari teks bahasa Inggris murni (seperti Staff Credit)
        english_match = re.findall(r'[A-Za-z\s]{5,}', raw_text)
        for eng in english_match:
            if "Staff Credit" in eng:
                print(f"Ditemukan: Staff Credit")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    smart_parse_scf('SCN002.SCF')