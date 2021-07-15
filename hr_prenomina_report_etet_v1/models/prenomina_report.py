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

        nominas = self.env['hr.payslip'].search([('payslip_run_id', '=', self.lote.id)], order="struct_id")
        nominas_administrativas = self.env['hr.payslip'].search([('payslip_run_id', '=', self.lote.id), ('struct_id.name', '=', 'Administrativa')], order="struct_id")
        nominas_operativas = self.env['hr.payslip'].search([('payslip_run_id', '=', self.lote.id), ('struct_id.name', '=', 'Operativa')], order="struct_id")
        nominas_ventas = self.env['hr.payslip'].search([('payslip_run_id', '=', self.lote.id), ('struct_id.name', '=', 'Ventas')], order="struct_id")
        nominas_sena_administrativas = self.env['hr.payslip'].search([('payslip_run_id', '=', self.lote.id), ('struct_id.name', '=', 'Aprendiz SENA Administrativa')], order="struct_id")
        nominas_sena_operativas = self.env['hr.payslip'].search([('payslip_run_id', '=', self.lote.id), ('struct_id.name', '=', 'Aprendiz SENA Operativa')], order="struct_id")


        if not nominas:
            raise Warning(_('!No hay resultados para los datos seleccionados¡'))

        buf = BytesIO()
        wb = xlsxwriter.Workbook(buf)
        lote_name = self.lote.name
        ws = wb.add_worksheet(lote_name)
        ws.set_column('A:B', 18)
        ws.set_column('C:C', 50)
        ws.set_column('D:D', 12)
        ws.set_column('E:G', 23)
        ws.set_column('H:ZZ', 18)

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

        ws.merge_range('A1:I1', 'PACIFICO SNACKS : Revisión Nomina', title_head)
        ws.write(0, 9, 'Fecha inicio', title_head)
        ws.write(0, 10, self.lote.date_start, format_date)
        ws.write(0, 11, 'Fecha fin', title_head)
        ws.write(0, 12, self.lote.date_end, format_date)

        rules_basic = self.env['hr.salary.rule'].search([('struct_id.name', '=', 'Administrativa'),('category_id.code', '=', 'BASIC')])
        rules_hora_extra = self.env['hr.salary.rule'].search([('struct_id.name', '=', 'Administrativa'), ('category_id.code', '=', 'HE')])
        rules_hora_recargo = self.env['hr.salary.rule'].search([('struct_id.name', '=', 'Administrativa'), ('category_id.code', '=', 'HR')])
        rules_ded = self.env['hr.salary.rule'].search([('struct_id.name', '=', 'Administrativa'),('category_id.code', '=', 'DED')])
        rules_tingresos = self.env['hr.salary.rule'].search([('struct_id.name', '=', 'Administrativa'),('code', '=', 'GROSS')])
        rules_tdeduciones = self.env['hr.salary.rule'].search([('struct_id.name', '=', 'Administrativa'),('code', '=', 'TOTALDED')])
        rules_neto = self.env['hr.salary.rule'].search([('struct_id.name', '=', 'Administrativa'),('code', '=', 'NET')])
        rules_aporte_empresa = self.env['hr.salary.rule'].search([('struct_id.name', '=', 'Administrativa'),('category_id.code', '=', 'APORTESEMPRESA')])
        rules_proviciones = self.env['hr.salary.rule'].search([('struct_id.name', '=', 'Administrativa'),('category_id.code', '=', 'PROVISION')])

        fila = 2
        col = 0

        # --------------------------------------------------- ADMINISTRATIVA ------------------------------------------------------------------------------

        if nominas_administrativas:
            ws.write(fila, col, 'Departamento', title_head)
            col += 1
            ws.write(fila, col, 'Identificación', title_head)
            col += 1
            ws.write(fila, col, 'Nombres', title_head)
            col += 1
            ws.write(fila, col, 'Concepto', title_head)
            col += 1

            for adm in rules_neto:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_tdeduciones:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_tingresos:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_basic:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_hora_extra:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_hora_recargo:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_ded:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_aporte_empresa:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_proviciones:
                ws.write(fila, col, adm.name, title_head)
                col += 1

        fila += 1
        for nom in nominas_administrativas:
            col = 0
            ws.write(fila, col, '', title_head) if not nom.contract_id.department_id.name else ws.write(fila,col,nom.contract_id.department_id.name, title_head)
            fila += 1
            ws.write(fila, col, '', title_head) if not nom.contract_id.department_id.name else ws.write(fila,
                                                                                                                   col,
                                                                                                                   nom.contract_id.department_id.name,
                                                                                                                   title_head)
            col += 1
            fila -= 1

            ws.write(fila, col, '', title_head) if not nom.contract_id.employee_id.identification_id else ws.write(fila, col, nom.contract_id.employee_id.identification_id, title_head)
            fila += 1
            ws.write(fila, col, '', title_head) if not nom.contract_id.employee_id.identification_id else ws.write(fila, col, nom.contract_id.employee_id.identification_id, title_head)
            col += 1
            fila -= 1

            ws.write(fila, col, '', title_head) if not nom.contract_id.employee_id.name else ws.write(fila, col, nom.contract_id.employee_id.name, title_head)
            fila += 1
            ws.write(fila, col, '', title_head) if not nom.contract_id.employee_id.name else ws.write(fila, col, nom.contract_id.employee_id.name, title_head)
            col += 1
            fila -= 1

            ws.write(fila, col, 'Cantidad' , title_head)
            fila += 1
            ws.write(fila, col, 'Importe', title_head)
            fila -= 1
            col += 1

            for adm in rules_neto:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.quantity, format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.total, format_number)
                fila -= 1
                col += 1

            for adm in rules_tdeduciones:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.quantity, format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.total, format_number)
                fila -= 1
                col += 1

            for adm in rules_tingresos:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.quantity, format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.total, format_number)
                fila -= 1
                col += 1

            for adm in rules_basic:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.quantity, format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.total, format_number)
                fila -= 1
                col += 1

            for adm in rules_hora_extra:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.quantity, format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.total, format_number)
                fila -= 1
                col += 1

            for adm in rules_hora_recargo:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.quantity, format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.total, format_number)
                fila -= 1
                col += 1

            for adm in rules_ded:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.quantity, format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.total, format_number)
                fila -= 1
                col += 1

            for adm in rules_aporte_empresa:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_proviciones:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            fila += 2

        fila += 1

        #--------------------------------------------------- OPERATIVO ------------------------------------------------------------------------------

        rules_basic = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Operativa'), ('category_id.code', '=', 'BASIC')])
        rules_hora_extra = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Operativa'), ('category_id.code', '=', 'HE')])
        rules_hora_recargo = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Operativa'), ('category_id.code', '=', 'HR')])
        rules_ded = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Operativa'), ('category_id.code', '=', 'DED')])
        rules_tingresos = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Operativa'), ('code', '=', 'GROSS')])
        rules_tdeduciones = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Operativa'), ('code', '=', 'TOTALDED')])
        rules_neto = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Operativa'), ('code', '=', 'NET')])
        rules_aporte_empresa = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Operativa'), ('category_id.code', '=', 'APORTESEMPRESA')])
        rules_proviciones = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Operativa'), ('category_id.code', '=', 'PROVISION')])

        if nominas_operativas:
            col = 0
            ws.write(fila, col, 'Departamento', title_head)
            col += 1
            ws.write(fila, col, 'Identificación', title_head)
            col += 1
            ws.write(fila, col, 'Nombres', title_head)
            col += 1
            ws.write(fila, col, 'Concepto', title_head)
            col += 1

            for adm in rules_neto:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_tdeduciones:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_tingresos:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_basic:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_hora_extra:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_hora_recargo:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_ded:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_aporte_empresa:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_proviciones:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            fila += 1

        for nom in nominas_operativas:
            col = 0
            ws.write(fila, col, '', title_head) if not nom.contract_id.department_id.name else ws.write(
                fila,
                col,
                nom.contract_id.department_id.name,
                title_head)
            fila += 1
            ws.write(fila, col, '', title_head) if not nom.contract_id.department_id.name else ws.write(
                fila,
                col,
                nom.contract_id.department_id.name,
                title_head)
            col += 1
            fila -= 1
            ws.write(fila, col, '', title_head) if not nom.contract_id.employee_id.identification_id else ws.write(
                fila, col, nom.contract_id.employee_id.identification_id, title_head)
            fila += 1
            ws.write(fila, col, '', title_head) if not nom.contract_id.employee_id.identification_id else ws.write(
                fila, col, nom.contract_id.employee_id.identification_id, title_head)
            col += 1
            fila -= 1

            ws.write(fila, col, '', title_head) if not nom.contract_id.employee_id.name else ws.write(fila, col,
                                                                                                      nom.contract_id.employee_id.name,
                                                                                                      title_head)
            fila += 1
            ws.write(fila, col, '', title_head) if not nom.contract_id.employee_id.name else ws.write(fila, col,
                                                                                                      nom.contract_id.employee_id.name,
                                                                                                      title_head)
            col += 1
            fila -= 1

            ws.write(fila, col, 'Cantidad', title_head)
            fila += 1
            ws.write(fila, col, 'Importe', title_head)
            fila -= 1
            col += 1

            for adm in rules_neto:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_tdeduciones:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_tingresos:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_basic:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_hora_extra:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_hora_recargo:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_ded:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_aporte_empresa:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_proviciones:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            fila += 2

        fila += 1
        # --------------------------------------------------- VENTAS  ------------------------------------------------------------------------------

        rules_basic = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Ventas'), ('category_id.code', '=', 'BASIC')])
        rules_hora_extra = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Ventas'), ('category_id.code', '=', 'HE')])
        rules_hora_recargo = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Ventas'), ('category_id.code', '=', 'HR')])
        rules_ded = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Ventas'), ('category_id.code', '=', 'DED')])
        rules_tingresos = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Ventas'), ('code', '=', 'GROSS')])
        rules_tdeduciones = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Ventas'), ('code', '=', 'TOTALDED')])
        rules_neto = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Ventas'), ('code', '=', 'NET')])
        rules_aporte_empresa = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Ventas'), ('category_id.code', '=', 'APORTESEMPRESA')])
        rules_proviciones = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Ventas'), ('category_id.code', '=', 'PROVISION')])

        if nominas_ventas:
            col = 0
            ws.write(fila, col, 'Departamento', title_head)
            col += 1
            ws.write(fila, col, 'Identificación', title_head)
            col += 1
            ws.write(fila, col, 'Nombres', title_head)
            col += 1
            ws.write(fila, col, 'Concepto', title_head)
            col += 1

            for adm in rules_neto:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_tdeduciones:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_tingresos:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_basic:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_hora_extra:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_hora_recargo:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_ded:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_aporte_empresa:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_proviciones:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            fila += 1
        for nom in nominas_ventas:
            col = 0
            ws.write(fila, col, '', title_head) if not nom.contract_id.department_id.name else ws.write(
                fila,
                col,
                nom.contract_id.department_id.name,
                title_head)
            fila += 1
            ws.write(fila, col, '', title_head) if not nom.contract_id.department_id.name else ws.write(
                fila,
                col,
                nom.contract_id.department_id.name,
                title_head)
            col += 1
            fila -= 1
            ws.write(fila, col, '', title_head) if not nom.contract_id.employee_id.identification_id else ws.write(
                fila, col, nom.contract_id.employee_id.identification_id, title_head)
            fila += 1
            ws.write(fila, col, '', title_head) if not nom.contract_id.employee_id.identification_id else ws.write(
                fila, col, nom.contract_id.employee_id.identification_id, title_head)
            col += 1
            fila -= 1

            ws.write(fila, col, '', title_head) if not nom.contract_id.employee_id.name else ws.write(fila, col,
                                                                                                      nom.contract_id.employee_id.name,
                                                                                                      title_head)
            fila += 1
            ws.write(fila, col, '', title_head) if not nom.contract_id.employee_id.name else ws.write(fila, col,
                                                                                                      nom.contract_id.employee_id.name,
                                                                                                      title_head)
            col += 1
            fila -= 1

            ws.write(fila, col, 'Cantidad', title_head)
            fila += 1
            ws.write(fila, col, 'Importe', title_head)
            fila -= 1
            col += 1

            for adm in rules_neto:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_tdeduciones:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_tingresos:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_basic:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_hora_extra:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_hora_recargo:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_ded:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col, concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_aporte_empresa:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_proviciones:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            fila += 2

        fila += 1


        # --------------------------------------------------- Aprendiz SENA Operativa  ------------------------------------------------------------------------------

        rules_basic = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Aprendiz SENA Operativa'), ('category_id.code', '=', 'BASIC')])
        rules_hora_extra = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Aprendiz SENA Operativa'), ('category_id.code', '=', 'HE')])
        rules_hora_recargo = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Aprendiz SENA Operativa'), ('category_id.code', '=', 'HR')])
        rules_ded = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Aprendiz SENA Operativa'), ('category_id.code', '=', 'DED')])
        rules_tingresos = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Aprendiz SENA Operativa'), ('code', '=', 'GROSS')])
        rules_tdeduciones = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Aprendiz SENA Operativa'), ('code', '=', 'TOTALDED')])
        rules_neto = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Aprendiz SENA Operativa'), ('code', '=', 'NET')])
        rules_aporte_empresa = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Aprendiz SENA Operativa'), ('category_id.code', '=', 'APORTESEMPRESA')])
        rules_proviciones = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Aprendiz SENA Operativa'), ('category_id.code', '=', 'PROVISION')])

        if nominas_sena_operativas:
            col = 0
            ws.write(fila, col, 'Departamento', title_head)
            col += 1
            ws.write(fila, col, 'Identificación', title_head)
            col += 1
            ws.write(fila, col, 'Nombres', title_head)
            col += 1
            ws.write(fila, col, 'Concepto', title_head)
            col += 1

            for adm in rules_neto:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_tdeduciones:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_tingresos:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_basic:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_hora_extra:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_hora_recargo:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_ded:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_aporte_empresa:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_proviciones:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            fila += 1
        for nom in nominas_sena_operativas:
            col = 0
            ws.write(fila, col, '',
                     title_head) if not nom.contract_id.department_id.name else ws.write(
                fila,
                col,
                nom.contract_id.department_id.name,
                title_head)
            fila += 1
            ws.write(fila, col, '',
                     title_head) if not nom.contract_id.department_id.name else ws.write(
                fila,
                col,
                nom.contract_id.department_id.name,
                title_head)
            col += 1
            fila -= 1
            ws.write(fila, col, '',
                     title_head) if not nom.contract_id.employee_id.identification_id else ws.write(
                fila, col, nom.contract_id.employee_id.identification_id, title_head)
            fila += 1
            ws.write(fila, col, '',
                     title_head) if not nom.contract_id.employee_id.identification_id else ws.write(
                fila, col, nom.contract_id.employee_id.identification_id, title_head)
            col += 1
            fila -= 1

            ws.write(fila, col, '', title_head) if not nom.contract_id.employee_id.name else ws.write(fila,
                                                                                                      col,
                                                                                                      nom.contract_id.employee_id.name,
                                                                                                      title_head)
            fila += 1
            ws.write(fila, col, '', title_head) if not nom.contract_id.employee_id.name else ws.write(fila,
                                                                                                      col,
                                                                                                      nom.contract_id.employee_id.name,
                                                                                                      title_head)
            col += 1
            fila -= 1

            ws.write(fila, col, 'Cantidad', title_head)
            fila += 1
            ws.write(fila, col, 'Importe', title_head)
            fila -= 1
            col += 1

            for adm in rules_neto:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_tdeduciones:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_tingresos:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_basic:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_hora_extra:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_hora_recargo:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_ded:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_aporte_empresa:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_proviciones:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            fila += 2

        fila += 1


        # --------------------------------------------------- Aprendiz SENA Administrativa  ------------------------------------------------------------------------------

        rules_basic = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Aprendiz SENA Administrativa'), ('category_id.code', '=', 'BASIC')])
        rules_hora_extra = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Aprendiz SENA Administrativa'), ('category_id.code', '=', 'HE')])
        rules_hora_recargo = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Aprendiz SENA Administrativa'), ('category_id.code', '=', 'HR')])
        rules_ded = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Aprendiz SENA Administrativa'), ('category_id.code', '=', 'DED')])
        rules_tingresos = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Aprendiz SENA Administrativa'), ('code', '=', 'GROSS')])
        rules_tdeduciones = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Aprendiz SENA Administrativa'), ('code', '=', 'TOTALDED')])
        rules_neto = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Aprendiz SENA Administrativa'), ('code', '=', 'NET')])
        rules_aporte_empresa = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Aprendiz SENA Administrativa'), ('category_id.code', '=', 'APORTESEMPRESA')])
        rules_proviciones = self.env['hr.salary.rule'].search(
            [('struct_id.name', '=', 'Aprendiz SENA Administrativa'), ('category_id.code', '=', 'PROVISION')])

        if nominas_sena_administrativas:
            col = 0
            ws.write(fila, col, 'Departamento', title_head)
            col += 1
            ws.write(fila, col, 'Identificación', title_head)
            col += 1
            ws.write(fila, col, 'Nombres', title_head)
            col += 1
            ws.write(fila, col, 'Concepto', title_head)
            col += 1

            for adm in rules_neto:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_tdeduciones:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_tingresos:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_basic:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_hora_extra:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_hora_recargo:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_ded:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_aporte_empresa:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            for adm in rules_proviciones:
                ws.write(fila, col, adm.name, title_head)
                col += 1

            fila += 1
        for nom in nominas_sena_administrativas:
            col = 0
            ws.write(fila, col, '',
                     title_head) if not nom.contract_id.department_id.name else ws.write(
                fila,
                col,
                nom.contract_id.department_id.name,
                title_head)
            fila += 1
            ws.write(fila, col, '',
                     title_head) if not nom.contract_id.department_id.name else ws.write(
                fila,
                col,
                nom.contract_id.department_id.name,
                title_head)
            col += 1
            fila -= 1
            ws.write(fila, col, '',
                     title_head) if not nom.contract_id.employee_id.identification_id else ws.write(
                fila, col, nom.contract_id.employee_id.identification_id, title_head)
            fila += 1
            ws.write(fila, col, '',
                     title_head) if not nom.contract_id.employee_id.identification_id else ws.write(
                fila, col, nom.contract_id.employee_id.identification_id, title_head)
            col += 1
            fila -= 1

            ws.write(fila, col, '', title_head) if not nom.contract_id.employee_id.name else ws.write(fila,
                                                                                                      col,
                                                                                                      nom.contract_id.employee_id.name,
                                                                                                      title_head)
            fila += 1
            ws.write(fila, col, '', title_head) if not nom.contract_id.employee_id.name else ws.write(fila,
                                                                                                      col,
                                                                                                      nom.contract_id.employee_id.name,
                                                                                                      title_head)
            col += 1
            fila -= 1

            ws.write(fila, col, 'Cantidad', title_head)
            fila += 1
            ws.write(fila, col, 'Importe', title_head)
            fila -= 1
            col += 1

            for adm in rules_neto:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_tdeduciones:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_tingresos:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_basic:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_hora_extra:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_hora_recargo:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_ded:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_aporte_empresa:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            for adm in rules_proviciones:
                concepto = (nom.line_ids).search([('code', '=', adm.code), ('slip_id', '=', nom.id)])
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.quantity,
                                                                                    format_number)
                fila += 1
                ws.write(fila, col, 0, format_number) if not concepto else ws.write(fila, col,
                                                                                    concepto.total,
                                                                                    format_number)
                fila -= 1
                col += 1

            fila += 2

        fila += 1



        try:
            wb.close()
            out = base64.encodestring(buf.getvalue())
            buf.close()
            self.data = out
            self.data_name = 'PRENOMINA' + ".xls"
        except ValueError:
            raise Warning('No se pudo generar el archivo')

#
