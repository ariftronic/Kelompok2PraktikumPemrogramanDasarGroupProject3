from app import validasi
from app.database import DatabaseError
from app.manager.manager_dasar import ManagerDasar
from app.models.mahasiswa import Mahasiswa
from app.repository.repo_mahasiswa import RepoMahasiswa


class ManagerMahasiswa(ManagerDasar):

    NAMA_DATA = 'Mahasiswa'
    NAMA_KUNCI = 'NIM'

    def _buat_repo(self, db):
        return RepoMahasiswa(db)

    def cari_berdasarkan_nim(self, nim):
        return self.repo.ambil(self._kunci(nim))

    def tambah(self, nim, nama, no_hp=''):
        nim = validasi.validasi_nim(nim)
        nama = validasi.validasi_nama(nama)
        no_hp = validasi.validasi_no_hp(no_hp)
        if self.repo.ambil(nim) is not None:
            raise ValueError('NIM %s sudah terdaftar.' % nim)
        mhs = Mahasiswa(nim, nama, no_hp)
        try:
            self.repo.tambah(mhs)
        except DatabaseError as e:
            if e.kode == 1062:
                raise ValueError('NIM %s sudah terdaftar.' % nim)
            raise
        self.logger.catat('Mahasiswa %s ditambahkan' % nim, 'tambah mahasiswa')
        return mhs

    def edit(self, nim, nama=None, no_hp=None):
        mhs = self.ambil(nim)
        mhs.nama = mhs.nama if validasi.kosong(nama) else validasi.validasi_nama(nama)
        mhs.no_hp = mhs.no_hp if validasi.kosong(no_hp) else validasi.validasi_no_hp(no_hp)
        self.repo.ubah(mhs)
        self.logger.catat('Mahasiswa %s diubah' % mhs.nim, 'ubah mahasiswa')
        return mhs

    def hapus(self, nim):
        mhs = self.ambil(nim)
        if self.repo.jumlah_transaksi_aktif(mhs.nim) > 0:
            raise ValueError('Mahasiswa %s masih memiliki transaksi aktif, tidak dapat dihapus.' % mhs.nim)
        if self.repo.punya_riwayat(mhs.nim):
            raise ValueError('Mahasiswa %s tercatat dalam riwayat transaksi, tidak dapat dihapus agar riwayat tetap utuh.' % mhs.nim)
        try:
            self.repo.hapus(mhs.nim)
        except DatabaseError as e:
            if e.kode == 1451:
                raise ValueError('Mahasiswa %s tercatat dalam transaksi, tidak dapat dihapus.' % mhs.nim)
            raise
        self.logger.catat('Mahasiswa %s dihapus' % mhs.nim, 'hapus mahasiswa')

    def cari(self, kata_kunci):
        if validasi.kosong(kata_kunci):
            raise ValueError('Kata kunci tidak boleh kosong.')
        return self.repo.cari(validasi.rapikan(kata_kunci))
