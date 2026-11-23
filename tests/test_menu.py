import io
import os
import unittest
from contextlib import redirect_stdout
from unittest import mock
from app.database import DatabaseError
from app.file_manager import FileManager
from app.menu import AplikasiPeminjaman
from tests.dasar_db import DasarDB, konfigurasi_uji

DATA_AWAL = ['1', '1', 'M001', 'Andi Pratama', '081234567890', '1', 'M002', "Siti O'Neil", '', '0', '2', '1', 'A001', 'Kamera Digital', 'perangkat multimedia', '', '1', 'A002', 'Tripod', 'perangkat multimedia', '', '1', 'A003', 'Kabel LAN', 'perangkat jaringan', 'rusak berat', '0']


def input_berskrip(masukan):
    antrean = iter(masukan)

    def palsu(pesan=''):
        try:
            return next(antrean)
        except StopIteration:
            raise EOFError from None
    return palsu


class UjiMenu(DasarDB):

    def buat_aplikasi(self, **ganti):
        konfigurasi = konfigurasi_uji()
        konfigurasi.update(ganti)
        aplikasi = AplikasiPeminjaman(konfigurasi)
        aplikasi.file_laporan = FileManager(os.path.join(self.folder, 'laporan'))
        return aplikasi

    def jalankan(self, masukan, aplikasi=None):
        aplikasi = aplikasi or self.buat_aplikasi()
        layar = io.StringIO()
        with mock.patch('builtins.input', input_berskrip(masukan)), redirect_stdout(layar):
            aplikasi.jalankan()
        self.assertFalse(aplikasi.db is not None and aplikasi.db.tersambung(), 'koneksi harus ditutup saat keluar')
        return layar.getvalue()

    def test_alur_lengkap_tersimpan_di_database(self):
        layar = self.jalankan(DATA_AWAL + ['3', 'M001', 'A001, A002', '4', '5', 'T001', 'A001', '1', '7', '8', '9', '6', 'M001', '10', 'M001', '12', '13', '1', '0', '14', '11', '0'])
        self.assertNotIn('[DITOLAK]', layar)
        self.assertNotIn('Traceback', layar)
        self.assertEqual(self.jumlah('mahasiswa'), 2)
        self.assertEqual(self.mahasiswa.ambil('M002').nama, "Siti O'Neil")
        self.assertEqual(self.transaksi.ambil('T001').status, 'sebagian dikembalikan')
        self.assertEqual([self.status_alat(k) for k in ('A001', 'A002', 'A003')], ['tersedia', 'dipinjam', 'tidak tersedia'])
        for teks in ('Alat yang sedang dipinjam (1 data)', 'Alat yang rusak (1 data)', 'STATISTIK PEMINJAMAN', '[OK] Laporan disimpan di', 'Transaksi terlambat (per hari ini) (0 data)', 'Log aktivitas terbaru', 'Koneksi database ditutup'):
            self.assertIn(teks, layar)
        self.assertEqual(len(os.listdir(os.path.join(self.folder, 'laporan'))), 1)

    def test_penolakan_tampil_dan_database_tidak_berubah(self):
        self.jalankan(DATA_AWAL + ['3', 'M001', 'A001', '0'])
        sebelum = self.isi_tabel()
        layar = self.jalankan(['1', '1', 'm001', 'Budi', '', '3', 'M001', 'n', '3', 'M001', 'y', '0', '3', 'M002', 'A001', '3', 'M002', 'A003', '0'])
        self.assertEqual(layar.count('[DITOLAK]'), 4)
        self.assertIn('[DITOLAK] NIM M001 sudah terdaftar.', layar)
        self.assertIn('Dibatalkan.', layar)
        self.assertIn('[DITOLAK] Alat A001 tidak tersedia (status: dipinjam).', layar)
        self.assertIn('masih memiliki transaksi aktif', layar)
        self.assertEqual(self.isi_tabel(), sebelum)

    def test_koneksi_gagal_saat_mulai_tidak_crash(self):
        layar = io.StringIO()
        aplikasi = self.buat_aplikasi(port=1)
        with mock.patch('builtins.input', side_effect=AssertionError('menu tidak boleh tampil')), redirect_stdout(layar):
            aplikasi.jalankan()
        self.assertIn('[!] Koneksi database gagal: Tidak dapat terhubung ke database', layar.getvalue())
        self.assertIn('Program tidak dapat dimulai', layar.getvalue())
        aplikasi = self.buat_aplikasi(user='bukan_user', password='salah')
        with mock.patch('builtins.input', side_effect=AssertionError('menu tidak boleh tampil')), redirect_stdout(layar):
            aplikasi.jalankan()
        self.assertIn('Login database ditolak', layar.getvalue())

    def test_error_database_di_tengah_sesi_tidak_menghentikan_program(self):
        aplikasi = self.buat_aplikasi()
        layar = io.StringIO()
        masukan = input_berskrip(['1', '5', '0', '0', '1', '5', '0', '0'])
        with redirect_stdout(layar), mock.patch('builtins.input', masukan):
            self.assertTrue(aplikasi.siapkan())
            rusak = DatabaseError('Koneksi ke database terputus. Periksa XAMPP atau koneksi internet, lalu coba lagi.', 2013)
            with mock.patch.object(aplikasi.manager['alat'], 'jumlah', side_effect=rusak):
                aplikasi._loop_menu('MENU UTAMA', [('Kelola data alat', aplikasi.menu_alat)], 'Keluar')
            aplikasi._loop_menu('MENU UTAMA', [('Kelola data alat', aplikasi.menu_alat)], 'Keluar')
            aplikasi._keluar()
        self.assertIn('[!] [ERROR DATABASE] Koneksi ke database terputus', layar.getvalue())
        self.assertIn('Daftar alat (0 data)', layar.getvalue())

    def test_koneksi_yang_diputus_server_disambung_ulang_otomatis(self):
        aplikasi = self.buat_aplikasi()
        with redirect_stdout(io.StringIO()):
            self.assertTrue(aplikasi.siapkan())
        id_koneksi = aplikasi.db.query_satu('SELECT CONNECTION_ID() AS id')['id']
        self.db.eksekusi('KILL %s', (id_koneksi,))
        self.assertEqual(aplikasi.manager['mahasiswa'].jumlah(), 0)
        aplikasi.db.tutup()

    def test_daftar_panjang_per_halaman(self):
        for i in range(1, 26):
            self.db.eksekusi('INSERT INTO alat (kode, nama, kategori) VALUES (%s, %s, %s)', ('A%03d' % i, 'Alat %d' % i, 'umum'))
        layar = self.jalankan(['2', '5', 'q', '5', '', '0', '0'])
        self.assertIn('20. A020', layar)
        self.assertIn('(5 data berikutnya tidak ditampilkan)', layar)
        self.assertIn('25. A025', layar)

    def test_input_berhenti_di_tengah_isian_tetap_keluar_rapi(self):
        layar = self.jalankan(['1', '1', 'M001'])
        self.assertNotIn('[ERROR]', layar)
        self.assertIn('Koneksi database ditutup', layar)
        self.assertEqual(self.jumlah('mahasiswa'), 0)


if __name__ == '__main__':
    unittest.main()
