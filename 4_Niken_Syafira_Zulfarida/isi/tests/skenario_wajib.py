"""Menjalankan 10 skenario pengujian wajib lewat `python main.py` sungguhan terhadap database MySQL.

Pemakaian (dari folder proyek, MySQL XAMPP menyala):  python tests/skenario_wajib.py

Skrip memakai database terpisah bernama <DB_NAME>_skenario (database utama tidak disentuh), menghapus dan membuatnya
ulang, menjalankan setiap skenario, memeriksa layar dan isi tabel, lalu menulis docs/bukti_eksekusi_skenario.md.
Berkas ini sengaja tidak bernama test*.py agar tidak ikut `python -m unittest`.
"""
import datetime
import os
import platform
import subprocess
import sys

if __name__ != '__main__':
    raise ImportError('tests/skenario_wajib.py adalah skrip. Jalankan dengan: python tests/skenario_wajib.py')

PROYEK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROYEK)
from app.config import baca_konfigurasi  # noqa: E402
from app.database import Database, DatabaseError  # noqa: E402
from app.konstanta import PATH_SCHEMA  # noqa: E402

OUT_MD = os.path.join(PROYEK, 'docs', 'bukti_eksekusi_skenario.md')
KONF = baca_konfigurasi()
KONF['database'] = os.environ.get('SKENARIO_DB_NAME') or KONF['database'] + '_skenario'
HARI_INI = datetime.date.today()
TGL = HARI_INI.strftime('%Y-%m-%d')
BATAS = (HARI_INI + datetime.timedelta(days=7)).strftime('%Y-%m-%d')
TABEL = ('mahasiswa', 'alat', 'transaksi', 'detail_transaksi')
MD, RINGKAS = [], []


def env_proses(**ganti):
    nilai = {'DB_HOST': KONF['host'], 'DB_PORT': str(KONF['port']), 'DB_USER': KONF['user'], 'DB_PASSWORD': KONF['password'], 'DB_NAME': KONF['database'], 'DB_SSL_CA': KONF['ssl_ca'], 'NAMA_PETUGAS': 'Skenario'}
    nilai.update(ganti)
    return dict(os.environ, PYTHONIOENCODING='utf-8', **nilai)


def jalan(masukan, **ganti):
    r = subprocess.run([sys.executable, 'main.py'], cwd=PROYEK, input='\n'.join(masukan) + '\n', capture_output=True, text=True, encoding='utf-8', timeout=120, env=env_proses(**ganti))
    return r.returncode, r.stdout, r.stderr


def db():
    d = Database(KONF)
    d.sambung()
    return d


def isi_tabel():
    d = db()
    try:
        return {t: d.query('SELECT * FROM %s ORDER BY 1, 2' % t) for t in TABEL}
    finally:
        d.tutup()


def query(sql, parameter=()):
    d = db()
    try:
        return d.query(sql, parameter)
    finally:
        d.tutup()


def teks_baris(daftar):
    return ['|'.join(('NULL' if v is None else str(v) for v in b.values())) for b in daftar]


def tampil_tabel(nama, where='', parameter=()):
    return ['SELECT * FROM %s%s;' % (nama, where)] + teks_baris(query('SELECT * FROM %s%s ORDER BY 1, 2' % (nama, where), parameter))


def tag(keluaran, *tanda):
    """Baris yang memuat salah satu tanda, dipotong mulai dari tanda pertama (teks prompt input di depannya dibuang)."""
    hasil = []
    for b in keluaran.splitlines():
        posisi = [b.find(t) for t in tanda if t in b]
        if posisi:
            hasil.append(b[min(posisi):].strip())
    return hasil


def blok(keluaran, awal, banyak=12):
    baris = keluaran.splitlines()
    for i, b in enumerate(baris):
        if b.startswith(awal):
            hasil = [b]
            for x in baris[i + 1:i + 1 + banyak]:
                if x.strip() == '' or x.startswith('=') or x.startswith('Pilih menu'):
                    break
                hasil.append(x)
            return hasil
    return []


def tanpa_error(*hasil):
    return all((k == 0 and 'Traceback' not in o + e for k, o, e in hasil))


def h(teks=''):
    MD.append(teks)


