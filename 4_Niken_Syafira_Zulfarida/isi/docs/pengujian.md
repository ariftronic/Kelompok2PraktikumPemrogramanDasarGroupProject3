# Dokumen Hasil Pengujian

**Proyek II Praktikum Pemrograman Dasar**
Sistem Pengelolaan Peminjaman Peralatan Laboratorium (versi database MySQL)

| Item | Isian |
|---|---|
| Penguji utama QA manual | Niken Syafira Zulfarida |
| Tanggal QA manual | 24 November 2026 |
| Versi program saat QA manual (commit) |  |
| Lingkungan QA manual (laptop A) | [ISI: OS, versi Python, XAMPP/MariaDB atau MySQL online] |
| Lingkungan QA manual (laptop B, Skenario 8) | Windows 10, Python 3.12, XAMPP (MariaDB 10.4) |
| Pengujian otomatis | 19 November 2026; Python 3.13 dan 3.8, Linux; MariaDB 10.11 (kompatibel dengan MariaDB 10.4 XAMPP) |

> Hasil eksekusi `python main.py` berskrip untuk kesepuluh skenario (layar program dan isi tabel) ada di
> `docs/bukti_eksekusi_skenario.md`, dibuat oleh `python tests/skenario_wajib.py`. Kolom "QA manual" di bawah diisi
> tim setelah menguji sendiri di XAMPP dan di database online, beserta tangkapan layarnya.
>
> Hasil pengujian versi `.txt` (9 skenario, 12 dan 18 November 2026) ada di repository lama (https://github.com/ariftronic/Kelompok2PraktikumPemrogramanDasarGroupProject2).

## 1. Persiapan Pengujian

- [ ] `pip install -r requirements.txt` berhasil di setiap laptop penguji.
- [v] `.env` terisi dan `python main.py` menampilkan `Terhubung ke database ...`.
- [v] Database uji dikosongkan lebih dulu, misalnya `python scripts/migrate_txt.py --sumber data_sampel --kosongkan`
      lalu hapus data yang tidak diperlukan, atau buat database baru dengan nama lain di `DB_NAME`.
- [ ] Untuk Skenario 8: dua laptop memakai `.env` yang sama yang menunjuk database online; `ca.pem` tersedia di kedua laptop.
- [v] phpMyAdmin (XAMPP) atau console database online terbuka untuk memeriksa isi tabel.

## 2. Ringkasan Hasil

| No | Skenario | Aturan / ketentuan | Eksekusi otomatis (19 Nov) | QA manual |
|----|----------|--------------------|----------------------------|-----------|
| 1 | Tambah beberapa mahasiswa dan alat | Menu 1, 2 | Lulus | 
| 2 | Satu mahasiswa pinjam beberapa alat dalam satu transaksi | Aturan 3, transaction | Lulus |
| 3 | Pinjam alat yang tidak tersedia | Aturan 1, 2, 7 | [ISI] |
| 4 | Kembalikan sebagian alat | Aturan 4 | Lulus |
| 5 | Alat kembali rusak ringan/berat | Aturan 5 | [ISI] |
| 6 | Hapus mahasiswa yang punya transaksi aktif | Aturan 6, 8 |  [ISI] |
| 7 | Tutup lalu jalankan ulang program | Aturan 7, 8 | [ISI] |
| 8 | Data anggota A terlihat oleh anggota B di komputer lain | database bersama | Lulus (dua proses, satu komputer) | [ISI: dua laptop, database online] |
| 9 | Internet mati / password salah di `.env` | koneksi gagal | [ISI] |
| 10 | NIM yang sudah ada / input berisi tanda kutip `'` | constraint, parameterized query | Lulus |

## 3. Detail Skenario

Data uji di bawah sama dengan yang dipakai `tests/skenario_wajib.py`; skenario dijalankan berurutan pada database yang
sama. Tanggal pinjam mengikuti tanggal pengujian (ditulis `<hari ini>`).

### Skenario 1: Tambah beberapa mahasiswa dan alat

**Langkah:** menu 1 → tambah M001 Andi Pratama (081234567890), M002 Budi Santoso (085612345678), M003 Citra Lestari (no. HP
dikosongkan); menu 2 → tambah A001 Kamera Digital, A002 Tripod, A005 Kabel HDMI (`perangkat multimedia`), A003 Kabel LAN
(`perangkat jaringan`), A004 Laptop (kategori baru `perangkat komputasi`). Periksa `SELECT * FROM mahasiswa;` dan
`SELECT * FROM alat;`.

**Hasil yang diharapkan:** 3 baris di `mahasiswa` (no. HP M003 `NULL`, `status_aktif` `tidak aktif`), 5 baris di `alat`
berstatus `tersedia`; kategori baru diterima tanpa mengubah kode.

**Hasil otomatis:** 8 pesan `[OK]`; isi tabel sesuai harapan. **Lulus.**
**QA manual:** [ISI: hasil dan nama file tangkapan layar]

### Skenario 2: Satu mahasiswa meminjam beberapa alat dalam satu transaksi

**Langkah:** menu 3 → NIM `M001`, kode `A001, A002, A003`; menu 8; periksa tabel `transaksi`, `detail_transaksi`, `alat`.

**Hasil yang diharapkan:** transaksi `T001` (`M001`, `<hari ini>`, batas 7 hari kemudian, `dipinjam`); 3 baris
`detail_transaksi` berstatus `dipinjam` dengan kondisi dan tanggal kembali `NULL`; A001 sampai A003 berstatus
`dipinjam`; `status_aktif` M001 menjadi `aktif`. Semua perubahan terjadi dalam satu transaction.

**Hasil otomatis:** sesuai harapan, menu 8 menampilkan 3 alat. **Lulus.**
**QA manual:** [ISI]

### Skenario 3: Meminjam alat yang tidak tersedia

**Langkah:** (a) M002 meminjam A001 (sedang dipinjam); (b) M002 meminjam `A004, A001`; (c) NIM `M999` meminjam A004.
Bandingkan isi keempat tabel sebelum dan sesudah. Tambahan Aturan 2: M001 membuat transaksi kedua (A004), lalu ketiga (A005).

**Hasil yang diharapkan:** ketiga percobaan `[DITOLAK]` dengan alasan yang jelas; pada (b) A004 juga tidak ikut
berubah (seluruh transaksi dibatalkan); isi tabel identik. Transaksi kedua M001 diterima, ketiga ditolak karena sudah
ada 2 transaksi aktif.

**Hasil otomatis:** 3 penolakan; isi `mahasiswa`, `alat`, `transaksi`, `detail_transaksi` identik sebelum dan sesudah;
transaksi kedua `T002` diterima, ketiga ditolak. **Lulus.**
**QA manual:** [ISI]

### Skenario 4: Mengembalikan sebagian alat

**Langkah:** menu 5 → `T001`, kembalikan hanya `A001`, kondisi `baik`; menu 7 dan 8.

**Hasil yang diharapkan:** T001 `sebagian dikembalikan`; detail A001 `dikembalikan`, `baik`, `<hari ini>`; A001
`tersedia`; A002 dan A003 masih `dipinjam` dan tampil di menu 8.

**Hasil otomatis:** sesuai harapan. **Lulus.**
**QA manual:** [ISI]

### Skenario 5: Alat kembali dalam kondisi rusak ringan dan rusak berat

**Langkah:** menu 5 → `T001`, kembalikan `A002, A003`, kondisi A002 `rusak ringan` dan A003 `rusak berat`; menu 7 dan 9.

**Hasil yang diharapkan:** A002 dan A003 berstatus `tidak tersedia` dengan kondisi sesuai input, tidak tampil di menu 7,
tampil di menu 9; T001 menjadi `selesai`.

**Hasil otomatis:** sesuai harapan. **Lulus.**
**QA manual:** [ISI]

### Skenario 6: Menghapus mahasiswa yang masih punya transaksi aktif

**Langkah:** menu 1 → hapus `M001` (masih memiliki T002); menu 2 → hapus `A004` (sedang dipinjam); sebagai pembanding,
tambah `M009` lalu hapus.

**Hasil yang diharapkan:** hapus M001 dan A004 `[DITOLAK]`; M009 berhasil dihapus; isi tabel lain tidak berubah.

**Hasil otomatis:** sesuai harapan; keempat tabel identik sebelum dan sesudah. **Lulus.**
**QA manual:** [ISI]

### Skenario 7: Tutup lalu jalankan ulang program

**Langkah:** M003 meminjam `A001, A005` (T003), lalu A001 dikembalikan sehingga T003 `sebagian dikembalikan`. Pilih
menu 0, jalankan ulang `python main.py`, buka menu 4. Ulangi beberapa kali.

**Hasil yang diharapkan:** T001 `selesai`, T002 `dipinjam`, T003 `sebagian dikembalikan` dengan status setiap alat tetap
benar; tidak ada data ganda.

**Hasil otomatis:** program dijalankan ulang 3 kali; isi keempat tabel identik. **Lulus.**
**QA manual:** [ISI]

### Skenario 8: Data anggota A terlihat oleh anggota B di komputer lain

**Langkah (manual, wajib):** laptop A dan laptop B memakai `.env` yang sama yang menunjuk database online, dengan
`NAMA_PETUGAS` masing-masing. Anggota A menambah mahasiswa `M010` (atau data lain). Anggota B menjalankan
`python main.py` di laptopnya, lalu menu 1 → cari `M010` dan menu 11 (log aktivitas).

**Hasil yang diharapkan:** B langsung melihat M010 tanpa menyalin file apa pun; log menampilkan nama petugas A.

**Hasil otomatis (simulasi):** dua proses `main.py` terpisah dengan koneksi database berbeda di satu komputer; proses B
langsung menemukan M010 dan log mencatat `Anggota A | tambah mahasiswa`. Tes `tests/test_transaksi.py` kelas
`UjiDuaKlien` juga memeriksa bahwa dua klien yang meminjam alat yang sama bersamaan tidak lolos keduanya. **Lulus.**

**QA manual dengan dua laptop:**

| Langkah | Laptop A ([ISI: nama anggota]) | Laptop B ([ISI: nama anggota]) |
|---|---|---|
| Data yang ditambah / dicari | [ISI] | [ISI] |
| Hasil yang terlihat | [ISI] | [ISI] |
| Tangkapan layar | [ISI] | [ISI] |

**Status QA manual:** [ISI]

### Skenario 9: Internet mati atau password salah di `.env`

**Langkah:** (a) ubah `DB_PASSWORD` di `.env` menjadi salah, jalankan program; (b) kembalikan password, lalu matikan
MySQL di XAMPP (atau putuskan internet untuk database online), jalankan program; (c) [opsional] matikan MySQL saat
program sedang berjalan lalu pilih menu apa pun.

**Hasil yang diharapkan:** muncul `[!] Koneksi database gagal: ...` dengan penyebab yang dapat dipahami (login ditolak /
tidak dapat terhubung), program berhenti rapi tanpa traceback, data tidak berubah. Untuk (c): muncul
`[!] [ERROR DATABASE] ...`, program tetap di menu, dan saat server menyala lagi koneksi disambung ulang otomatis.

**Hasil otomatis:** (a) `Login database ditolak. Periksa DB_USER dan DB_PASSWORD di .env.`; (b) `Tidak dapat terhubung ke
database. Pastikan MySQL di XAMPP menyala ...`; tanpa traceback, menu tidak ditampilkan, isi tabel tidak berubah.
Kondisi (c) diperiksa `tests/test_menu.py` (`test_error_database_di_tengah_sesi_tidak_menghentikan_program`,
`test_koneksi_yang_diputus_server_disambung_ulang_otomatis`). **Lulus.**
**QA manual:** [ISI]

### Skenario 10: NIM yang sudah ada dan input berisi tanda kutip

**Langkah:** menu 1 → tambah `M001` lagi; tambah `M011` dengan nama `Siti O'Neil`; tambah `M012` dengan nama
`x'); DROP TABLE mahasiswa; --`; cari `o'neil`.

**Hasil yang diharapkan:** NIM ganda ditolak dengan `[DITOLAK] NIM M001 sudah terdaftar.`, tanpa pesan SQL mentah; nama
bertanda kutip tersimpan utuh dan dapat dicari; teks injeksi tersimpan sebagai data biasa dan tabel `mahasiswa` tetap
ada; data M001 lama tidak berubah.

**Hasil otomatis:** sesuai harapan. **Lulus.**
**QA manual:** [ISI]

## 4. Temuan Selama Pengembangan dan Pengujian

Temuan (nomor 1 dan 2) dan risiko yang sengaja diuji (nomor 3 dan 4) saat mengembangkan versi MySQL, beserta penanganannya:

| No | Temuan / risiko | Dampak | Penanganan |
|---|---|---|---|
| 1 | Dengan `autocommit=False`, koneksi yang hanya membaca tetap melihat snapshot lama | data yang ditambah anggota lain tidak terlihat sampai program ditutup (Skenario 8 gagal) | koneksi memakai `autocommit=True`; operasi beberapa tabel memakai `BEGIN` eksplisit lewat `db.transaksi()` |
| 2 | Pada `sql_mode` bawaan MariaDB tertentu, nilai ENUM yang salah disimpan sebagai string kosong dengan peringatan saja | data tidak valid dapat masuk tanpa error | setiap sesi menjalankan `SET SESSION sql_mode` ketat (`STRICT_ALL_TABLES`, ...) |
| 3 | Dua klien yang membuat transaksi bersamaan dapat menghitung ID baru yang sama | INSERT kedua gagal (1062) | ID dibuat di dalam transaction dan pembuatan diulang maksimal 3 kali bila bertabrakan |
| 4 | Dua klien yang meminjam alat yang sama bersamaan | tanpa penguncian, keduanya dapat lolos pemeriksaan | `SELECT ... FOR UPDATE` pada mahasiswa dan alat; klien kedua menunggu lalu ditolak |

Bug yang ditemukan saat QA manual:

| No | Skenario | Deskripsi bug | Penyebab | Status | Diperbaiki oleh |
|---|---|---|---|---|---|
| [ISI] | | | | | |

## 5. Pengujian Silang (Setiap Anggota Menguji Modul Anggota Lain)

| Penguji | Modul yang diuji | Hasil / temuan |
|---|---|---|
| [ISI] | [ISI] | [ISI] |

## 6. Hasil Pengujian Otomatis

Perintah: `python -m unittest -v`. Tes database memakai database terpisah `<DB_NAME>_test` dan dikosongkan sebelum setiap
tes. Hasil 19 November 2026: **60 tes, semuanya lulus** di Python 3.13 dan Python 3.8 (MariaDB 10.11). Tanpa server
database: 18 tes non-database lulus dan tes database dilewati (`skipped`).

| File | Jumlah tes | Yang diuji |
|---|---|---|
| `tests/test_tanpa_db.py` | 18 | validasi input, model (`dari_dict`, status turunan), konfigurasi `.env`, terjemahan kode error, escape `LIKE` dan placeholder, FileManager laporan dan pembacaan `.txt` lama |
| `tests/test_mahasiswa_alat.py` | 14 | CRUD tersimpan di tabel dan log, `NULL` untuk no. HP kosong, NIM/kode ganda ditolak tanpa perubahan, tanda kutip dan upaya injeksi, pencarian per kata dan per halaman, penolakan hapus (Aturan 6 dan 8) |
| `tests/test_transaksi.py` | 8 | satu transaksi beberapa alat, penolakan tanpa perubahan, maksimal 2 transaksi aktif, ROLLBACK bila gagal di tengah, ID urut dan diulang bila bentrok, data klien lain langsung terlihat, alat yang dikunci klien lain tidak dapat dipinjam ganda |
| `tests/test_pengembalian.py` | 6 | pengembalian sebagian, alat rusak tidak tersedia, input tidak valid tanpa perubahan, ROLLBACK bila gagal di tengah, data tetap ada di koneksi baru, keterlambatan di log |
| `tests/test_laporan.py` | 4 | statistik kosong dan `GROUP BY`, transaksi terlambat, ekspor empat laporan |
| `tests/test_migrasi.py` | 3 | data sampel pindah utuh, baris rusak dilewati dan status diselaraskan, folder sumber tidak ada |
| `tests/test_menu.py` | 7 | alur menu lengkap, penolakan tampil tanpa perubahan, koneksi gagal saat mulai, error database di tengah sesi, sambung ulang otomatis, daftar per halaman, input berhenti di tengah |

Skrip `python tests/skenario_wajib.py` menjalankan 10 skenario wajib lewat `main.py` sungguhan (50 pemeriksaan otomatis,
semuanya lulus pada 19 November 2026).

## 7. Kesimpulan

Hasil pengujian otomatis: kesepuluh skenario wajib dan 60 tes otomatis lulus. Hal yang masih harus dibuktikan tim secara
manual: Skenario 8 dengan dua laptop dan database online, serta QA manual dengan tangkapan layar untuk skenario lainnya.

[ISI: kesimpulan tim setelah QA manual]
