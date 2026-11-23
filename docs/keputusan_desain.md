# Dokumen Keputusan Desain

> Bagian 1 sampai 7 mencatat keputusan pada **tahap `.txt`** (versi pertama Proyek II) dan dipertahankan sebagai
> riwayat perubahan desain. Keputusan untuk **perpindahan ke MySQL** ada di bagian 8 sampai 11. Class yang disebut di
> bagian 3 dan 6 seperti `muat`/`simpan`, `_selaraskan`, `log.txt`, dan `baris_rusak.txt` sudah tidak ada di kode akhir.

Bahan yang dibandingkan:

- empat UML individu di `docs/individu/` (`UML_Kelompok2-<nama>.png`) dan rancangan format text file setiap anggota;
- UML final hasil diskusi kelompok pada Tahap 1: `docs/final/UML_Final_Rancangan_Kelompok2.png`;
- UML final yang sesuai kode akhir: `docs/final/UML_Final_Implementasi_Kelompok2.png` (sumber `.drawio` di folder yang sama);
- `docs/kontrak_antarmodul.md`, yaitu pembagian tanggung jawab antarmodul yang disepakati agar anggota dapat bekerja paralel.

## 1. Rancangan yang menjadi dasar solusi

Dasar solusi kelompok adalah **rancangan Muhammad Nur Arif**. UML final rancangan kelompok memakai struktur class yang sama
dengan rancangan Arif: `MenuApp`, tiga manager per jenis data (`MahasiswaManager`, `AlatManager`, `TransaksiManager`),
`FileHandler` sebagai satu-satunya akses file, serta model `Mahasiswa`, `Alat`, `Transaksi`, dan `DetailTransaksi`.
Rancangan Fatimah memiliki struktur class yang sama dengan rancangan Arif, dan UML final rancangan kelompok diunggah oleh
Fatimah.

Alasan rancangan ini dipilih:

1. **Satu manager untuk setiap jenis data.** Aturan bisnis setiap data berada di satu tempat, sehingga mudah diuji tanpa menu.
2. **Sesuai pembagian tugas.** Pembagian kerja kelompok mengikuti class: Fatimah mengerjakan data mahasiswa dan alat,
   Faris transaksi, Niken pengembalian, dan Arif file dan menu. Dengan satu manager per bagian, anggota dapat bekerja paralel.
3. **Akses file terpusat.** Semua baca/tulis lewat satu class, sehingga ketentuan "kode baca/tulis file tidak ditulis
   berulang" terpenuhi dan penyimpanan mudah diganti.
4. **Dibanding rancangan Niken**, yang menaruh semua data dan aturan di satu class `PeminjamanService`, rancangan dengan
   beberapa manager membagi tanggung jawab dengan lebih jelas dan tidak menghasilkan satu class yang sangat besar.

Perbandingan keempat rancangan individu dengan UML rancangan kelompok dan implementasi akhir:

