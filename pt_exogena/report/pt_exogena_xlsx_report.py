# -*- coding:utf-8 -*-
from odoo import api, fields, models, _


class ExogenaReportXLSX(models.AbstractModel):
    _name = 'report.pt_exogena.exogena_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Exogena information XLSX'

    def generate_xlsx_report(self, workbook, data, partners):
        columns = data["columns"]
        lineas = data["lines"]

        ws = workbook.add_worksheet("Informacion Formato " + data["type"])
        title = workbook.add_format({'bold': True, 'font_color': 'blue', 'align': 'center', 'font_size': '20'})
        title.set_align('center')
        header_row_style = workbook.add_format({'bold': True, 'font_color': 'blue', 'align': 'center', 'border': 1})
        header_row_style.set_align('center')
        ws.merge_range('A1:H1', 'Informacion Formato ' + data["type"], title)

        # Header
        row = 3
        col = 0
        for column in columns:
            ws.write(row, col, column, header_row_style)
            col += 1

        # Data
        row = 4
        for line in lineas:
            col = 0
            for column in columns:
                ws.write(row, col, line[column])
                col += 1
            row += 1
