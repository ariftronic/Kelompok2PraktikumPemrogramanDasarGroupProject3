-- schema.sql Kelompok 2: struktur tabel database peminjaman_lab.
-- Aman dijalankan berulang (CREATE TABLE IF NOT EXISTS); program juga menjalankannya otomatis saat mulai.
-- Panjang kolom mengikuti app/validasi.py (NIM 20, kode 15, nama 60, kategori 40, no HP 16).

CREATE TABLE IF NOT EXISTS mahasiswa (
    nim          VARCHAR(20) NOT NULL,
    nama         VARCHAR(60) NOT NULL,
    no_hp        VARCHAR(16) NULL,
    status_aktif ENUM('aktif','tidak aktif') NOT NULL DEFAULT 'tidak aktif',
    PRIMARY KEY (nim)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS alat (
    kode     VARCHAR(15) NOT NULL,
    nama     VARCHAR(60) NOT NULL,
    kategori VARCHAR(40) NOT NULL,
    kondisi  ENUM('baik','rusak ringan','rusak berat') NOT NULL DEFAULT 'baik',
    status   ENUM('tersedia','dipinjam','tidak tersedia') NOT NULL DEFAULT 'tersedia',
    PRIMARY KEY (kode),
    INDEX idx_alat_status (status),
    INDEX idx_alat_kategori (kategori)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS transaksi (
    id            VARCHAR(20) NOT NULL,
    nim           VARCHAR(20) NOT NULL,
    tgl_pinjam    DATE NOT NULL,
    batas_kembali DATE NOT NULL,
    status        ENUM('dipinjam','sebagian dikembalikan','selesai') NOT NULL DEFAULT 'dipinjam',
    PRIMARY KEY (id),
    INDEX idx_transaksi_nim_status (nim, status),
    CONSTRAINT fk_transaksi_mahasiswa FOREIGN KEY (nim) REFERENCES mahasiswa (nim),
    CONSTRAINT chk_transaksi_batas CHECK (batas_kembali >= tgl_pinjam)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS detail_transaksi (
    id_transaksi    VARCHAR(20) NOT NULL,
    kode_alat       VARCHAR(15) NOT NULL,
    status          ENUM('dipinjam','dikembalikan') NOT NULL DEFAULT 'dipinjam',
    kondisi_kembali ENUM('baik','rusak ringan','rusak berat') NULL,
    tgl_kembali     DATE NULL,
    PRIMARY KEY (id_transaksi, kode_alat),
    INDEX idx_detail_alat (kode_alat, status),
    CONSTRAINT fk_detail_transaksi FOREIGN KEY (id_transaksi) REFERENCES transaksi (id),
    CONSTRAINT fk_detail_alat FOREIGN KEY (kode_alat) REFERENCES alat (kode),
    CONSTRAINT chk_detail_kembali CHECK (
        (status = 'dipinjam' AND kondisi_kembali IS NULL AND tgl_kembali IS NULL)
        OR (status = 'dikembalikan' AND kondisi_kembali IS NOT NULL AND tgl_kembali IS NOT NULL))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS log_aktivitas (
    id         INT NOT NULL AUTO_INCREMENT,
    waktu      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    petugas    VARCHAR(50) NOT NULL,
    aksi       VARCHAR(30) NOT NULL,
    keterangan VARCHAR(255) NOT NULL,
    PRIMARY KEY (id),
    INDEX idx_log_waktu (waktu)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
