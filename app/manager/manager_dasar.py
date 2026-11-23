from app import validasi


class ManagerDasar:

    NAMA_DATA = 'Data'
    NAMA_KUNCI = 'kunci'

    def __init__(self, db, logger):
        self.db = db
        self.logger = logger
        self.repo = self._buat_repo(db)

    def _buat_repo(self, db):
        raise NotImplementedError

    @staticmethod
    def _kunci(teks):
        return validasi.rapikan(teks).upper()

    def ambil(self, kunci):
        objek = self.repo.ambil(self._kunci(kunci))
        if objek is None:
            raise ValueError('%s dengan %s %s tidak ditemukan.' % (self.NAMA_DATA, self.NAMA_KUNCI, self._kunci(kunci)))
        return objek

    def ada(self, kunci):
        return self.repo.ambil(self._kunci(kunci)) is not None

    def semua(self, batas=None, mulai=0):
        return self.repo.semua(batas, mulai)

    def jumlah(self):
        return self.repo.jumlah()
