from datetime import date, datetime
from app import validasi
from app.konstanta import FORMAT_TANGGAL, MHS_AKTIF, MHS_TIDAK_AKTIF
from app.repository.repo_alat import RepoAlat
from app.repository.repo_mahasiswa import RepoMahasiswa
from app.repository.repo_transaksi import RepoTransaksi


class ManagerPengembalian:

    def __init__(self, db, logger):
        self.db = db
        self.logger = logger
        self.repo_transaksi = RepoTransaksi(db)
        self.repo_alat = RepoAlat(db)
        self.repo_mahasiswa = RepoMahasiswa(db)

    def daftar_belum_kembali(self, id_transaksi):
        transaksi = self.repo_transaksi.ambil(validasi.rapikan(id_transaksi).upper())
        if transaksi is None:
            raise ValueError('Transaksi %s tidak ditemukan.' % validasi.rapikan(id_transaksi).upper())
        return [d for d in transaksi.daftar_detail if not d.sudah_kembali()]

    @staticmethod
    def hari_terlambat(transaksi, tanggal=None):
        tanggal = tanggal or date.today()
        batas = datetime.strptime(transaksi.batas_kembali, FORMAT_TANGGAL).date()
        return max((tanggal - batas).days, 0)

    def kembalikan(self, id_transaksi, kode_alat, kondisi):
        id_transaksi = validasi.rapikan(id_transaksi).upper()
        kode_alat = validasi.rapikan(kode_alat).upper()
        kondisi = validasi.validasi_kondisi(kondisi)
        tanggal = date.today().strftime(FORMAT_TANGGAL)
        with self.db.transaksi():
            transaksi = self.repo_transaksi.ambil(id_transaksi, kunci=True)
            if transaksi is None:
                raise ValueError('Transaksi %s tidak ditemukan.' % id_transaksi)
            detail = next((d for d in transaksi.daftar_detail if d.kode_alat == kode_alat), None)
            if detail is None:
                raise ValueError('Alat %s tidak ada pada transaksi %s.' % (kode_alat, id_transaksi))
            if detail.sudah_kembali():
                raise ValueError('Alat %s pada transaksi %s sudah dikembalikan.' % (kode_alat, id_transaksi))
            alat = self.repo_alat.ambil(kode_alat, kunci=True)
            if alat is None:
                raise ValueError('Alat %s tidak ditemukan di data alat.' % kode_alat)
            terlambat = self.hari_terlambat(transaksi)
            if self.repo_transaksi.kembalikan_detail(id_transaksi, kode_alat, kondisi, tanggal) != 1:
                raise ValueError('Alat %s pada transaksi %s sudah dikembalikan.' % (kode_alat, id_transaksi))
            detail.kembalikan(kondisi, tanggal)
            alat.tandai_dikembalikan(kondisi)
            self.repo_alat.set_status(alat.kode, alat.status, alat.kondisi)
            transaksi.perbarui_status()
            self.repo_transaksi.set_status(id_transaksi, transaksi.status)
            aktif = self.repo_mahasiswa.jumlah_transaksi_aktif(transaksi.nim)
            self.repo_mahasiswa.set_status_aktif(transaksi.nim, MHS_AKTIF if aktif > 0 else MHS_TIDAK_AKTIF)
        pesan = 'Alat %s dikembalikan dalam kondisi %s (%s)' % (kode_alat, kondisi, id_transaksi)
        if terlambat:
            pesan += ' - TERLAMBAT %d hari' % terlambat
        self.logger.catat(pesan, 'pengembalian')
        return transaksi
