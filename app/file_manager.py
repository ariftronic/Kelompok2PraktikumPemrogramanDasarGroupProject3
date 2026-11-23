import os
from app.konstanta import DIR_DATA, JUMLAH_KOLOM, PEMISAH


class FileManagerError(Exception):
    pass


class FileManager:

    def __init__(self, direktori=DIR_DATA):
        self.direktori = direktori
        self.daftar_peringatan = []

    def path_file(self, nama_file):
        return os.path.join(self.direktori, nama_file)

    def catat_peringatan(self, sumber, pesan):
        teks = '[PERINGATAN] %s: %s' % (sumber, pesan)
        self.daftar_peringatan.append(teks)
        print(teks)

    def baca_baris(self, nama_file, jumlah_kolom=None):
        if jumlah_kolom is None:
            jumlah_kolom = JUMLAH_KOLOM.get(nama_file)
        path = self.path_file(nama_file)
        if not os.path.exists(path):
            return []
        hasil = []
        try:
            with open(path, 'r', encoding='utf-8-sig') as f:
                for nomor, baris in enumerate(f, start=1):
                    teks = baris.strip()
                    if not teks:
                        continue
                    kolom = [k.strip() for k in teks.split(PEMISAH)]
                    if jumlah_kolom is not None and len(kolom) != jumlah_kolom:
                        self.catat_peringatan(nama_file, 'baris %d dilewati (ada %d kolom, seharusnya %d): %s' % (nomor, len(kolom), jumlah_kolom, teks))
                    elif '' in kolom:
                        self.catat_peringatan(nama_file, 'baris %d dilewati (ada kolom kosong): %s' % (nomor, teks))
                    else:
                        hasil.append(kolom)
        except (OSError, UnicodeDecodeError) as e:
            raise FileManagerError("Tidak dapat membaca file '%s': %s" % (nama_file, e))
        return hasil

    def tulis_teks(self, nama_file, daftar_teks):
        path = self.path_file(nama_file)
        path_sementara = path + '.tmp'
        try:
            os.makedirs(self.direktori, exist_ok=True)
            with open(path_sementara, 'w', encoding='utf-8', newline='\n') as f:
                for teks in daftar_teks:
                    f.write(' '.join(str(teks).splitlines()) + '\n')
            os.replace(path_sementara, path)
        except OSError as e:
            try:
                if os.path.exists(path_sementara):
                    os.remove(path_sementara)
            except OSError:
                pass
            raise FileManagerError("Tidak dapat menulis file '%s': %s" % (nama_file, e))
