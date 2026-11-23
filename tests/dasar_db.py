import io
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from app.config import baca_konfigurasi
from app.database import Database, DatabaseError
from app.konstanta import PATH_SCHEMA
from app.logger import Logger
from app.manager.manager_alat import ManagerAlat
from app.manager.manager_mahasiswa import ManagerMahasiswa
from app.manager.manager_pengembalian import ManagerPengembalian
from app.manager.manager_transaksi import ManagerTransaksi

URUTAN_HAPUS = ('detail_transaksi', 'transaksi', 'alat', 'mahasiswa', 'log_aktivitas')
_GAGAL = []


def konfigurasi_uji():
    k = baca_konfigurasi()
    k['database'] = os.environ.get('TEST_DB_NAME') or k['database'] + '_test'
    if not k['database'].endswith('_test'):
        raise unittest.SkipTest('Nama database uji harus berakhiran _test agar database utama tidak tersentuh.')
    k['petugas'] = 'Tes'
    return k


def buka_db_uji():
    if _GAGAL:
        raise unittest.SkipTest(_GAGAL[0])
    db = Database(konfigurasi_uji())
    try:
        db.sambung()
        db.pastikan_tabel(PATH_SCHEMA)
    except DatabaseError as e:
        _GAGAL.append('Database uji tidak tersedia (%s). Nyalakan MySQL di XAMPP lalu ulangi.' % e)
        raise unittest.SkipTest(_GAGAL[0])
    return db


def kosongkan(db):
    for tabel in URUTAN_HAPUS:
        db.eksekusi('DELETE FROM ' + tabel)


class DasarDB(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db = buka_db_uji()

    @classmethod
    def tearDownClass(cls):
        cls.db.tutup()

    def setUp(self):
        kosongkan(self.db)
        self.logger = Logger(self.db, 'Tes')
        self.mahasiswa = ManagerMahasiswa(self.db, self.logger)
        self.alat = ManagerAlat(self.db, self.logger)
        self.transaksi = ManagerTransaksi(self.db, self.logger)
        self.pengembalian = ManagerPengembalian(self.db, self.logger)
        self.folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.folder, ignore_errors=True)

    def isi_contoh(self):
        self.mahasiswa.tambah('M001', 'Andi', '081234567890')
        self.mahasiswa.tambah('M002', 'Budi', '')
        for kode, nama in (('A001', 'Kamera'), ('A002', 'Tripod'), ('A003', 'Kabel LAN')):
            self.alat.tambah(kode, nama, 'perangkat multimedia')

    def isi_tabel(self):
        return {t: self.db.query('SELECT * FROM %s ORDER BY 1, 2' % t) for t in URUTAN_HAPUS[:4]}

    def jumlah(self, tabel):
        return self.db.query_satu('SELECT COUNT(*) AS n FROM ' + tabel)['n']

    def status_alat(self, kode):
        return self.alat.ambil(kode).status

    def diam(self, fungsi, *arg, **kw):
        layar = io.StringIO()
        with redirect_stdout(layar):
            hasil = fungsi(*arg, **kw)
        return hasil, layar.getvalue()
