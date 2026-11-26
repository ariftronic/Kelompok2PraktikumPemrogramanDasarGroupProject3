import unittest
from datetime import date
from unittest import mock
from app.database import Database, DatabaseError
from app.konstanta import MHS_AKTIF, MHS_TIDAK_AKTIF, STATUS_DIPINJAM, STATUS_TERSEDIA, STATUS_TIDAK_TERSEDIA, TRX_SEBAGIAN, TRX_SELESAI
from app.logger import Logger
from app.manager.manager_transaksi import ManagerTransaksi
from app.repository.repo_alat import RepoAlat
from tests.dasar_db import DasarDB, konfigurasi_uji


class UjiPengembalian(DasarDB):

    def setUp(self):
        super().setUp()
        self.isi_contoh()
        self.transaksi.buat('M001', ['A001', 'A002', 'A003'])

    def test_pengembalian_sebagian(self):
        t = self.pengembalian.kembalikan('t001', 'a001', 'baik')
        self.assertEqual(t.status, TRX_SEBAGIAN)
        self.assertEqual(self.db.query_satu("SELECT status FROM transaksi WHERE id = 'T001'")['status'], TRX_SEBAGIAN)
        self.assertEqual([self.status_alat(k) for k in ('A001', 'A002', 'A003')], [STATUS_TERSEDIA, STATUS_DIPINJAM, STATUS_DIPINJAM])
        self.assertEqual([d.kode_alat for d in self.pengembalian.daftar_belum_kembali('T001')], ['A002', 'A003'])
        detail = self.db.query_satu("SELECT * FROM detail_transaksi WHERE kode_alat = 'A001'")
        self.assertEqual((detail['status'], detail['kondisi_kembali'], detail['tgl_kembali']), ('dikembalikan', 'baik', date.today()))
        self.assertEqual(self.mahasiswa.ambil('M001').status_aktif, MHS_AKTIF)

    def test_rusak_tidak_kembali_tersedia_lalu_transaksi_selesai(self):
        self.pengembalian.kembalikan('T001', 'A001', 'baik')
        self.pengembalian.kembalikan('T001', 'A002', 'rusak ringan')
        t = self.pengembalian.kembalikan('T001', 'A003', 'rusak berat')
        self.assertEqual(t.status, TRX_SELESAI)
        self.assertEqual([self.status_alat(k) for k in ('A002', 'A003')], [STATUS_TIDAK_TERSEDIA, STATUS_TIDAK_TERSEDIA])
        self.assertEqual([a.kode for a in self.alat.tersedia()], ['A001'])
        self.assertEqual([a.kode for a in self.alat.rusak()], ['A002', 'A003'])
        self.assertEqual(self.mahasiswa.ambil('M001').status_aktif, MHS_TIDAK_AKTIF)

    def test_pengembalian_tidak_valid_ditolak_tanpa_perubahan(self):
        self.pengembalian.kembalikan('T001', 'A001', 'baik')
        sebelum = self.isi_tabel()
        for id_trx, kode, kondisi in (('T001', 'A001', 'baik'), ('T001', 'A999', 'baik'), ('T999', 'A002', 'baik'), ('T001', 'A002', 'hancur')):
            with self.assertRaises(ValueError, msg=(id_trx, kode, kondisi)):
                self.pengembalian.kembalikan(id_trx, kode, kondisi)
        self.assertEqual(self.isi_tabel(), sebelum)

    def test_gagal_di_tengah_dibatalkan_semua(self):
        sebelum = self.isi_tabel()
        with mock.patch.object(RepoAlat, 'set_status', side_effect=DatabaseError('koneksi putus (simulasi)')):
            with self.assertRaises(DatabaseError):
                self.pengembalian.kembalikan('T001', 'A001', 'rusak berat')
        self.assertEqual(self.isi_tabel(), sebelum)

    def test_data_tetap_ada_setelah_koneksi_baru(self):
        self.pengembalian.kembalikan('T001', 'A001', 'baik')
        db_baru = Database(konfigurasi_uji())
        db_baru.sambung()
        self.addCleanup(db_baru.tutup)
        t = ManagerTransaksi(db_baru, Logger(db_baru, 'Tes')).ambil('T001')
        self.assertEqual((t.status, [d.status for d in t.daftar_detail]), (TRX_SEBAGIAN, ['dikembalikan', 'dipinjam', 'dipinjam']))

    def test_keterlambatan_dicatat_di_log(self):
        self.db.eksekusi("UPDATE transaksi SET tgl_pinjam = '2026-01-01', batas_kembali = '2026-01-08' WHERE id = 'T001'")
        self.pengembalian.kembalikan('T001', 'A001', 'baik')
        self.assertIn('TERLAMBAT', self.logger.baca_terakhir(1)[0])


if __name__ == '__main__':
    unittest.main()
