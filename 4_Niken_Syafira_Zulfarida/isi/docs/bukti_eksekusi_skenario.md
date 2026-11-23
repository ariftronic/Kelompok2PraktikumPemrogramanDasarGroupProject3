# Bukti Eksekusi Skenario Pengujian Wajib

Dokumen ini berisi hasil menjalankan **`python main.py` sungguhan** untuk 10 skenario wajib terhadap database MySQL. Masukan keyboard diberikan lewat stdin, jadi layar dan isi tabel di bawah adalah keluaran program yang sebenarnya.

| Item | Isian |
|---|---|
| Tanggal eksekusi | 2026-11-19 |
| Lingkungan | Python 3.13.18, Linux; server database 10.11.14-MariaDB-0ubuntu0.24.04.1 |
| Database | `peminjaman_lab_skenario` (dibuat ulang setiap kali skrip dijalankan; database utama tidak disentuh) |
| Cara mengulang | `python tests/skenario_wajib.py` dari folder proyek (menulis ulang dokumen ini) |

Skenario 1 sampai 10 dijalankan berurutan pada database yang sama. Tanggal pinjam pada contoh sama dengan tanggal eksekusi.

**Yang tidak dicakup dokumen ini:** Skenario 8 dengan dua laptop sungguhan dan database online, tangkapan layar QA manual (`docs/pengujian.md`), serta review kelompok lain (`docs/cross_group_review.md`).

## Ringkasan

| No | Skenario | Jumlah pemeriksaan | Hasil |
|---|---|---|---|
| 1 | Tambah mahasiswa dan alat | 5 | LULUS |
| 2 | Peminjaman beberapa alat dalam satu transaksi | 6 | LULUS |
| 3 | Meminjam alat yang tidak tersedia | 5 | LULUS |
| 4 | Pengembalian sebagian | 5 | LULUS |
| 5 | Pengembalian alat rusak | 5 | LULUS |
| 6 | Hapus mahasiswa dengan transaksi aktif | 5 | LULUS |
| 7 | Tutup lalu jalankan ulang (termasuk transaksi sebagian) | 4 | LULUS |
| 8 | Data anggota A terlihat oleh anggota B | 4 | LULUS |
| 9 | Koneksi gagal | 5 | LULUS |
| 10 | NIM ganda dan input bertanda kutip | 6 | LULUS |

---

## Skenario 1: Tambah beberapa mahasiswa dan alat

**Langkah:** menu 1 menambah 3 mahasiswa (M003 tanpa no. HP), menu 2 menambah 5 alat termasuk kategori baru `perangkat komputasi`.

```text
[OK] Mahasiswa berhasil ditambahkan.
[OK] Mahasiswa berhasil ditambahkan.
[OK] Mahasiswa berhasil ditambahkan.
[OK] Alat berhasil ditambahkan.
[OK] Alat berhasil ditambahkan.
[OK] Alat berhasil ditambahkan.
[OK] Alat berhasil ditambahkan.
[OK] Alat berhasil ditambahkan.
```

```text
SELECT * FROM mahasiswa;
M001|Andi Pratama|081234567890|tidak aktif
M002|Budi Santoso|085612345678|tidak aktif
M003|Citra Lestari|NULL|tidak aktif

SELECT * FROM alat;
A001|Kamera Digital|perangkat multimedia|baik|tersedia
A002|Tripod|perangkat multimedia|baik|tersedia
A003|Kabel LAN|perangkat jaringan|baik|tersedia
A004|Laptop|perangkat komputasi|baik|tersedia
A005|Kabel HDMI|perangkat multimedia|baik|tersedia
```

**Pemeriksaan otomatis:**

- [x] ada 8 pesan `[OK]`
- [x] 3 baris di tabel `mahasiswa`, no. HP M003 tersimpan `NULL`
- [x] 5 baris di tabel `alat`, semuanya `tersedia`
- [x] kategori baru diterima tanpa mengubah kode
- [x] program berakhir normal

**Hasil: LULUS**

---

## Skenario 2: Satu mahasiswa meminjam beberapa alat dalam satu transaksi

**Langkah:** M001 meminjam `A001, A002, A003` (menu 3), lalu menu 8.

