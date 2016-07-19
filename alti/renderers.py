# -*- coding: utf-8 -*-


class CSVRenderer(object):

    def __init__(self, info):
        pass

    def __call__(self, value, system):
        import csv
        import StringIO
        fout = StringIO.StringIO()
        writer = csv.writer(fout, delimiter=';', quoting=csv.QUOTE_ALL)

        writer.writerow(value['headers'])
        writer.writerows(value['rows'])

        resp = system['request'].response
        resp.content_type = 'text/csv'
        resp.content_disposition = 'attachment;filename="profile.csv"'
        return fout.getvalue()
