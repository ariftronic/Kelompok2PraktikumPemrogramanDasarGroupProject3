import unittest
from app.konstanta import KONDISI_RUSAK_BERAT, STATUS_TERSEDIA, STATUS_TIDAK_TERSEDIA
from tests.dasar_db import DasarDB


class UjiMahasiswa(DasarDB):

    def test_tambah_tersimpan_di_tabel_dan_log(self):
        m = self.mahasiswa.tambah(' m001 ', '  Andi   Pratama ', '081234567890')
        self.assertEqual((m.nim, m.nama), ('M001', 'Andi Pratama'))
        self.assertEqual(self.db.query('SELECT * FROM mahasiswa'), [{'nim': 'M001', 'nama': 'Andi Pratama', 'no_hp': '081234567890', 'status_aktif': 'tidak aktif'}])
        self.assertIn('Mahasiswa M001 ditambahkan', self.logger.baca_terakhir(5)[-1])

    def test_no_hp_kosong_disimpan_null(self):
        self.mahasiswa.tambah('M001', 'Andi', '')
        self.assertIsNone(self.db.query_satu('SELECT no_hp FROM mahasiswa')['no_hp'])
        self.assertEqual(self.mahasiswa.ambil('m001').no_hp, '')

    def test_nim_ganda_ditolak_dan_tabel_tidak_berubah(self):
        self.mahasiswa.tambah('M001', 'Andi', '081234567890')
        sebelum = self.isi_tabel()
        with self.assertRaises(ValueError) as konteks:
            self.mahasiswa.tambah('m001', 'Budi', '081111111111')
        self.assertIn('sudah terdaftar', str(konteks.exception))
        self.assertEqual(self.isi_tabel(), sebelum)

    def test_tanda_kutip_dan_upaya_injeksi_tersimpan_apa_adanya(self):
        for nim, nama in (('M001', "Siti O'Neil"), ('M002', "x'); DROP TABLE mahasiswa; --")):
            self.mahasiswa.tambah(nim, nama, '')
        self.assertEqual([m.nama for m in self.mahasiswa.semua()], ["Siti O'Neil", "x'); DROP TABLE mahasiswa; --"])
        self.assertEqual([m.nim for m in self.mahasiswa.cari("o'neil")], ['M001'])

    def test_edit_dan_kosongkan_no_hp(self):
        self.mahasiswa.tambah('M001', 'Andi', '081234567890')
        self.mahasiswa.edit('M001', nama='Andi Pratama', no_hp='-')
        m = self.mahasiswa.ambil('M001')
        self.assertEqual((m.nama, m.no_hp), ('Andi Pratama', ''))

    def test_cari_per_kata_dan_halaman(self):
        for i, nama in enumerate(('Andi Pratama', 'Budi Santoso', 'Andi Wijaya'), start=1):
            self.mahasiswa.tambah('M00%d' % i, nama, '')
        self.assertEqual([m.nim for m in self.mahasiswa.cari('andi')], ['M001', 'M003'])
        self.assertEqual([m.nim for m in self.mahasiswa.cari('andi wij')], ['M003'])
        self.assertEqual([m.nim for m in self.mahasiswa.semua(2, 1)], ['M002', 'M003'])
        self.assertEqual(self.mahasiswa.jumlah(), 3)
        with self.assertRaises(ValueError):
            self.mahasiswa.cari('  ')

    def test_hapus_ditolak_bila_ada_transaksi_aktif_atau_riwayat(self):
        self.isi_contoh()
        self.transaksi.buat('M001', ['A001'])
        sebelum = self.isi_tabel()
        with self.assertRaises(ValueError) as konteks:
            self.mahasiswa.hapus('M001')
        self.assertIn('transaksi aktif', str(konteks.exception))
        self.assertEqual(self.isi_tabel(), sebelum)
        self.pengembalian.kembalikan('T001', 'A001', 'baik')
        with self.assertRaises(ValueError) as konteks:
            self.mahasiswa.hapus('M001')
        self.assertIn('riwayat', str(konteks.exception))
        self.mahasiswa.hapus('M002')
        self.assertFalse(self.mahasiswa.ada('M002'))

    def test_input_tidak_valid_ditolak(self):
        for nim, nama, hp in (('', 'Andi', ''), ('M 1', 'Andi', ''), ('M001', '', ''), ('M001', '123', ''), ('M001', 'Andi', 'abc')):
            with self.assertRaises(ValueError, msg=(nim, nama, hp)):
                self.mahasiswa.tambah(nim, nama, hp)
        self.assertEqual(self.jumlah('mahasiswa'), 0)


