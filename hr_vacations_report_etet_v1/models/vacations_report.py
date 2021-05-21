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

class VacationsReport(models.TransientModel):
    _name = 'vacations.report'
    _description = 'Reporte Libro Vacaciones'

    data = fields.Binary("Archivo")
    data_name = fields.Char("nombre del archivo")
    contratos = fields.Many2many('hr.contract')
    modo = fields.Selection(string="Generar reporte por:", selection=[('1', 'Empleado'), ('2', 'Estructura'),('3', 'General')])
    empleado = fields.Many2one('hr.employee', string='Empleado')
    departamento = fields.Many2one('hr.department', string='Departamento')
    date_creation = fields.Date('Created Date', default=fields.Date.today())
    hora = time.strftime('%Y-%m-%d')

    def do_report(self):

        _logger.error("INICIA LA FUNCIÓN GENERAR EL REPORTE ")
        self.make_file()
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=vacations.report&field=data&id=%s&filename=%s' % (
            self.id, self.data_name),
            'target': 'new',
            'nodestroy': False,
        }

    def make_file(self):
        _logger.error("INICIA LA FUNCIÓN CONSTRUIR EL ARCHIVO ")

        if self.modo == '1':
            contratos = self.env['hr.contract'].search([('employee_id', '=', self.empleado.id)])
        elif self.modo == '2':
            contratos = self.env['hr.contract'].search([('department_id', '=', self.departamento.id), ('employee_id', '!=', False)])
        else:
            contratos = self.env['hr.contract'].search([('employee_id', '!=', False)])

        date_creation = fields.Date.today()
        hora = time.strftime('%H:%M:%S')
        if not contratos:
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
        ws.write(1, 10, date_creation, format_date)
        ws.merge_range('A2:I2', 'LIBRO DE VACACIONES', title_head)
        ws.write(1, 9, 'Fecha de corte:', title_head)
        ws.write(2, 9, 'Hora de generación:', title_head)
        ws.write(2, 10, hora)

        fila = 3
        for cont in contratos:
            ws.write(fila, 0, 'DOCUMENTO', title_head)
            ws.write(fila, 1, 'NOMBRE', title_head)
            ws.write(fila, 2, 'FECHA INGRESO ', title_head)
            ws.write(fila, 3, 'DÍAS LABORADOS ', title_head)
            ws.write(fila, 4, 'DÍAS PENDIENTES A LA FECHA', title_head)
            ws.write(fila, 5, 'FECHA INICIO DISFRUTE', title_head)
            ws.write(fila, 6, 'FECHA FIN DISFRUTE', title_head)
            ws.write(fila, 7, 'DÍAS HÁBILES', title_head)
            ws.write(fila, 8, 'DÍAS NO HÁBILES', title_head)
            ws.write(fila, 9, 'DÍAS TOTALES', title_head)
            ws.write(fila, 10, 'VALOR PAGADO', title_head)

            fila += 1

            ws.write(fila, 0, '') if not cont.employee_id.identification_id else ws.write(fila, 0, cont.employee_id.identification_id)
            ws.write(fila, 1, '') if not cont.employee_id.name else ws.write(fila, 1, cont.employee_id.name)
            ws.write(fila, 2, '') if not cont.date_start else ws.write(fila, 2, cont.date_start, format_date)
            dias_calculo = date_creation - cont.date_start
            dias_lab = dias_calculo.days
            ws.write(fila, 3, 0) if not dias_lab else ws.write(fila, 3, dias_lab)
            ws.write(fila, 4, 0) if not cont.vacations_available else ws.write(fila, 4, cont.vacations_available)

            total_dias_habiles = 0
            total_dias_no_habiles = 0
            total_dias = 0
            total_valor_pagado = 0
            if cont.vacations_history:

                for vac in cont.vacations_history:
                    ws.write(fila, 5, '') if not vac.request_date_from else ws.write(fila, 5, vac.request_date_from, format_date)
                    ws.write(fila, 6, '') if not vac.request_date_to else ws.write(fila, 6, vac.request_date_to, format_date)
                    #
                    dias_totales = ((vac.request_date_to - vac.request_date_from).days) + 1
                    dias_no_habiles = dias_totales - vac.number_of_days

                    ws.write(fila, 7, 0) if not vac.name else ws.write(fila, 7, vac.number_of_days)
                    total_dias_habiles += int(vac.number_of_days)
                    ws.write(fila, 8, 0) if not vac.name else ws.write(fila, 8, dias_no_habiles)
                    total_dias_no_habiles += int(dias_no_habiles)
                    ws.write(fila, 9, 0) if not vac.name else ws.write(fila, 9, dias_totales)
                    total_dias += int(dias_totales)
                    ws.write(fila, 10, 0) if not vac.name else ws.write(fila, 10, vac.amount_vacations, format_number)
                    total_valor_pagado += vac.amount_vacations


                    fila += 1

            if not cont.vacations_history:
                fila += 1
            ws.write(fila, 0, '', title_head)
            ws.write(fila, 1, '', title_head)
            ws.write(fila, 2, '', title_head)
            ws.write(fila, 3, '', title_head)
            ws.write(fila, 4, '', title_head)
            ws.write(fila, 5, '', title_head)
            ws.write(fila, 6, 'TOTAL', title_head)

            ws.write(fila, 7, 0, format_number1) if not total_dias_habiles else ws.write(fila, 7, total_dias_habiles, format_number1)
            ws.write(fila, 8, 0, format_number1) if not total_dias_no_habiles else ws.write(fila, 8, total_dias_no_habiles, format_number1)
            ws.write(fila, 9, 0, format_number1), format_number1 if not total_dias else ws.write(fila, 9, total_dias, format_number1)
            ws.write(fila, 10, 0,format_number1) if not total_dias else ws.write(fila, 10, total_valor_pagado, format_number1)
            fila += 1
            ws.write(fila, 0, '')
            fila += 1
            ws.write(fila, 1, '')

        try:
            wb.close()
            out = base64.encodestring(buf.getvalue())
            buf.close()
            self.data = out
            self.data_name = 'Libro de vacaciones' + ".xls"
        except ValueError:
            raise Warning('No se pudo generar el archivo')

#
