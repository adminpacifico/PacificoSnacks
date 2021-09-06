# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning, ValidationError
import time
from datetime import date, timedelta, datetime
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

class plantillaReport(models.TransientModel):
    _name = 'plantilla.report'
    _description = 'verificacion de nomina empleados'

    data = fields.Binary("Archivo")
    data_name = fields.Char("nombre del archivo")
    nominas = fields.Many2one('hr.payslip', string='nomina')
    date_creation = fields.Date('Created Date', default=fields.Date.today())
    date_ini = fields.Date('fecha inicio', default=fields.Date.today())
    date_fin = fields.Date('fecha fin', default=fields.Date.today())

    lote = fields.Many2one('hr.payslip.run', string='LOTE')
    hora = time.strftime('%Y-%m-%d')

    def do_report(self):

        _logger.error("INICIA LA FUNCIÓN GENERAR EL REPORTE ")
        self.make_file()
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=plantilla.report&field=data&id=%s&filename=%s' % (
            self.id, self.data_name),
            'target': 'new',
            'nodestroy': False,
        }

    def make_file(self):
        _logger.error("INICIA LA FUNCIÓN CONSTRUIR EL ARCHIVO ")

        año = self.date_ini.strftime('%Y')
        mes = self.date_ini.strftime('%m')

        #nominas = self.env['hr.payslip'].search([('date_from', '=', self.date_ini)])
        #hdate_init_6month = date(self.date_from.year, 1, 1)

        nominas = self.env['hr.payslip'].search([("date_from", ">=", self.date_ini), ("date_to", "<=", self.date_fin)])
        date_creation = fields.Date.today()

        hora = time.strftime('%H:%M:%S')
        if not nominas:
            raise Warning(_('!No hay resultados para los datos seleccionados¡'))

        buf = BytesIO()
        wb = xlsxwriter.Workbook(buf)
        ws = wb.add_worksheet('Report')
        ws.set_column('A:E', 10)
        ws.set_column('F:F', 60)
        ws.set_column('G:G', 12)
        ws.set_column('J:K', 10)
        ws.set_column('H:Z', 18)

        # formatos
        title_head = wb.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'fg_color': '#33CCCC',
            'valign': 'vcenter',
            })
        title_single = wb.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })
        title_head.set_font_name('Arial')
        title_head.set_font_size(10)
        title_head.set_font_color('black')
        format_date = wb.add_format({'num_format': 'mm/dd/yyyy'})
        format_number = wb.add_format({'num_format': '#,##0.00'})
        format_number1 = wb.add_format({'num_format': '#,##0.00', 'fg_color': '#33CCCC', 'border': 1})

        ws.merge_range('B1:J1', 'PACIFICO SNACKS', title_head)
        ws.write(1, 10, date_creation, format_date)
        ws.merge_range('A2:I2', 'PLANILLA LIQUIDACIÓN APORTES SEGURIDAD SOCIAL', title_head)
        ws.write(1, 9, 'Fecha de corte:', title_head)
        ws.write(2, 9, 'Hora de generación:', title_head)
        ws.write(2, 10, hora)
        ws.merge_range('A4:C4', 'Identificación', title_single)
        ws.merge_range('D4:E4', 'Periodo Pensión', title_single)
        ws.merge_range('F4:I4', 'Novedad', title_single)
        ws.merge_range('J4:K4', 'Días', title_single)
        ws.write(3, 11, 'Ing y Ret', title_single)
        ws.merge_range('M4:N4', 'VST', title_single)
        ws.merge_range('P4:Q4', 'SLN', title_single)
        ws.write(3, 14, 'IGE', title_single)
        ws.write(3, 17, 'VAC', title_single)
        ws.write(3, 18, 'VHL', title_single)

        fila = 5
        ws.write(4, 0, 'No.', title_head)
        ws.write(4, 1, 'Tipo ID', title_head)
        ws.write(4, 2, 'No ID', title_head)
        ws.write(4, 3, 'Año', title_head)
        ws.write(4, 4, 'Mes', title_head)
        ws.write(4, 5, 'Tipo de Novedad', title_head)
        ws.write(4, 6, 'Valor Total', title_head)
        ws.write(4, 7, 'Ajustar Valor de la Novedad', title_head)
        ws.write(4, 8, 'Realizar Aportes Parafiscales', title_head)
        ws.write(4, 9, 'Inicial', title_head)
        ws.write(4, 10, 'Duración', title_head)
        ws.write(4, 11, 'Tipo de Ingreso o Retiro', title_head)
        ws.write(4, 12, 'La variacion de salario aplica para el IBC de Parafiscales', title_head)
        ws.write(4, 13, 'La variacion de salario aplica para el IBC de SENA e ICBF', title_head)
        ws.write(4, 14, 'Cotizar los Días de la Incapacidad con el 100% del Salario', title_head)
        ws.write(4, 15, 'Tipo de Licencia', title_head)
        ws.write(4, 16, 'Tarifa de Pensión', title_head)
        ws.write(4, 17, 'Tipo de Vacaciones', title_head)
        ws.write(4, 18, 'Total Horas Laboradas Mes', title_head)
        n = 1
        for nom in nominas:

            ws.write(fila, 0, 0) if not fila else ws.write(fila, 0, n)
            ws.write(fila, 0, 1) if not 'CC' else ws.write(fila, 1, 'CC')
            identificacion = nom.contract_id.employee_id.identification_id
            ws.write(fila, 0, 2) if not identificacion else ws.write(fila, 2, identificacion)

            ws.write(fila, 0, 3) if not año else ws.write(fila, 3, año)
            ws.write(fila, 0, 4) if not mes else ws.write(fila, 4, mes)


            ws.write(fila, 0, '') if not '' else ws.write(fila, 11, '')

            ws.write(fila, 0, 16) if not '' else ws.write(fila, 16, 'TARIFA DEL EMPLEADOR')
            for work in nom.worked_days_line_ids.filtered(lambda x: x.work_entry_type_id.name == 'Total Días'):
                ws.write(fila, 0, 18) if not work.number_of_hours else ws.write(fila, 18, work.number_of_hours)


            if nom.line_ids.filtered(lambda x: x.code == 'VST'):


                for line in nom.line_ids.filtered(lambda x: x.code == 'VST'):

                    ws.write(fila, 0, '') if not line.name else ws.write(fila, 5, line.name)
                    variacion = line.amount
                    valor_vst = line.amount + variacion

                    ws.write(fila, 0, '') if not valor_vst else ws.write(fila, 6, valor_vst, format_number)
                    ws.write(fila, 0, 'NO') if not 'SI' else ws.write(fila, 7, 'SI')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 8, 'NO')
                    ws.write(fila, 0, '') if not '' else ws.write(fila, 9, '')
                    ws.write(fila, 0, '') if not '' else ws.write(fila, 10, '')
                    ws.write(fila, 0, 'SI') if not 'SI' else ws.write(fila, 12, 'SI')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 13, 'NO')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 14, 'NO')
            if nom.line_ids.filtered(lambda x: x.code == 'INCAPACIDADGENERAL'):
                for line in nom.line_ids.filtered(lambda x: x.code == 'INCAPACIDADGENERAL'):
                    ws.write(fila, 0, '') if not line.name else ws.write(fila, 5, 'INCAPACIDAD GENERAL (IGE)')
                    incapacidad_gen = line.amount
                    valor_incapacidad_gen = line.amount + incapacidad_gen
                    ws.write(fila, 0, '') if not valor_incapacidad_gen else ws.write(fila, 6, valor_incapacidad_gen, format_number)
                    ws.write(fila, 0, 'NO') if not 'SI' else ws.write(fila, 7, 'SI')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 8, 'NO')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 9, 'NO')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 10, 'NO')
                    ws.write(fila, 0, 'SI') if not 'SI' else ws.write(fila, 12, 'SI')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 13, 'NO')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 14, 'NO')
            if nom.line_ids.filtered(lambda x: x.code == 'INCAPACIDADLABORAL'):
                for line in nom.line_ids.filtered(lambda x: x.code == 'INCAPACIDADLABORAL'):
                    ws.write(fila, 0, '') if not line.name else ws.write(fila, 5, 'INCAPACIDAD lABORAL (IRL)')
                    incapacidad_lab = line.amount
                    valor_incapacidad_lab = line.amount + incapacidad_lab
                    ws.write(fila, 0, '') if not valor_incapacidad_lab else ws.write(fila, 6, valor_incapacidad_lab, format_number)
                    ws.write(fila, 0, 'NO') if not 'SI' else ws.write(fila, 7, 'SI')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 8, 'NO')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 9, 'NO')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 10, 'NO')
                    ws.write(fila, 0, 'SI') if not 'SI' else ws.write(fila, 12, 'SI')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 13, 'NO')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 14, 'NO')
            if nom.line_ids.filtered(lambda x: x.code == 'VACATIONS'):
                for line in nom.line_ids.filtered(lambda x: x.code == 'VACATIONS'):
                    ws.write(fila, 0, '') if not line.name else ws.write(fila, 5, 'VACACIONES (VAC)')
                    vacaciones = line.amount
                    valor_vacaciones = line.amount + vacaciones
                    ws.write(fila, 0, '') if not valor_vacaciones else ws.write(fila, 6, valor_vacaciones, format_number)
                    ws.write(fila, 0, 'NO') if not 'SI' else ws.write(fila, 7, 'SI')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 8, 'NO')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 9, 'NO')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 10, 'NO')
                    ws.write(fila, 0, 'SI') if not 'SI' else ws.write(fila, 12, 'SI')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 13, 'NO')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 14, 'NO')
            if nom.line_ids.filtered(lambda x: x.code == 'LICENCIALUTO'):
                for line in nom.line_ids.filtered(lambda x: x.code == 'LICENCIALUTO'):
                    ws.write(fila, 0, '') if not line.name else ws.write(fila, 5, 'VACACIONES (VAC)')
                    licencia_luto = line.amount
                    valor_licencia_luto = line.amount + licencia_luto
                    ws.write(fila, 0, '') if not valor_licencia_luto else ws.write(fila, 6, valor_licencia_luto, format_number)
                    ws.write(fila, 0, 'NO') if not 'SI' else ws.write(fila, 7, 'SI')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 8, 'NO')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 9, 'NO')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 10, 'NO')
                    ws.write(fila, 0, 'SI') if not 'SI' else ws.write(fila, 12, 'SI')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 13, 'NO')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 14, 'NO')
            if nom.line_ids.filtered(lambda x: x.code == 'LICENCIAMATERNIDAD'):
                for line in nom.line_ids.filtered(lambda x: x.code == 'LICENCIAMATERNIDAD'):
                    ws.write(fila, 0, '') if not line.name else ws.write(fila, 5, 'LICENCIA DE MATERNIDAD (LMA)')
                    licencia_maternidad = line.amount
                    valor_maternidad = line.amount + licencia_maternidad
                    ws.write(fila, 0, '') if not valor_maternidad else ws.write(fila, 6, valor_maternidad, format_number)
                    ws.write(fila, 0, 'NO') if not 'SI' else ws.write(fila, 7, 'SI')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 8, 'NO')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 9, 'NO')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 10, 'NO')
                    ws.write(fila, 0, 'SI') if not 'SI' else ws.write(fila, 12, 'SI')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 13, 'NO')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 14, 'NO')
            if nom.line_ids.filtered(lambda x: x.code == 'LICENCIANOREMUNERADA'):
                for line in nom.line_ids.filtered(lambda x: x.code == 'LICENCIANOREMUNERADA'):
                    licencia_no_remunerada = line.amount
                    valor_licencia_no_remunerada = line.amount + licencia_no_remunerada
                    if valor_licencia_no_remunerada >= 0:
                        ws.write(fila, 0, '') if not line.name else ws.write(fila, 5, 'SUSPENSIÓN TEMPORAL DEL CONTRATO DE TRABAJO (SLN)')

                        ws.write(fila, 0, '') if not valor_licencia_no_remunerada else ws.write(fila, 6, valor_licencia_no_remunerada, format_number)
                        ws.write(fila, 0, 'NO') if not 'SI' else ws.write(fila, 7, 'SI')
                        ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 8, 'NO')
                        ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 9, 'NO')
                        ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 10, 'NO')
                        ws.write(fila, 0, 'SI') if not 'SI' else ws.write(fila, 12, 'SI')
                        ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 13, 'NO')
                        ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 14, 'NO')
            if nom.line_ids.filtered(lambda x: x.code == 'IMPAGADA'):
                for line in nom.line_ids.filtered(lambda x: x.code == 'IMPAGADA'):
                    licencia_impagada = line.amount
                    valor_licencia_impagada = line.amount + licencia_impagada
                    if valor_licencia_impagada >= 0:

                        ws.write(fila, 0, '') if not line.name else ws.write(fila, 5, 'SUSPENSIÓN TEMPORAL DEL CONTRATO DE TRABAJO (SLN)')
                        ws.write(fila, 0, '') if not valor_licencia_impagada else ws.write(fila, 6, valor_licencia_impagada, format_number)
                        ws.write(fila, 0, 'NO') if not 'SI' else ws.write(fila, 7, 'SI')
                        ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 8, 'NO')
                        ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 9, 'NO')
                        ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 10, 'NO')
                        ws.write(fila, 0, 'SI') if not 'SI' else ws.write(fila, 12, 'SI')
                        ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 13, 'NO')
                        ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 14, 'NO')
            if nom.line_ids.filtered(lambda x: x.code == 'VACATIONS_LIQ'):
                for line in nom.line_ids.filtered(lambda x: x.code == 'VACATIONS_LIQ'):
                    ws.write(fila, 0, '') if not line.name else ws.write(fila, 5, 'VARIACIÓN IBC PARAFISCALES (VIP)')
                    variacion_liq = line.amount
                    valor_variacion_liq = line.amount + variacion_liq
                    ws.write(fila, 0, '') if not valor_variacion_liq else ws.write(fila, 6, valor_variacion_liq, format_number)
                    ws.write(fila, 0, 'NO') if not 'SI' else ws.write(fila, 7, 'SI')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 8, 'NO')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 9, 'NO')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 10, 'NO')
                    ws.write(fila, 0, 'SI') if not 'SI' else ws.write(fila, 12, 'SI')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 13, 'NO')
                    ws.write(fila, 0, 'NO') if not 'NO' else ws.write(fila, 14, 'NO')

            n += 1
            fila += 1

        try:
            wb.close()
            out = base64.encodestring(buf.getvalue())
            buf.close()
            self.data = out
            self.data_name = 'Plantilla Aportes en Linea' + ".xls"
        except ValueError:
            raise Warning('No se pudo generar el archivo')