| Aspek | Arif | Fatimah | Faris | Niken | Implementasi akhir |
|---|---|---|---|---|---|
| Pemegang data dan aturan bisnis | tiga manager: `MahasiswaManager`, `AlatManager`, `TransaksiManager` | sama dengan Arif | tiga manager dengan nama yang sama | satu class `PeminjamanService` | `ManagerDasar` sebagai class dasar, lalu `ManagerMahasiswa`, `ManagerAlat`, `ManagerTransaksi`, `ManagerPengembalian`, `ManagerLaporan` |
| Class akses file | `FileHandler` (`pastikan_file`, `baca_baris`, `tulis_baris`) | sama dengan Arif | `FileManager` (`pastikan_file_ada`, `baca_data`, `tulis_data`) | `FileManager` dengan daftar peringatan dan `tambah_baris` (mode append) | `FileManager` dan `FileManagerError` |
| Class transaksi | `Transaksi` berisi `DetailTransaksi`; detail tanpa `id_transaksi`, `ke_baris(id_transaksi)` | sama dengan Arif | `Transaksi` berisi `DetailTransaksi` yang menyimpan `id_transaksi` | `TransaksiPeminjaman` berisi `ItemPeminjaman` | `Transaksi` berisi list `DetailTransaksi` yang menyimpan `id_transaksi` |
| Konversi objek dan baris file | `dari_baris`, `ke_baris` | `dari_baris`, `ke_baris` | `from_line`, `to_line` | `dari_baris`, `ke_baris` | `dari_baris`, `ke_baris` |
| Pengembalian | `TransaksiManager.proses_pengembalian` | sama dengan Arif | `TransaksiManager.kembalikan_alat` | `PeminjamanService.proses_pengembalian` | class terpisah `ManagerPengembalian.kembalikan` |
| Hapus dengan pemeriksaan transaksi | `TransaksiManager.hapus_mahasiswa` dan `hapus_alat` | sama dengan Arif | `hapus(nim, trx_mgr)` di manager masing-masing | method di service | `hapus()` di manager masing-masing, referensi ke `ManagerTransaksi` dipasang sekali lewat `sambungkan_transaksi` |
| Status aktif mahasiswa | atribut biasa | sama dengan Arif | `set_status_aktif(nim, aktif)` manual | `set_status_aktif(aktif)` manual | diatur otomatis oleh `ManagerTransaksi.perbarui_status_mahasiswa` |
| Laporan | `MenuApp.menu_laporan()` | sama dengan Arif | `MenuApp.menu_laporan()` | `MenuApp.menu_laporan()` | `ManagerLaporan` (Tantangan B dan F) |
| Log aktivitas | tidak ada | tidak ada | tidak ada | tidak ada | `Logger` (Tantangan D) |

## 2. Bagian yang diambil atau dimodifikasi dari rancangan anggota lain

Dari **rancangan Arif** (dasar): struktur menu, tiga manager, dan empat model; nama `dari_baris`/`ke_baris`; method file
`pastikan_file`, `baca_baris(nama_file, jumlah_kolom)`, dan `tulis_baris`.

Dari **rancangan Faris**:
- nama class `FileManager`;
- `DetailTransaksi` menyimpan `id_transaksi` sendiri, sehingga satu baris `detail_transaksi.txt` dapat dibaca dan ditulis
  tanpa bantuan objek lain (`ke_baris()` tanpa parameter);
- `Alat.tandai_dikembalikan(kondisi)`, `daftar_kategori()` pada manager alat, dan `riwayat_mahasiswa(nim)` pada manager
  transaksi;
- pemeriksaan transaksi aktif dilakukan oleh manager masing-masing saat menghapus. Parameter `trx_mgr` diganti referensi
  yang dipasang sekali (`sambungkan_transaksi`) agar menu tidak perlu meneruskannya setiap kali.

Dari **rancangan Niken**:
- `FileManager` menyimpan daftar peringatan baris rusak (`daftar_peringatan`) dan memiliki `tambah_baris` untuk mode
  append, yang dipakai untuk `log.txt`;
- `masih_aktif()` dan `baris_detail()` pada `Transaksi`;
- alur baca/tulis file: data dimuat sekali saat program mulai, setiap perubahan langsung disimpan, operasi yang ditolak
  tidak menyimpan, dan seluruh data disimpan sekali lagi saat keluar sebagai pengaman.

Dari **rancangan Fatimah**: struktur class sama dengan rancangan Arif. UML final rancangan kelompok digambar dan diunggah
oleh Fatimah.

Modifikasi yang tidak ada di rancangan mana pun:
- pengembalian dipisah menjadi `ManagerPengembalian` agar `ManagerTransaksi` tidak terlalu besar;
- `Logger` (Tantangan D), `FileManagerError`, `validasi.py`, dan `konstanta.py`;
- status aktif mahasiswa diatur otomatis;
- setelah code review: `ManagerDasar`, `ManagerLaporan` (Tantangan B dan F), dan karantina baris rusak ke `baris_rusak.txt`.

## 3. Alasan memilih struktur class