class UjiAlat(DasarDB):

    def test_tambah_dengan_kategori_baru_dan_status_mengikuti_kondisi(self):
        self.alat.tambah('A001', 'Kamera', 'Perangkat Multimedia')
        self.alat.tambah('A002', 'Laptop', 'perangkat komputasi', 'rusak berat')
        self.alat.tambah('A003', 'Tripod', 'PERANGKAT MULTIMEDIA')
        self.assertEqual(self.alat.daftar_kategori(), ['perangkat komputasi', 'perangkat multimedia'])
        self.assertEqual(self.alat.ambil('A003').kategori, 'perangkat multimedia')
        self.assertEqual(self.status_alat('A002'), STATUS_TIDAK_TERSEDIA)

    def test_kode_ganda_ditolak(self):
        self.alat.tambah('A001', 'Kamera', 'multimedia')
        with self.assertRaises(ValueError):
            self.alat.tambah('a001', 'Kamera Lain', 'multimedia')
        self.assertEqual(self.jumlah('alat'), 1)

    def test_cari_kode_sebagian_nama_kategori(self):
        self.isi_contoh()
        self.alat.tambah('A010', 'Kabel 50%', 'perangkat jaringan')
        self.assertEqual([a.kode for a in self.alat.cari('a002')], ['A002'])
        self.assertEqual([a.kode for a in self.alat.cari('kab')], ['A003', 'A010'])
        self.assertEqual([a.kode for a in self.alat.cari('jaringan')], ['A010'])
        self.assertEqual([a.kode for a in self.alat.cari('50%')], ['A010'])
        self.assertEqual([a.kode for a in self.alat.cari('%')], ['A010'])
        self.assertEqual(self.alat.cari('tidakada'), [])

    def test_edit_kondisi_mengubah_status_kecuali_sedang_dipinjam(self):
        self.isi_contoh()
        self.alat.edit('A002', kondisi=KONDISI_RUSAK_BERAT)
        self.assertEqual(self.status_alat('A002'), STATUS_TIDAK_TERSEDIA)
        self.alat.edit('A002', kondisi='baik')
        self.assertEqual(self.status_alat('A002'), STATUS_TERSEDIA)
        self.transaksi.buat('M001', ['A001'])
        self.alat.edit('A001', kondisi='rusak ringan')
        self.assertEqual(self.status_alat('A001'), 'dipinjam')

    def test_daftar_per_status(self):
        self.isi_contoh()
        self.alat.edit('A003', kondisi='rusak ringan')
        self.transaksi.buat('M001', ['A001'])
        self.assertEqual([a.kode for a in self.alat.tersedia()], ['A002'])
        self.assertEqual([a.kode for a in self.alat.dipinjam()], ['A001'])
        self.assertEqual([a.kode for a in self.alat.rusak()], ['A003'])

    def test_hapus_alat_dipinjam_atau_punya_riwayat_ditolak(self):
        self.isi_contoh()
        self.transaksi.buat('M001', ['A001'])
        with self.assertRaises(ValueError):
            self.alat.hapus('A001')
        self.pengembalian.kembalikan('T001', 'A001', 'baik')
        with self.assertRaises(ValueError):
            self.alat.hapus('A001')
        self.alat.hapus('A002')
        self.assertEqual([a.kode for a in self.alat.semua()], ['A001', 'A003'])


if __name__ == '__main__':
    unittest.main()
