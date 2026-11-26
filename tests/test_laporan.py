import os
import unittest
from datetime import date
from app.file_manager import FileManager
from app.manager.manager_laporan import ManagerLaporan
from tests.dasar_db import DasarDB


class UjiLaporan(DasarDB):

    def setUp(self):
        super().setUp()
        self.folder_laporan = os.path.join(self.folder, 'laporan')
        self.laporan = ManagerLaporan(self.db, self.logger, FileManager(self.folder_laporan))

    def baca(self, path):
        with open(path, encoding='utf-8') as f:
            return f.read()

    def test_statistik_kosong(self):
        data = self.laporan.statistik()
        self.assertEqual((data['total_transaksi'], data['transaksi_aktif'], data['transaksi_selesai'], data['alat_terbanyak'], data['mahasiswa_terbanyak']), (0, 0, 0, [], []))
        self.assertIn('  (belum ada peminjaman)', self.laporan.baris_statistik())

    def test_statistik_group_by(self):
        self.isi_contoh()
        self.transaksi.buat('M001', ['A001', 'A002'])
        self.pengembalian.kembalikan('T001', 'A001', 'baik')
        self.pengembalian.kembalikan('T001', 'A002', 'baik')
        self.transaksi.buat('M001', ['A001'])
        self.transaksi.buat('M002', ['A002', 'A003'])
        data = self.laporan.statistik()
        self.assertEqual((data['total_transaksi'], data['transaksi_aktif'], data['transaksi_selesai']), (3, 2, 1))
        self.assertEqual([(b['kode'], b['jumlah']) for b in data['alat_terbanyak']], [('A001', 2), ('A002', 2), ('A003', 1)])
        self.assertEqual([(b['nim'], b['jumlah']) for b in data['mahasiswa_terbanyak']], [('M001', 2), ('M002', 1)])
        self.assertIn('  1. A001 Kamera - 2 kali', self.laporan.baris_statistik())

    def test_transaksi_terlambat(self):
        self.isi_contoh()
        self.transaksi.buat('M001', ['A001'])
        self.transaksi.buat('M002', ['A002'])
        self.db.eksekusi("UPDATE transaksi SET tgl_pinjam = '2026-01-01', batas_kembali = '2026-01-08' WHERE id = 'T001'")
        hasil = self.laporan.terlambat(date(2026, 1, 11))
        self.assertEqual([(b['id'], b['hari']) for b in hasil], [('T001', 3)])
        self.assertIn('terlambat 3 hari', self.laporan.baris_terlambat(date(2026, 1, 11))[0])

    def test_ekspor_empat_laporan(self):
        self.isi_contoh()
        self.alat.edit('A003', kondisi='rusak berat')
        self.transaksi.buat('M001', ['A001', 'A002'])
        self.pengembalian.kembalikan('T001', 'A001', 'baik')
        isi = self.baca(self.laporan.ekspor_alat_dipinjam())
        self.assertIn('A002', isi)
        self.assertIn('M001 Andi', isi)
        self.assertIn('Jumlah alat yang sedang dipinjam: 1', isi)
        self.assertIn('rusak berat', self.baca(self.laporan.ekspor_alat_rusak()))
        riwayat = self.baca(self.laporan.ekspor_riwayat_mahasiswa('m001'))
        self.assertIn('sebagian dikembalikan', riwayat)
        self.assertEqual(riwayat.count('T001'), 2)
        self.assertIn('Transaksi masih aktif    : 1', self.baca(self.laporan.ekspor_statistik()))
        self.assertEqual(len(os.listdir(self.folder_laporan)), 4)
        with self.assertRaises(ValueError):
            self.laporan.ekspor_riwayat_mahasiswa('M999')
        baris = self.baca(self.laporan.ekspor_alat_dipinjam()).splitlines()
        self.assertEqual(len(baris[0]), max((len(b) for b in baris)))
        self.assertIn('Laporan diekspor ke laporan_alat_dipinjam_', self.logger.baca_terakhir(1)[0])


if __name__ == '__main__':
    unittest.main()