```text
[OK] Transaksi peminjaman berhasil dibuat.
T001 | M001 | pinjam 2026-11-19 | batas 2026-11-26 | dipinjam
- A001: dipinjam
- A002: dipinjam
- A003: dipinjam

Alat yang sedang dipinjam (3 data)
------------------------------------------------------------
1. A001 | Kamera Digital | kategori: perangkat multimedia | kondisi: baik | status: dipinjam
2. A002 | Tripod | kategori: perangkat multimedia | kondisi: baik | status: dipinjam
3. A003 | Kabel LAN | kategori: perangkat jaringan | kondisi: baik | status: dipinjam
```

```text
SELECT * FROM transaksi;
T001|M001|2026-11-19|2026-11-26|dipinjam

SELECT * FROM detail_transaksi;
T001|A001|dipinjam|NULL|NULL
T001|A002|dipinjam|NULL|NULL
T001|A003|dipinjam|NULL|NULL

SELECT * FROM alat;
A001|Kamera Digital|perangkat multimedia|baik|dipinjam
A002|Tripod|perangkat multimedia|baik|dipinjam
A003|Kabel LAN|perangkat jaringan|baik|dipinjam
A004|Laptop|perangkat komputasi|baik|tersedia
A005|Kabel HDMI|perangkat multimedia|baik|tersedia
```

**Pemeriksaan otomatis:**

- [x] transaksi `T001` milik M001 dengan batas tepat 7 hari
- [x] `detail_transaksi` berisi 3 baris berstatus `dipinjam`
- [x] A001, A002, A003 berstatus `dipinjam` di database
- [x] status aktif M001 menjadi `aktif`
- [x] layar menampilkan 3 alat dipinjam
- [x] program berakhir normal

**Hasil: LULUS**

---

## Skenario 3: Meminjam alat yang tidak tersedia

**Langkah:** (a) M002 meminjam A001 yang sedang dipinjam; (b) M002 meminjam `A004, A001`; (c) NIM `M999` yang tidak terdaftar. Isi keempat tabel dibandingkan sebelum dan sesudah. Tambahan Aturan 2: M001 membuat transaksi kedua lalu ketiga.

```text
[DITOLAK] Alat A001 tidak tersedia (status: dipinjam).
[DITOLAK] Alat A001 tidak tersedia (status: dipinjam).
[DITOLAK] Mahasiswa dengan NIM M999 tidak ditemukan.

perbandingan isi tabel:
mahasiswa         sebelum 3 baris | sesudah 3 baris | identik: True
alat              sebelum 5 baris | sesudah 5 baris | identik: True
transaksi         sebelum 1 baris | sesudah 1 baris | identik: True
detail_transaksi  sebelum 3 baris | sesudah 3 baris | identik: True
```

```text
[OK] Transaksi peminjaman berhasil dibuat.
[DITOLAK] Mahasiswa M001 sudah memiliki 2 transaksi aktif (maksimal 2).
```

**Pemeriksaan otomatis:**

- [x] ketiga percobaan ditolak dengan `[DITOLAK]`
- [x] pesan menyebut alasan (alat tidak tersedia / NIM tidak ditemukan)
- [x] isi keempat tabel identik sebelum dan sesudah
- [x] Aturan 2: transaksi kedua diterima, ketiga ditolak (maksimal 2 aktif)
- [x] program berakhir normal

**Hasil: LULUS**

---

## Skenario 4: Mengembalikan sebagian alat

**Langkah:** T001 berisi A001, A002, A003; hanya A001 dikembalikan dengan kondisi `baik` (menu 5), lalu menu 7 dan 8.

```text
[OK] Alat A001 dikembalikan (baik).
T001 | M001 | pinjam 2026-11-19 | batas 2026-11-26 | sebagian dikembalikan
- A001: dikembalikan (baik, 2026-11-19)
- A002: dipinjam
- A003: dipinjam

Alat yang tersedia (2 data)
------------------------------------------------------------
1. A001 | Kamera Digital | kategori: perangkat multimedia | kondisi: baik | status: tersedia
2. A005 | Kabel HDMI | kategori: perangkat multimedia | kondisi: baik | status: tersedia

Alat yang sedang dipinjam (3 data)
------------------------------------------------------------
1. A002 | Tripod | kategori: perangkat multimedia | kondisi: baik | status: dipinjam
2. A003 | Kabel LAN | kategori: perangkat jaringan | kondisi: baik | status: dipinjam
3. A004 | Laptop | kategori: perangkat komputasi | kondisi: baik | status: dipinjam
```