| Class | Tanggung jawab | Alasan |
|---|---|---|
| `Mahasiswa`, `Alat`, `Transaksi`, `DetailTransaksi` | menyimpan data, memvalidasi satu baris file (`dari_baris`), dan membuat baris file (`ke_baris`) | satu class per entitas; format baris diketahui model, bukan manager atau menu |
| `Transaksi` berisi list `DetailTransaksi` | satu transaksi memuat banyak alat | Aturan 3: jumlah dan jenis alat dinamis tanpa variabel terpisah |
| `ManagerDasar` | dictionary data, `muat`, `simpan`, dan pemulihan bila penyimpanan gagal | pola yang sama dipakai `ManagerMahasiswa` dan `ManagerAlat` (pewarisan), sehingga tidak ditulis dua kali |
| `ManagerMahasiswa`, `ManagerAlat` | aturan tambah, edit, hapus, dan cari | turunan `ManagerDasar`; hanya menambahkan hal yang khas untuk datanya |
| `ManagerTransaksi` | membuat transaksi, menyimpan dua file transaksi, dan menyelaraskan status turunan saat dimuat (`_selaraskan`) | Aturan 1, 2, 3, 7, dan 8 diperiksa di satu tempat sebelum data berubah |
| `ManagerPengembalian` | pengembalian satu per satu, kondisi alat, dan keterlambatan | Aturan 4 dan 5 terpisah dari pembuatan transaksi |
| `ManagerLaporan` | statistik dan ekspor laporan | Tantangan B dan F hanya membaca data, tidak mengubahnya |
| `FileManager` | satu-satunya tempat `open()`, `with`, dan `try-except` | kode baca/tulis tidak berulang; mengganti penyimpanan hanya menyentuh `FileManager` dan `muat`/`simpan` di manager |
| `Logger` | menulis `log.txt` dengan mode append | Tantangan D; kegagalan log tidak menggagalkan operasi utama |
| `AplikasiPeminjaman` (`menu.py`) | tampilan dan alur input | tanpa logika bisnis; `ValueError` ditampilkan sebagai `[DITOLAK]` |
| `validasi.py`, `konstanta.py` | fungsi validasi dan nilai tetap | tidak ada string status, kondisi, atau angka aturan yang ditulis berulang |

Dictionary dipakai dengan kunci NIM, kode alat, dan ID transaksi: pencarian O(1) dan data ganda langsung terdeteksi
(Aturan 8). List dipakai untuk `daftar_detail` karena jumlah alat per transaksi berubah-ubah dan urutannya dipertahankan.

## 4. Alasan memilih format text file dan pemisah

- Satu baris satu data dengan pemisah `|`: mudah diurai dengan `split()` dan `join()` (soal melarang `json`, `csv`,
  dan `pickle`), dan `|` jarang muncul di nama atau kategori. Nilai yang mengandung `|` atau baris baru ditolak saat input
  dan saat menulis.
- Nilai kosong ditulis `-` agar jumlah kolom selalu tetap, sehingga baris yang kolomnya tidak sesuai mudah dikenali.
- `detail_transaksi.txt` terpisah dari `transaksi.txt`: setiap alat punya baris sendiri, sehingga jumlah alat dinamis
  dan pengembalian sebagian (status, kondisi, tanggal per alat) tercatat tanpa mengubah struktur file.
- Tanggal `YYYY-MM-DD` persis: mudah divalidasi dan dapat dibandingkan sebagai teks.
- Penulisan ulang memakai file `.tmp` lalu `os.replace`, sehingga kegagalan di tengah penulisan tidak merusak file lama.
- `baris_rusak.txt` (`waktu|file asal|baris asli`, mode append) menampung baris yang tidak dapat dimuat, sehingga file
  data tetap sama dengan data di program tanpa membuang baris yang mungkin masih diperlukan.

## 5. Alternatif yang dipertimbangkan tetapi tidak dipilih

