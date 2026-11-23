import os
import shutil
import tempfile
import unittest
from datetime import date
from unittest import mock
import pymysql
from app import validasi
from app.config import baca_konfigurasi
from app.database import Database, DatabaseError, terjemahkan
from app.file_manager import FileManager
from app.konstanta import KONDISI_BAIK, KONDISI_RUSAK_BERAT, STATUS_DIPINJAM, STATUS_TERSEDIA, STATUS_TIDAK_TERSEDIA, TRX_DIPINJAM, TRX_SEBAGIAN, TRX_SELESAI
from app.manager.manager_laporan import ManagerLaporan
from app.manager.manager_pengembalian import ManagerPengembalian
from app.models.alat import Alat
from app.models.mahasiswa import Mahasiswa
from app.models.transaksi import DetailTransaksi, Transaksi
from app.repository.repo_dasar import RepoDasar


class UjiValidasi(unittest.TestCase):

    def test_input_valid_dirapikan(self):
        self.assertEqual(validasi.validasi_nim(' m001 '), 'M001')
        self.assertEqual(validasi.validasi_nama('  Siti   O\'Neil '), "Siti O'Neil")
        self.assertEqual(validasi.validasi_no_hp('0812-3456-789'), '08123456789')
        self.assertEqual(validasi.validasi_no_hp('-'), '')
        self.assertEqual(validasi.validasi_kode_alat('a-01'), 'A-01')
        self.assertEqual(validasi.validasi_kondisi('Rusak_Berat'), KONDISI_RUSAK_BERAT)

    def test_input_tidak_valid_ditolak(self):
        for fungsi, nilai in ((validasi.validasi_nim, 'M 1'), (validasi.validasi_nim, ''), (validasi.validasi_nama, '123'), (validasi.validasi_no_hp, 'abc'), (validasi.validasi_kode_alat, 'A'), (validasi.validasi_kondisi, 'hancur'), (validasi.validasi_kategori, 'x' * 41)):
            with self.assertRaises(ValueError, msg=(fungsi.__name__, nilai)):
                fungsi(nilai)


class UjiModel(unittest.TestCase):

    def test_dari_dict_mengubah_null_dan_tanggal(self):
        mhs = Mahasiswa.dari_dict({'nim': 'M001', 'nama': 'Andi', 'no_hp': None, 'status_aktif': 'aktif'})
        self.assertEqual(mhs.ke_baris(), ['M001', 'Andi', '-', 'aktif'])
        detail = DetailTransaksi.dari_dict({'id_transaksi': 'T001', 'kode_alat': 'A001', 'status': 'dipinjam', 'kondisi_kembali': None, 'tgl_kembali': None})
        self.assertEqual(detail.ke_baris(), ['T001', 'A001', 'dipinjam', '-', '-'])
        t = Transaksi.dari_dict({'id': 'T001', 'nim': 'M001', 'tgl_pinjam': date(2026, 11, 2), 'batas_kembali': date(2026, 11, 9), 'status': 'dipinjam'}, [detail])
        self.assertEqual((t.tgl_pinjam, t.batas_kembali, len(t.daftar_detail)), ('2026-11-02', '2026-11-09', 1))
        alat = Alat.dari_dict({'kode': 'A001', 'nama': 'Kamera', 'kategori': 'multimedia', 'kondisi': 'baik', 'status': 'tersedia'})
        self.assertEqual(alat.status, STATUS_TERSEDIA)

    def test_status_transaksi_mengikuti_detail(self):
        t = Transaksi('T001', 'M001', '2026-11-10', '2026-11-17')
        t.daftar_detail = [DetailTransaksi('T001', 'A001'), DetailTransaksi('T001', 'A002')]
        t.perbarui_status()
        self.assertEqual(t.status, TRX_DIPINJAM)
        t.daftar_detail[0].kembalikan(KONDISI_BAIK, '2026-11-12')
        t.perbarui_status()
        self.assertEqual(t.status, TRX_SEBAGIAN)
        t.daftar_detail[1].kembalikan(KONDISI_RUSAK_BERAT, '2026-11-12')
        t.perbarui_status()
        self.assertEqual((t.status, t.masih_aktif()), (TRX_SELESAI, False))

    def test_status_alat_mengikuti_kondisi(self):
        alat = Alat('A001', 'Kamera', 'multimedia')
        alat.tandai_dipinjam()
        self.assertEqual(alat.status, STATUS_DIPINJAM)
        with self.assertRaises(ValueError):
            alat.tandai_dipinjam()
        alat.tandai_dikembalikan('rusak ringan')
        self.assertEqual(alat.status, STATUS_TIDAK_TERSEDIA)
        alat.tandai_dikembalikan('baik')
        self.assertEqual(alat.status, STATUS_TERSEDIA)

    def test_baris_txt_lama_divalidasi(self):
        with self.assertRaises(ValueError):
            Transaksi.dari_baris(['T001', 'M001', '2026-11-2', '2026-11-08', 'dipinjam'])
        with self.assertRaises(ValueError):
            DetailTransaksi.dari_baris(['T001', 'A001', 'dipinjam', 'baik', '-'])

    def test_hari_terlambat(self):
        t = Transaksi('T001', 'M001', '2026-11-01', '2026-11-08')
        self.assertEqual(ManagerPengembalian.hari_terlambat(t, date(2026, 11, 8)), 0)
        self.assertEqual(ManagerPengembalian.hari_terlambat(t, date(2026, 11, 11)), 3)


