from app.konstanta import TRX_SELESAI
from app.repository.repo_dasar import RepoDasar


class RepoLaporan(RepoDasar):

    def alat_terbanyak(self, jumlah):
        return self.db.query('SELECT d.kode_alat AS kode, a.nama, COUNT(*) AS jumlah FROM detail_transaksi d JOIN alat a ON a.kode = d.kode_alat GROUP BY d.kode_alat, a.nama ORDER BY jumlah DESC, d.kode_alat LIMIT %s', (jumlah,))

    def mahasiswa_terbanyak(self, jumlah):
        return self.db.query('SELECT t.nim, m.nama, COUNT(*) AS jumlah FROM transaksi t JOIN mahasiswa m ON m.nim = t.nim GROUP BY t.nim, m.nama ORDER BY jumlah DESC, t.nim LIMIT %s', (jumlah,))

    def jumlah_per_status(self):
        return {b['status']: b['jumlah'] for b in self.db.query('SELECT status, COUNT(*) AS jumlah FROM transaksi GROUP BY status')}

    def terlambat(self, tanggal):
        return self.db.query('SELECT t.id, t.nim, m.nama, t.tgl_pinjam, t.batas_kembali, t.status, DATEDIFF(%s, t.batas_kembali) AS hari FROM transaksi t JOIN mahasiswa m ON m.nim = t.nim WHERE t.status <> %s AND t.batas_kembali < %s ORDER BY t.batas_kembali, t.id', (tanggal, TRX_SELESAI, tanggal))
