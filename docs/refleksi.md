# Refleksi dan Rencana Perbaikan Solusi

Jawaban di bawah menjawab pertanyaan refleksi panduan bagian 10.3 untuk versi database MySQL. Isinya **draf dari
analisis kode akhir** (lihat `docs/final/UML_Final_Implementasi_Kelompok2.png` dan `database/schema.sql`); bagian
bertanda `[ISI]` dilengkapi tim setelah diskusi dan cross-group code review. Temuan dari kelompok lain dicatat di
`docs/cross_group_review.md` bagian 7. Refleksi versi `.txt` ada di repository lama (https://github.com/ariftronic/Kelompok2PraktikumPemrogramanDasarGroupProject2).

## 1. Apa kelemahan utama rancangan kelompok?

- **Status turunan tetap disimpan.** `alat.status`, `transaksi.status`, dan `mahasiswa.status_aktif` dapat dihitung dari
  `detail_transaksi`, tetapi tetap disimpan agar query daftar alat cukup `WHERE status = ...`. Bila tabel diedit langsung
  lewat phpMyAdmin, nilainya dapat tidak sinkron; program hanya menjaganya saat operasi berjalan lewat program.
- **ID transaksi dibuat program** (`T` + angka terbesar + 1), bukan `AUTO_INCREMENT`. Ini dipertahankan agar sama dengan
  data lama, tetapi memerlukan pengulangan bila dua komputer membuat ID yang sama bersamaan.
- **Belum ada hak akses.** Semua anggota memakai satu akun database dari `.env`, dan `NAMA_PETUGAS` dapat diisi apa saja,
  sehingga log aktivitas tidak dapat dipercaya penuh.
- **Pencarian `LIKE '%kata%'`** tidak dapat memakai index biasa, sehingga melambat pada data sangat besar.
- **Penghapusan lebih ketat dari teks Aturan 6.** Mahasiswa dan alat yang pernah tercatat di transaksi tidak dapat
  dihapus sama sekali (Aturan 8). Sistem nyata perlu soft delete.
- **Aturan peminjaman bersifat global** (dua transaksi aktif, tujuh hari) dan belum ada denda.
- [ISI: kelemahan lain menurut tim atau hasil review]

## 2. Bagian apa yang pertama diperbaiki jika menjadi sistem nyata?

1. **Hak akses:** login petugas (atau akun database per petugas dengan hak terbatas), sehingga log mencatat orang yang
   benar dan mahasiswa tidak dapat mengubah data sendiri.
2. **Cadangan data:** ekspor dan pemulihan rutin (Tantangan E), karena data sekarang hanya ada di satu server.
3. **Kebijakan peminjaman dan denda** dalam satu objek atau tabel, sehingga dapat berbeda per jenis pengguna.
4. [ISI: pilihan dan urutan menurut tim]

## 3. Adakah class dengan terlalu banyak tanggung jawab?

- **`AplikasiPeminjaman`** (`menu.py`) berisi seluruh alur menu (lebih dari 30 method). Setiap method pendek dan tanpa
  SQL atau aturan bisnis, tetapi class ini dapat dipecah per submenu.
- **`ManagerLaporan`** memakai empat repository, menyusun teks tabel, dan menulis file. Penyusunan teks laporan dapat
  dipisah dari pengambilan data.
- **`ManagerTransaksi`** menjadi jauh lebih kecil dibanding versi `.txt` (penyelarasan status dan pemulihan file hilang
  karena digantikan transaction), sehingga sekarang tanggung jawabnya cukup satu: membuat transaksi.
- [ISI: pendapat tim atau temuan review]

## 4. Seberapa banyak kode yang harus diubah saat migrasi dari `.txt` ke MySQL? Apa artinya bagi desain awal?

Diukur dengan `git diff --numstat` pada folder `app/`, antara kode versi `.txt` terakhir dan kode versi MySQL
(diukur sebelum proyek dipindah ke repository baru):

| Bagian | Baris ditambah | Baris dihapus | Keterangan |
|---|---|---|---|
| Baru: `config.py`, `database.py`, `repository/*` | 453 | 0 | lapisan database |
| Manager (6 file) | 257 | 451 | `muat`/`simpan`, `_selaraskan`, pemulihan file, dan dictionary di memori diganti panggilan repository dan transaction |
| `file_manager.py` | 26 | 137 | dipersempit menjadi penulis laporan dan pembaca `.txt` lama |
| `menu.py` | 77 | 62 | dari 358 baris: koneksi saat mulai, pesan error database, daftar per halaman dengan `LIMIT`, menu 14, keluar tanpa menyimpan ulang |
| Model (3 file) | 29 | 0 | hanya menambah `dari_dict()`; `dari_baris()` tetap untuk migrasi |
| `logger.py`, `konstanta.py`, `validasi.py` | 33 | 29 | log ke tabel, konstanta koneksi, batasan `\|` dihapus |

Artinya:

- **Yang terbukti baik:** model dan aturan bisnis hampir tidak berubah, dan nama method manager yang dipanggil menu
  (`tambah`, `edit`, `hapus`, `cari`, `buat`, `kembalikan`, `ekspor_*`) tetap sama. Ini hasil dari keputusan awal bahwa
  menu tidak membaca file dan model tidak tahu cara penyimpanan.
- **Yang kurang baik:** satu pintu I/O di desain awal hanya berlaku untuk *membuka file*. Manager tetap memegang seluruh
  data di dictionary dan memutuskan kapan menyimpan, sehingga hampir separuh kode manager harus ditulis ulang. Bila
  manager sejak awal memanggil antarmuka penyimpanan per operasi (seperti repository sekarang), migrasi cukup mengganti
  isi repository.
- `menu.py` ikut berubah sekitar seperlima barisnya, terutama karena daftar per halaman sekarang diambil per halaman dari
  database, bukan dipotong dari list.
- [ISI: pendapat tim]

## 5. Apakah desain tabel dan constraint sudah tepat?

Yang sudah dijaga database: PK di setiap tabel (termasuk PK gabungan `detail_transaksi` agar satu alat tidak dua kali di
transaksi yang sama), FK `RESTRICT` untuk Aturan 8, `NOT NULL` kecuali kolom yang memang boleh kosong, `ENUM` untuk
status dan kondisi, CHECK `batas_kembali >= tgl_pinjam`, CHECK konsistensi detail (`dipinjam` berarti kondisi dan
tanggal kembali kosong), dan index pada kolom yang dipakai `WHERE`.

Yang belum atau sengaja tidak dijaga database:

- tanggal kembali tidak diperiksa terhadap tanggal pinjam (kolomnya berada di tabel berbeda, tidak dapat dengan CHECK);
- aturan "maksimal dua transaksi aktif" dan "alat tidak tersedia tidak dapat dipinjam" hanya dijaga program (dengan
  `FOR UPDATE`), karena tidak dapat dinyatakan sebagai constraint biasa;
- kategori berupa teks bebas, sehingga salah ketik (misalnya `multimedia` dan `multi media`) menjadi dua kategori; tabel
  `kategori` dengan FK akan mencegahnya;
- format nomor HP hanya diperiksa program.

[ISI: pendapat tim, misalnya apakah perlu tabel kategori atau kolom `dihapus` untuk soft delete]

## 6. Apa kelebihan dan kekurangan database online dibanding text file yang dipakai sebelumnya?

| | Text file (versi sebelumnya) | Database online |
|---|---|---|
| Kelebihan | tanpa instalasi dan tanpa internet; isi dapat dibaca dan diedit langsung; mudah disalin | data bersama untuk semua anggota (Skenario 8); transaction COMMIT/ROLLBACK; PK/FK/CHECK dijaga server; query terfilter dan index; penguncian baris untuk akses bersamaan; program tidak perlu memuat semua data di awal |
| Kekurangan | setiap perubahan menulis ulang seluruh file; tidak ada transaction antarfile; dua program pada folder yang sama dapat saling menimpa; integritas rujukan diperiksa sendiri | butuh internet (Skenario 9); perlu akun, password, dan sertifikat SSL yang harus dijaga agar tidak bocor; layanan gratis dapat tidur atau dibatasi; latensi jaringan pada setiap query; isi tidak dapat diperiksa tanpa alat bantu |

[ISI: pengalaman tim saat memakai database online, misalnya waktu respon atau kendala koneksi]

## 7. Adakah duplikasi kode?

- `ambil`, `semua`, dan `jumlah` di `RepoMahasiswa`, `RepoAlat`, dan `RepoTransaksi` memiliki pola SQL yang sama (beda
  nama tabel dan kolom kunci). Bagian yang benar-benar sama (LIKE, `LIMIT/OFFSET`, `FOR UPDATE`) sudah dipindah ke
  `RepoDasar`.
- Normalisasi kunci (`rapikan(...).upper()`) ada di `ManagerDasar`, `ManagerTransaksi`, dan `ManagerPengembalian`.
- Pemetaan `DatabaseError` 1062/1451 menjadi `ValueError` ditulis serupa di `ManagerMahasiswa` dan `ManagerAlat`.
- Method menu memiliki pola mirip (baca input, panggil manager, cetak hasil).
- [ISI: duplikasi lain yang ditemukan review]

## 8. Bagaimana desain class diperbaiki agar lebih scalable?

1. **Repository generik**: `RepoDasar` menerima nama tabel dan kolom kunci sehingga `ambil`, `semua`, `jumlah`, dan
   `hapus` tidak ditulis di setiap repository.
2. **Objek kebijakan peminjaman** (`maks_aktif`, `maks_hari`, `denda_per_hari`) per jenis pengguna; jenis pengguna baru
   cukup menjadi data atau class turunan.
3. **Pencarian teks** dengan index FULLTEXT bila data alat sangat banyak.
4. **Status turunan dihitung oleh database** (VIEW atau query `JOIN`) agar tidak dapat tidak sinkron.
5. **Pemecahan `AplikasiPeminjaman`** per submenu, dan lapisan manager yang sama dapat dipakai antarmuka lain (web/GUI).
6. [ISI: usulan tim]

## 9. Perubahan apa yang dilakukan setelah menerima hasil code review?

Perubahan setelah cross-group code review versi MySQL:

| Temuan dari kelompok lain | Perubahan | Status |
|---|---|---|
| [ISI] | [ISI] | [ISI] |

Perubahan dari code review internal versi `.txt` (rincian di `docs/code_review.md`) yang masih berlaku di versi MySQL:
tanggal harus persis `YYYY-MM-DD`, status alat diatur lewat method model, class dasar `ManagerDasar`, daftar panjang
ditampilkan per halaman, Tantangan B dan F, docstring pada semua class dan method publik, dan skenario wajib dijalankan
lewat `main.py` sungguhan. Temuan versi `.txt` tentang file (F1, F2, K1) tidak lagi relevan karena penyimpanan file
digantikan transaction database.

## Rencana Perbaikan

| Prioritas | Rencana | Alasan |
|---|---|---|
| 1 | Menindaklanjuti temuan cross-group code review | masukan dari pengguna di luar kelompok |
| 2 | Mengonfirmasi ke asisten tafsiran Aturan 6 (lebih ketat) dan status aktif mahasiswa otomatis | keduanya tafsiran kelompok terhadap soal |
| 3 | Login petugas atau akun database per petugas | log aktivitas dapat dipercaya, data terlindungi |
| 4 | Backup dan restore (Tantangan E) | data hanya tersimpan di satu server |
| 5 | Objek kebijakan peminjaman dan denda keterlambatan | kebutuhan baru yang paling mungkin muncul |
| 6 | Soft delete dan tabel kategori | data lama dapat disembunyikan; kategori tidak ganda karena salah ketik |
| [ISI] | [ISI] | [ISI] |
