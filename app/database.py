from contextlib import contextmanager
import pymysql
from pymysql.cursors import DictCursor
from app.konstanta import BATAS_WAKTU_KONEKSI, MODE_SQL_KETAT

PESAN_ERROR = {
    2003: 'Tidak dapat terhubung ke database. Pastikan MySQL di XAMPP menyala (atau internet tersambung untuk database online) dan DB_HOST/DB_PORT di .env benar.',
    2006: 'Koneksi ke database terputus. Periksa XAMPP atau koneksi internet, lalu coba lagi.',
    2013: 'Koneksi ke database terputus. Periksa XAMPP atau koneksi internet, lalu coba lagi.',
    1045: 'Login database ditolak. Periksa DB_USER dan DB_PASSWORD di .env.',
    1044: 'User database tidak punya akses ke database ini. Periksa DB_USER dan DB_NAME di .env.',
    1049: 'Database belum ada. Buat lewat phpMyAdmin atau jalankan database/schema.sql.',
    1062: 'Data dengan kunci tersebut sudah ada.',
    1451: 'Data masih tercatat di transaksi, tidak dapat dihapus.',
    1452: 'NIM atau kode alat yang dirujuk tidak ditemukan.',
    1205: 'Data sedang diproses pengguna lain. Coba lagi.',
    1213: 'Data sedang diproses pengguna lain. Coba lagi.',
    1265: 'Nilai tidak sesuai aturan tabel.',
    1364: 'Ada kolom wajib yang belum diisi.',
    1406: 'Isian terlalu panjang untuk kolom di database.',
    3819: 'Nilai tidak sesuai aturan tabel.',
    4025: 'Nilai tidak sesuai aturan tabel.',
}


class DatabaseError(Exception):

    def __init__(self, pesan, kode=None):
        super().__init__(pesan)
        self.kode = kode


def terjemahkan(error):
    kode = error.args[0] if error.args and isinstance(error.args[0], int) else None
    pesan = PESAN_ERROR.get(kode, 'Terjadi kesalahan database (kode %s).' % kode if kode else 'Terjadi kesalahan database.')
    return DatabaseError(pesan, kode)


class Database:

    def __init__(self, konfigurasi):
        self.konfigurasi = konfigurasi
        self._koneksi = None
        self._dalam_transaksi = False

    def _parameter(self, dengan_database=True):
        k = self.konfigurasi
        parameter = dict(host=k['host'], port=k['port'], user=k['user'], password=k['password'], charset='utf8mb4', cursorclass=DictCursor, autocommit=True, connect_timeout=BATAS_WAKTU_KONEKSI, init_command=MODE_SQL_KETAT)
        if dengan_database:
            parameter['database'] = k['database']
        if k.get('ssl_ca'):
            parameter['ssl'] = {'ca': k['ssl_ca']}
        return parameter

    def sambung(self, buat_database=True):
        try:
            self._koneksi = pymysql.connect(**self._parameter())
        except pymysql.err.MySQLError as e:
            if not (buat_database and e.args and e.args[0] == 1049):
                raise terjemahkan(e) from None
            self._buat_database()

    def _buat_database(self):
        nama = self.konfigurasi['database']
        if not nama.replace('_', '').isalnum():
            raise DatabaseError('DB_NAME hanya boleh berisi huruf, angka, dan garis bawah.')
        try:
            koneksi = pymysql.connect(**self._parameter(dengan_database=False))
            with koneksi.cursor() as kursor:
                kursor.execute('CREATE DATABASE IF NOT EXISTS `%s` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci' % nama)
            koneksi.select_db(nama)
            self._koneksi = koneksi
        except pymysql.err.MySQLError as e:
            raise DatabaseError(PESAN_ERROR[1049], 1049) if e.args and e.args[0] in (1044, 1045) else terjemahkan(e) from None

    def tersambung(self):
        return self._koneksi is not None

    def tutup(self):
        if self._koneksi is not None:
            try:
                self._koneksi.close()
            except pymysql.err.Error:
                pass
            self._koneksi = None

    def _pastikan_koneksi(self):
        # Di luar transaction, koneksi yang terputus (misalnya server sempat mati) disambung ulang otomatis.
        if self._koneksi is None:
            raise DatabaseError('Belum terhubung ke database.')
        if not self._dalam_transaksi:
            try:
                self._koneksi.ping(reconnect=True)
            except pymysql.err.MySQLError as e:
                raise terjemahkan(e) from None

    def _kursor(self):
        self._pastikan_koneksi()
        return self._koneksi.cursor()

    def query(self, sql, parameter=()):
        try:
            with self._kursor() as kursor:
                kursor.execute(sql, parameter)
                return list(kursor.fetchall())
        except pymysql.err.MySQLError as e:
            raise terjemahkan(e) from None

    def query_satu(self, sql, parameter=()):
        hasil = self.query(sql, parameter)
        return hasil[0] if hasil else None

    def eksekusi(self, sql, parameter=()):
        try:
            with self._kursor() as kursor:
                return kursor.execute(sql, parameter)
        except pymysql.err.MySQLError as e:
            raise terjemahkan(e) from None

    @contextmanager
    def transaksi(self):
        if self._dalam_transaksi:
            yield self
            return
        self._pastikan_koneksi()
        try:
            self._koneksi.begin()
        except pymysql.err.MySQLError as e:
            raise terjemahkan(e) from None
        self._dalam_transaksi = True
        try:
            yield self
            self._koneksi.commit()
        except BaseException as e:
            try:
                self._koneksi.rollback()
            except pymysql.err.Error:
                pass
            if isinstance(e, pymysql.err.MySQLError):
                raise terjemahkan(e) from None
            raise
        finally:
            self._dalam_transaksi = False

    def jalankan_file_sql(self, path):
        try:
            with open(path, encoding='utf-8') as f:
                teks = '\n'.join((baris for baris in f.read().splitlines() if not baris.strip().startswith('--')))
        except OSError as e:
            raise DatabaseError('File SQL tidak dapat dibaca: %s (%s)' % (path, e))
        for pernyataan in (p.strip() for p in teks.split(';')):
            if pernyataan:
                self.eksekusi(pernyataan)

    def pastikan_tabel(self, path_schema):
        self.jalankan_file_sql(path_schema)
