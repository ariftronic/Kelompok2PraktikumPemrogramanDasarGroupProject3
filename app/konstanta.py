import os

# Lokasi folder (absolut, sehingga program dapat dijalankan dari folder mana pun)
DIR_PROYEK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_DATA = os.path.join(DIR_PROYEK, 'data')
DIR_LAPORAN = os.path.join(DIR_PROYEK, 'laporan')
PATH_ENV = os.path.join(DIR_PROYEK, '.env')
PATH_SCHEMA = os.path.join(DIR_PROYEK, 'database', 'schema.sql')

# File .txt lama (arsip di data/, hanya dibaca scripts/migrate_txt.py)
FILE_MAHASISWA = 'mahasiswa.txt'
FILE_ALAT = 'alat.txt'
FILE_TRANSAKSI = 'transaksi.txt'
FILE_DETAIL_TRANSAKSI = 'detail_transaksi.txt'
PEMISAH = '|'
NILAI_KOSONG = '-'
KOLOM_FILE = {FILE_MAHASISWA: ('nim', 'nama', 'no_hp', 'status_aktif'), FILE_ALAT: ('kode', 'nama', 'kategori', 'kondisi', 'status'), FILE_TRANSAKSI: ('id', 'nim', 'tgl_pinjam', 'batas_kembali', 'status'), FILE_DETAIL_TRANSAKSI: ('id', 'kode', 'status', 'kondisi', 'tgl_kembali')}
JUMLAH_KOLOM = {nama: len(kolom) for nama, kolom in KOLOM_FILE.items()}

# Format waktu
FORMAT_TANGGAL = '%Y-%m-%d'
FORMAT_WAKTU_LOG = '%Y-%m-%d %H:%M'

# Status aktif peminjaman mahasiswa (diatur otomatis dari transaksi aktif)
MHS_AKTIF = 'aktif'
MHS_TIDAK_AKTIF = 'tidak aktif'

# Status dan kondisi alat
STATUS_TERSEDIA = 'tersedia'
STATUS_DIPINJAM = 'dipinjam'
STATUS_TIDAK_TERSEDIA = 'tidak tersedia'
KONDISI_BAIK = 'baik'
KONDISI_RUSAK_RINGAN = 'rusak ringan'
KONDISI_RUSAK_BERAT = 'rusak berat'
DAFTAR_KONDISI = (KONDISI_BAIK, KONDISI_RUSAK_RINGAN, KONDISI_RUSAK_BERAT)

# Status transaksi dan status tiap alat di dalam transaksi
TRX_DIPINJAM = 'dipinjam'
TRX_SEBAGIAN = 'sebagian dikembalikan'
TRX_SELESAI = 'selesai'
DETAIL_DIPINJAM = 'dipinjam'
DETAIL_DIKEMBALIKAN = 'dikembalikan'

# Aturan bisnis
MAKS_TRANSAKSI_AKTIF = 2
MAKS_HARI_PINJAM = 7

# Database
MODE_SQL_KETAT = "SET SESSION sql_mode='STRICT_ALL_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION'"
BATAS_WAKTU_KONEKSI = 5
MAKS_ULANG_TRANSAKSI = 3

# Tampilan dan laporan
BARIS_PER_HALAMAN = 20
JUMLAH_PERINGKAT = 5
