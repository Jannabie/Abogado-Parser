# Abogado Parser

Parser untuk file script visual novel **~Shuumatsu no Sugoshikata The World is Drawing to an W/end.~**

## Deskripsi

Tool ini digunakan untuk ekstrak dan modifikasi file script (.SCF) dari game visual novel. Berguna untuk keperluan translation, modding, atau analisis konten game.

## Fitur

- **Parser SCF**: Ekstrak teks dari file .SCF ke format yang mudah dibaca
- **Injector SCF**: Masukkan kembali teks yang sudah dimodifikasi ke file .SCF
- **SDK Tools**: Utilitas tambahan untuk verifikasi dan testing
- **Format Output**: Support untuk JSON dan TXT

## File Utama

| File | Fungsi |
|------|--------|
| `parser_scf.py` | Parser utama untuk file SCF |
| `scf_parser_v2.py` | Versi 2 dari parser dengan fitur tambahan |
| `injector_scf.py` | Inject .SCF to .SCF untuk tampilan menu |
| `sdk_tools.py` | Tools SDK untuk manipulasi file game |
| `sdk_verify.py` | Verifikasi integritas file |
| `workflow.py` | Otomasi workflow parsing dan injecting |
| `rapihkan.py` | Utilitas untuk clean up output |

## Cara Pakai

### 1. Parse File SCF

```bash
python parser_scf.py SCN001.SCF
```

Output akan berupa file JSON atau TXT yang berisi dialog dan script dari game.

### 2. Edit Text

Edit file output (`.json` atau `.txt`) sesuai kebutuhan.

### 3. Inject Kembali

```bash
python injector_scf.py SCN001.json SCN001.SCF
```

File SCF akan ter-update dengan text baru.

## Requirements

- Python 3.x
- Dependencies standar (jika ada, install dengan `pip install -r requirements.txt`)

## Struktur File Game

- `SCN***.SCF` - File script scene
- `SCNDAT.TBL` - Table data scene
- `scene.DSK` / `scene.PFT` - File asset game

## Catatan

- Backup file original sebelum melakukan modifikasi
- Verifikasi hasil inject dengan `sdk_verify.py`
- File `SCN002.SCF_FIXED` adalah contoh file yang sudah diperbaiki

## Disclaimer

Tool ini dibuat untuk keperluan edukasi dan research. Pastikan mengikuti aturan copyright dan ToS dari game original.

## Kontribusi

Pull request dan issue welcome. Untuk perubahan major, buka issue dulu untuk diskusi.

## License

Lihat file LICENSE (jika ada) untuk detail.
