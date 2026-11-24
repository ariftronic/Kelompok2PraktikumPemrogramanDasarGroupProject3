import argparse
import os
import sys

PROYEK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROYEK not in sys.path:
    sys.path.insert(0, PROYEK)

from app.config import baca_konfigurasi  # noqa: E402
from app.database import Database, DatabaseError  # noqa: E402
from app.file_manager import FileManager, FileManagerError  # noqa: E402
from app.konstanta import FILE_ALAT, FILE_DETAIL_TRANSAKSI, FILE_MAHASISWA, FILE_TRANSAKSI, MHS_AKTIF, MHS_TIDAK_AKTIF, NILAI_KOSONG, PATH_SCHEMA, STATUS_DIPINJAM  # noqa: E402
from app.models.alat import Alat  # noqa: E402
from app.models.mahasiswa import Mahasiswa  # noqa: E402
from app.models.transaksi import DetailTransaksi, Transaksi  # noqa: E402

TABEL = ('mahasiswa', 'alat', 'transaksi', 'detail_transaksi')


def baca_data(folder):
    fm = FileManager(direktori=folder)
    peringatan = fm.daftar_peringatan

    def muat(nama_file, kelas, kunci):
        hasil = {}
        for kolom in fm.baca_baris(nama_file):
            try:
                objek = kelas.dari_baris(kolom)
            except (ValueError, TypeError) as e:
                fm.catat_peringatan(nama_file, 'baris dilewati (%s): %s' % (e, '|'.join(kolom)))
                continue
            k = kunci(objek)
            if k in hasil:
                fm.catat_peringatan(nama_file, 'baris dilewati (%s ganda): %s' % (k, '|'.join(kolom)))
                continue
            hasil[k] = objek
        return hasil

    mahasiswa = muat(FILE_MAHASISWA, Mahasiswa, lambda m: m.nim)
    alat = muat(FILE_ALAT, Alat, lambda a: a.kode)
    transaksi = {}
    for k, t in muat(FILE_TRANSAKSI, Transaksi, lambda t: t.id_transaksi.upper()).items():
        t.id_transaksi, t.nim = k, t.nim.upper()
        if t.nim not in mahasiswa:
            fm.catat_peringatan(FILE_TRANSAKSI, 'transaksi %s dilewati: NIM %s tidak ada' % (k, t.nim))
        else:
            transaksi[k] = t
    for detail in muat(FILE_DETAIL_TRANSAKSI, DetailTransaksi, lambda d: (d.id_transaksi.upper(), d.kode_alat.upper())).values():
        detail.id_transaksi, detail.kode_alat = detail.id_transaksi.upper(), detail.kode_alat.upper()
        if detail.id_transaksi not in transaksi:
            fm.catat_peringatan(FILE_DETAIL_TRANSAKSI, 'detail %s/%s dilewati: transaksi tidak ada' % (detail.id_transaksi, detail.kode_alat))
        elif detail.kode_alat not in alat:
            fm.catat_peringatan(FILE_DETAIL_TRANSAKSI, 'detail %s/%s dilewati: alat tidak ada' % (detail.id_transaksi, detail.kode_alat))
        else:
            transaksi[detail.id_transaksi].daftar_detail.append(detail)
    for k in [k for k, t in transaksi.items() if not t.daftar_detail]:
        fm.catat_peringatan(FILE_TRANSAKSI, 'transaksi %s dilewati: tidak memiliki alat' % k)
        del transaksi[k]
    return {'mahasiswa': mahasiswa, 'alat': alat, 'transaksi': transaksi}, peringatan


def selaraskan(data):
    perbaikan = 0
    for t in data['transaksi'].values():
        lama = t.status
        t.perbarui_status()
        perbaikan += t.status != lama
    dipinjam = {d.kode_alat for t in data['transaksi'].values() for d in t.daftar_detail if not d.sudah_kembali()}
    for alat in data['alat'].values():
        seharusnya = STATUS_DIPINJAM if alat.kode in dipinjam else Alat.status_dari_kondisi(alat.kondisi)
        perbaikan += alat.status != seharusnya
        alat.status = seharusnya
    aktif = {t.nim for t in data['transaksi'].values() if t.masih_aktif()}
    for mhs in data['mahasiswa'].values():
        seharusnya = MHS_AKTIF if mhs.nim in aktif else MHS_TIDAK_AKTIF
        perbaikan += mhs.status_aktif != seharusnya
        mhs.status_aktif = seharusnya
    return perbaikan


