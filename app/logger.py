from app.database import DatabaseError
from app.konstanta import FORMAT_WAKTU_LOG
from app.repository.repo_log import RepoLog


class Logger:

    def __init__(self, db, petugas):
        self.repo = RepoLog(db)
        self.petugas = petugas

    def catat(self, keterangan, aksi='info'):
        try:
            self.repo.catat(self.petugas, aksi, keterangan)
            return True
        except DatabaseError as e:
            print('[PERINGATAN] Log gagal dicatat: %s' % e)
            return False

    def baca_terakhir(self, jumlah=20):
        if jumlah <= 0:
            return []
        return ['[%s] %s | %s | %s' % (b['waktu'].strftime(FORMAT_WAKTU_LOG), b['petugas'], b['aksi'], b['keterangan']) for b in self.repo.terakhir(jumlah)]
