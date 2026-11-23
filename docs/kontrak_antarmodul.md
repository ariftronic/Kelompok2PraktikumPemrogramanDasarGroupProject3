# Kontrak Antarmodul

Dokumen ini mendefinisikan method yang dipanggil `app/menu.py` dan cara modul saling terhubung pada versi MySQL.
Isinya disesuaikan dengan kode akhir (lihat juga `docs/final/UML_Final_Implementasi_Kelompok2.png`). Bila kontrak berubah,
ubah dokumen ini, UML implementasi, dan `menu.py` bersamaan.

## 1. Aturan umum

- **Satu pintu database.** Hanya `app/database.py` yang memanggil `pymysql.connect()`, `cursor.execute()`, `commit()`, dan
  `rollback()`. Semua teks SQL ada di `app/repository/`. Manager dan menu tidak berisi SQL.
- **Parameterized query.** Nilai dari pengguna selalu dikirim lewat placeholder `%s` dan tuple parameter, tidak pernah
  disusun dengan f-string, `%`, atau `+`. Bagian SQL yang disusun program (daftar kolom, `LIMIT %d`, `FOR UPDATE`)
  hanya berasal dari konstanta atau angka.
- **Transaction.** Operasi yang mengubah lebih dari satu tabel dibungkus `with db.transaksi():`. Bila ada exception di
  dalam blok, semua perubahan di-ROLLBACK lalu exception dilempar ulang. Operasi satu query langsung di-commit
  (autocommit).
- **Pesan kesalahan.**
  - pelanggaran aturan bisnis dan input tidak valid: `ValueError("pesan jelas")`, ditampilkan menu sebagai `[DITOLAK] pesan`;
  - kesalahan database: `DatabaseError` (pesan ramah, atribut `kode` berisi kode error MySQL), ditampilkan sebagai
    `[!] [ERROR DATABASE] pesan`;
  - kesalahan menulis laporan: `FileManagerError`, ditampilkan sebagai `[ERROR FILE] pesan`.
  Periksa aturan bisnis SEBELUM mengubah data (Aturan 7). Bila constraint database tetap menolak (misalnya dua komputer
  menambah NIM yang sama bersamaan), manager mengubah `DatabaseError` 1062/1451 menjadi `ValueError` yang sama dengan
  pemeriksaan biasa.
- **Hasil query** berupa list `dict` (`DictCursor`). Repository mengubahnya menjadi objek model dengan
  `Model.dari_dict(baris)`; nilai `NULL` menjadi `-` dan tanggal menjadi teks `YYYY-MM-DD`, sama seperti tahap `.txt`.
- Setiap model memiliki `__str__` satu baris (transaksi: beberapa baris) karena menu mencetak hasil dengan `str()`.
- Gunakan konstanta dari `konstanta.py` untuk status, kondisi, dan aturan bisnis. Jangan menulis string literalnya.
- `status` alat dan `status_aktif` mahasiswa adalah data turunan dari transaksi, diatur oleh `ManagerTransaksi` dan
  `ManagerPengembalian` di dalam transaction yang sama.
- Setiap operasi yang berhasil memanggil `logger.catat(keterangan, aksi)` SETELAH transaction selesai. Contoh:
  `catat('Mahasiswa M001 ditambahkan', 'tambah mahasiswa')`,
  `catat('Transaksi T001 dibuat oleh M001 (A001, A002)', 'buat transaksi')`,
  `catat('Alat A001 dikembalikan dalam kondisi baik (T001)', 'pengembalian')`.

## 2. Pembuatan dan penyambungan (dilakukan `AplikasiPeminjaman.siapkan()`)

```python
konfigurasi = baca_konfigurasi()          # dari .env; ValueError bila isinya salah
db = Database(konfigurasi)
db.sambung()                              # DatabaseError bila gagal -> pesan koneksi gagal, program berhenti rapi
db.pastikan_tabel(PATH_SCHEMA)            # CREATE TABLE IF NOT EXISTS dari database/schema.sql
logger = Logger(db, konfigurasi['petugas'])

mahasiswa    = ManagerMahasiswa(db, logger)
alat         = ManagerAlat(db, logger)
transaksi    = ManagerTransaksi(db, logger)
pengembalian = ManagerPengembalian(db, logger)
laporan      = ManagerLaporan(db, logger, FileManager('laporan'))
# saat keluar: db.tutup()
```

Manager tidak saling menyimpan referensi. Setiap manager membuat repository yang ia perlukan (misalnya
`ManagerMahasiswa.hapus` memakai `RepoMahasiswa.jumlah_transaksi_aktif`), sehingga pemeriksaan antar-tabel cukup satu query.

