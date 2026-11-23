from app.konstanta import DETAIL_DIPINJAM, KONDISI_BAIK
from app.models.alat import Alat
from app.repository.repo_dasar import RepoDasar


class RepoAlat(RepoDasar):

    def ambil(self, kode, kunci=False):
        baris = self.db.query_satu('SELECT * FROM alat WHERE kode = %s' + self.kunci_sql(kunci), (kode,))
        return Alat.dari_dict(baris) if baris else None

    def semua(self, batas=None, mulai=0):
        halaman, param = self.potongan_halaman(batas, mulai)
        return [Alat.dari_dict(b) for b in self.db.query('SELECT * FROM alat ORDER BY kode' + halaman, param)]

    def jumlah(self):
        return self.db.query_satu('SELECT COUNT(*) AS n FROM alat')['n']

    def cari(self, kata_kunci):
        syarat, param = self.syarat_kata(kata_kunci, ('kode', 'nama', 'kategori'))
        sql = 'SELECT * FROM alat WHERE ' + syarat + ' ORDER BY (kode = %s) DESC, kode'
        return [Alat.dari_dict(b) for b in self.db.query(sql, param + (kata_kunci.strip(),))]

    def per_status(self, status):
        return [Alat.dari_dict(b) for b in self.db.query('SELECT * FROM alat WHERE status = %s ORDER BY kode', (status,))]

    def rusak(self):
        return [Alat.dari_dict(b) for b in self.db.query('SELECT * FROM alat WHERE kondisi <> %s ORDER BY kode', (KONDISI_BAIK,))]

    def daftar_kategori(self):
        return [b['kategori'] for b in self.db.query('SELECT DISTINCT kategori FROM alat ORDER BY kategori')]

    def kategori_sama(self, kategori):
        baris = self.db.query_satu('SELECT kategori FROM alat WHERE LOWER(kategori) = LOWER(%s) LIMIT 1', (kategori,))
        return baris['kategori'] if baris else None

    def tambah(self, alat):
        self.db.eksekusi('INSERT INTO alat (kode, nama, kategori, kondisi, status) VALUES (%s, %s, %s, %s, %s)', (alat.kode, alat.nama, alat.kategori, alat.kondisi, alat.status))

    def ubah(self, alat):
        self.db.eksekusi('UPDATE alat SET nama = %s, kategori = %s, kondisi = %s, status = %s WHERE kode = %s', (alat.nama, alat.kategori, alat.kondisi, alat.status, alat.kode))

    def set_status(self, kode, status, kondisi=None):
        if kondisi is None:
            self.db.eksekusi('UPDATE alat SET status = %s WHERE kode = %s', (status, kode))
        else:
            self.db.eksekusi('UPDATE alat SET status = %s, kondisi = %s WHERE kode = %s', (status, kondisi, kode))

    def hapus(self, kode):
        self.db.eksekusi('DELETE FROM alat WHERE kode = %s', (kode,))

    def punya_riwayat(self, kode):
        return self.db.query_satu('SELECT 1 AS ada FROM detail_transaksi WHERE kode_alat = %s LIMIT 1', (kode,)) is not None

    def dalam_transaksi_aktif(self, kode):
        return self.db.query_satu('SELECT 1 AS ada FROM detail_transaksi WHERE kode_alat = %s AND status = %s LIMIT 1', (kode, DETAIL_DIPINJAM)) is not None