def kode(baris):
    h('```text')
    MD.extend(baris if isinstance(baris, list) else [baris])
    h('```')
    h()


def selesai(no, judul, cek):
    gagal = [k for k, ok in cek if not ok]
    RINGKAS.append((no, judul, not gagal, len(cek), gagal))
    h('**Pemeriksaan otomatis:**')
    h()
    for keterangan, ok in cek:
        h('- [%s] %s' % ('x' if ok else ' ', keterangan))
    h()
    h('**Hasil: %s**' % ('LULUS' if not gagal else 'GAGAL'))
    h()
    h('---')
    h()


# ===================== persiapan database skenario =====================
try:
    awal = Database(dict(KONF, database=KONF['database']))
    awal.sambung()
    awal.eksekusi('DROP DATABASE `%s`' % KONF['database'])
    awal.tutup()
    awal = Database(KONF)
    awal.sambung()
    awal.pastikan_tabel(PATH_SCHEMA)
    VERSI_SERVER = awal.query_satu('SELECT VERSION() AS v')['v']
    awal.tutup()
except DatabaseError as e:
    print('[!] Database skenario tidak dapat disiapkan: %s' % e)
    sys.exit(1)

# ===================== Skenario 1 =====================
masuk1 = ['1', '1', 'M001', 'Andi Pratama', '081234567890', '1', 'M002', 'Budi Santoso', '085612345678', '1', 'M003', 'Citra Lestari', '', '5', '0',
          '2', '1', 'A001', 'Kamera Digital', 'perangkat multimedia', '', '1', 'A002', 'Tripod', 'perangkat multimedia', '', '1', 'A003', 'Kabel LAN', 'perangkat jaringan', '',
          '1', 'A004', 'Laptop', 'perangkat komputasi', '', '1', 'A005', 'Kabel HDMI', 'perangkat multimedia', '', '5', '0', '0']
r1 = jalan(masuk1)
h('## Skenario 1: Tambah beberapa mahasiswa dan alat')
h()
h('**Langkah:** menu 1 menambah 3 mahasiswa (M003 tanpa no. HP), menu 2 menambah 5 alat termasuk kategori baru `perangkat komputasi`.')
h()
kode(tag(r1[1], '[OK]'))
kode(tampil_tabel('mahasiswa') + [''] + tampil_tabel('alat'))
cek = [('ada 8 pesan `[OK]`', len(tag(r1[1], '[OK]')) == 8),
       ('3 baris di tabel `mahasiswa`, no. HP M003 tersimpan `NULL`', len(query('SELECT * FROM mahasiswa')) == 3 and query("SELECT no_hp FROM mahasiswa WHERE nim = 'M003'")[0]['no_hp'] is None),
       ('5 baris di tabel `alat`, semuanya `tersedia`', [b['status'] for b in query('SELECT status FROM alat')] == ['tersedia'] * 5),
       ('kategori baru diterima tanpa mengubah kode', query("SELECT COUNT(*) AS n FROM alat WHERE kategori = 'perangkat komputasi'")[0]['n'] == 1),
       ('program berakhir normal', tanpa_error(r1))]
selesai(1, 'Tambah mahasiswa dan alat', cek)

# ===================== Skenario 2 =====================
r2 = jalan(['3', 'M001', 'A001, A002, A003', '8', '0'])
h('## Skenario 2: Satu mahasiswa meminjam beberapa alat dalam satu transaksi')
h()
h('**Langkah:** M001 meminjam `A001, A002, A003` (menu 3), lalu menu 8.')
h()
kode(tag(r2[1], '[OK]', 'T001 |', '- A00') + [''] + blok(r2[1], 'Alat yang sedang dipinjam ('))
kode(tampil_tabel('transaksi') + [''] + tampil_tabel('detail_transaksi') + [''] + tampil_tabel('alat'))
cek = [('transaksi `T001` milik M001 dengan batas tepat 7 hari', teks_baris(query('SELECT * FROM transaksi')) == ['T001|M001|%s|%s|dipinjam' % (TGL, BATAS)]),
       ('`detail_transaksi` berisi 3 baris berstatus `dipinjam`', [b['status'] for b in query('SELECT status FROM detail_transaksi')] == ['dipinjam'] * 3),
       ('A001, A002, A003 berstatus `dipinjam` di database', [b['status'] for b in query("SELECT status FROM alat WHERE kode IN ('A001','A002','A003')")] == ['dipinjam'] * 3),
       ('status aktif M001 menjadi `aktif`', query("SELECT status_aktif FROM mahasiswa WHERE nim = 'M001'")[0]['status_aktif'] == 'aktif'),
       ('layar menampilkan 3 alat dipinjam', 'Alat yang sedang dipinjam (3 data)' in r2[1]),
       ('program berakhir normal', tanpa_error(r2))]
