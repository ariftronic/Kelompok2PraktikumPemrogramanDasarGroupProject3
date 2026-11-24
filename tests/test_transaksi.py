"""Tes peminjaman pada database uji (Skenario 2, 3, 8; Aturan 1, 2, 3, 7, 8; transaction dan konkurensi)."""
import unittest
from datetime import date, timedelta
from unittest import mock
from app.database import Database, DatabaseError
from app.konstanta import FORMAT_TANGGAL, MAKS_HARI_PINJAM, MHS_AKTIF, STATUS_DIPINJAM, STATUS_TERSEDIA
from app.logger import Logger
from app.manager.manager_mahasiswa import ManagerMahasiswa
from app.manager.manager_transaksi import ManagerTransaksi
from app.repository.repo_transaksi import RepoTransaksi
from tests.dasar_db import DasarDB, konfigurasi_uji


class UjiBuatTransaksi(DasarDB):

    def setUp(self):
        super().setUp()
        self.isi_contoh()

    def test_satu_transaksi_beberapa_alat(self):
        t = self.transaksi.buat(' m001 ', ['a001', ' a002'])
        hari_ini = date.today()
        self.assertEqual((t.id_transaksi, t.nim, t.tgl_pinjam, t.batas_kembali), ('T001', 'M001', hari_ini.strftime(FORMAT_TANGGAL), (hari_ini + timedelta(days=MAKS_HARI_PINJAM)).strftime(FORMAT_TANGGAL)))
        self.assertEqual(self.db.query('SELECT id_transaksi, kode_alat, status, kondisi_kembali FROM detail_transaksi ORDER BY kode_alat'), [{'id_transaksi': 'T001', 'kode_alat': 'A001', 'status': 'dipinjam', 'kondisi_kembali': None}, {'id_transaksi': 'T001', 'kode_alat': 'A002', 'status': 'dipinjam', 'kondisi_kembali': None}])
        self.assertEqual([self.status_alat(k) for k in ('A001', 'A002', 'A003')], [STATUS_DIPINJAM, STATUS_DIPINJAM, STATUS_TERSEDIA])
        self.assertEqual(self.mahasiswa.ambil('M001').status_aktif, MHS_AKTIF)
        self.assertEqual([x.kode_alat for x in self.transaksi.ambil('t001').daftar_detail], ['A001', 'A002'])
        self.assertIn('Transaksi T001 dibuat oleh M001 (A001, A002)', self.logger.baca_terakhir(1)[0])

    def test_penolakan_tidak_mengubah_database(self):
        self.transaksi.buat('M001', ['A001'])
        sebelum = self.isi_tabel()
        kasus = [('M002', ['A001']), ('M002', ['A002', 'A001']), ('M999', ['A002']), ('M002', ['A999']), ('M002', ['A002', 'a002']), ('M002', [])]
        for nim, kode in kasus:
            with self.assertRaises(ValueError, msg=(nim, kode)):
                self.transaksi.buat(nim, kode)
        self.assertEqual(self.isi_tabel(), sebelum)
        self.assertEqual(self.status_alat('A002'), STATUS_TERSEDIA)

    def test_maksimal_dua_transaksi_aktif(self):
        self.transaksi.buat('M001', ['A001'])
        self.transaksi.buat('M001', ['A002'])
        with self.assertRaises(ValueError) as konteks:
            self.transaksi.buat('M001', ['A003'])
        self.assertIn('2 transaksi aktif', str(konteks.exception))
        self.pengembalian.kembalikan('T001', 'A001', 'baik')
        self.assertEqual(self.transaksi.buat('M001', ['A003']).id_transaksi, 'T003')

    def test_gagal_di_tengah_transaction_di_rollback(self):

        def gagal_setelah_header(repo, transaksi):
            repo.db.eksekusi('INSERT INTO transaksi (id, nim, tgl_pinjam, batas_kembali) VALUES (%s, %s, CURDATE(), CURDATE())', (transaksi.id_transaksi, transaksi.nim))
            raise DatabaseError('disk penuh (simulasi)')
        sebelum = self.isi_tabel()
        with mock.patch.object(RepoTransaksi, 'tambah', gagal_setelah_header):
            with self.assertRaises(DatabaseError):
                self.transaksi.buat('M001', ['A001', 'A002'])
        self.assertEqual(self.isi_tabel(), sebelum)

    def test_id_urut_angka_dan_tidak_ganda(self):
        self.db.eksekusi("INSERT INTO transaksi VALUES ('T999', 'M002', '2026-01-01', '2026-01-08', 'selesai')")
        self.db.eksekusi("INSERT INTO detail_transaksi VALUES ('T999', 'A003', 'dikembalikan', 'baik', '2026-01-02')")
        self.assertEqual(self.transaksi.buat('M001', ['A001']).id_transaksi, 'T1000')
        self.assertEqual([t.id_transaksi for t in self.transaksi.semua()], ['T999', 'T1000'])
        self.assertEqual([t.id_transaksi for t in self.transaksi.semua(1, 1)], ['T1000'])

    def test_id_bentrok_dari_komputer_lain_diulang(self):
        asli = RepoTransaksi.id_baru
        panggilan = []

        def id_kedaluwarsa(repo):
            panggilan.append(1)
            return 'T001' if len(panggilan) == 1 else asli(repo)
        self.transaksi.buat('M002', ['A003'])
        with mock.patch.object(RepoTransaksi, 'id_baru', id_kedaluwarsa):
            t = self.transaksi.buat('M001', ['A001'])
        self.assertEqual((t.id_transaksi, len(panggilan)), ('T002', 2))
        self.assertEqual(self.jumlah('transaksi'), 2)


class UjiDuaKlien(DasarDB):
    """Dua koneksi terpisah mensimulasikan dua komputer yang memakai database yang sama."""

    def setUp(self):
        super().setUp()
        self.isi_contoh()
        self.db_b = Database(konfigurasi_uji())
        self.db_b.sambung()
        self.addCleanup(self.db_b.tutup)

    def test_data_baru_langsung_terlihat_di_klien_lain(self):
        mahasiswa_b = ManagerMahasiswa(self.db_b, Logger(self.db_b, 'B'))
        self.assertEqual(mahasiswa_b.jumlah(), 2)
        self.mahasiswa.tambah('M003', 'Citra', '')
        self.assertEqual(mahasiswa_b.jumlah(), 3)
        self.assertEqual(mahasiswa_b.ambil('M003').nama, 'Citra')

    def test_alat_yang_sedang_diproses_klien_lain_tidak_bisa_dipinjam_ganda(self):
        transaksi_b = ManagerTransaksi(self.db_b, Logger(self.db_b, 'B'))
        self.db_b.eksekusi('SET SESSION innodb_lock_wait_timeout = 1')
        with self.db.transaksi():
            self.db.query('SELECT * FROM alat WHERE kode = %s FOR UPDATE', ('A001',))
            with self.assertRaises(DatabaseError) as konteks:
                transaksi_b.buat('M002', ['A001'])
            self.assertEqual(konteks.exception.kode, 1205)
            self.assertIn('pengguna lain', str(konteks.exception))
        self.transaksi.buat('M001', ['A001'])
        with self.assertRaises(ValueError):
            transaksi_b.buat('M002', ['A001'])
        self.assertEqual(self.jumlah('transaksi'), 1)


if __name__ == '__main__':
    unittest.main()
