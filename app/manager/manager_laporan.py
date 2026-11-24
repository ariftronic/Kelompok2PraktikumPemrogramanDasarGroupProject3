from datetime import date, datetime
from app.konstanta import FORMAT_TANGGAL, FORMAT_WAKTU_LOG, JUMLAH_PERINGKAT, NILAI_KOSONG, STATUS_DIPINJAM, TRX_DIPINJAM, TRX_SEBAGIAN, TRX_SELESAI
from app.manager.manager_pengembalian import ManagerPengembalian
from app.repository.repo_alat import RepoAlat
from app.repository.repo_laporan import RepoLaporan
from app.repository.repo_mahasiswa import RepoMahasiswa
from app.repository.repo_transaksi import RepoTransaksi

LEBAR_LAPORAN = 72


class ManagerLaporan:

    def __init__(self, db, logger, file_laporan):
        self.db = db
        self.logger = logger
        self.file_laporan = file_laporan
        self.repo = RepoLaporan(db)
        self.repo_alat = RepoAlat(db)
        self.repo_mahasiswa = RepoMahasiswa(db)
        self.repo_transaksi = RepoTransaksi(db)

    def statistik(self):
        per_status = self.repo.jumlah_per_status()
        selesai = per_status.get(TRX_SELESAI, 0)
        aktif = per_status.get(TRX_DIPINJAM, 0) + per_status.get(TRX_SEBAGIAN, 0)
        return {'total_transaksi': aktif + selesai, 'transaksi_aktif': aktif, 'transaksi_selesai': selesai, 'alat_terbanyak': self.repo.alat_terbanyak(JUMLAH_PERINGKAT), 'mahasiswa_terbanyak': self.repo.mahasiswa_terbanyak(JUMLAH_PERINGKAT)}

    def baris_statistik(self):
        data = self.statistik()
        baris = ['Jumlah seluruh transaksi : %d' % data['total_transaksi'], 'Transaksi masih aktif    : %d' % data['transaksi_aktif'], 'Transaksi selesai        : %d' % data['transaksi_selesai'], '', 'Alat yang paling sering dipinjam:']
        if not data['alat_terbanyak']:
            baris.append('  (belum ada peminjaman)')
        for nomor, b in enumerate(data['alat_terbanyak'], start=1):
            baris.append('  %d. %s %s - %d kali' % (nomor, b['kode'], b['nama'], b['jumlah']))
        baris += ['', 'Mahasiswa yang paling sering meminjam:']
        if not data['mahasiswa_terbanyak']:
            baris.append('  (belum ada peminjaman)')
        for nomor, b in enumerate(data['mahasiswa_terbanyak'], start=1):
            baris.append('  %d. %s %s - %d transaksi' % (nomor, b['nim'], b['nama'], b['jumlah']))
        return baris

    def terlambat(self, tanggal=None):
        return self.repo.terlambat((tanggal or date.today()).strftime(FORMAT_TANGGAL))

    def baris_terlambat(self, tanggal=None):
        return ['%s | %s %s | batas %s | %s | terlambat %d hari' % (b['id'], b['nim'], b['nama'], b['batas_kembali'].strftime(FORMAT_TANGGAL), b['status'], b['hari']) for b in self.terlambat(tanggal)]

    @staticmethod
    def tabel(judul_kolom, daftar_baris):
        semua = [list(judul_kolom)] + [[str(nilai) for nilai in baris] for baris in daftar_baris]
        lebar = [max((len(baris[i]) for baris in semua)) for i in range(len(judul_kolom))]

        def susun(baris):
            return '  '.join((nilai.ljust(lebar[i]) for i, nilai in enumerate(baris))).rstrip()
        return [susun(semua[0]), '  '.join(('-' * n for n in lebar))] + [susun(baris) for baris in semua[1:]]

    def _tulis(self, nama_file, judul, isi):
        garis = '=' * max([LEBAR_LAPORAN] + [len(teks) for teks in isi])
        baris = [garis, judul, 'Dibuat: %s' % datetime.now().strftime(FORMAT_WAKTU_LOG), garis] + isi + [garis]
        self.file_laporan.tulis_teks(nama_file, baris)
        self.logger.catat('Laporan diekspor ke %s' % nama_file, 'ekspor laporan')
        return self.file_laporan.path_file(nama_file)

    @staticmethod
    def _nama_file(jenis):
        return 'laporan_%s_%s.txt' % (jenis, date.today().strftime(FORMAT_TANGGAL))

    def ekspor_alat_dipinjam(self):
        baris_tabel = []
        for nomor, alat in enumerate(self.repo_alat.per_status(STATUS_DIPINJAM), start=1):
            transaksi = self.repo_transaksi.aktif_untuk_alat(alat.kode)
            if transaksi is None:
                baris_tabel.append([nomor, alat.kode, alat.nama, NILAI_KOSONG, NILAI_KOSONG, NILAI_KOSONG, NILAI_KOSONG, 'tidak ada transaksi aktif'])
                continue
            mhs = self.repo_mahasiswa.ambil(transaksi.nim)
            terlambat = ManagerPengembalian.hari_terlambat(transaksi)
            keterangan = 'terlambat %d hari' % terlambat if terlambat else 'belum lewat batas'
            peminjam = '%s %s' % (transaksi.nim, mhs.nama if mhs else NILAI_KOSONG)
            baris_tabel.append([nomor, alat.kode, alat.nama, peminjam, transaksi.id_transaksi, transaksi.tgl_pinjam, transaksi.batas_kembali, keterangan])
        isi = self.tabel(('No', 'Kode', 'Nama Alat', 'Peminjam', 'ID', 'Tgl Pinjam', 'Batas', 'Keterangan'), baris_tabel) if baris_tabel else ['(tidak ada alat yang sedang dipinjam)']
        isi += ['', 'Jumlah alat yang sedang dipinjam: %d' % len(baris_tabel)]
        return self._tulis(self._nama_file('alat_dipinjam'), 'LAPORAN ALAT YANG SEDANG DIPINJAM', isi)

    def ekspor_alat_rusak(self):
        baris_tabel = [[nomor, a.kode, a.nama, a.kategori, a.kondisi, a.status] for nomor, a in enumerate(self.repo_alat.rusak(), start=1)]
        isi = self.tabel(('No', 'Kode', 'Nama Alat', 'Kategori', 'Kondisi', 'Status'), baris_tabel) if baris_tabel else ['(tidak ada alat yang rusak)']
        isi += ['', 'Jumlah alat rusak: %d' % len(baris_tabel)]
        return self._tulis(self._nama_file('alat_rusak'), 'LAPORAN ALAT YANG RUSAK', isi)

    def ekspor_riwayat_mahasiswa(self, nim):
        nim = nim.strip().upper()
        mahasiswa = self.repo_mahasiswa.ambil(nim)
        if mahasiswa is None:
            raise ValueError('Mahasiswa dengan NIM %s tidak ditemukan.' % nim)
        riwayat = self.repo_transaksi.riwayat(nim)
        nama_alat = {}
        baris_tabel = []
        for transaksi in riwayat:
            for detail in transaksi.daftar_detail:
                if detail.kode_alat not in nama_alat:
                    alat = self.repo_alat.ambil(detail.kode_alat)
                    nama_alat[detail.kode_alat] = alat.nama if alat else NILAI_KOSONG
                baris_tabel.append([transaksi.id_transaksi, transaksi.tgl_pinjam, transaksi.batas_kembali, transaksi.status, detail.kode_alat, nama_alat[detail.kode_alat], detail.status, detail.kondisi, detail.tgl_kembali])
        isi = ['NIM            : %s' % mahasiswa.nim, 'Nama           : %s' % mahasiswa.nama, 'No. HP         : %s' % (mahasiswa.no_hp or NILAI_KOSONG), 'Status pinjam  : %s' % mahasiswa.status_aktif, '']
        isi += self.tabel(('ID', 'Tgl Pinjam', 'Batas', 'Status Transaksi', 'Kode', 'Nama Alat', 'Status Alat', 'Kondisi', 'Tgl Kembali'), baris_tabel) if baris_tabel else ['(belum pernah meminjam)']
        isi += ['', 'Jumlah transaksi: %d' % len(riwayat)]
        return self._tulis(self._nama_file('riwayat_%s' % mahasiswa.nim), 'LAPORAN RIWAYAT PEMINJAMAN MAHASISWA', isi)

    def ekspor_statistik(self):
        return self._tulis(self._nama_file('statistik'), 'LAPORAN STATISTIK PEMINJAMAN', self.baris_statistik())