selesai(2, 'Peminjaman beberapa alat dalam satu transaksi', cek)

# ===================== Skenario 3 =====================
sebelum3 = isi_tabel()
r3 = jalan(['3', 'M002', 'A001', '3', 'M002', 'A004, A001', '3', 'M999', 'A004', '0'])
sesudah3 = isi_tabel()
r3b = jalan(['3', 'M001', 'A004', '3', 'M001', 'A005', '0'])
h('## Skenario 3: Meminjam alat yang tidak tersedia')
h()
h('**Langkah:** (a) M002 meminjam A001 yang sedang dipinjam; (b) M002 meminjam `A004, A001`; (c) NIM `M999` yang tidak terdaftar. '
  'Isi keempat tabel dibandingkan sebelum dan sesudah. Tambahan Aturan 2: M001 membuat transaksi kedua lalu ketiga.')
h()
kode(tag(r3[1], '[DITOLAK]', '[OK]') + ['', 'perbandingan isi tabel:'] + ['%-17s sebelum %d baris | sesudah %d baris | identik: %s' % (t, len(sebelum3[t]), len(sesudah3[t]), sebelum3[t] == sesudah3[t]) for t in TABEL])
kode(tag(r3b[1], '[DITOLAK]', '[OK]'))
cek = [('ketiga percobaan ditolak dengan `[DITOLAK]`', len(tag(r3[1], '[DITOLAK]')) == 3 and not tag(r3[1], '[OK]')),
       ('pesan menyebut alasan (alat tidak tersedia / NIM tidak ditemukan)', sum(('tidak tersedia' in b for b in tag(r3[1], '[DITOLAK]'))) == 2 and any(('M999 tidak ditemukan' in b for b in tag(r3[1], '[DITOLAK]')))),
       ('isi keempat tabel identik sebelum dan sesudah', sebelum3 == sesudah3),
       ('Aturan 2: transaksi kedua diterima, ketiga ditolak (maksimal 2 aktif)', len(tag(r3b[1], '[OK]')) == 1 and any(('2 transaksi aktif' in b for b in tag(r3b[1], '[DITOLAK]')))),
       ('program berakhir normal', tanpa_error(r3, r3b))]
selesai(3, 'Meminjam alat yang tidak tersedia', cek)

# ===================== Skenario 4 =====================
r4 = jalan(['5', 'T001', 'A001', '1', '7', '8', '0'])
h('## Skenario 4: Mengembalikan sebagian alat')
h()
h('**Langkah:** T001 berisi A001, A002, A003; hanya A001 dikembalikan dengan kondisi `baik` (menu 5), lalu menu 7 dan 8.')
h()
kode(tag(r4[1], '[OK]', 'T001 |', '- A00') + [''] + blok(r4[1], 'Alat yang tersedia (') + [''] + blok(r4[1], 'Alat yang sedang dipinjam ('))
kode(tampil_tabel('transaksi', " WHERE id = 'T001'") + [''] + tampil_tabel('detail_transaksi', " WHERE id_transaksi = 'T001'"))
cek = [('status T001 menjadi `sebagian dikembalikan`', query("SELECT status FROM transaksi WHERE id = 'T001'")[0]['status'] == 'sebagian dikembalikan'),
       ('A001 tercatat `dikembalikan|baik|%s` dan kembali `tersedia`' % TGL, teks_baris(query("SELECT status, kondisi_kembali, tgl_kembali FROM detail_transaksi WHERE kode_alat = 'A001'")) == ['dikembalikan|baik|%s' % TGL] and query("SELECT status FROM alat WHERE kode = 'A001'")[0]['status'] == 'tersedia'),
       ('A002 dan A003 masih `dipinjam`', [b['status'] for b in query("SELECT status FROM alat WHERE kode IN ('A002','A003')")] == ['dipinjam'] * 2),
       ('layar: alat yang masih dipinjam di T001 tampil di menu 8', 'A002' in '\n'.join(blok(r4[1], 'Alat yang sedang dipinjam ('))),
       ('program berakhir normal', tanpa_error(r4))]