## 3. Lapisan database

### Database (`app/database.py`)

| Method | Keterangan |
|---|---|
| `Database(konfigurasi)` | dict `host`, `port`, `user`, `password`, `database`, `ssl_ca` dari `baca_konfigurasi()` |
| `sambung(buat_database=True)` | membuka koneksi (autocommit, `DictCursor`, `utf8mb4`, `sql_mode` ketat, SSL bila `ssl_ca` diisi); bila database belum ada (1049), membuatnya lalu menyambung ulang |
| `tersambung()`, `tutup()` | status koneksi dan menutup koneksi |
| `query(sql, parameter=())` | list `dict` hasil SELECT |
| `query_satu(sql, parameter=())` | satu `dict` atau `None` |
| `eksekusi(sql, parameter=())` | INSERT/UPDATE/DELETE; mengembalikan jumlah baris yang berubah |
| `transaksi()` | context manager: BEGIN, lalu COMMIT bila blok selesai, ROLLBACK bila ada exception. Bila dipanggil di dalam transaction lain, ikut transaction luar |
| `jalankan_file_sql(path)`, `pastikan_tabel(path_schema)` | menjalankan `schema.sql` |

`DatabaseError(pesan, kode)` dan `terjemahkan(error_pymysql)` mengubah kode MySQL menjadi pesan: 2003/2006/2013 server
tidak terjangkau, 1045 login ditolak, 1044 tidak punya hak akses, 1049 database belum ada, 1062 data sudah ada,
1451 masih dipakai data lain, 1452 rujukan tidak ada, 1205/1213 data sedang dipakai pengguna lain, 1265/1406/1364 nilai
tidak sesuai kolom, 3819/4025 melanggar aturan tabel (CHECK).

### Repository (`app/repository/`)

