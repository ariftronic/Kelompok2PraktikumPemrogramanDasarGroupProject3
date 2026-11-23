from app.repository.repo_dasar import RepoDasar


class RepoLog(RepoDasar):

    def catat(self, petugas, aksi, keterangan):
        self.db.eksekusi('INSERT INTO log_aktivitas (petugas, aksi, keterangan) VALUES (%s, %s, %s)', (petugas[:50], aksi[:30], keterangan[:255]))

    def terakhir(self, jumlah):
        hasil = self.db.query('SELECT waktu, petugas, aksi, keterangan FROM log_aktivitas ORDER BY id DESC LIMIT %s', (jumlah,))
        return list(reversed(hasil))