selesai(4, 'Pengembalian sebagian', cek)

# ===================== Skenario 5 =====================
r5 = jalan(['5', 'T001', 'A002, A003', '2', '3', '7', '9', '0'])
h('## Skenario 5: Alat kembali dalam kondisi rusak ringan dan rusak berat')
h()
h('**Langkah:** sisa alat T001 dikembalikan: A002 `rusak ringan`, A003 `rusak berat`; lalu menu 7 dan 9.')
h()
kode(tag(r5[1], '[OK]') + [''] + blok(r5[1], 'Alat yang rusak ('))
kode(tampil_tabel('alat', " WHERE kode IN ('A002', 'A003')"))
cek = [('A002 dan A003 berstatus `tidak tersedia` dengan kondisi sesuai input', teks_baris(query("SELECT kode, kondisi, status FROM alat WHERE kode IN ('A002','A003') ORDER BY kode")) == ['A002|rusak ringan|tidak tersedia', 'A003|rusak berat|tidak tersedia']),
       ('keduanya tidak muncul di daftar alat tersedia', not any(('A002' in b or 'A003' in b for b in blok(r5[1], 'Alat yang tersedia (')))),
       ('keduanya muncul di daftar alat rusak', 'Alat yang rusak (2 data)' in r5[1]),
       ('T001 menjadi `selesai`', query("SELECT status FROM transaksi WHERE id = 'T001'")[0]['status'] == 'selesai'),
       ('program berakhir normal', tanpa_error(r5))]
selesai(5, 'Pengembalian alat rusak', cek)

# ===================== Skenario 6 =====================
sebelum6 = isi_tabel()
r6 = jalan(['1', '3', 'M001', 'y', '0', '2', '3', 'A004', 'y', '0', '1', '1', 'M009', 'Uji Hapus', '', '3', 'M009', 'y', '0', '0'])
sesudah6 = isi_tabel()
h('## Skenario 6: Menghapus mahasiswa yang masih punya transaksi aktif')
h()
h('**Langkah:** M001 masih memiliki transaksi aktif T002 (A004). Hapus M001 dan alat A004; sebagai pembanding tambah M009 lalu hapus.')
h()
kode(tag(r6[1], '[DITOLAK]', '[OK]'))
cek = [('hapus M001 ditolak karena transaksi aktif', any(('M001 masih memiliki transaksi aktif' in b for b in tag(r6[1], '[DITOLAK]')))),
       ('hapus alat A004 yang sedang dipinjam ditolak', any(('A004 sedang dipinjam' in b for b in tag(r6[1], '[DITOLAK]')))),
       ('mahasiswa tanpa transaksi (M009) dapat dihapus', any(('Mahasiswa M009 dihapus' in b for b in tag(r6[1], '[OK]')))),
       ('isi keempat tabel sama dengan sebelum percobaan', sebelum6 == sesudah6),
       ('program berakhir normal', tanpa_error(r6))]
selesai(6, 'Hapus mahasiswa dengan transaksi aktif', cek)