| Alternatif | Asal | Alasan tidak dipilih |
|---|---|---|
| Satu class service yang memegang semua data dan aturan | rancangan Niken (`PeminjamanService`) | tanggung jawab bercampur dan class menjadi sangat besar; sulit dibagi ke empat anggota |
| Nama method `to_line`/`from_line` | rancangan Faris | dipilih `dari_baris`/`ke_baris` agar seluruh kode berbahasa Indonesia |
| `DetailTransaksi` tanpa `id_transaksi`, ditulis dengan `ke_baris(id_transaksi)` | rancangan Arif dan Fatimah | baris detail tidak dapat dibaca dan diperiksa tanpa objek transaksinya |
| Penghapusan mahasiswa dan alat lewat `TransaksiManager` | rancangan Arif dan Fatimah | aturan hapus milik data mahasiswa dan alat, jadi diletakkan di manager masing-masing |
| Tanggal disimpan sebagai objek `date` | rancangan Arif, Fatimah, Niken | disimpan sebagai teks `YYYY-MM-DD` seperti di file, lalu divalidasi saat dimuat |
| `status_aktif` diubah manual (`set_status_aktif`) dan dapat memblokir peminjaman | rancangan Faris dan Niken | dapat bertentangan dengan transaksi yang sebenarnya (Aturan 7), dan pemblokiran tidak diminta aturan mana pun |
| Database, `json`, `csv`, `pickle`, `shelve` | - | dilarang oleh soal |
| Daftar alat dalam satu kolom di `transaksi.txt` | - | sulit diurai, pengembalian per alat tidak tercatat rapi |
| Menambah baris saja (append) untuk semua perubahan | - | edit dan hapus tidak dapat dilakukan; hanya `log.txt` dan `baris_rusak.txt` memakai append |
| Menyalin file ke `.bak` sebelum ditimpa | perbaikan awal setelah code review | diganti `baris_rusak.txt`: lebih jelas baris mana yang bermasalah dan dari file mana, serta file cadangan tidak menumpuk |
| Tidak menulis ulang file saat keluar | saran code review (S5) | baris yang dilewati akan tetap ada di file sehingga file berbeda dari data di program (Aturan 7) |

## 6. Perubahan dari UML rancangan ke implementasi

| UML rancangan (Tahap 1) | Implementasi akhir | Alasan |
|---|---|---|
| `MenuApp` dengan `menu_peminjaman`, `menu_pengembalian`, `menu_laporan` | `AplikasiPeminjaman` dengan satu method per pilihan menu | setiap pilihan menu dapat diuji sendiri; nama class menjelaskan perannya |
| `MahasiswaManager`, `AlatManager`, `TransaksiManager` | `ManagerMahasiswa`, `ManagerAlat`, `ManagerTransaksi` | penamaan Indonesia yang konsisten |
| tidak ada | `ManagerDasar` | menghapus duplikasi `muat`/`simpan` pada dua manager (temuan S6) |
| `TransaksiManager.proses_pengembalian` | `ManagerPengembalian.kembalikan` | pengembalian dikerjakan Niken secara terpisah dan `ManagerTransaksi` tidak terlalu besar |
| `TransaksiManager.hapus_mahasiswa`, `hapus_alat` | `ManagerMahasiswa.hapus`, `ManagerAlat.hapus` | aturan hapus milik data masing-masing |
| `get(nim)`, `get(kode)`, `tambah(mhs)`, `tambah(alat)` | `ambil()`, `cari_berdasarkan_nim()`, `cari_berdasarkan_kode()`, `tambah(nim, nama, no_hp)` | validasi input dilakukan di manager, menu hanya meneruskan teks |
| `hitung_aktif`, `cari_by_mahasiswa`, `daftar_semua`, `buat_id` | `punya_transaksi_aktif`, `cari_berdasarkan_mahasiswa`, `semua`, `_id_baru` | nama berbahasa Indonesia; `_id_baru` tidak memakai ulang ID di `baris_rusak.txt` |
| `FileHandler` dengan `tulis_baris(): bool` | `FileManager` yang melempar `FileManagerError` | kegagalan file tidak dapat diabaikan diam-diam; manager memulihkan data lalu menu menampilkan `[ERROR FILE]` |
| tidak ada | `Logger`, `ManagerLaporan` | Tantangan D, B, dan F |
| `Alat.tersedia()`, `terima_kembali(kondisi)` | `Alat.status_dari_kondisi()`, `tandai_dipinjam()`, `tandai_dikembalikan(kondisi)` | aturan kondisi menjadi status (Aturan 5) hanya ditulis sekali |
| `Transaksi.tambah_detail`, `kembalikan_alat`, `punya_alat`, `aktif` | `daftar_detail` diisi manager, `DetailTransaksi.kembalikan`, `masih_aktif()` | pengembalian dicatat pada detail alat yang bersangkutan |
| `DetailTransaksi` tanpa `id_transaksi` | `DetailTransaksi` dengan `id_transaksi` | satu baris detail dapat diperiksa sendiri saat dimuat |
| tidak ada | `ManagerTransaksi._selaraskan()` | menyesuaikan status transaksi, alat, dan mahasiswa dengan detail transaksi saat dimuat (temuan R2) |

