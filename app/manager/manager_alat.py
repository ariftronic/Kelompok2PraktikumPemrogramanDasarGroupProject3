from app import validasi
from app.database import DatabaseError
from app.konstanta import KONDISI_BAIK, STATUS_DIPINJAM, STATUS_TERSEDIA, STATUS_TIDAK_TERSEDIA
from app.manager.manager_dasar import ManagerDasar
from app.models.alat import Alat
from app.repository.repo_alat import RepoAlat


class ManagerAlat(ManagerDasar):

    NAMA_DATA = 'Alat'
    NAMA_KUNCI = 'kode'

    def _buat_repo(self, db):
        return RepoAlat(db)

    def cari_berdasarkan_kode(self, kode):
        return self.repo.ambil(self._kunci(kode))

    def daftar_kategori(self):
        return self.repo.daftar_kategori()

    def _normalisasi_kategori(self, kategori):
        # Kategori yang sudah ada dipakai dengan ejaan aslinya agar tidak muncul kategori ganda beda huruf.
        bersih = validasi.validasi_kategori(kategori)
        return self.repo.kategori_sama(bersih) or bersih.lower()

    def tambah(self, kode, nama, kategori, kondisi=KONDISI_BAIK):
        kode = validasi.validasi_kode_alat(kode)
        nama = validasi.validasi_nama_alat(nama)
        kondisi = validasi.validasi_kondisi(kondisi)
        kategori = self._normalisasi_kategori(kategori)
        if self.repo.ambil(kode) is not None:
            raise ValueError('Kode alat %s sudah terdaftar.' % kode)
        alat = Alat(kode, nama, kategori, kondisi)
        try:
            self.repo.tambah(alat)
        except DatabaseError as e:
            if e.kode == 1062:
                raise ValueError('Kode alat %s sudah terdaftar.' % kode)
            raise
        self.logger.catat('Alat %s ditambahkan' % kode, 'tambah alat')
        return alat

    def edit(self, kode, nama=None, kategori=None, kondisi=None):
        alat = self.ambil(kode)
        alat.nama = alat.nama if validasi.kosong(nama) else validasi.validasi_nama_alat(nama)
        alat.kategori = alat.kategori if validasi.kosong(kategori) else self._normalisasi_kategori(kategori)
        alat.kondisi = alat.kondisi if validasi.kosong(kondisi) else validasi.validasi_kondisi(kondisi)
        alat.sesuaikan_status()
        self.repo.ubah(alat)
        self.logger.catat('Alat %s diubah' % alat.kode, 'ubah alat')
        return alat

    def hapus(self, kode):
        alat = self.ambil(kode)
        if alat.status == STATUS_DIPINJAM or self.repo.dalam_transaksi_aktif(alat.kode):
            raise ValueError('Alat %s sedang dipinjam (transaksi aktif), tidak dapat dihapus.' % alat.kode)
        if self.repo.punya_riwayat(alat.kode):
            raise ValueError('Alat %s tercatat dalam riwayat transaksi, tidak dapat dihapus agar riwayat tetap utuh.' % alat.kode)
        try:
            self.repo.hapus(alat.kode)
        except DatabaseError as e:
            if e.kode == 1451:
                raise ValueError('Alat %s tercatat dalam transaksi, tidak dapat dihapus.' % alat.kode)
            raise
        self.logger.catat('Alat %s dihapus' % alat.kode, 'hapus alat')

    def cari(self, kata_kunci):
        if validasi.kosong(kata_kunci):
            raise ValueError('Kata kunci tidak boleh kosong.')
        return self.repo.cari(validasi.rapikan(kata_kunci))

    def tersedia(self):
        return self.repo.per_status(STATUS_TERSEDIA)

    def dipinjam(self):
        return self.repo.per_status(STATUS_DIPINJAM)

    def tidak_tersedia(self):
        return self.repo.per_status(STATUS_TIDAK_TERSEDIA)

    def rusak(self):
        return self.repo.rusak()