# ===================== Skenario 7 =====================
r7a = jalan(['3', 'M003', 'A001, A005', '5', 'T003', 'A001', '1', '0'])
sebelum7 = isi_tabel()
ulang = [jalan(['4', '0']) for _ in range(3)]
sesudah7 = isi_tabel()
h('## Skenario 7: Tutup lalu jalankan ulang program')
h()
h('**Langkah:** M003 meminjam `A001, A005` (T003), A001 dikembalikan sehingga T003 `sebagian dikembalikan`. Program ditutup lalu dijalankan ulang 3 kali (menu 4).')
h()
kode(blok(ulang[-1][1], 'Daftar transaksi (', 20))
kode(['%-17s %d baris -> %d baris | identik: %s' % (t, len(sebelum7[t]), len(sesudah7[t]), sebelum7[t] == sesudah7[t]) for t in TABEL])
cek = [('T003 tersimpan `sebagian dikembalikan`', query("SELECT status FROM transaksi WHERE id = 'T003'")[0]['status'] == 'sebagian dikembalikan'),
       ('setiap jalan ulang menampilkan T001 `selesai`, T002 `dipinjam`, T003 `sebagian dikembalikan`', all(('T001 | M001' in o and 'selesai' in o and 'T003 | M003' in o and 'sebagian dikembalikan' in o for _, o, _ in ulang))),
       ('isi tabel identik setelah 3 kali jalan ulang (tidak ada data ganda)', sebelum7 == sesudah7),
       ('program berakhir normal', tanpa_error(r7a, *ulang))]
selesai(7, 'Tutup lalu jalankan ulang (termasuk transaksi sebagian)', cek)

# ===================== Skenario 8 =====================
r8a = jalan(['1', '1', 'M010', 'Dian Anggota A', '', '0', '0'], NAMA_PETUGAS='Anggota A')
r8b = jalan(['1', '4', 'M010', '0', '11', '0'], NAMA_PETUGAS='Anggota B')
h('## Skenario 8: Data yang diinput anggota A terlihat oleh anggota B')
h()
h('**Langkah (otomatis):** dua proses program yang terpisah (dua koneksi database berbeda) memakai database yang sama: proses A '
  'menambah M010, lalu proses B mencari M010 dan melihat log aktivitas. Ini mensimulasikan dua komputer.')
h()
h('**Langkah (manual, wajib saat demo):** dua laptop dengan `.env` yang sama menunjuk database online (Aiven). Anggota A '
  'menambah data, anggota B menjalankan program di laptopnya lalu menampilkan data tersebut. Simpan tangkapan layar kedua '
  'laptop di `docs/pengujian.md`.')
h()
kode(['# proses A'] + tag(r8a[1], '[OK]') + ['', '# proses B'] + blok(r8b[1], 'Hasil pencarian mahasiswa (') + [b for b in blok(r8b[1], 'Log aktivitas terbaru (', 20) if 'M010' in b])
cek = [('proses A menyimpan M010', any(('Mahasiswa berhasil ditambahkan' in b for b in tag(r8a[1], '[OK]')))),
       ('proses B (koneksi lain) langsung menemukan M010', 'M010 | Dian Anggota A' in r8b[1]),
       ('log mencatat siapa yang menambah (Anggota A)', 'Anggota A | tambah mahasiswa | Mahasiswa M010 ditambahkan' in r8b[1]),
       ('program berakhir normal', tanpa_error(r8a, r8b))]
selesai(8, 'Data anggota A terlihat oleh anggota B', cek)

# ===================== Skenario 9 =====================
sebelum9 = isi_tabel()
r9a = jalan(['1', '0'], DB_PASSWORD='password-salah', DB_USER='user_salah')
r9b = jalan(['1', '0'], DB_PORT='1')
sesudah9 = isi_tabel()
h('## Skenario 9: Koneksi gagal (password salah / server tidak dapat dihubungi)')
h()
h('**Langkah:** program dijalankan dengan user/password salah, lalu dengan port yang tidak dipakai server (sama seperti MySQL '
  'XAMPP dimatikan atau internet terputus untuk database online).')
h()
kode(tag(r9a[1], '[!]', 'Program tidak dapat') + [''] + tag(r9b[1], '[!]', 'Program tidak dapat'))
cek = [('password salah: pesan "Login database ditolak"', 'Login database ditolak' in r9a[1]),
       ('server tidak terjangkau: pesan "Tidak dapat terhubung ke database"', 'Tidak dapat terhubung ke database' in r9b[1]),
       ('tidak ada traceback dan kode keluar 0 pada kedua percobaan', tanpa_error(r9a, r9b)),
       ('menu tidak ditampilkan (tidak ada operasi tanpa database)', 'MENU UTAMA' not in r9a[1] + r9b[1]),
       ('isi database tidak berubah', sebelum9 == sesudah9)]
