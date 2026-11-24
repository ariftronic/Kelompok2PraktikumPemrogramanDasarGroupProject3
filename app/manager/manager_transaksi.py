from datetime import date, timedelta
from app import validasi
from app.database import DatabaseError
from app.konstanta import FORMAT_TANGGAL, MAKS_HARI_PINJAM, MAKS_TRANSAKSI_AKTIF, MAKS_ULANG_TRANSAKSI, MHS_AKTIF, STATUS_DIPINJAM, STATUS_TERSEDIA
from app.models.transaksi import DetailTransaksi, Transaksi
from app.repository.repo_alat import RepoAlat
from app.repository.repo_mahasiswa import RepoMahasiswa
from app.repository.repo_transaksi import RepoTransaksi


class ManagerTransaksi:

    def __init__(self, db, logger):
        self.db = db
        self.logger = logger
        self.repo = RepoTransaksi(db)
        self.repo_mahasiswa = RepoMahasiswa(db)
        self.repo_alat = RepoAlat(db)

    @staticmethod
    def _kunci(teks):
        return validasi.rapikan(teks).upper()

    def buat(self, nim, daftar_kode_alat):
        nim = self._kunci(nim)
        daftar_kode_alat = [self._kunci(k) for k in daftar_kode_alat]
        if not daftar_kode_alat:
            raise ValueError('Pilih minimal satu alat.')
        if len(set(daftar_kode_alat)) != len(daftar_kode_alat):
            raise ValueError('Kode alat tidak boleh dobel dalam satu transaksi.')
        for percobaan in range(MAKS_ULANG_TRANSAKSI):
            try:
                transaksi = self._buat_sekali(nim, daftar_kode_alat)
                break
            except DatabaseError as e:
                # ID yang sama dibuat bersamaan di komputer lain: ulangi dengan ID berikutnya.
                if e.kode != 1062 or percobaan == MAKS_ULANG_TRANSAKSI - 1:
                    raise
        self.logger.catat('Transaksi %s dibuat oleh %s (%s)' % (transaksi.id_transaksi, nim, ', '.join(daftar_kode_alat)), 'buat transaksi')
        return transaksi

    def _buat_sekali(self, nim, daftar_kode_alat):
        with self.db.transaksi():
            mahasiswa = self.repo_mahasiswa.ambil(nim, kunci=True)
            if mahasiswa is None:
                raise ValueError('Mahasiswa dengan NIM %s tidak ditemukan.' % nim)
            aktif = self.repo_mahasiswa.jumlah_transaksi_aktif(nim)
            if aktif >= MAKS_TRANSAKSI_AKTIF:
                raise ValueError('Mahasiswa %s sudah memiliki %d transaksi aktif (maksimal %d).' % (nim, aktif, MAKS_TRANSAKSI_AKTIF))
            for kode in daftar_kode_alat:
                alat = self.repo_alat.ambil(kode, kunci=True)
                if alat is None:
                    raise ValueError('Alat %s tidak ditemukan.' % kode)
                if alat.status != STATUS_TERSEDIA:
                    raise ValueError('Alat %s tidak tersedia (status: %s).' % (kode, alat.status))
            hari_ini = date.today()
            transaksi = Transaksi(self.repo.id_baru(), nim, hari_ini.strftime(FORMAT_TANGGAL), (hari_ini + timedelta(days=MAKS_HARI_PINJAM)).strftime(FORMAT_TANGGAL))
            transaksi.daftar_detail = [DetailTransaksi(transaksi.id_transaksi, kode) for kode in daftar_kode_alat]
            self.repo.tambah(transaksi)
            for kode in daftar_kode_alat:
                self.repo_alat.set_status(kode, STATUS_DIPINJAM)
            self.repo_mahasiswa.set_status_aktif(nim, MHS_AKTIF)
        return transaksi

    def ambil(self, id_transaksi):
        id_transaksi = self._kunci(id_transaksi)
        transaksi = self.repo.ambil(id_transaksi)
        if transaksi is None:
            raise ValueError('Transaksi %s tidak ditemukan.' % id_transaksi)
        return transaksi

    def semua(self, batas=None, mulai=0):
        return self.repo.semua(batas, mulai)

    def jumlah(self):
        return self.repo.jumlah()

    def cari_berdasarkan_mahasiswa(self, nim):
        return self.repo.aktif_milik(self._kunci(nim))

    def riwayat_mahasiswa(self, nim):
        return self.repo.riwayat(self._kunci(nim))

    def transaksi_aktif_alat(self, kode):
        return self.repo.aktif_untuk_alat(self._kunci(kode))

    def punya_transaksi_aktif(self, nim):
        return self.repo_mahasiswa.jumlah_transaksi_aktif(self._kunci(nim)) > 0