## 7. Keputusan setelah analisis kode dan code review

| Keputusan | Alasan | Catatan |
|---|---|---|
| Alat atau mahasiswa yang tercatat di transaksi mana pun tidak dapat dihapus | Aturan 8: transaksi harus merujuk NIM dan kode alat yang ada | lebih ketat dari teks Aturan 6 (yang hanya menyebut transaksi aktif); alternatif lain adalah soft delete |
| `status_aktif` mahasiswa diatur otomatis | soal menyebut "status aktif peminjaman", dan contoh soal cocok dengan bacaan ini (M001 yang meminjam `aktif`, M002 `tidak aktif`) | status tidak dapat diedit manual dan tidak memblokir peminjaman |
| Status alat yang bertentangan dengan kondisi atau transaksi diperbaiki saat dimuat, dengan peringatan | Aturan 5 dan 7 | misalnya `rusak berat` dengan status `tersedia` menjadi `tidak tersedia` |
| Batas 7 hari hanya diperiksa saat transaksi dibuat; saat dimuat cukup `batas_kembali >= tgl_pinjam` | transaksi lama tidak boleh ditolak bila aturan hari diubah (temuan S2) | |
| Baris yang dilewati dipindahkan ke `baris_rusak.txt` sebelum file ditimpa | file tetap sama dengan data di program tanpa kehilangan data (temuan F1) | alat yang tercatat dipinjam pada baris itu tetap `dipinjam` (temuan K1), dan ID-nya tidak dipakai ulang |
| Bila penyimpanan gagal, semua data dimuat ulang dari file lalu ditulis ulang | Aturan 7, termasuk saat file transaksi sempat tertulis sebagian (temuan F2) | kondisi alat juga dipulihkan pada pengembalian |
| Keterlambatan dihitung, ditampilkan, dan dicatat di log | keterlambatan pengembalian termasuk masalah yang disebut soal | denda belum ada |
| Daftar panjang di menu ditampilkan per halaman | menu tetap dapat dipakai pada data besar (temuan S4) | 20 baris per halaman |

## 8. Rancangan tabel (ERD) yang menjadi dasar skema

Bahan yang dibandingkan: rancangan tabel/ERD setiap anggota di `docs/individu/` dan ERD final
`docs/final/ERD_Final_Kelompok2.png` (sumber `database/schema.sql`).

| Aspek | Arif | Fatimah | Faris | Niken | Skema akhir |
|---|---|---|---|---|---|
| Tabel | [ISI] | [ISI] | [ISI] | [ISI] | `mahasiswa`, `alat`, `transaksi`, `detail_transaksi`, `log_aktivitas` |
| Primary key `detail_transaksi` | [ISI] | [ISI] | [ISI] | [ISI] | gabungan (`id_transaksi`, `kode_alat`) |
| Tipe status/kondisi | [ISI] | [ISI] | [ISI] | [ISI] | `ENUM` |
| Kategori alat | [ISI] | [ISI] | [ISI] | [ISI] | kolom teks `kategori` di tabel `alat` |
| Nilai kosong (no. HP, kondisi kembali) | [ISI] | [ISI] | [ISI] | [ISI] | `NULL` |

Rancangan yang dipilih sebagai dasar: [ISI: nama anggota dan alasan hasil diskusi]. Bagian yang diambil dari rancangan
lain: [ISI].

## 9. Keputusan skema dan constraint

