"""Akses tabel transaksi dan detail_transaksi."""
from app.konstanta import DETAIL_DIKEMBALIKAN, DETAIL_DIPINJAM, TRX_SELESAI
from app.models.transaksi import DetailTransaksi, Transaksi
from app.repository.repo_dasar import RepoDasar

URUT_ID = ' ORDER BY CAST(SUBSTRING(id, 2) AS UNSIGNED), id'


class RepoTransaksi(RepoDasar):
    """Semua SQL untuk transaksi beserta daftar alatnya."""

    def _lengkapi(self, daftar_baris):
        # Detail semua transaksi diambil dengan satu query (IN), lalu dikelompokkan dengan dictionary.
        if not daftar_baris:
            return []
        id_list = [b['id'] for b in daftar_baris]
        tanda = ', '.join(['%s'] * len(id_list))
        detail = {}
        for b in self.db.query('SELECT * FROM detail_transaksi WHERE id_transaksi IN (' + tanda + ') ORDER BY id_transaksi, kode_alat', tuple(id_list)):
            detail.setdefault(b['id_transaksi'], []).append(DetailTransaksi.dari_dict(b))
        return [Transaksi.dari_dict(b, detail.get(b['id'], [])) for b in daftar_baris]

    def ambil(self, id_transaksi, kunci=False):
        """Transaksi beserta detailnya atau None; kunci=True mengunci baris transaksi (FOR UPDATE)."""
        baris = self.db.query_satu('SELECT * FROM transaksi WHERE id = %s' + self.kunci_sql(kunci), (id_transaksi,))
        return self._lengkapi([baris])[0] if baris else None

    def semua(self, batas=None, mulai=0):
        """Transaksi urut nomor ID; batas/mulai untuk tampilan per halaman."""
        halaman, param = self.potongan_halaman(batas, mulai)
        return self._lengkapi(self.db.query('SELECT * FROM transaksi' + URUT_ID + halaman, param))

    def jumlah(self):
        """Jumlah seluruh transaksi."""
        return self.db.query_satu('SELECT COUNT(*) AS n FROM transaksi')['n']

    def aktif_milik(self, nim):
        """Transaksi yang belum selesai milik NIM."""
        return self._lengkapi(self.db.query('SELECT * FROM transaksi WHERE nim = %s AND status <> %s' + URUT_ID, (nim, TRX_SELESAI)))

    def riwayat(self, nim):
        """Semua transaksi milik NIM, termasuk yang selesai."""
        return self._lengkapi(self.db.query('SELECT * FROM transaksi WHERE nim = %s' + URUT_ID, (nim,)))

    def aktif_untuk_alat(self, kode):
        """Transaksi yang sedang memegang alat tersebut, atau None."""
        baris = self.db.query_satu('SELECT t.* FROM transaksi t JOIN detail_transaksi d ON d.id_transaksi = t.id WHERE d.kode_alat = %s AND d.status = %s LIMIT 1', (kode, DETAIL_DIPINJAM))
        return self._lengkapi([baris])[0] if baris else None

    def id_baru(self):
        """ID berikutnya berformat T001, T002, ... (nomor terbesar + 1)."""
        baris = self.db.query_satu("SELECT MAX(CAST(SUBSTRING(id, 2) AS UNSIGNED)) AS n FROM transaksi WHERE id REGEXP '^T[0-9]+$'")
        return 'T%03d' % ((baris['n'] or 0) + 1)

    def tambah(self, transaksi):
        """INSERT transaksi dan satu baris detail per alat (dipanggil di dalam transaction)."""
        self.db.eksekusi('INSERT INTO transaksi (id, nim, tgl_pinjam, batas_kembali, status) VALUES (%s, %s, %s, %s, %s)', (transaksi.id_transaksi, transaksi.nim, transaksi.tgl_pinjam, transaksi.batas_kembali, transaksi.status))
        for detail in transaksi.daftar_detail:
            self.db.eksekusi('INSERT INTO detail_transaksi (id_transaksi, kode_alat, status) VALUES (%s, %s, %s)', (transaksi.id_transaksi, detail.kode_alat, DETAIL_DIPINJAM))

    def kembalikan_detail(self, id_transaksi, kode, kondisi, tanggal):
        """Mencatat pengembalian satu alat; mengembalikan jumlah baris yang berubah (0 bila sudah kembali)."""
        return self.db.eksekusi('UPDATE detail_transaksi SET status = %s, kondisi_kembali = %s, tgl_kembali = %s WHERE id_transaksi = %s AND kode_alat = %s AND status = %s', (DETAIL_DIKEMBALIKAN, kondisi, tanggal, id_transaksi, kode, DETAIL_DIPINJAM))

    def set_status(self, id_transaksi, status):
        """Mengubah status transaksi."""
        self.db.eksekusi('UPDATE transaksi SET status = %s WHERE id = %s', (status, id_transaksi))