```text
SELECT * FROM transaksi WHERE id = 'T001';
T001|M001|2026-11-19|2026-11-26|sebagian dikembalikan

SELECT * FROM detail_transaksi WHERE id_transaksi = 'T001';
T001|A001|dikembalikan|baik|2026-11-19
T001|A002|dipinjam|NULL|NULL
T001|A003|dipinjam|NULL|NULL
```

**Pemeriksaan otomatis:**

- [x] status T001 menjadi `sebagian dikembalikan`
- [x] A001 tercatat `dikembalikan|baik|2026-11-19` dan kembali `tersedia`
- [x] A002 dan A003 masih `dipinjam`
- [x] layar: alat yang masih dipinjam di T001 tampil di menu 8
- [x] program berakhir normal

**Hasil: LULUS**

---

## Skenario 5: Alat kembali dalam kondisi rusak ringan dan rusak berat

**Langkah:** sisa alat T001 dikembalikan: A002 `rusak ringan`, A003 `rusak berat`; lalu menu 7 dan 9.

```text
[OK] Alat A002 dikembalikan (rusak ringan).
[OK] Alat A003 dikembalikan (rusak berat).

Alat yang rusak (2 data)
------------------------------------------------------------
1. A002 | Tripod | kategori: perangkat multimedia | kondisi: rusak ringan | status: tidak tersedia
2. A003 | Kabel LAN | kategori: perangkat jaringan | kondisi: rusak berat | status: tidak tersedia
```

```text
SELECT * FROM alat WHERE kode IN ('A002', 'A003');
A002|Tripod|perangkat multimedia|rusak ringan|tidak tersedia
A003|Kabel LAN|perangkat jaringan|rusak berat|tidak tersedia
```

**Pemeriksaan otomatis:**

- [x] A002 dan A003 berstatus `tidak tersedia` dengan kondisi sesuai input
- [x] keduanya tidak muncul di daftar alat tersedia
- [x] keduanya muncul di daftar alat rusak
- [x] T001 menjadi `selesai`
- [x] program berakhir normal

**Hasil: LULUS**

---

## Skenario 6: Menghapus mahasiswa yang masih punya transaksi aktif

**Langkah:** M001 masih memiliki transaksi aktif T002 (A004). Hapus M001 dan alat A004; sebagai pembanding tambah M009 lalu hapus.

```text
[DITOLAK] Mahasiswa M001 masih memiliki transaksi aktif, tidak dapat dihapus.
[DITOLAK] Alat A004 sedang dipinjam (transaksi aktif), tidak dapat dihapus.
[OK] Mahasiswa berhasil ditambahkan.
[OK] Mahasiswa M009 dihapus.
```

**Pemeriksaan otomatis:**

- [x] hapus M001 ditolak karena transaksi aktif
- [x] hapus alat A004 yang sedang dipinjam ditolak
- [x] mahasiswa tanpa transaksi (M009) dapat dihapus
- [x] isi keempat tabel sama dengan sebelum percobaan
- [x] program berakhir normal

**Hasil: LULUS**

---

## Skenario 7: Tutup lalu jalankan ulang program

**Langkah:** M003 meminjam `A001, A005` (T003), A001 dikembalikan sehingga T003 `sebagian dikembalikan`. Program ditutup lalu dijalankan ulang 3 kali (menu 4).

```text
Daftar transaksi (3 data)
------------------------------------------------------------
1. T001 | M001 | pinjam 2026-11-19 | batas 2026-11-26 | selesai
     - A001: dikembalikan (baik, 2026-11-19)
     - A002: dikembalikan (rusak ringan, 2026-11-19)
     - A003: dikembalikan (rusak berat, 2026-11-19)
2. T002 | M001 | pinjam 2026-11-19 | batas 2026-11-26 | dipinjam
     - A004: dipinjam
3. T003 | M003 | pinjam 2026-11-19 | batas 2026-11-26 | sebagian dikembalikan
     - A001: dikembalikan (baik, 2026-11-19)
     - A005: dipinjam
```

```text
mahasiswa         3 baris -> 3 baris | identik: True
alat              5 baris -> 5 baris | identik: True
transaksi         3 baris -> 3 baris | identik: True
detail_transaksi  6 baris -> 6 baris | identik: True
```