class UjiKonfigurasi(unittest.TestCase):

    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.folder, ignore_errors=True)
        lingkungan = mock.patch.dict(os.environ, {}, clear=True)
        lingkungan.start()
        self.addCleanup(lingkungan.stop)

    def tulis_env(self, isi):
        path = os.path.join(self.folder, '.env')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(isi)
        return path

    def test_nilai_bawaan_xampp_bila_env_tidak_ada(self):
        k = baca_konfigurasi(os.path.join(self.folder, 'tidak_ada.env'))
        self.assertEqual((k['host'], k['port'], k['user'], k['password'], k['database']), ('127.0.0.1', 3306, 'root', '', 'peminjaman_lab'))

    def test_isi_env_dipakai(self):
        k = baca_konfigurasi(self.tulis_env('DB_HOST=db.contoh.test\nDB_PORT=12345\nDB_USER=lab\nDB_PASSWORD=rahasia\nDB_NAME=lab_db\nNAMA_PETUGAS=Arif\n'))
        self.assertEqual((k['host'], k['port'], k['user'], k['password'], k['database'], k['petugas']), ('db.contoh.test', 12345, 'lab', 'rahasia', 'lab_db', 'Arif'))

    def test_isi_env_salah_ditolak(self):
        with self.assertRaises(ValueError):
            baca_konfigurasi(self.tulis_env('DB_PORT=tiga\n'))
        os.environ.pop('DB_PORT', None)
        with self.assertRaises(ValueError):
            baca_konfigurasi(self.tulis_env('DB_SSL_CA=/tidak/ada/ca.pem\n'))


class UjiDatabaseTanpaServer(unittest.TestCase):

    def test_kode_error_diterjemahkan_menjadi_pesan_ramah(self):
        for kode, kata in ((2003, 'Tidak dapat terhubung'), (1045, 'Login database ditolak'), (1049, 'Database belum ada'), (1062, 'sudah ada'), (1451, 'tidak dapat dihapus'), (1205, 'pengguna lain'), (4025, 'aturan tabel')):
            e = terjemahkan(pymysql.err.OperationalError(kode, 'pesan mentah SQL'))
            self.assertIsInstance(e, DatabaseError)
            self.assertEqual(e.kode, kode)
            self.assertIn(kata, str(e))
            self.assertNotIn('pesan mentah', str(e))

    def test_query_tanpa_koneksi_ditolak(self):
        with self.assertRaises(DatabaseError):
            Database({'host': '127.0.0.1', 'port': 1, 'user': 'x', 'password': '', 'database': 'x', 'ssl_ca': ''}).query('SELECT 1')

    def test_server_tidak_terjangkau(self):
        db = Database({'host': '127.0.0.1', 'port': 1, 'user': 'x', 'password': '', 'database': 'x', 'ssl_ca': ''})
        with self.assertRaises(DatabaseError) as konteks:
            db.sambung()
        self.assertEqual(konteks.exception.kode, 2003)


class UjiBantuanSQL(unittest.TestCase):

    def test_pola_like_meng_escape_karakter_khusus(self):
        self.assertEqual(RepoDasar.pola_like('50%_a\\b'), '%50\\%\\_a\\\\b%')

    def test_syarat_kata_hanya_berisi_placeholder(self):
        syarat, param = RepoDasar(None).syarat_kata("kamera O'Neil", ('kode', 'nama'))
        self.assertEqual(syarat, '(kode LIKE %s OR nama LIKE %s) AND (kode LIKE %s OR nama LIKE %s)')
        self.assertEqual(param, ('%kamera%', '%kamera%', "%O'Neil%", "%O'Neil%"))
        self.assertNotIn("O'Neil", syarat)

    def test_tabel_laporan_rata_kiri(self):
        self.assertEqual(ManagerLaporan.tabel(('No', 'Nama'), [[1, 'Kamera Digital'], [10, 'Tripod']]), ['No  Nama', '--  --------------', '1   Kamera Digital', '10  Tripod'])


class UjiFileManager(unittest.TestCase):

    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.folder, ignore_errors=True)

    def test_baca_txt_lama_dan_lewati_baris_salah(self):
        with open(os.path.join(self.folder, 'alat.txt'), 'w', encoding='utf-8') as f:
            f.write('A001|Kamera|multimedia|baik|tersedia\nA002|kurang\n\nA003|Tripod||baik|tersedia\n')
        fm = FileManager(self.folder)
        with mock.patch('builtins.print'):
            hasil = fm.baca_baris('alat.txt')
        self.assertEqual(hasil, [['A001', 'Kamera', 'multimedia', 'baik', 'tersedia']])
        self.assertEqual(len(fm.daftar_peringatan), 2)
        self.assertEqual(fm.baca_baris('tidak_ada.txt'), [])

    def test_tulis_teks_membuat_folder_dan_tanpa_file_sementara(self):
        fm = FileManager(os.path.join(self.folder, 'laporan'))
        fm.tulis_teks('a.txt', ['baris 1', 'baris\n2'])
        with open(fm.path_file('a.txt'), encoding='utf-8') as f:
            self.assertEqual(f.read(), 'baris 1\nbaris 2\n')
        self.assertEqual(os.listdir(fm.direktori), ['a.txt'])


if __name__ == '__main__':
    unittest.main()
