from app.konstanta import TRX_SELESAI
from app.models.mahasiswa import Mahasiswa
from app.repository.repo_dasar import RepoDasar


class RepoMahasiswa(RepoDasar):

    def ambil(self, nim, kunci=False):
        baris = self.db.query_satu('SELECT * FROM mahasiswa WHERE nim = %s' + self.kunci_sql(kunci), (nim,))
        return Mahasiswa.dari_dict(baris) if baris else None

    def semua(self, batas=None, mulai=0):
        halaman, param = self.potongan_halaman(batas, mulai)
        return [Mahasiswa.dari_dict(b) for b in self.db.query('SELECT * FROM mahasiswa ORDER BY nim' + halaman, param)]

    def jumlah(self):
        return self.db.query_satu('SELECT COUNT(*) AS n FROM mahasiswa')['n']

    def cari(self, kata_kunci):
        syarat, param = self.syarat_kata(kata_kunci, ('nim', 'nama'))
        return [Mahasiswa.dari_dict(b) for b in self.db.query('SELECT * FROM mahasiswa WHERE ' + syarat + ' ORDER BY nim', param)]

    def tambah(self, mhs):
        self.db.eksekusi('INSERT INTO mahasiswa (nim, nama, no_hp, status_aktif) VALUES (%s, %s, %s, %s)', (mhs.nim, mhs.nama, mhs.no_hp or None, mhs.status_aktif))

    def ubah(self, mhs):
        self.db.eksekusi('UPDATE mahasiswa SET nama = %s, no_hp = %s WHERE nim = %s', (mhs.nama, mhs.no_hp or None, mhs.nim))

    def hapus(self, nim):
        self.db.eksekusi('DELETE FROM mahasiswa WHERE nim = %s', (nim,))

    def jumlah_transaksi_aktif(self, nim):
        return self.db.query_satu('SELECT COUNT(*) AS n FROM transaksi WHERE nim = %s AND status <> %s', (nim, TRX_SELESAI))['n']

    def punya_riwayat(self, nim):
        return self.db.query_satu('SELECT 1 AS ada FROM transaksi WHERE nim = %s LIMIT 1', (nim,)) is not None

    def set_status_aktif(self, nim, status):
        self.db.eksekusi('UPDATE mahasiswa SET status_aktif = %s WHERE nim = %s', (status, nim))
