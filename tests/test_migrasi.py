import io
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from scripts import migrate_txt
from tests.dasar_db import DasarDB, konfigurasi_uji

DIR_SAMPEL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data_sampel')


class UjiMigrasi(DasarDB):

    def jalankan(self, *argumen):
        layar = io.StringIO()
        with redirect_stdout(layar):
            kode = migrate_txt.main(list(argumen), konfigurasi=konfigurasi_uji())
        return kode, layar.getvalue()

    def test_data_sampel_pindah_utuh(self):
        kode, layar = self.jalankan('--sumber', DIR_SAMPEL)
        self.assertEqual(kode, 0, layar)
        self.assertEqual([self.jumlah(t) for t in ('mahasiswa', 'alat', 'transaksi', 'detail_transaksi')], [5, 10, 3, 5])
        self.assertEqual(self.transaksi.ambil('T003').status, 'sebagian dikembalikan')
        self.assertIsNone(self.db.query_satu("SELECT no_hp FROM mahasiswa WHERE nim = 'M005'")['no_hp'])
        kode, layar = self.jalankan('--sumber', DIR_SAMPEL)
        self.assertEqual(kode, 1)
        self.assertIn('sudah berisi data', layar)
        kode, _ = self.jalankan('--sumber', DIR_SAMPEL, '--kosongkan')
        self.assertEqual((kode, self.jumlah('mahasiswa')), (0, 5))

    def test_baris_rusak_dilewati_dan_status_diselaraskan(self):
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        for nama in os.listdir(DIR_SAMPEL):
            shutil.copy(os.path.join(DIR_SAMPEL, nama), folder)
        with open(os.path.join(folder, 'alat.txt'), 'a', encoding='utf-8') as f:
            f.write('A777|Kolom Kurang|jaringan\n')
        with open(os.path.join(folder, 'transaksi.txt'), 'a', encoding='utf-8') as f:
            f.write('T009|M999|2026-11-01|2026-11-08|dipinjam\n')
        with open(os.path.join(folder, 'mahasiswa.txt'), 'a', encoding='utf-8') as f:
            f.write('M001|Ganda|081111111111|tidak aktif\n')
        with open(os.path.join(folder, 'alat.txt'), 'r+', encoding='utf-8') as f:
            isi = f.read().replace('A003|Power Supply DC|sumber daya|baik|tersedia', 'A003|Power Supply DC|sumber daya|baik|dipinjam')
            f.seek(0)
            f.write(isi)
            f.truncate()
        kode, layar = self.jalankan('--sumber', folder)
        self.assertEqual(kode, 0, layar)
        self.assertEqual(sum((1 for b in layar.splitlines() if b.startswith('[PERINGATAN]'))), 3)
        self.assertIn('status diselaraskan 1', layar)
        self.assertEqual(self.status_alat('A003'), 'tersedia')
        self.assertEqual(self.jumlah('mahasiswa'), 5)

    def test_folder_tidak_ada(self):
        kode, layar = self.jalankan('--sumber', '/tidak/ada')
        self.assertEqual(kode, 1)
        self.assertEqual(self.jumlah('mahasiswa'), 0)


if __name__ == '__main__':
    unittest.main()
