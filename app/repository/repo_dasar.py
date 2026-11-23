

class RepoDasar:

    def __init__(self, db):
        self.db = db

    @staticmethod
    def pola_like(kata):
        return '%' + kata.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'

    @staticmethod
    def potongan_halaman(batas, mulai):
        if batas is None:
            return '', ()
        return ' LIMIT %s OFFSET %s', (int(batas), int(mulai))

    @staticmethod
    def kunci_sql(kunci):
        return ' FOR UPDATE' if kunci else ''

    def syarat_kata(self, kata_kunci, kolom):
        bagian, parameter = [], []
        for kata in kata_kunci.split():
            bagian.append('(' + ' OR '.join(('%s LIKE %%s' % k for k in kolom)) + ')')
            parameter.extend([self.pola_like(kata)] * len(kolom))
        return ' AND '.join(bagian) or '1=0', tuple(parameter)
