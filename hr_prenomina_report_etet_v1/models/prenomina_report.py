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

class PrenominaReport(models.TransientModel):
    _name = 'prenomina.report'
    _description = 'verificacion de nomina empleados'

    data = fields.Binary("Archivo")
    data_name = fields.Char("nombre del archivo")
    nominas = fields.Many2one('hr.payslip', string='nomina')
    lote = fields.Many2one('hr.payslip.run', string='LOTE')
    date_creation = fields.Date('Created Date', default=fields.Date.today())
    hora = time.strftime('%Y-%m-%d')

    def do_report(self):

        _logger.error("INICIA LA FUNCIÓN GENERAR EL REPORTE ")
        self.make_file()
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=prenomina.report&field=data&id=%s&filename=%s' % (
            self.id, self.data_name),
            'target': 'new',
            'nodestroy': False,
        }

    def make_file(self):
        _logger.error("INICIA LA FUNCIÓN CONSTRUIR EL ARCHIVO ")

       # nominas = self.env['hr.payslip'].search([])
        nominas = self.env['hr.payslip'].search([('payslip_run_id', '=', self.lote.id)], order="struct_id")
        pass
        date_creation = fields.Date.today()
        hora = time.strftime('%H:%M:%S')
        if not nominas:
            raise Warning(_('!No hay resultados para los datos seleccionados¡'))

        buf = BytesIO()
        wb = xlsxwriter.Workbook(buf)
        ws = wb.add_worksheet('Report')
        ws.set_column('A:B', 15)
        ws.set_column('C:C', 65)
        ws.set_column('D:G', 23)
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

        ws.merge_range('B1:J1', 'PACIFICO SNACKS', title_head)
        ws.write(1, 10, date_creation, format_date)
        ws.merge_range('A2:I2', 'REVISIÓN NOMINA', title_head)
        ws.write(1, 9, 'Fecha de corte:', title_head)
        ws.write(2, 9, 'Hora de generación:', title_head)
        ws.write(2, 10, hora)

        fila = 3

        ws.write(3, 0, 'DEPARTAMENTO', title_head)
        ws.write(3, 1, 'IDENTIFICACIÓN', title_head)
        ws.write(3, 2, 'NOMBRE', title_head)
        ws.write(3, 3, 'SUELDO BASE', title_head)
        ws.write(3, 4, 'DÍAS', title_head)
        ws.write(3, 5, 'SUELDO', title_head)
        ws.write(3, 6, 'TOTAL DÍAS', title_head)
        ws.write(3, 7, 'DÍAS INC', title_head)
        ws.write(3, 8, 'INCAPACIDAD', title_head)
        ws.write(3, 9, 'PRIMA PROVISIÓN', title_head)
        ws.write(3, 10, 'AUXILIO DE TRANSPORTE', title_head)
        ws.write(3, 11, 'TOTAL DEVENGADO', title_head)
        ws.write(3, 12, 'SALUD', title_head)
        ws.write(3, 13, 'PENSIÓN', title_head)
        ws.write(3, 14, 'FSP', title_head)
        ws.write(3, 15, 'RETENCION', title_head)
        ws.write(3, 16, 'DESCUENTOS', title_head)
        ws.write(3, 17, 'TOTAL DEDUCCIONES', title_head)
        ws.write(3, 18, 'TOTAL A PAGAR', title_head)

        total_salario_adm = 0
        total_dias_adm = 0
        total_sueldo_adm = 0
        total_dias_no_lab_adm = 0
        total_dias_inc_adm = 0
        total_incapacidad_adm = 0
        total_prima_adm = 0
        total_auxiliot_adm = 0
        total_devengado_adm = 0
        total_salud_adm = 0
        total_pension_adm = 0
        total_fsp_adm = 0
        total_retencion_adm = 0
        total_descuentos_adm = 0
        total_deducciones_adm = 0
        total_a_pagar_adm = 0
        for nom in nominas:

            if nom.struct_id.name == 'Administrativa':
                fila += 1
                ws.write(fila, 0, 0) if not nom.contract_id.employee_id.department_id.name else ws.write(fila, 0, nom.contract_id.employee_id.department_id.name)
                ws.write(fila, 1, 0) if not nom.contract_id.employee_id.identification_id else ws.write(fila, 1, nom.contract_id.employee_id.identification_id)
                ws.write(fila, 2, 0) if not nom.contract_id.employee_id.name else ws.write(fila, 2, nom.contract_id.employee_id.name)
                salm = (nom.line_ids).search([('code', '=', 'SALCONTRACTO'), ('slip_id', '=', nom.id)])
                ws.write(fila, 3, 0) if not salm.total else ws.write(fila, 3, salm.total, format_number)
                total_salario_adm += salm.total
                work_day = (nom.worked_days_line_ids).search([('work_entry_type_id.code', '=', 'WORK100'), ('payslip_id', '=', nom.id)])
                ws.write(fila, 4, 0) if not work_day.number_of_days else ws.write(fila, 4, work_day.number_of_days)
                total_dias_adm += work_day.number_of_days
                sal = (nom.line_ids).search([('code', '=', 'SALARIO'), ('slip_id', '=', nom.id)])
                ws.write(fila, 5, 0) if not sal.total else ws.write(fila, 5, sal.total, format_number)
                total_sueldo_adm += sal.total
                work_days = (nom.worked_days_line_ids).search([('work_entry_type_id.code', '=', 'WORK100'), ('payslip_id', '=', nom.id)])
                ws.write(fila, 6, 0) if not work_days.number_of_days else ws.write(fila, 6, work_days.number_of_days)
                total_dias_no_lab_adm += work_days.number_of_days

                day_inc = (nom.worked_days_line_ids).search([('work_entry_type_id.code', '=', 'LEAVE110'), ('payslip_id', '=', nom.id)])
                ws.write(fila, 7, 0) if not day_inc.number_of_days else ws.write(fila, 7, day_inc.number_of_days)
                total_dias_inc_adm += day_inc.number_of_days
                incapacidades = (nom.line_ids).search([('code', '=', 'INCAPACIDADE'), ('slip_id', '=', nom.id)])
                ws.write(fila, 8, 0) if not incapacidades.total else ws.write(fila, 8, incapacidades.total)
                total_incapacidad_adm += incapacidades.total
                prima = (nom.line_ids).search([('code', '=', 'PROVPRIMA'), ('slip_id', '=', nom.id) ])
                ws.write(fila, 9, 0) if not prima.total else ws.write(fila, 9, prima.total, format_number)
                total_prima_adm += prima.total
                aux = (nom.line_ids).search([('code', '=', 'SUBSTRAN'), ('slip_id', '=', nom.id)])
                ws.write(fila, 10, 0) if not aux.total else ws.write(fila, 10, aux.total, format_number)
                total_auxiliot_adm += aux.total
                t_dev = (nom.line_ids).search([('code', '=', 'GROSS'), ('slip_id', '=', nom.id)])
                ws.write(fila, 11, 0) if not t_dev.total else ws.write(fila, 11, t_dev.total, format_number)
                total_devengado_adm += t_dev.total
                salud = (nom.line_ids).search([('code', '=', 'SALUDEMPLEADO'), ('slip_id', '=', nom.id)])
                ws.write(fila, 12, 0) if not salud.total else ws.write(fila, 12, salud.total, format_number)
                total_salud_adm += salud.total
                pension = (nom.line_ids).search([('code', '=', 'PENSIONEMPLEADO'), ('slip_id', '=', nom.id)])
                ws.write(fila, 13, 0) if not pension.total else ws.write(fila, 13, pension.total, format_number)
                total_pension_adm += pension.total
                fsp = (nom.line_ids).search([('code', '=', 'FSP'), ('slip_id', '=', nom.id)])
                ws.write(fila, 14, 0) if not fsp.total else ws.write(fila, 14, fsp.total, format_number)
                total_fsp_adm += fsp.total
                rtf = (nom.line_ids).search([('code', '=', 'RTFM1'), ('slip_id', '=', nom.id)])
                ws.write(fila, 15, 0) if not rtf.total else ws.write(fila, 15, rtf.total, format_number)
                total_retencion_adm += rtf.total
                descuentos = (nom.line_ids).search([('code', '=', 'DESCUENTOS'), ('slip_id', '=', nom.id)])
                ws.write(fila, 16, 0) if not descuentos.amount else ws.write(fila, 16, descuentos.amount, format_number)
                total_descuentos_adm += descuentos.amount
                t_ded = (nom.line_ids).search([('code', '=', 'TOTALDED'), ('slip_id', '=', nom.id)])
                ws.write(fila, 17, 0) if not t_ded.total else ws.write(fila, 17, t_ded.total, format_number)
                total_deducciones_adm += t_ded.total
                net = (nom.line_ids).search([('code', '=', 'NET'), ('slip_id', '=', nom.id)])
                ws.write(fila, 18, 0) if not net.total else ws.write(fila, 18, net.total, format_number)
                total_a_pagar_adm += net.total
        fila += 1
        ws.write(fila, 0, '', title_head)
        ws.write(fila, 1, '', title_head)
        ws.write(fila, 2, 'TOTAL ADMINISTRATIVO', title_head)
        ws.write(fila, 3, total_salario_adm, format_number1)
        ws.write(fila, 4, total_dias_adm, format_number1)
        ws.write(fila, 5, total_sueldo_adm, format_number1)
        ws.write(fila, 5, total_sueldo_adm, format_number1)
        ws.write(fila, 6, total_dias_no_lab_adm, format_number1)
        ws.write(fila, 7, total_dias_inc_adm, format_number1)
        ws.write(fila, 8, total_incapacidad_adm, format_number1)
        ws.write(fila, 9, total_prima_adm, format_number1)
        ws.write(fila, 10, total_auxiliot_adm, format_number1)
        ws.write(fila, 11, total_devengado_adm, format_number1)
        ws.write(fila, 12, total_salud_adm, format_number1)
        ws.write(fila, 13, total_pension_adm, format_number1)
        ws.write(fila, 14, total_fsp_adm, format_number1)
        ws.write(fila, 15, total_retencion_adm, format_number1)
        ws.write(fila, 16, total_descuentos_adm, format_number1)
        ws.write(fila, 17, total_deducciones_adm, format_number1)
        ws.write(fila, 18, total_a_pagar_adm, format_number1)

        total_salario_ope = 0
        total_dias_ope = 0
        total_sueldo_ope = 0
        total_dias_no_lab_ope = 0
        total_dias_inc_ope = 0
        total_incapacidad_ope = 0
        total_prima_ope = 0
        total_auxiliot_ope = 0
        total_devengado_ope = 0
        total_salud_ope = 0
        total_pension_ope = 0
        total_fsp_ope = 0
        total_retencion_ope = 0
        total_descuentos_ope = 0
        total_deducciones_ope = 0
        total_a_pagar_ope = 0
        for nom in nominas:

            if nom.struct_id.name == 'Operativa':
                fila += 1
                ws.write(fila, 0, 0) if not nom.contract_id.employee_id.department_id.name else ws.write(fila, 0,nom.contract_id.employee_id.department_id.name)
                ws.write(fila, 1, 0) if not nom.contract_id.employee_id.identification_id else ws.write(fila, 1, nom.contract_id.employee_id.identification_id)
                ws.write(fila, 2, 0) if not nom.contract_id.employee_id.name else ws.write(fila, 2, nom.contract_id.employee_id.name)
                salm = (nom.line_ids).search([('code', '=', 'SALCONTRACTO'), ('slip_id', '=', nom.id)])
                ws.write(fila, 3, 0) if not salm.total else ws.write(fila, 3, salm.total, format_number)
                total_salario_ope += salm.total
                work_day = (nom.worked_days_line_ids).search([('work_entry_type_id.code', '=', 'WORK100'), ('payslip_id', '=', nom.id)])
                ws.write(fila, 4, 0) if not work_day.number_of_days else ws.write(fila, 4, work_day.number_of_days)

                total_dias_ope += work_day.number_of_days
                sal = (nom.line_ids).search([('code', '=', 'SALARIO'), ('slip_id', '=', nom.id)])
                ws.write(fila, 5, 0) if not sal.total else ws.write(fila, 5, sal.total, format_number)
                total_sueldo_ope += sal.total
                work_days = (nom.worked_days_line_ids).search([('work_entry_type_id.code', '=', 'WORK100'), ('payslip_id', '=', nom.id)])
                ws.write(fila, 6, 0) if not work_days.number_of_days else ws.write(fila, 6, work_days.number_of_days)
                total_dias_no_lab_ope += work_days.number_of_days

                day_inc = (nom.worked_days_line_ids).search([('work_entry_type_id.code', '=', 'LEAVE110'), ('payslip_id', '=', nom.id)])
                ws.write(fila, 7, 0) if not day_inc.number_of_days else ws.write(fila, 7, day_inc.number_of_days)
                total_dias_inc_ope += day_inc.number_of_days
                incapacidades = (nom.line_ids).search([('code', '=', 'INCAPACIDADE'), ('slip_id', '=', nom.id)])
                ws.write(fila, 8, 0) if not incapacidades.total else ws.write(fila, 8, incapacidades.total, format_number)
                total_incapacidad_ope += incapacidades.total
                prima = (nom.line_ids).search([('code', '=', 'PROVPRIMA'), ('slip_id', '=', nom.id)])
                ws.write(fila, 9, 0) if not prima.total else ws.write(fila, 9, prima.total, format_number)
                total_prima_ope += prima.total
                aux = (nom.line_ids).search([('code', '=', 'SUBSTRAN'), ('slip_id', '=', nom.id)])
                ws.write(fila, 10, 0) if not aux.total else ws.write(fila, 10, aux.total, format_number)
                total_auxiliot_ope += aux.total
                t_dev = (nom.line_ids).search([('code', '=', 'GROSS'), ('slip_id', '=', nom.id)])
                ws.write(fila, 11, 0) if not t_dev.total else ws.write(fila, 11, t_dev.total, format_number)
                total_devengado_ope += t_dev.total
                salud = (nom.line_ids).search([('code', '=', 'SALUDEMPLEADO'), ('slip_id', '=', nom.id)])
                ws.write(fila, 12, 0) if not salud.total else ws.write(fila, 12, salud.total, format_number)
                total_salud_ope += salud.total
                pension = (nom.line_ids).search([('code', '=', 'PENSIONEMPLEADO'), ('slip_id', '=', nom.id)])
                ws.write(fila, 13, 0) if not pension.total else ws.write(fila, 13, pension.total, format_number)
                total_pension_ope += pension.total
                fsp = (nom.line_ids).search([('code', '=', 'FSP'), ('slip_id', '=', nom.id)])
                ws.write(fila, 14, 0) if not fsp.total else ws.write(fila, 14, fsp.total, format_number)
                total_fsp_ope += fsp.total
                rtf = (nom.line_ids).search([('code', '=', 'RTFM1'), ('slip_id', '=', nom.id)])
                ws.write(fila, 15, 0) if not rtf.total else ws.write(fila, 15, rtf.total, format_number)
                total_retencion_ope += rtf.total
                descuentos = (nom.line_ids).search([('code', '=', 'DESCUENTOS'), ('slip_id', '=', nom.id)])
                ws.write(fila, 16, 0) if not descuentos.amount else ws.write(fila, 16, descuentos.amount,
                                                                              format_number)
                total_descuentos_ope += descuentos.amount
                t_ded = (nom.line_ids).search([('code', '=', 'TOTALDED'), ('slip_id', '=', nom.id)])
                ws.write(fila, 17, 0) if not t_ded.total else ws.write(fila, 17, t_ded.total, format_number)
                total_deducciones_ope += t_ded.total
                net = (nom.line_ids).search([('code', '=', 'NET'), ('slip_id', '=', nom.id)])
                ws.write(fila, 18, 0) if not net.total else ws.write(fila, 18, net.total, format_number)
                total_a_pagar_ope += net.total
        fila += 1
        ws.write(fila, 0, '', title_head)
        ws.write(fila, 1, '', title_head)
        ws.write(fila, 2, 'TOTAL OPERATIVO', title_head)
        ws.write(fila, 3, total_salario_ope, format_number1)
        ws.write(fila, 4, total_dias_ope, format_number1)
        ws.write(fila, 5, total_sueldo_ope, format_number1)
        ws.write(fila, 5, total_sueldo_ope, format_number1)
        ws.write(fila, 6, total_dias_no_lab_ope, format_number1)
        ws.write(fila, 7, total_dias_inc_ope, format_number1)
        ws.write(fila, 8, total_incapacidad_ope, format_number1)
        ws.write(fila, 9, total_prima_ope, format_number1)
        ws.write(fila, 10, total_auxiliot_ope, format_number1)
        ws.write(fila, 11, total_devengado_ope, format_number1)
        ws.write(fila, 12, total_salud_ope, format_number1)
        ws.write(fila, 13, total_pension_ope, format_number1)
        ws.write(fila, 14, total_fsp_ope, format_number1)
        ws.write(fila, 15, total_retencion_ope, format_number1)
        ws.write(fila, 16, total_descuentos_ope, format_number1)
        ws.write(fila, 17, total_deducciones_ope, format_number1)
        ws.write(fila, 18, total_a_pagar_ope, format_number1)

        total_salario_ven = 0
        total_dias_ven = 0
        total_sueldo_ven = 0
        total_dias_no_lab_ven = 0
        total_dias_inc_ven = 0
        total_incapacidad_ven = 0
        total_prima_ven = 0
        total_auxiliot_ven = 0
        total_devengado_ven = 0
        total_salud_ven = 0
        total_pension_ven = 0
        total_fsp_ven = 0
        total_retencion_ven = 0
        total_descuentos_ven = 0
        total_deducciones_ven = 0
        total_a_pagar_ven = 0

        for nom in nominas:

            if nom.struct_id.name == 'Ventas':
                fila += 1
                ws.write(fila, 0, 0) if not nom.contract_id.employee_id.department_id.name else ws.write(fila, 0, nom.contract_id.employee_id.department_id.name)
                ws.write(fila, 1, 0) if not nom.contract_id.employee_id.identification_id else ws.write(fila, 1, nom.contract_id.employee_id.identification_id)
                ws.write(fila, 2, 0) if not nom.contract_id.employee_id.name else ws.write(fila, 2, nom.contract_id.employee_id.name)
                salm = (nom.line_ids).search([('code', '=', 'SALCONTRACTO'), ('slip_id', '=', nom.id)])
                ws.write(fila, 3, 0) if not salm.total else ws.write(fila, 3, salm.total, format_number)
                total_salario_ven += salm.total
                work_day = (nom.worked_days_line_ids).search([('work_entry_type_id.code', '=', 'WORK100'), ('payslip_id', '=', nom.id)])
                ws.write(fila, 4, 0) if not work_day.number_of_days else ws.write(fila, 4, work_day.number_of_days)
                total_dias_ven += work_day.number_of_days
                sal = (nom.line_ids).search([('code', '=', 'SALARIO'), ('slip_id', '=', nom.id)])
                ws.write(fila, 5, 0) if not sal.total else ws.write(fila, 5, sal.total, format_number)
                total_sueldo_ven += sal.total
                work_days = (nom.worked_days_line_ids).search([('work_entry_type_id.code', '=', 'WORK100'), ('payslip_id', '=', nom.id)])
                ws.write(fila, 6, 0) if not work_days.number_of_days else ws.write(fila, 6, work_days.number_of_days)
                total_dias_no_lab_ven += work_days.number_of_days

                day_inc = (nom.worked_days_line_ids).search([('work_entry_type_id.code', '=', 'LEAVE110'), ('payslip_id', '=', nom.id)])
                ws.write(fila, 7, 0) if not day_inc.number_of_days else ws.write(fila, 7, day_inc.number_of_days)
                total_dias_inc_ven += day_inc.number_of_days
                incapacidades = (nom.line_ids).search([('code', '=', 'INCAPACIDADE'), ('slip_id', '=', nom.id)])
                ws.write(fila, 8, 0) if not incapacidades.total else ws.write(fila, 8, incapacidades.total)
                total_incapacidad_ven += incapacidades.total
                prima = (nom.line_ids).search([('code', '=', 'PROVPRIMA'), ('slip_id', '=', nom.id)])
                ws.write(fila, 9, 0) if not prima.total else ws.write(fila, 9, prima.total, format_number)
                total_prima_ven += prima.total
                aux = (nom.line_ids).search([('code', '=', 'SUBSTRAN'), ('slip_id', '=', nom.id)])
                ws.write(fila, 10, 0) if not aux.total else ws.write(fila, 10, aux.total, format_number)
                total_auxiliot_ven += aux.total
                t_dev = (nom.line_ids).search([('code', '=', 'GROSS'), ('slip_id', '=', nom.id)])
                ws.write(fila, 11, 0) if not t_dev.total else ws.write(fila, 11, t_dev.total, format_number)
                total_devengado_ven += t_dev.total
                salud = (nom.line_ids).search([('code', '=', 'SALUDEMPLEADO'), ('slip_id', '=', nom.id)])
                ws.write(fila, 12, 0) if not salud.total else ws.write(fila, 12, salud.total, format_number)
                total_salud_ven += salud.total
                pension = (nom.line_ids).search([('code', '=', 'PENSIONEMPLEADO'), ('slip_id', '=', nom.id)])
                ws.write(fila, 13, 0) if not pension.total else ws.write(fila, 13, pension.total, format_number)
                total_pension_ven += pension.total
                fsp = (nom.line_ids).search([('code', '=', 'FSP'), ('slip_id', '=', nom.id)])
                ws.write(fila, 14, 0) if not fsp.total else ws.write(fila, 14, fsp.total, format_number)
                total_fsp_ven += fsp.total
                rtf = (nom.line_ids).search([('code', '=', 'RTFM1'), ('slip_id', '=', nom.id)])
                ws.write(fila, 15, 0) if not rtf.total else ws.write(fila, 15, rtf.total, format_number)
                total_retencion_ven += rtf.total
                descuentos = (nom.line_ids).search([('code', '=', 'DESCUENTOS'), ('slip_id', '=', nom.id)])
                ws.write(fila, 16, 0) if not descuentos.amount else ws.write(fila, 16, descuentos.amount,
                                                                              format_number)
                total_descuentos_ven += descuentos.amount
                t_ded = (nom.line_ids).search([('code', '=', 'TOTALDED'), ('slip_id', '=', nom.id)])
                ws.write(fila, 17, 0) if not t_ded.total else ws.write(fila, 17, t_ded.total, format_number)
                total_deducciones_ven += t_ded.total
                net = (nom.line_ids).search([('code', '=', 'NET'), ('slip_id', '=', nom.id)])
                ws.write(fila, 18, 0) if not net.total else ws.write(fila, 18, net.total, format_number)
                total_a_pagar_ven += net.total
        fila += 1
        ws.write(fila, 0, '', title_head)
        ws.write(fila, 1, '', title_head)
        ws.write(fila, 2, 'TOTAL VENTAS', title_head)
        ws.write(fila, 3, total_salario_ven, format_number1)
        ws.write(fila, 4, total_dias_ven, format_number1)
        ws.write(fila, 5, total_sueldo_ven, format_number1)
        ws.write(fila, 5, total_sueldo_ven, format_number1)
        ws.write(fila, 6, total_dias_no_lab_ven, format_number1)
        ws.write(fila, 7, total_dias_inc_ven, format_number1)
        ws.write(fila, 8, total_incapacidad_ven, format_number1)
        ws.write(fila, 9, total_prima_ven, format_number1)
        ws.write(fila, 10, total_auxiliot_ven, format_number1)
        ws.write(fila, 11, total_devengado_ven, format_number1)
        ws.write(fila, 12, total_salud_ven, format_number1)
        ws.write(fila, 13, total_pension_ven, format_number1)
        ws.write(fila, 14, total_fsp_ven, format_number1)
        ws.write(fila, 15, total_retencion_ven, format_number1)
        ws.write(fila, 16, total_descuentos_ven, format_number1)
        ws.write(fila, 17, total_deducciones_ven, format_number1)
        ws.write(fila, 18, total_a_pagar_ven, format_number1)

        total_salario_asa = 0
        total_dias_asa = 0
        total_sueldo_asa = 0
        total_dias_no_lab_asa = 0
        total_dias_inc_asa = 0
        total_incapacidad_asa = 0
        total_prima_asa = 0
        total_auxiliot_asa = 0
        total_devengado_asa = 0
        total_salud_asa = 0
        total_pension_asa = 0
        total_fsp_asa = 0
        total_retencion_asa = 0
        total_descuentos_asa = 0
        total_deducciones_asa = 0
        total_a_pagar_asa = 0

        for nom in nominas:

            if nom.struct_id.name == 'Aprendiz SENA Administrativa':
                fila += 1
                ws.write(fila, 0, 0) if not nom.contract_id.employee_id.department_id.name else ws.write(fila, 0, nom.contract_id.employee_id.department_id.name)
                ws.write(fila, 1, 0) if not nom.contract_id.employee_id.identification_id else ws.write(fila, 1, nom.contract_id.employee_id.identification_id)
                ws.write(fila, 2, 0) if not nom.contract_id.employee_id.name else ws.write(fila, 2, nom.contract_id.employee_id.name)
                salm = (nom.line_ids).search([('code', '=', 'SALCONTRACTO'), ('slip_id', '=', nom.id)])
                ws.write(fila, 3, 0) if not salm.total else ws.write(fila, 3, salm.total, format_number)
                total_salario_asa += salm.total
                work_day = (nom.worked_days_line_ids).search(
                    [('work_entry_type_id.code', '=', 'WORK100'), ('payslip_id', '=', nom.id)])
                ws.write(fila, 4, 0) if not work_day.number_of_days else ws.write(fila, 4, work_day.number_of_days)

                total_dias_asa += work_day.number_of_days
                sal = (nom.line_ids).search([('code', '=', 'SALARIO'), ('slip_id', '=', nom.id)])
                ws.write(fila, 5, 0) if not sal.total else ws.write(fila, 5, sal.total, format_number)
                total_sueldo_asa += sal.total
                work_days = (nom.worked_days_line_ids).search(
                    [('work_entry_type_id.code', '=', 'WORK100'), ('payslip_id', '=', nom.id)])
                ws.write(fila, 6, 0) if not work_days.number_of_days else ws.write(fila, 6, work_days.number_of_days)
                total_dias_no_lab_asa += work_days.number_of_days

                day_inc = (nom.worked_days_line_ids).search(
                    [('work_entry_type_id.code', '=', 'LEAVE110'), ('payslip_id', '=', nom.id)])
                ws.write(fila, 7, 0) if not day_inc.number_of_days else ws.write(fila, 7, day_inc.number_of_days)
                total_dias_inc_asa += day_inc.number_of_days
                incapacidades = (nom.line_ids).search([('code', '=', 'INCAPACIDADE'), ('slip_id', '=', nom.id)])
                ws.write(fila, 8, 0) if not incapacidades.total else ws.write(fila, 8, incapacidades.total,
                                                                                format_number)
                total_incapacidad_asa += incapacidades.total
                prima = (nom.line_ids).search([('code', '=', 'PROVPRIMA'), ('slip_id', '=', nom.id)])
                ws.write(fila, 9, 0) if not prima.total else ws.write(fila, 9, prima.total, format_number)
                total_prima_asa += prima.total
                aux = (nom.line_ids).search([('code', '=', 'SUBSTRAN'), ('slip_id', '=', nom.id)])
                ws.write(fila, 10, 0) if not aux.total else ws.write(fila, 10, aux.total, format_number)
                total_auxiliot_asa += aux.total
                t_dev = (nom.line_ids).search([('code', '=', 'GROSS'), ('slip_id', '=', nom.id)])
                ws.write(fila, 11, 0) if not t_dev.total else ws.write(fila, 11, t_dev.total, format_number)
                total_devengado_asa += t_dev.total
                salud = (nom.line_ids).search([('code', '=', 'SALUDEMPLEADO'), ('slip_id', '=', nom.id)])
                ws.write(fila, 12, 0) if not salud.total else ws.write(fila, 12, salud.total, format_number)
                total_salud_asa += salud.total
                pension = (nom.line_ids).search([('code', '=', 'PENSIONEMPLEADO'), ('slip_id', '=', nom.id)])
                ws.write(fila, 13, 0) if not pension.total else ws.write(fila, 13, pension.total, format_number)
                total_pension_asa += pension.total
                fsp = (nom.line_ids).search([('code', '=', 'FSP'), ('slip_id', '=', nom.id)])
                ws.write(fila, 14, 0) if not fsp.total else ws.write(fila, 14, fsp.total, format_number)
                total_fsp_asa += fsp.total
                rtf = (nom.line_ids).search([('code', '=', 'RTFM1'), ('slip_id', '=', nom.id)])
                ws.write(fila, 15, 0) if not rtf.total else ws.write(fila, 15, rtf.total, format_number)
                total_retencion_asa += rtf.total
                descuentos = (nom.line_ids).search([('code', '=', 'DESCUENTOS'), ('slip_id', '=', nom.id)])
                ws.write(fila, 16, 0) if not descuentos.amount else ws.write(fila, 16, descuentos.amount,
                                                                               format_number)
                total_descuentos_asa += descuentos.amount
                t_ded = (nom.line_ids).search([('code', '=', 'TOTALDED'), ('slip_id', '=', nom.id)])
                ws.write(fila, 17, 0) if not t_ded.total else ws.write(fila, 17, t_ded.total, format_number)
                total_deducciones_asa += t_ded.total
                net = (nom.line_ids).search([('code', '=', 'NET'), ('slip_id', '=', nom.id)])
                ws.write(fila, 18, 0) if not net.total else ws.write(fila, 18, net.total, format_number)
                total_a_pagar_asa += net.total
        fila += 1
        ws.write(fila, 0, '', title_head)
        ws.write(fila, 1, '', title_head)
        ws.write(fila, 2, 'TOTAL SENA ADMINISTRATIVO', title_head)
        ws.write(fila, 3, total_salario_asa, format_number1)
        ws.write(fila, 4, total_dias_asa, format_number1)
        ws.write(fila, 5, total_sueldo_asa, format_number1)
        ws.write(fila, 5, total_sueldo_asa, format_number1)
        ws.write(fila, 6, total_dias_no_lab_asa, format_number1)
        ws.write(fila, 7, total_dias_inc_asa, format_number1)
        ws.write(fila, 8, total_incapacidad_asa, format_number1)
        ws.write(fila, 9, total_prima_asa, format_number1)
        ws.write(fila, 10, total_auxiliot_asa, format_number1)
        ws.write(fila, 11, total_devengado_asa, format_number1)
        ws.write(fila, 12, total_salud_asa, format_number1)
        ws.write(fila, 13, total_pension_asa, format_number1)
        ws.write(fila, 14, total_fsp_asa, format_number1)
        ws.write(fila, 15, total_retencion_asa, format_number1)
        ws.write(fila, 16, total_descuentos_asa, format_number1)
        ws.write(fila, 17, total_deducciones_asa, format_number1)
        ws.write(fila, 18, total_a_pagar_asa, format_number1)
        total_salario_asop = 0
        total_dias_asop = 0
        total_sueldo_asop = 0
        total_dias_no_lab_asop = 0
        total_dias_inc_asop = 0
        total_incapacidad_asop = 0
        total_prima_asop = 0
        total_auxiliot_asop = 0
        total_devengado_asop = 0
        total_salud_asop = 0
        total_pension_asop = 0
        total_fsp_asop = 0
        total_retencion_asop = 0
        total_descuentos_asop = 0
        total_deducciones_asop = 0
        total_a_pagar_asop = 0

        for nom in nominas:

            if nom.struct_id.name == 'Aprendiz SENA Operativa':
                fila += 1
                ws.write(fila, 0, 0) if not nom.contract_id.employee_id.department_id.name else ws.write(fila, 0,
                                                                                                           nom.contract_id.employee_id.department_id.name)
                ws.write(fila, 1, 0) if not nom.contract_id.employee_id.identification_id else ws.write(fila, 1,
                                                                                                          nom.contract_id.employee_id.identification_id)
                ws.write(fila, 2, 0) if not nom.contract_id.employee_id.name else ws.write(fila, 2,
                                                                                             nom.contract_id.employee_id.name)
                salm = (nom.line_ids).search([('code', '=', 'SALCONTRACTO'), ('slip_id', '=', nom.id)])
                ws.write(fila, 3, 0) if not salm.total else ws.write(fila, 3, salm.total, format_number)
                total_salario_asop += salm.total
                work_day = (nom.worked_days_line_ids).search(
                    [('work_entry_type_id.code', '=', 'WORK100'), ('payslip_id', '=', nom.id)])
                ws.write(fila, 4, 0) if not work_day.number_of_days else ws.write(fila, 4, work_day.number_of_days)

                total_dias_asop += work_day.number_of_days
                sal = (nom.line_ids).search([('code', '=', 'SALARIO'), ('slip_id', '=', nom.id)])
                ws.write(fila, 5, 0) if not sal.total else ws.write(fila, 5, sal.total, format_number)
                total_sueldo_asop += sal.total
                work_days = (nom.worked_days_line_ids).search(
                    [('work_entry_type_id.code', '=', 'WORK100'), ('payslip_id', '=', nom.id)])
                ws.write(fila, 6, 0) if not work_days.number_of_days else ws.write(fila, 6, work_days.number_of_days)
                total_dias_no_lab_asop += work_days.number_of_days

                day_inc = (nom.worked_days_line_ids).search(
                    [('work_entry_type_id.code', '=', 'LEAVE110'), ('payslip_id', '=', nom.id)])
                ws.write(fila, 7, 0) if not day_inc.number_of_days else ws.write(fila, 7, day_inc.number_of_days)
                total_dias_inc_asop += day_inc.number_of_days
                incapacidades = (nom.line_ids).search([('code', '=', 'INCAPACIDADE'), ('slip_id', '=', nom.id)])
                ws.write(fila, 8, 0) if not incapacidades.total else ws.write(fila, 8, incapacidades.total,
                                                                                format_number)
                total_incapacidad_asop += incapacidades.total
                prima = (nom.line_ids).search([('code', '=', 'PROVPRIMA'), ('slip_id', '=', nom.id)])
                ws.write(fila, 9, 0) if not prima.total else ws.write(fila, 9, prima.total, format_number)
                total_prima_asop += prima.total
                aux = (nom.line_ids).search([('code', '=', 'SUBSTRAN'), ('slip_id', '=', nom.id)])
                ws.write(fila, 10, 0) if not aux.total else ws.write(fila, 10, aux.total, format_number)
                total_auxiliot_asop += aux.total
                t_dev = (nom.line_ids).search([('code', '=', 'GROSS'), ('slip_id', '=', nom.id)])
                ws.write(fila, 11, 0) if not t_dev.total else ws.write(fila, 11, t_dev.total, format_number)
                total_devengado_asop += t_dev.total
                salud = (nom.line_ids).search([('code', '=', 'SALUDEMPLEADO'), ('slip_id', '=', nom.id)])
                ws.write(fila, 12, 0) if not salud.total else ws.write(fila, 12, salud.total, format_number)
                total_salud_asop += salud.total
                pension = (nom.line_ids).search([('code', '=', 'PENSIONEMPLEADO'), ('slip_id', '=', nom.id)])
                ws.write(fila, 13, 0) if not pension.total else ws.write(fila, 13, pension.total, format_number)
                total_pension_asop += pension.total
                fsp = (nom.line_ids).search([('code', '=', 'FSP'), ('slip_id', '=', nom.id)])
                ws.write(fila, 14, 0) if not fsp.total else ws.write(fila, 14, fsp.total, format_number)
                total_fsp_asop += fsp.total
                rtf = (nom.line_ids).search([('code', '=', 'RTFM1'), ('slip_id', '=', nom.id)])
                ws.write(fila, 15, 0) if not rtf.total else ws.write(fila, 15, rtf.total, format_number)
                total_retencion_asop += rtf.total
                descuentos = (nom.line_ids).search([('code', '=', 'DESCUENTOS'), ('slip_id', '=', nom.id)])
                ws.write(fila, 16, 0) if not descuentos.amount else ws.write(fila, 16, descuentos.amount,
                                                                               format_number)
                total_descuentos_asop += descuentos.amount
                t_ded = (nom.line_ids).search([('code', '=', 'TOTALDED'), ('slip_id', '=', nom.id)])
                ws.write(fila, 17, 0) if not t_ded.total else ws.write(fila, 17, t_ded.total, format_number)
                total_deducciones_asop += t_ded.total
                net = (nom.line_ids).search([('code', '=', 'NET'), ('slip_id', '=', nom.id)])
                ws.write(fila, 18, 0) if not net.total else ws.write(fila, 18, net.total, format_number)
                total_a_pagar_asop += net.total
        fila += 1
        ws.write(fila, 0, '', title_head)
        ws.write(fila, 1, '', title_head)
        ws.write(fila, 2, 'TOTAL SENA OPERATIVO', title_head)
        ws.write(fila, 3, total_salario_asop, format_number1)
        ws.write(fila, 4, total_dias_asop, format_number1)
        ws.write(fila, 5, total_sueldo_asop, format_number1)
        ws.write(fila, 5, total_sueldo_asop, format_number1)
        ws.write(fila, 6, total_dias_no_lab_asop, format_number1)
        ws.write(fila, 7, total_dias_inc_asop, format_number1)
        ws.write(fila, 8, total_incapacidad_asop, format_number1)
        ws.write(fila, 9, total_prima_asop, format_number1)
        ws.write(fila, 10, total_auxiliot_asop, format_number1)
        ws.write(fila, 11, total_devengado_asop, format_number1)
        ws.write(fila, 12, total_salud_asop, format_number1)
        ws.write(fila, 13, total_pension_asop, format_number1)
        ws.write(fila, 14, total_fsp_asop, format_number1)
        ws.write(fila, 15, total_retencion_asop, format_number1)
        ws.write(fila, 16, total_descuentos_asop, format_number1)
        ws.write(fila, 17, total_deducciones_asop, format_number1)
        ws.write(fila, 18, total_a_pagar_asop, format_number1)
        try:
            wb.close()
            out = base64.encodestring(buf.getvalue())
            buf.close()
            self.data = out
            self.data_name = 'PRENOMINA' + ".xls"
        except ValueError:
            raise Warning('No se pudo generar el archivo')

#