selesai(9, 'Koneksi gagal', cek)

# ===================== Skenario 10 =====================
r10 = jalan(['1', '1', 'M001', 'Andi Ganda', '', '1', 'M011', "Siti O'Neil", '', '1', 'M012', "x'); DROP TABLE mahasiswa; --", '', '4', "o'neil", '0', '0'])
h('## Skenario 10: NIM yang sudah ada dan input berisi tanda kutip')
h()
h("**Langkah:** tambah mahasiswa dengan NIM `M001` yang sudah ada, nama `Siti O'Neil`, dan nama berisi upaya SQL injection; lalu cari `o'neil`.")
h()
kode(tag(r10[1], '[DITOLAK]', '[OK]', 'M011 |', 'M012 |'))
kode(tampil_tabel('mahasiswa', ' WHERE nim IN (%s, %s, %s)', ('M001', 'M011', 'M012')))
cek = [('NIM ganda ditolak dengan pesan ramah', '[DITOLAK] NIM M001 sudah terdaftar.' in r10[1]),
       ('tidak ada pesan error SQL mentah', not any((k in r10[1] for k in ('Duplicate entry', 'IntegrityError', 'syntax', 'Traceback')))),
       ("nama `Siti O'Neil` tersimpan utuh dan dapat dicari", query("SELECT nama FROM mahasiswa WHERE nim = 'M011'")[0]['nama'] == "Siti O'Neil" and 'M011 | Siti' in r10[1]),
       ('teks upaya injeksi tersimpan sebagai data biasa; tabel mahasiswa tetap ada', query("SELECT nama FROM mahasiswa WHERE nim = 'M012'")[0]['nama'] == "x'); DROP TABLE mahasiswa; --"),
       ('data M001 lama tidak berubah', query("SELECT nama FROM mahasiswa WHERE nim = 'M001'")[0]['nama'] == 'Andi Pratama'),
       ('program berakhir normal', tanpa_error(r10))]
selesai(10, 'NIM ganda dan input bertanda kutip', cek)

# ===================== dokumen =====================
kepala = ['# Bukti Eksekusi Skenario Pengujian Wajib', '',
          'Dokumen ini berisi hasil menjalankan **`python main.py` sungguhan** untuk 10 skenario wajib terhadap database MySQL. '
          'Masukan keyboard diberikan lewat stdin, jadi layar dan isi tabel di bawah adalah keluaran program yang sebenarnya.', '',
          '| Item | Isian |', '|---|---|', '| Tanggal eksekusi | %s |' % TGL,
          '| Lingkungan | Python %s, %s; server database %s |' % (sys.version.split()[0], platform.system() or 'OS tidak diketahui', VERSI_SERVER),
          '| Database | `%s` (dibuat ulang setiap kali skrip dijalankan; database utama tidak disentuh) |' % KONF['database'],
          '| Cara mengulang | `python tests/skenario_wajib.py` dari folder proyek (menulis ulang dokumen ini) |', '',
          'Skenario 1 sampai 10 dijalankan berurutan pada database yang sama. Tanggal pinjam pada contoh sama dengan tanggal eksekusi.', '',
          '**Yang tidak dicakup dokumen ini:** Skenario 8 dengan dua laptop sungguhan dan database online, tangkapan layar QA manual '
          '(`docs/pengujian.md`), serta review kelompok lain (`docs/cross_group_review.md`).', '',
          '## Ringkasan', '', '| No | Skenario | Jumlah pemeriksaan | Hasil |', '|---|---|---|---|']
for no, judul, lulus, n, _ in RINGKAS:
    kepala.append('| %d | %s | %d | %s |' % (no, judul, n, 'LULUS' if lulus else 'GAGAL'))
kepala += ['', '---', '']
with open(OUT_MD, 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(kepala + MD).rstrip('\n') + '\n')
print('Dokumen ditulis:', OUT_MD)
for no, judul, lulus, n, gagal in RINGKAS:
    print('Skenario %d: %s (%d pemeriksaan)%s' % (no, 'LULUS' if lulus else 'GAGAL', n, '' if lulus else ' -> ' + '; '.join(gagal)))
sys.exit(0 if all((r[2] for r in RINGKAS)) else 1)
