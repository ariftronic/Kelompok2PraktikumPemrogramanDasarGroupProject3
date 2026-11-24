"""Model Transaksi dan DetailTransaksi: baris di transaksi.txt dan detail_transaksi.txt."""
from datetime import datetime
from app.konstanta import NILAI_KOSONG, FORMAT_TANGGAL, DAFTAR_KONDISI, DETAIL_DIPINJAM, DETAIL_DIKEMBALIKAN, TRX_DIPINJAM, TRX_SEBAGIAN, TRX_SELESAI

def teks_tanggal(nilai):
    """Tanggal dari database (date atau None) menjadi teks YYYY-MM-DD atau '-'."""
    if nilai is None:
        return NILAI_KOSONG
    return nilai.strftime(FORMAT_TANGGAL) if hasattr(nilai, 'strftime') else str(nilai)


def _periksa_tanggal(nilai, nama_kolom):
    try:
        tanggal = datetime.strptime(nilai, FORMAT_TANGGAL).date()
    except ValueError:
        tanggal = None
    # strptime menerima bulan/hari satu digit (2026-11-2); format baku harus persis YYYY-MM-DD.
    if tanggal is None or tanggal.strftime(FORMAT_TANGGAL) != nilai:
        raise ValueError("%s harus berformat YYYY-MM-DD: '%s'" % (nama_kolom, nilai))
    return tanggal

class DetailTransaksi:
    """Satu alat di dalam sebuah transaksi beserta data pengembaliannya."""

    def __init__(self, id_transaksi, kode_alat, status=DETAIL_DIPINJAM, kondisi=NILAI_KOSONG, tgl_kembali=NILAI_KOSONG):
        self.id_transaksi = id_transaksi
        self.kode_alat = kode_alat
        self.status = status
        self.kondisi = kondisi
        self.tgl_kembali = tgl_kembali

    @classmethod
    def dari_baris(cls, kolom):
        """Membuat DetailTransaksi dari list kolom; ValueError bila status, kondisi, atau tanggal tidak valid."""
        _, _, status, kondisi, tgl_kembali = kolom
        if status == DETAIL_DIKEMBALIKAN:
            if kondisi not in DAFTAR_KONDISI:
                raise ValueError("kondisi alat tidak dikenal: '%s'" % kondisi)
            _periksa_tanggal(tgl_kembali, 'tgl_kembali')
        elif status == DETAIL_DIPINJAM:
            if kondisi != NILAI_KOSONG or tgl_kembali != NILAI_KOSONG:
                raise ValueError("alat yang masih dipinjam harus berkondisi dan bertanggal kembali '%s'" % NILAI_KOSONG)
        else:
            raise ValueError("status detail tidak dikenal: '%s'" % status)
        return cls(*kolom)

    @classmethod
    def dari_dict(cls, baris):
        """Membuat DetailTransaksi dari baris tabel detail_transaksi (NULL ditampilkan sebagai '-')."""
        return cls(baris['id_transaksi'], baris['kode_alat'], baris['status'], baris['kondisi_kembali'] or NILAI_KOSONG, teks_tanggal(baris['tgl_kembali']))

    def ke_baris(self):
        """List kolom untuk ditulis ke detail_transaksi.txt."""
        return [self.id_transaksi, self.kode_alat, self.status, self.kondisi, self.tgl_kembali]

    def sudah_kembali(self):
        """True bila alat ini sudah dikembalikan."""
        return self.status == DETAIL_DIKEMBALIKAN

    def kembalikan(self, kondisi, tanggal):
        """Mencatat pengembalian alat: kondisi dan tanggal kembali."""
        self.status = DETAIL_DIKEMBALIKAN
        self.kondisi = kondisi
        self.tgl_kembali = tanggal

    def __str__(self):
        if self.sudah_kembali():
            return '%s: %s (%s, %s)' % (self.kode_alat, self.status, self.kondisi, self.tgl_kembali)
        return '%s: %s' % (self.kode_alat, self.status)

class Transaksi:
    """Satu transaksi peminjaman; daftar_detail berisi satu DetailTransaksi untuk setiap alat (Aturan 3)."""

    def __init__(self, id_transaksi, nim, tgl_pinjam, batas_kembali, status=TRX_DIPINJAM):
        self.id_transaksi = id_transaksi
        self.nim = nim
        self.tgl_pinjam = tgl_pinjam
        self.batas_kembali = batas_kembali
        self.status = status
        self.daftar_detail = []

    @classmethod
    def dari_baris(cls, kolom):
        """Membuat Transaksi dari list kolom; ValueError bila status atau tanggal tidak valid."""
        _, _, tgl_pinjam, batas_kembali, status = kolom
        if status not in (TRX_DIPINJAM, TRX_SEBAGIAN, TRX_SELESAI):
            raise ValueError("status transaksi tidak dikenal: '%s'" % status)
        pinjam = _periksa_tanggal(tgl_pinjam, 'tgl_pinjam')
        batas = _periksa_tanggal(batas_kembali, 'batas_kembali')
        # Batas maksimal hari hanya diterapkan saat transaksi baru dibuat (ManagerTransaksi.buat),
        # agar transaksi lama tetap dapat dimuat bila aturan MAKS_HARI_PINJAM berubah.
        if batas < pinjam:
            raise ValueError('batas_kembali tidak boleh sebelum tgl_pinjam (%s sampai %s)' % (tgl_pinjam, batas_kembali))
        return cls(*kolom)

    @classmethod
    def dari_dict(cls, baris, daftar_detail=()):
        """Membuat Transaksi dari baris tabel transaksi beserta list DetailTransaksi-nya."""
        transaksi = cls(baris['id'], baris['nim'], teks_tanggal(baris['tgl_pinjam']), teks_tanggal(baris['batas_kembali']), baris['status'])
        transaksi.daftar_detail = list(daftar_detail)
        return transaksi

    def ke_baris(self):
        """List kolom untuk ditulis ke transaksi.txt."""
        return [self.id_transaksi, self.nim, self.tgl_pinjam, self.batas_kembali, self.status]

    def baris_detail(self):
        """List kolom semua detail, untuk ditulis ke detail_transaksi.txt."""
        return [detail.ke_baris() for detail in self.daftar_detail]

    def masih_aktif(self):
        """True selama masih ada alat yang belum dikembalikan (Aturan 4)."""
        return self.status != TRX_SELESAI

    def perbarui_status(self):
        """Status menjadi 'dipinjam', 'sebagian dikembalikan', atau 'selesai' sesuai detailnya."""
        jumlah_kembali = sum((1 for detail in self.daftar_detail if detail.sudah_kembali()))
        if jumlah_kembali == 0:
            self.status = TRX_DIPINJAM
        elif jumlah_kembali == len(self.daftar_detail):
            self.status = TRX_SELESAI
        else:
            self.status = TRX_SEBAGIAN

    def __str__(self):
        baris = ['%s | %s | pinjam %s | batas %s | %s' % (self.id_transaksi, self.nim, self.tgl_pinjam, self.batas_kembali, self.status)]
        baris += ['     - %s' % detail for detail in self.daftar_detail]
        return '\n'.join(baris)
