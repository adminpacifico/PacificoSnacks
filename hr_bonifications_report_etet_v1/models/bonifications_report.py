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
import time
_logger = logging.getLogger(__name__)

class BonificationsReport(models.TransientModel):
    _name = 'bonifications.report'
    _description = 'Reporte Bonificaciones'

    data = fields.Binary("Archivo")
    data_name = fields.Char("nombre del archivo")
    loans = fields.Many2many('hr.loan')
    modo = fields.Selection(string="Generar reporte por:", selection=[('1', 'Empleado'), ('2', 'Empleados Activos'), ('3', 'General')])
    empleado = fields.Many2one('hr.employee', string='Empleado')
    date_creation = fields.Date('Created Date', default=fields.Date.today())
    hora = time.strftime('%Y-%m-%d')

    def do_report(self):

        _logger.error("INICIA LA FUNCIÓN GENERAR EL REPORTE ")
        self.make_file()
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=bonifications.report&field=data&id=%s&filename=%s' % (
            self.id, self.data_name),
            'target': 'new',
            'nodestroy': False,
        }

    def make_file(self):
        _logger.error("INICIA LA FUNCIÓN CONSTRUIR EL ARCHIVO ")

        if self.modo == '1':
            loans = self.env['hr.loan'].search([('employee_id', '=', self.empleado.id)])
        elif self.modo == '2':
            loans = self.env['hr.loan'].search([('employee_id', '!=', False), ('state', '!=', 'Terminado')])
        else:
            loans = self.env['hr.loan'].search([('employee_id', '!=', False)])




        date_creation = fields.Date.today()
        hora = time.strftime('%H:%M:%S')
        if not loans:
            raise Warning(_('!No hay resultados para los datos seleccionados¡'))

        buf = BytesIO()
        wb = xlsxwriter.Workbook(buf)
        ws = wb.add_worksheet('Report')
        ws.set_column('A:A', 15)
        ws.set_column('B:B', 65)
        ws.set_column('C:G', 23)
        ws.set_column('H:Z', 18)

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
        format_number1 = wb.add_format({'num_format': '#,##0.00', 'fg_color': '#33CCCC', 'border': 1})

        ws.write(0, 1, 'PACIFICO SNACKS', title_head)
        ws.write(1, 3, date_creation, format_date)
        ws.merge_range('A2:B2', 'REPORTE BONIFICACIONES', title_head)
        ws.write(1, 2, 'Fecha de corte:', title_head)
        ws.write(2, 2, 'Hora de generación:', title_head)
        ws.write(2, 3, hora)

        fila = 3
        for l in loans:
            ws.write(fila, 0, 'NOMBRE', title_head)
            ws.write(fila, 1, 'DOCUMENTO', title_head)
            ws.write(fila, 2, 'FECHA ', title_head)
            ws.write(fila, 3, 'VALOR BONIFICACIÓN', title_head)

            fila += 1

            ws.write(fila, 1, '') if not l.employee_id.identification_id else ws.write(fila, 0, l.employee_id.identification_id)
            ws.write(fila, 0, '') if not l.employee_id.name else ws.write(fila, 1, l.employee_id.name)



            total_bonificaciones = 0
            total_dias_no_habiles = 0
            total_dias = 0
            total_valor_pagado = 0
            if l.loan_lines:

                for line in l.loan_lines:
                    ws.write(fila, 2, '') if not line.date else ws.write(fila, 2, line.date, format_date)
                    ws.write(fila, 3, '') if not line.amount else ws.write(fila, 3, line.amount, format_number)
                    total_bonificaciones += line.amount


                    fila += 1

            if not l.loan_lines:
                fila += 1
            ws.write(fila, 0, '', title_head)
            ws.write(fila, 1, '', title_head)


            ws.write(fila, 2, 'TOTAL', title_head)

            ws.write(fila, 3, 0, format_number1) if not total_bonificaciones else ws.write(fila, 3, total_bonificaciones, format_number1)
            #ws.write(fila, 8, 0, format_number1) if not total_dias_no_habiles else ws.write(fila, 8, total_dias_no_habiles, format_number1)
            #ws.write(fila, 9, 0, format_number1), format_number1 if not total_dias else ws.write(fila, 9, total_dias, format_number1)
            #ws.write(fila, 10, 0,format_number1) if not total_dias else ws.write(fila, 10, total_valor_pagado, format_number1)
            fila += 1
            ws.write(fila, 0, '')
            fila += 1
            ws.write(fila, 1, '')

        try:
            wb.close()
            out = base64.encodestring(buf.getvalue())
            buf.close()
            self.data = out
            self.data_name = 'Reporte Bonificaciones' + ".xls"
        except ValueError:
            raise Warning('No se pudo generar el archivo')

#
