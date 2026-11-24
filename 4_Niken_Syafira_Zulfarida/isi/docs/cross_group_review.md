# Lembar Cross-Group Code Review

Lembar ini dipakai Kelompok 2 untuk mereview repository kelompok lain sesuai bagian 8.3 panduan (versi database MySQL).
Setiap aspek dikerjakan oleh satu anggota, sama seperti pembagian pada review internal (`docs/code_review.md`), lalu
hasilnya diperiksa bersama sebelum dikumpulkan.

| | |
|---|---|
| Kelompok yang direview | Kelompok ___ |
| URL repository | |
| Commit yang direview | (`git rev-parse --short HEAD` pada salinan yang direview) |
| Tanggal review | |
| Reviewer | Kesesuaian rancangan: Fatimah. Ketepatan solusi: Niken. Pengelolaan database: Arif. Skalabilitas: Faris |
| Lingkungan | versi Python, sistem operasi, dan server database (XAMPP / MySQL online) |

Cara kerja yang disepakati:

1. Clone repository ke folder terpisah. Semua percobaan dijalankan pada **database milik Kelompok 2 sendiri** (XAMPP
   lokal, `DB_NAME` misalnya `review_kelompok_x`) dengan `.env` yang dibuat sendiri dari `.env.example`, bukan pada
   database online kelompok yang direview.
2. Baca README, UML final, ERD, dan `database/schema.sql`, jalankan `schema.sql` dan `seed.sql` (atau cara setup di
   README), lalu jalankan program dan tes bawaannya (bila ada).
3. Jalankan sepuluh skenario wajib (tabel di bagian 2), lalu periksa isi tabel dengan phpMyAdmin atau `SELECT`.
4. Setiap temuan ditulis dengan langkah mengulang dan bukti (keluaran layar atau hasil query), lalu diberi tingkat:
   **Tinggi** = pelanggaran keamanan (SQL injection, password di repository), data hilang, atau aturan bisnis terlanggar;
   **Sedang** = menyulitkan pengembangan atau penggunaan; **Rendah** = perbaikan kecil.
   Urutan pelaporan: aturan dan keamanan, bug, desain/skalabilitas, gaya kode.

## 1. Kesesuaian Rancangan dan Implementasi (Fatimah)

| Pemeriksaan | Hasil | Bukti / keterangan |
|---|---|---|
| Class pada UML benar-benar diimplementasikan | | |
| Atribut sesuai rancangan | | |
| Method sesuai rancangan | | |
| Hubungan antarclass sesuai implementasi | | |
| Tabel, kolom, tipe, PK/FK pada `schema.sql` sesuai ERD dan README | | |
| Kode memakai nama tabel/kolom yang sama dengan `schema.sql` | | |

## 2. Ketepatan Solusi (Niken)

| Pemeriksaan | Hasil | Bukti / keterangan |
|---|---|---|
| Program dapat dijalankan | | |
| Operasi CRUD berfungsi dan hasilnya tersimpan di tabel | | |
| Transaksi peminjaman berjalan benar | | |
| Status ketersediaan alat diperbarui dengan benar | | |
| Pengembalian sebagian dapat diproses | | |
| Aturan bisnis 1 sampai 8 diterapkan | | |

Sepuluh skenario wajib:

| No | Skenario | Hasil (Lulus/Gagal) | Catatan |
|---|---|---|---|
| 1 | Tambah mahasiswa dan alat, periksa tabel | | |
| 2 | Pinjam beberapa alat dalam satu transaksi | | |
| 3 | Pinjam alat yang tidak tersedia (isi database tidak boleh berubah) | | |
| 4 | Pengembalian sebagian | | |
| 5 | Pengembalian rusak ringan atau rusak berat | | |
| 6 | Hapus mahasiswa yang masih punya transaksi aktif | | |
| 7 | Tutup lalu jalankan ulang program | | |
| 8 | Data yang ditambah di satu komputer terlihat di komputer lain (dua anggota reviewer, database yang sama) | | |
| 9 | Password salah di `.env` / MySQL dimatikan | | |
| 10 | NIM yang sudah ada / nama berisi tanda kutip `'` | | |

## 3. Pengelolaan Database (Arif)

| Pemeriksaan | Hasil | Bukti / keterangan |
|---|---|---|
| Satu pintu akses database: `connect()`/`execute()` hanya di satu class atau modul | | `grep -rn "connect(\|execute(" --include=*.py .` |
| Semua query memakai parameter (`%s`), tidak ada f-string, `%`, atau `+` dengan input pengguna | | `grep -rn "execute(f\|f\"SELECT\|f\"INSERT\|f\"UPDATE\|f\"DELETE" --include=*.py .` |
| Operasi beberapa tabel (pinjam, kembali) memakai transaction dengan `commit` dan `rollback` | | |
| Koneksi gagal ditangani: pesan jelas, tidak ada traceback | | |
| Pelanggaran constraint (duplikat, FK) ditangkap dan ditampilkan ramah | | |
| PK, FK, `NOT NULL` dipakai di `schema.sql` | | |
| Tabel belum ada / tabel kosong tidak menyebabkan error | | |
| Password tidak bocor: `.env` ada di `.gitignore`, tidak ada password di kode, README, atau riwayat commit | | `git log --all -p -S "DB_PASSWORD=" -- . ":(exclude).env.example"` |
| Data teks `.txt` tidak lagi dipakai sebagai penyimpanan utama; ada script migrasi | | |

Percobaan tambahan yang disarankan:

- masukkan nama `x'); DROP TABLE mahasiswa; --` dan kata kunci pencarian `%`: apakah tersimpan sebagai teks biasa dan
  pencarian `%` tidak menampilkan semua data?
- matikan MySQL saat program berjalan, pilih menu, lalu nyalakan lagi: apakah program pulih tanpa ditutup?
- pinjam alat yang sama dari dua terminal hampir bersamaan: apakah keduanya lolos?

## 4. Skalabilitas Program (Faris)

Skenario yang dinilai: 10.000 alat dan 20.000 mahasiswa, serta kebutuhan baru (kategori alat baru, jenis pengguna baru,
aturan peminjaman baru, denda keterlambatan).

| Pertanyaan | Jawaban dan bagian kode yang terkait |
|---|---|
| Apakah struktur program cukup mudah dikembangkan untuk kebutuhan baru tersebut? | |
| Apakah query terfilter dengan `WHERE`/`JOIN`/`COUNT`/`LIMIT`, atau seluruh tabel diambil lalu disaring di Python? | |
| Apakah ada query di dalam perulangan (satu query per baris data)? | |
| Apakah kolom yang sering dicari (status alat, NIM di transaksi, kode alat di detail) diberi index? | |
| Apakah daftar panjang ditampilkan per halaman? | |
| Bagian kode yang kemungkinan sulit dipelihara bila sistem berkembang | |

## 5. Daftar Temuan

| No | Aspek | Tingkat | Temuan (dengan langkah mengulang) | Saran perbaikan |
|---|---|---|---|---|
| 1 | | | | |

## 6. Ringkasan untuk Kelompok yang Direview

- Hal yang sudah baik:
- Temuan prioritas:
- Saran utama:

## 7. Hasil Review yang Diterima Kelompok 2

Temuan dari kelompok yang mereview repository Kelompok 2 dicatat di sini, lalu tindak lanjutnya ditulis di
`docs/refleksi.md` (pertanyaan 9).

| No | Temuan dari kelompok lain | Tindak lanjut Kelompok 2 | Status |
|---|---|---|---|
| 1 | | | |
