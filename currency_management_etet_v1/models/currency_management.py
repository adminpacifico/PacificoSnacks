# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning, ValidationError
import time
from datetime import datetime, timedelta, date
import xlwt
import base64
# from cStringIO import StringIO
from io import StringIO
from io import BytesIO
import xlsxwriter
import types
import logging

_logger = logging.getLogger(__name__)


class DivisasReport(models.TransientModel):
    _name = 'divisas.report'
    _description = 'Reporte Divisas'

    data = fields.Binary("Archivo")
    data_name = fields.Char("nombre del archivo")
    fecha_inicial = fields.Date(string='Fecha de Inicial')
    fecha_final = fields.Date(string='Fecha de Final')
    estado = fields.Boolean(string='pago')
    date_creation = fields.Date('Created Date', required=True, default=fields.Date.today())
    hora = time.strftime('%Y-%m-%d')
    facturas = fields.Many2many('account.move', string='facturas', required=True)
    pagos = fields.Many2many('account.payment', string='pagos')
    modo = fields.Selection(string="Generar reporte por:", selection=[('1', 'Clientes'), ('2', 'Proveedores'), ('3', 'General')])



    def do_report(self):

        _logger.error("INICIA LA FUNCIÓN GENERAR EL REPORTE ")
        self.make_file()
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=divisas.report&field=data&id=%s&filename=%s' % (
                self.id, self.data_name),
            'target': 'new',
            'nodestroy': False,
        }

    def make_file(self):
        _logger.error("INICIA LA FUNCIÓN CONSTRUIR EL ARCHIVO ")

        #proveedores = self.env['res.partner'].search([("category_id.name", "=", 'Cliente Exportación')])
        #for p in proveedores:
        #    pagos = self.env['account.payment'].search(
        #        [("currency_id", "!=", 8), '&', ("payment_date", ">=", self.fecha_inicial),
        #         ("payment_date", "<=", self.fecha_final), ("partner_id", "=", p.id)])
        pagos = self.env['account.payment'].search([("currency_id", "!=", 8), '&', ("payment_date", ">=", self.fecha_inicial), ("payment_date", "<=", self.fecha_final)])
        date_creation = fields.Date.today()
        hora = time.strftime('%H:%M:%S')
        if not pagos:
            raise Warning(_('!No hay resultados para los datos seleccionados¡'))

        buf = BytesIO()
        wb = xlsxwriter.Workbook(buf)
        ws = wb.add_worksheet('Report')
        ws.set_column('A:A', 15)
        ws.set_column('B:B', 65)
        ws.set_column('C:Z', 18)
        # formatos
        title_head = wb.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'fg_color': '#33CCCC',
            'valign': 'vcenter',

        })
        title_head.set_font_name('Arial')
        title_head.set_font_size(10)
        title_head.set_font_color('black')
        format_date = wb.add_format({'num_format': 'mm/dd/yyyy'})
        format_number = wb.add_format({'num_format': '#,##0.00'})
        format_number1 = wb.add_format({'num_format': '#,##0.00', 'border': 1, 'fg_color': '#33CCCC'})

        ws.merge_range('A1:K1', 'PACIFICO SNACKS', title_head)
        ws.merge_range('A2:I2', 'REPORTE DIVISAS', title_head)
        ws.write(1, 10, date_creation, format_date)

        ws.write(1, 9, 'Fecha:')
        ws.write(2, 9, 'hora:')
        ws.write(2, 10, hora)


        fila = 2
        for pay in pagos:
            fila += 1
            if pay.invoice_ids:
                ws.write(fila, 0, 'FECHA', title_head)
                ws.write(fila, 1, 'TERCERO', title_head)
                ws.write(fila, 2, 'SEDE', title_head)
                ws.write(fila, 3, 'N° DE FV', title_head)
                ws.write(fila, 4, 'TRM EN VENTA', title_head)
                ws.write(fila, 5, 'TOTAL USD', title_head)
                ws.write(fila, 6, 'TOTAL FISCAL', title_head)
                ws.write(fila, 7, 'TRM PGO', title_head)
                ws.write(fila, 8, 'TOTAL CONTABLE', title_head)
                ws.write(fila, 9, 'DIFERENCIA', title_head)
                ws.write(fila, 10, 'FECHA DE PAGO', title_head)

                total_trm = 0
                total_factura = 0
                total_fiscal = 0
                total_trm_pago = 0
                total_contable = 0
                total_diferencia = 0
                for fv in pay.invoice_ids:
                    fila += 1
                    ws.write(fila, 0, '') if not fv.invoice_date else ws.write(fila, 0, fv.invoice_date, format_date)
                    ws.write(fila, 1, '') if not fv.invoice_partner_display_name else ws.write(fila, 1,
                                                                                               fv.invoice_partner_display_name)
                    ws.write(fila, 2, '') if not fv.partner_id.street else ws.write(fila, 2, fv.partner_id.street)
                    ws.write(fila, 3, '') if not fv.name else ws.write(fila, 3, fv.name)
                    valor_trm = fv.trm
                    ws.write(fila, 4, '') if not fv.name else ws.write(fila, 4, valor_trm, format_number)
                    total_trm += valor_trm
                    valor_factura = fv.amount_total
                    ws.write(fila, 5, '') if not fv.name else ws.write(fila, 5, valor_factura, format_number)
                    total_factura += valor_factura
                    valor_total_fiscal = valor_factura * valor_trm
                    ws.write(fila, 6, '') if not fv.name else ws.write(fila, 6, valor_total_fiscal, format_number)
                    total_fiscal += valor_total_fiscal
                    trm_pago = pay.trm
                    ws.write(fila, 7, '') if not fv.name else ws.write(fila, 7, trm_pago, format_number)
                    total_trm_pago += trm_pago
                    valor_total_contable = valor_factura * trm_pago
                    ws.write(fila, 8, '') if not fv.name else ws.write(fila, 8, valor_total_contable, format_number)
                    total_contable += valor_total_contable
                    valor_diferencia = valor_total_fiscal - valor_total_contable
                    ws.write(fila, 9, '') if not fv.name else ws.write(fila, 9, valor_diferencia, format_number)
                    total_diferencia += valor_diferencia
                    ws.write(fila, 10, '') if not fv.name else ws.write(fila, 10, pay.payment_date, format_date)
            else:
                ws.write(fila, 0, '')
            fila += 1
            ws.write(fila, 0, '', format_number1)
            ws.write(fila, 1, '', format_number1)
            ws.write(fila, 2, '', format_number1)
            ws.write(fila, 3, 'TOTAL', format_number1)
            ws.write(fila, 4, '') if not total_trm else ws.write(fila, 4, total_trm, format_number1)
            ws.write(fila, 5, 0, format_number1) if not total_factura else ws.write(fila, 5, total_factura, format_number1)
            ws.write(fila, 6, 0, format_number1) if not total_fiscal else ws.write(fila, 6, total_fiscal,
                                                                                   format_number1)
            ws.write(fila, 7, 0, format_number1) if not total_trm_pago else ws.write(fila, 7, total_trm_pago,
                                                                                     format_number1)
            ws.write(fila, 8, 0, format_number1) if not total_contable else ws.write(fila, 8, total_contable,
                                                                                     format_number1)
            ws.write(fila, 9, 0, format_number1) if not total_diferencia else ws.write(fila, 9, total_diferencia,
                                                                                       format_number1)
            ws.write(fila, 10, '', format_number1)
            fila += 1

        try:
            wb.close()
            out = base64.encodestring(buf.getvalue())
            buf.close()
            self.data = out
            self.data_name = 'REPORTE DIVISAS' + ".xls"
        except ValueError:
            raise Warning('No se pudo generar el archivo')

#