| Keputusan | Alasan | Alternatif yang tidak dipilih |
|---|---|---|
| Kolom tabel mengikuti format `.txt` lama (nama kolom dan nilai status sama) | migrasi cukup memetakan kolom satu per satu; model tidak berubah | mengganti nama dan nilai status (perlu konversi saat migrasi) |
| `detail_transaksi` memakai PK gabungan (`id_transaksi`, `kode_alat`) | satu alat tidak dapat muncul dua kali di transaksi yang sama (Aturan 3), tanpa kolom ID tambahan | kolom `id` AUTO_INCREMENT (duplikat alat dalam satu transaksi tetap mungkin) |
| ID transaksi teks `T001`, `T002`, ... dibuat program | sama dengan data lama dan contoh soal, mudah dibaca dan diketik saat pengembalian | AUTO_INCREMENT angka (ID lama `T001` harus diubah) |
| Status, kondisi, dan `status_aktif` memakai `ENUM`; sesi memakai `sql_mode` ketat | nilai di luar daftar ditolak database, bukan disimpan sebagai string kosong | `VARCHAR` bebas (salah ketik lolos) atau tabel referensi status (lebih rumit untuk nilai yang tetap) |
| Kategori alat berupa kolom teks berindex, bukan ENUM | kategori baru dapat ditambah tanpa mengubah skema ("kategori dinamis") | `ENUM` kategori (perlu `ALTER TABLE`) atau tabel `kategori` terpisah ([ISI: dibahas atau tidak]) |
| `no_hp`, `kondisi_kembali`, `tgl_kembali` boleh `NULL`; kolom lain `NOT NULL` | kosong berarti "belum ada", bukan teks `-` seperti di `.txt` | menyimpan `-` (sulit dibedakan dari data asli) |
| CHECK `batas_kembali >= tgl_pinjam` dan CHECK konsistensi detail (dipinjam berarti kondisi/tanggal kembali `NULL`) | data yang tidak masuk akal ditolak oleh database, tidak hanya oleh program | hanya diperiksa di Python |
| Foreign key tanpa `ON DELETE CASCADE` (RESTRICT) | riwayat transaksi tidak boleh ikut terhapus diam-diam (Aturan 6 dan 8); program memeriksa lebih dulu agar pesannya jelas | `CASCADE` (riwayat hilang) atau soft delete (kolom `dihapus`) |
| Index `alat(status)`, `alat(kategori)`, `transaksi(nim, status)`, `detail_transaksi(kode_alat, status)`, `log_aktivitas(waktu)` | kolom yang dipakai di `WHERE`/`ORDER BY` menu 6–9, 14, pemeriksaan hapus, dan log, sehingga tetap cepat untuk 10.000 alat dan 20.000 mahasiswa | tanpa index (pencarian menyisir seluruh tabel) |
| `status_aktif` tetap `aktif`/`tidak aktif` dan diatur otomatis | sama dengan keputusan tahap `.txt` (bagian 7) | `aktif`/`nonaktif` yang diubah manual |

## 10. Keputusan akses database

