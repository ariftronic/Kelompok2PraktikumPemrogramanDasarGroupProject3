-- Data contoh Kelompok 2: 5 mahasiswa, 10 alat, 3 transaksi (dari data_sampel/).
-- Jalankan setelah schema.sql. Urutan: tabel induk (mahasiswa, alat) lalu anak (transaksi, detail).

INSERT INTO mahasiswa VALUES
  ('M001', 'Andi Pratama', '081234567890', 'aktif'),
  ('M002', 'Budi Santoso', '081298765432', 'tidak aktif'),
  ('M003', 'Citra Lestari', '085712345678', 'aktif'),
  ('M004', 'Dewi Anggraini', '087811223344', 'tidak aktif'),
  ('M005', 'Eko Prasetyo', NULL, 'tidak aktif');

INSERT INTO alat VALUES
  ('A001', 'Multimeter Digital', 'pengukuran', 'baik', 'dipinjam'),
  ('A002', 'Osiloskop', 'pengukuran', 'baik', 'dipinjam'),
  ('A003', 'Power Supply DC', 'sumber daya', 'baik', 'tersedia'),
  ('A004', 'Breadboard', 'prototyping', 'rusak ringan', 'tidak tersedia'),
  ('A005', 'Arduino Uno', 'mikrokontroler', 'baik', 'dipinjam'),
  ('A006', 'Solder Station', 'perkakas', 'baik', 'tersedia'),
  ('A007', 'Kabel Jumper', 'prototyping', 'baik', 'tersedia'),
  ('A008', 'Logic Analyzer', 'pengukuran', 'baik', 'tersedia'),
  ('A009', 'Function Generator', 'pengukuran', 'rusak berat', 'tidak tersedia'),
  ('A010', 'Sensor Ultrasonik HC-SR04', 'sensor', 'baik', 'tersedia');

INSERT INTO transaksi VALUES
  ('T001', 'M001', '2026-11-02', '2026-11-09', 'dipinjam'),
  ('T002', 'M002', '2026-10-26', '2026-11-02', 'selesai'),
  ('T003', 'M003', '2026-11-03', '2026-11-10', 'sebagian dikembalikan');

INSERT INTO detail_transaksi VALUES
  ('T001', 'A001', 'dipinjam', NULL, NULL),
  ('T001', 'A002', 'dipinjam', NULL, NULL),
  ('T002', 'A003', 'dikembalikan', 'baik', '2026-11-01'),
  ('T003', 'A004', 'dikembalikan', 'rusak ringan', '2026-11-05'),
  ('T003', 'A005', 'dipinjam', NULL, NULL);
