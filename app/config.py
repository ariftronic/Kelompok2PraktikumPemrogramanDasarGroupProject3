import os
from dotenv import load_dotenv
from app.konstanta import PATH_ENV

BAWAAN = {'DB_HOST': '127.0.0.1', 'DB_PORT': '3306', 'DB_USER': 'root', 'DB_PASSWORD': '', 'DB_NAME': 'peminjaman_lab', 'DB_SSL_CA': '', 'NAMA_PETUGAS': 'Petugas Lab'}


def baca_konfigurasi(path_env=PATH_ENV):
    if os.path.exists(path_env):
        load_dotenv(path_env, override=False)
    nilai = {kunci: os.environ.get(kunci, bawaan).strip() for kunci, bawaan in BAWAAN.items()}
    if not nilai['DB_PORT'].isdigit():
        raise ValueError("DB_PORT di .env harus berupa angka, bukan '%s'." % nilai['DB_PORT'])
    if not nilai['DB_NAME']:
        raise ValueError('DB_NAME di .env tidak boleh kosong.')
    if nilai['DB_SSL_CA'] and (not os.path.exists(nilai['DB_SSL_CA'])):
        raise ValueError("File sertifikat DB_SSL_CA tidak ditemukan: %s" % nilai['DB_SSL_CA'])
    return {'host': nilai['DB_HOST'] or BAWAAN['DB_HOST'], 'port': int(nilai['DB_PORT']), 'user': nilai['DB_USER'], 'password': nilai['DB_PASSWORD'], 'database': nilai['DB_NAME'], 'ssl_ca': nilai['DB_SSL_CA'], 'petugas': nilai['NAMA_PETUGAS'] or BAWAAN['NAMA_PETUGAS']}