| Keputusan | Alasan |
|---|---|
| Lapisan `menu` → `manager` → `repository` → `Database` | semua SQL ada di `app/repository/`, dan hanya `app/database.py` yang memanggil `connect()`/`execute()`/`commit()`/`rollback()` (satu pintu). Menu tidak berisi SQL, manager tidak berisi SQL |
| Satu koneksi selama program berjalan, dibuka saat mulai dan ditutup saat keluar; bila terputus, disambung ulang otomatis (`ping`) di luar transaction | tidak membuka-tutup koneksi di setiap menu; koneksi yang tertidur (database online) pulih sendiri |
| `autocommit=True` untuk operasi satu query; `with db.transaksi():` (BEGIN, lalu COMMIT atau ROLLBACK) untuk operasi beberapa tabel | setiap perubahan langsung tersimpan, dan setiap pembacaan melihat data terbaru dari anggota lain (Skenario 8). Dengan `autocommit=False`, koneksi yang hanya membaca tetap melihat snapshot lama sampai ada COMMIT |
| Peminjaman: kunci baris mahasiswa dan setiap alat dengan `SELECT ... FOR UPDATE`, periksa ulang aturan di dalam transaction, lalu INSERT dan UPDATE | dua petugas yang meminjamkan alat yang sama bersamaan tidak lolos keduanya; yang kedua menunggu lalu ditolak karena alat sudah `dipinjam` |
| ID transaksi baru = angka terbesar + 1, dibuat di dalam transaction dan diulang (maksimal 3 kali) bila bertabrakan (error 1062) | dua komputer yang membuat transaksi bersamaan tidak memakai ID yang sama |
| Hasil query berupa `dict` (`DictCursor`), lalu diubah menjadi objek lewat `dari_dict()` | model dan aturan bisnis yang sama dipakai seperti tahap `.txt`; `dari_baris()` tetap ada untuk migrasi |
| Error PyMySQL diterjemahkan menjadi `DatabaseError` dengan pesan berbahasa Indonesia berdasarkan kodenya (2003, 1045, 1049, 1062, 1451, 1452, 1205, ...) | pengguna tidak melihat pesan SQL mentah (Skenario 9 dan 10) |
| Data diambil terfilter (`WHERE`, `JOIN`, `COUNT`, `GROUP BY`, `LIMIT/OFFSET`), detail transaksi diambil dengan satu query `IN (...)` | tidak memuat seluruh tabel ke memori; tidak ada query berulang per baris (N+1) |
| Kredensial hanya di `.env` (dibaca `python-dotenv`), `.env.example` tanpa password, `*.pem` dan `.env` di `.gitignore` | password tidak bocor di repository |
| Tabel dibuat otomatis dari `database/schema.sql` saat program mulai, dan database dibuat bila belum ada | Skenario "tabel belum ada" berjalan tanpa error; `schema.sql` menjadi satu-satunya sumber struktur tabel |
| Log aktivitas ditulis di luar transaction utama dan kegagalannya hanya menampilkan peringatan | log yang gagal tidak membatalkan peminjaman atau pengembalian |
| Driver PyMySQL | murni Python sehingga mudah dipasang di Windows, dan bekerja untuk MariaDB XAMPP maupun MySQL 8 online; [ISI: alasan tambahan hasil diskusi, bila ada] |

## 11. Perubahan class dari tahap `.txt` ke MySQL

| Tahap `.txt` | Tahap MySQL | Keterangan |
|---|---|---|
| `FileManager` sebagai satu pintu penyimpanan | `Database` sebagai satu pintu; `FileManager` tersisa untuk laporan dan migrasi | sesuai panduan 3.4 |
| `ManagerDasar.muat()`/`simpan()` dan dictionary seluruh data di memori | `ManagerDasar` memakai repository; data diambil saat diperlukan | dictionary tidak lagi dibutuhkan karena database yang menjamin keunikan (PK) |
| `ManagerTransaksi._selaraskan()` dan pemulihan saat simpan gagal | transaction dengan ROLLBACK | Aturan 7 dijamin database |
| `baris_rusak.txt`, `_id_baru` yang memeriksa baris rusak | dihapus; validasi baris lama hanya di `scripts/migrate_txt.py` | database tidak menyimpan baris rusak karena constraint |
| `Logger` menulis `log.txt` | `Logger` menulis tabel `log_aktivitas` dengan kolom petugas dan aksi | Tantangan D sesuai panduan |
| referensi antarmanager (`sambungkan_transaksi`) | setiap manager memakai repository yang diperlukan langsung | pemeriksaan "masih dipinjam" cukup satu query |
| tidak ada | `config.py`, `database.py`, `repository/*`, `RepoLaporan.terlambat`, menu 14 | koneksi, SQL, dan Tantangan G |

Nama method publik manager yang dipanggil menu (`tambah`, `edit`, `hapus`, `cari`, `buat`, `kembalikan`, `ekspor_*`)
tetap sama, sehingga `menu.py` hanya berubah pada bagian koneksi, pesan error database, dan menu 14. Ukuran perubahan
ini dibahas di `docs/refleksi.md` (pertanyaan 4).