def kosong_atau_none(nilai):
    return None if nilai in ('', NILAI_KOSONG) else nilai


def masukkan(db, data):
    harapan = {'mahasiswa': len(data['mahasiswa']), 'alat': len(data['alat']), 'transaksi': len(data['transaksi']), 'detail_transaksi': sum((len(t.daftar_detail) for t in data['transaksi'].values()))}
    with db.transaksi():
        for m in data['mahasiswa'].values():
            db.eksekusi('INSERT INTO mahasiswa (nim, nama, no_hp, status_aktif) VALUES (%s, %s, %s, %s)', (m.nim, m.nama, kosong_atau_none(m.no_hp), m.status_aktif))
        for a in data['alat'].values():
            db.eksekusi('INSERT INTO alat (kode, nama, kategori, kondisi, status) VALUES (%s, %s, %s, %s, %s)', (a.kode, a.nama, a.kategori, a.kondisi, a.status))
        for t in data['transaksi'].values():
            db.eksekusi('INSERT INTO transaksi (id, nim, tgl_pinjam, batas_kembali, status) VALUES (%s, %s, %s, %s, %s)', (t.id_transaksi, t.nim, t.tgl_pinjam, t.batas_kembali, t.status))
            for d in t.daftar_detail:
                db.eksekusi('INSERT INTO detail_transaksi (id_transaksi, kode_alat, status, kondisi_kembali, tgl_kembali) VALUES (%s, %s, %s, %s, %s)', (d.id_transaksi, d.kode_alat, d.status, kosong_atau_none(d.kondisi), kosong_atau_none(d.tgl_kembali)))
        for tabel, jumlah in harapan.items():
            ada = db.query_satu('SELECT COUNT(*) AS n FROM ' + tabel)['n']
            if ada != jumlah:
                raise DatabaseError('Jumlah baris %s tidak cocok: txt %d, tabel %d. Migrasi dibatalkan.' % (tabel, jumlah, ada))
    return harapan


def kosongkan(db):
    with db.transaksi():
        for tabel in reversed(TABEL):
            db.eksekusi('DELETE FROM ' + tabel)


def main(argv=None, konfigurasi=None):
    parser = argparse.ArgumentParser(description='Migrasi data .txt ke MySQL.')
    parser.add_argument('--sumber', default='data', help='folder berisi mahasiswa.txt, alat.txt, transaksi.txt, detail_transaksi.txt (bawaan: data)')
    parser.add_argument('--kosongkan', action='store_true', help='hapus isi semua tabel sebelum migrasi')
    arg = parser.parse_args(argv)
    folder = arg.sumber if os.path.isabs(arg.sumber) else os.path.join(PROYEK, arg.sumber)
    if not os.path.isdir(folder):
        print('[!] Folder sumber tidak ditemukan: %s' % folder)
        return 1
    db = None
    try:
        konfigurasi = konfigurasi or baca_konfigurasi()
        db = Database(konfigurasi)
        db.sambung()
        db.pastikan_tabel(PATH_SCHEMA)
        terisi = {t: db.query_satu('SELECT COUNT(*) AS n FROM ' + t)['n'] for t in TABEL}
        if any(terisi.values()) and (not arg.kosongkan):
            print('[!] Tabel sudah berisi data %s. Jalankan dengan --kosongkan untuk mengganti isinya.' % terisi)
            return 1
        data, peringatan = baca_data(folder)
        perbaikan = selaraskan(data)
        if arg.kosongkan:
            kosongkan(db)
        hasil = masukkan(db, data)
    except (DatabaseError, FileManagerError, ValueError) as e:
        print('[!] Migrasi gagal, database tidak berubah: %s' % e)
        return 1
    finally:
        if db is not None:
            db.tutup()
    print('Migrasi dari %s ke database %s berhasil.' % (folder, konfigurasi['database']))
    for tabel, jumlah in hasil.items():
        print('  %-17s %d baris' % (tabel, jumlah))
    print('  baris dilewati      %d (lihat [PERINGATAN] di atas)' % len(peringatan))
    print('  status diselaraskan %d' % perbaikan)
    return 0


if __name__ == '__main__':
    sys.exit(main())