Semua repository turunan `RepoDasar(db)`, yang menyediakan `pola_like(kata)` (escape `%`, `_`, `\`),
`syarat_kata(kata_kunci, kolom)` (setiap kata harus cocok dengan salah satu kolom), `potongan_halaman(batas, mulai)`
(`LIMIT`/`OFFSET`), dan `kunci_sql(kunci)` (`FOR UPDATE`). Parameter `kunci=True` pada `ambil` hanya dipakai di dalam
transaction.

| Repository | Method |
|---|---|
| `RepoMahasiswa` | `ambil(nim, kunci=False)`, `semua(batas, mulai)`, `jumlah()`, `cari(kata_kunci)`, `tambah(mhs)`, `ubah(mhs)`, `hapus(nim)`, `jumlah_transaksi_aktif(nim)`, `punya_riwayat(nim)`, `set_status_aktif(nim, status)` |
| `RepoAlat` | `ambil(kode, kunci=False)`, `semua(batas, mulai)`, `jumlah()`, `cari(kata_kunci)`, `per_status(status)`, `rusak()`, `daftar_kategori()`, `kategori_sama(kategori)`, `tambah(alat)`, `ubah(alat)`, `set_status(kode, status, kondisi=None)`, `hapus(kode)`, `punya_riwayat(kode)`, `dalam_transaksi_aktif(kode)` |
| `RepoTransaksi` | `ambil(id, kunci=False)` (header dan detail), `semua(batas, mulai)`, `jumlah()`, `aktif_milik(nim)`, `riwayat(nim)`, `aktif_untuk_alat(kode)`, `id_baru()`, `tambah(transaksi)` (header dan semua detail), `kembalikan_detail(id, kode, kondisi, tanggal)` (jumlah baris berubah), `set_status(id, status)` |
| `RepoLaporan` | `alat_terbanyak(n)`, `mahasiswa_terbanyak(n)`, `jumlah_per_status()`, `terlambat(tanggal)` |
| `RepoLog` | `catat(petugas, aksi, keterangan)`, `terakhir(n)` |

## 4. Method manager yang dipanggil menu

### ManagerDasar (class dasar ManagerMahasiswa dan ManagerAlat)

| Method | Keterangan |
|---|---|
| `ambil(kunci)`, `ada(kunci)` | objek (atau `ValueError` bila tidak ada) dan pemeriksaan keberadaan |
| `semua(batas=None, mulai=0)`, `jumlah()` | daftar urut kunci per halaman, dan jumlah seluruh data |
| `_buat_repo(db)` | wajib diisi subclass (repository tabelnya) |

### ManagerMahasiswa

| Method | Keterangan |
|---|---|
| `tambah(nim, nama, no_hp='')` | mengembalikan `Mahasiswa`; tolak NIM ganda |
| `edit(nim, nama=None, no_hp=None)` | `None` berarti tidak diubah; `no_hp='-'` mengosongkan nomor; `status_aktif` diatur otomatis |
| `hapus(nim)` | tolak bila punya transaksi aktif (Aturan 6) atau tercatat di riwayat (Aturan 8) |
| `cari_berdasarkan_nim(nim)` | objek atau `None` |
| `cari(kata_kunci)` | list `Mahasiswa` (NIM atau nama, `LIKE`) |

### ManagerAlat

| Method | Keterangan |
|---|---|
| `tambah(kode, nama, kategori, kondisi='baik')` | kategori baru diterima dan disimpan dengan huruf kecil; bila sama dengan kategori yang sudah ada (beda huruf besar/kecil), ejaan yang sudah ada dipakai; tolak kode ganda |
| `edit(kode, nama=None, kategori=None, kondisi=None)` | status menyesuaikan kondisi kecuali alat sedang dipinjam |
| `hapus(kode)` | tolak bila sedang dipinjam (Aturan 6) atau tercatat di riwayat (Aturan 8) |
| `cari_berdasarkan_kode(kode)` | objek atau `None` |
| `cari(kata_kunci)` | Tantangan A: kode, sebagian nama, atau kategori; kode yang persis sama ditampilkan pertama |
| `tersedia()`, `dipinjam()`, `tidak_tersedia()`, `rusak()`, `daftar_kategori()` | list hasil query `WHERE` |

### ManagerTransaksi

| Method | Keterangan |
|---|---|
| `buat(nim, daftar_kode_alat)` | mengembalikan `Transaksi`. Dalam satu transaction: kunci mahasiswa, periksa maksimal 2 transaksi aktif (Aturan 2), kunci dan periksa setiap alat (Aturan 1), INSERT header dan detail (Aturan 3), ubah status alat dan `status_aktif`. Batas kembali 7 hari. ID diulang bila bertabrakan |
| `ambil(id_transaksi)`, `semua(batas, mulai)`, `jumlah()` | satu transaksi (atau `ValueError`), daftar per halaman, dan jumlah |
| `cari_berdasarkan_mahasiswa(nim)`, `riwayat_mahasiswa(nim)` | transaksi aktif milik NIM, dan semua transaksi milik NIM |
| `transaksi_aktif_alat(kode)`, `punya_transaksi_aktif(nim)` | transaksi yang sedang memegang alat (atau `None`), dan bool |

### ManagerPengembalian

| Method | Keterangan |
|---|---|
| `daftar_belum_kembali(id_transaksi)` | list detail yang masih `dipinjam` |
| `hari_terlambat(transaksi, tanggal=None)` | jumlah hari melewati `batas_kembali` (0 bila tepat waktu) |
| `kembalikan(id_transaksi, kode_alat, kondisi)` | satu alat per panggilan, dalam satu transaction: kunci transaksi dan alat, catat kondisi dan tanggal, status alat lewat `Alat.tandai_dikembalikan` (Aturan 5), status transaksi (Aturan 4), dan `status_aktif` mahasiswa; keterlambatan dicatat di log; mengembalikan `Transaksi` |

### ManagerLaporan (Tantangan B, F, G)

| Method | Keterangan |
|---|---|
| `statistik()`, `baris_statistik()` | dict jumlah transaksi total/aktif/selesai dan lima alat serta mahasiswa terbanyak; versi baris teks |
| `terlambat(tanggal=None)`, `baris_terlambat(tanggal=None)` | transaksi aktif yang melewati batas kembali beserta jumlah hari |
| `ekspor_alat_dipinjam()`, `ekspor_alat_rusak()`, `ekspor_riwayat_mahasiswa(nim)`, `ekspor_statistik()` | menulis `laporan/*.txt` lewat `FileManager.tulis_teks`, mencatat log, mengembalikan path file |

### Logger

| Method | Keterangan |
|---|---|
| `catat(keterangan, aksi='info')` | INSERT ke `log_aktivitas` dengan nama petugas; bila gagal hanya menampilkan peringatan dan mengembalikan `False` |
| `baca_terakhir(jumlah=20)` | list teks `[waktu] petugas \| aksi \| keterangan`, urut lama ke baru |

## 5. Fitur yang ditangani menu sendiri

Tampilan menu, pembacaan input, konfirmasi hapus, pemisahan input kode alat berkoma, pilihan kondisi, tampilan daftar per
halaman (20 baris, setiap halaman diambil dengan `LIMIT`/`OFFSET`), pesan `(data kosong)`, pesan koneksi gagal saat
mulai, dan penutupan koneksi saat keluar.