**Pemeriksaan otomatis:**

- [x] T003 tersimpan `sebagian dikembalikan`
- [x] setiap jalan ulang menampilkan T001 `selesai`, T002 `dipinjam`, T003 `sebagian dikembalikan`
- [x] isi tabel identik setelah 3 kali jalan ulang (tidak ada data ganda)
- [x] program berakhir normal

**Hasil: LULUS**

---

## Skenario 8: Data yang diinput anggota A terlihat oleh anggota B

**Langkah (otomatis):** dua proses program yang terpisah (dua koneksi database berbeda) memakai database yang sama: proses A menambah M010, lalu proses B mencari M010 dan melihat log aktivitas. Ini mensimulasikan dua komputer.

**Langkah (manual, wajib saat demo):** dua laptop dengan `.env` yang sama menunjuk database online (Aiven). Anggota A menambah data, anggota B menjalankan program di laptopnya lalu menampilkan data tersebut. Simpan tangkapan layar kedua laptop di `docs/pengujian.md`.

```text
# proses A
[OK] Mahasiswa berhasil ditambahkan.

# proses B
Hasil pencarian mahasiswa (1 data)
------------------------------------------------------------
1. M010 | Dian Anggota A | HP: - | peminjaman: tidak aktif
18. [2026-11-19 01:56] Anggota A | tambah mahasiswa | Mahasiswa M010 ditambahkan
```

**Pemeriksaan otomatis:**

- [x] proses A menyimpan M010
- [x] proses B (koneksi lain) langsung menemukan M010
- [x] log mencatat siapa yang menambah (Anggota A)
- [x] program berakhir normal

**Hasil: LULUS**

---

## Skenario 9: Koneksi gagal (password salah / server tidak dapat dihubungi)

**Langkah:** program dijalankan dengan user/password salah, lalu dengan port yang tidak dipakai server (sama seperti MySQL XAMPP dimatikan atau internet terputus untuk database online).

```text
[!] Koneksi database gagal: Login database ditolak. Periksa DB_USER dan DB_PASSWORD di .env.
Program tidak dapat dimulai. Perbaiki pengaturan di .env lalu jalankan ulang program.

[!] Koneksi database gagal: Tidak dapat terhubung ke database. Pastikan MySQL di XAMPP menyala (atau internet tersambung untuk database online) dan DB_HOST/DB_PORT di .env benar.
Program tidak dapat dimulai. Perbaiki pengaturan di .env lalu jalankan ulang program.
```

**Pemeriksaan otomatis:**

- [x] password salah: pesan "Login database ditolak"
- [x] server tidak terjangkau: pesan "Tidak dapat terhubung ke database"
- [x] tidak ada traceback dan kode keluar 0 pada kedua percobaan
- [x] menu tidak ditampilkan (tidak ada operasi tanpa database)
- [x] isi database tidak berubah

**Hasil: LULUS**

---

## Skenario 10: NIM yang sudah ada dan input berisi tanda kutip

**Langkah:** tambah mahasiswa dengan NIM `M001` yang sudah ada, nama `Siti O'Neil`, dan nama berisi upaya SQL injection; lalu cari `o'neil`.

```text
[DITOLAK] NIM M001 sudah terdaftar.
[OK] Mahasiswa berhasil ditambahkan.
M011 | Siti O'Neil | HP: - | peminjaman: tidak aktif
[OK] Mahasiswa berhasil ditambahkan.
M012 | x'); DROP TABLE mahasiswa; -- | HP: - | peminjaman: tidak aktif
M011 | Siti O'Neil | HP: - | peminjaman: tidak aktif
```

```text
SELECT * FROM mahasiswa WHERE nim IN (%s, %s, %s);
M001|Andi Pratama|081234567890|aktif
M011|Siti O'Neil|NULL|tidak aktif
M012|x'); DROP TABLE mahasiswa; --|NULL|tidak aktif
```

**Pemeriksaan otomatis:**

- [x] NIM ganda ditolak dengan pesan ramah
- [x] tidak ada pesan error SQL mentah
- [x] nama `Siti O'Neil` tersimpan utuh dan dapat dicari
- [x] teks upaya injeksi tersimpan sebagai data biasa; tabel mahasiswa tetap ada
- [x] data M001 lama tidak berubah
- [x] program berakhir normal

**Hasil: LULUS**

---
