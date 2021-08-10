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
from dateutil.relativedelta import relativedelta

def days360(s, e):
    return ( ((e.year * 12 + e.month) * 30 + e.day) - ((s.year * 12 + s.month) * 30 + s.day))

class VacationsReport(models.TransientModel):
    _name = 'vacations.report'
    _description = 'Reporte Libro Vacaciones'

    data = fields.Binary("Archivo")
    data_name = fields.Char("nombre del archivo")
    contratos = fields.Many2many('hr.contract')
    modo = fields.Selection(string="Generar reporte por:", selection=[('1', 'Empleado'), ('2', 'Estructura'),('3', 'General')])
    empleado = fields.Many2one('hr.employee', string='Empleado')
    departamento = fields.Many2one('hr.department', string='Departamento')
    date_creation = fields.Date(string='Fecha')
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
            contratos = self.env['hr.contract'].search([('employee_id', '=', self.empleado.id), ('state', '=', 'open')])
        elif self.modo == '2':
            contratos = self.env['hr.contract'].search([('department_id', '=', self.departamento.id), ('employee_id', '!=', False), ('state', '=', 'open')])
        else:
            contratos = self.env['hr.contract'].search([('employee_id', '!=', False), ('state', '=', 'open')])

        date_creation = self.date_creation
        #date_creation = fields.Date.today()

        hora = time.strftime('%H:%M:%S')
        if not contratos:
            raise Warning(_('!No hay resultados para los datos seleccionados¡'))

        buf = BytesIO()
        wb = xlsxwriter.Workbook(buf)
        ws = wb.add_worksheet('Report')
        ws.set_column('A:A', 15)
        ws.set_column('B:B', 65)
        ws.set_column('C:D', 23)
        ws.set_column('E:E', 28)
        ws.set_column('F:G', 23)
        ws.set_column('H:K', 18)
        ws.set_column('L:Z', 23)

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
            #ws.write(fila, 11, 'HORAS EXTRA DIURNA PROMEDIO 12M', title_head)
            #ws.write(fila, 12, 'HORAS EXTRA DIURNA FESTIVO PROMEDIO 12M', title_head)
            #ws.write(fila, 13, 'HORAS EXTRA NOCTURNA PROMEDIO 12M', title_head)
            #ws.write(fila, 14, 'HORAS EXTRA NOCTURNA FESTIVO PROMEDIO 12M', title_head)
            #ws.write(fila, 15, 'HORAS RECARGO NOCTURNO PROMEDIO 12M', title_head)
            #ws.write(fila, 16, 'HORAS RECARGO DIURNO FESTIVO PROMEDIO 12M', title_head)
            #ws.write(fila, 17, 'HORAS RECARGO NOCTURNO FESTIVO PROMEDIO 12M', title_head)
            #ws.write(fila, 18, 'BONIFICACION PROMEDIO 12M', title_head)
            #ws.write(fila, 19, 'COMISION PROMEDIO 12M', title_head)
            #ws.write(fila, 20, 'SALARIO CONTRATO', title_head)
            #ws.write(fila, 21, 'SALARIO PROMEDIO 12M', title_head)
            ws.write(fila, 11, 'SALARIO PROMEDIO 12M', title_head)

            fila += 1

            ws.write(fila, 0, '') if not cont.employee_id.identification_id else ws.write(fila, 0, cont.employee_id.identification_id)
            ws.write(fila, 1, '') if not cont.employee_id.name else ws.write(fila, 1, cont.employee_id.name)
            ws.write(fila, 2, '') if not cont.date_start else ws.write(fila, 2, cont.date_start, format_date)
            dias_lab = days360(cont.date_start, date_creation) + 1
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

                    ws.write(fila, 7, 0) if not vac.name else ws.write(fila, 7, vac.workday)
                    total_dias_habiles += int(vac.workday)
                    ws.write(fila, 8, 0) if not vac.name else ws.write(fila, 8, vac.holiday)
                    total_dias_no_habiles += int(vac.holiday)
                    ws.write(fila, 9, 0) if not vac.name else ws.write(fila, 9, vac.number_of_days)
                    total_dias += int(vac.number_of_days)
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

            # Horas extras promedio 12 meses atras
            horas_extras_12month_before = self.env['hr.payslip'].get_inputs_hora_extra_12month_before(cont, date_creation, date_creation)
            extradiurna_amount = 0
            extradiurnafestivo_amount = 0
            extranocturna_amount = 0
            extranocturnafestivo_amount = 0
            recargonocturno_amount = 0
            recargodiurnofestivo_amount = 0
            recargonocturnofestivo_amount = 0

            hm12_date_ini = date_creation - relativedelta(months=12)
            hm12_date_ini = hm12_date_ini + relativedelta(days=1)
            if cont.date_start <= hm12_date_ini:
                hm12_date_init = hm12_date_ini
            else:
                hm12_date_init = cont.date_start
            if date_creation.day == 31:
                date_creation = date_creation - relativedelta(days=1)
            total_days12y = days360(hm12_date_init, date_creation) + 1

            if total_days12y < 30:
                day_base = total_days12y
            else:
                day_base = 30

            for hora in horas_extras_12month_before:
                if hora[1] == 'EXTRADIURNA':
                    extradiurna_amount = extradiurna_amount + hora[2]
                if hora[1] == 'EXTRADIURNAFESTIVO':
                    extradiurnafestivo_amount = extradiurnafestivo_amount + hora[2]
                if hora[1] == 'EXTRANOCTURNA':
                    extranocturna_amount = extranocturna_amount + hora[2]
                if hora[1] == 'EXTRANOCTURNAFESTIVO':
                    extranocturnafestivo_amount = extranocturnafestivo_amount + hora[2]
                if hora[1] == 'RECARGONOCTURNO':
                    recargonocturno_amount = recargonocturno_amount + hora[2]
                if hora[1] == 'RECARGODIURNOFESTIVO':
                    recargodiurnofestivo_amount = recargodiurnofestivo_amount + hora[2]
                if hora[1] == 'RECARGONOCTURNOFESTIVO':
                    recargonocturnofestivo_amount = recargonocturnofestivo_amount + hora[2]

            extradiurna12m = (extradiurna_amount / total_days12y) * day_base
            extradiurnafestivo12m = (extradiurnafestivo_amount / total_days12y) * day_base
            extranocturna12m = (extranocturna_amount / total_days12y) * day_base
            extranocturnafestivo12m = (extranocturnafestivo_amount / total_days12y) * day_base
            recargonocturno12m = (recargonocturno_amount / total_days12y) * day_base
            recargodiurnofestivo12m = (recargodiurnofestivo_amount / total_days12y) * day_base
            recargonocturnofestivo12m = (recargonocturnofestivo_amount / total_days12y) * day_base

            #ws.write(fila, 11, 0, format_number1) if not total_dias else ws.write(fila, 11, extradiurna12m, format_number1)
            #ws.write(fila, 12, 0, format_number1) if not total_dias else ws.write(fila, 12, extradiurnafestivo12m, format_number1)
            #ws.write(fila, 13, 0, format_number1) if not total_dias else ws.write(fila, 13, extranocturna12m, format_number1)
            #ws.write(fila, 14, 0, format_number1) if not total_dias else ws.write(fila, 14, extranocturnafestivo12m, format_number1)
            #ws.write(fila, 15, 0, format_number1) if not total_dias else ws.write(fila, 15, recargonocturno12m, format_number1)
            #ws.write(fila, 16, 0, format_number1) if not total_dias else ws.write(fila, 16, recargodiurnofestivo12m, format_number1)
            #ws.write(fila, 17, 0, format_number1) if not total_dias else ws.write(fila, 17, recargonocturnofestivo12m, format_number1)

            # Bonificaciones y comisiones  promedio 12 meses atras
            inputs_loans_12month_before = self.env['hr.payslip'].get_inputs_loans_12month_before(cont, date_creation, date_creation)
            amountb = 0
            amountc = 0
            lm12_date_ini = date_creation - relativedelta(months=12)
            lm12_date_ini = lm12_date_ini + relativedelta(days=1)
            if cont.date_start <= lm12_date_ini:
                lm12_date_init = lm12_date_ini
            else:
                lm12_date_init = cont.date_start
            if date_creation.day == 31:
                date_creation = date_creation - relativedelta(days=1)
            total_dayl12 = days360(lm12_date_init, date_creation) + 1

            if total_dayl12 < 30:
                day_base = total_dayl12
            else:
                day_base = 30

            for loans in inputs_loans_12month_before:
                if loans[1] == 'BONIFICACION':
                    amountb = amountb + loans[2]
                if loans[1] == 'COMISION':
                    amountc = amountc + loans[2]

            bonificacion12m = (amountb / total_dayl12) * day_base
            comision12m = (amountc / total_dayl12) * day_base

            #ws.write(fila, 18, 0, format_number1) if not total_dias else ws.write(fila, 11, bonificacion12m, format_number1)
            #ws.write(fila, 19, 0, format_number1) if not total_dias else ws.write(fila, 11, comision12m, format_number1)

            salario = cont.wage

            #ws.write(fila, 20, 0, format_number1) if not total_dias else ws.write(fila, 11, salario, format_number1)

            salario12m =  salario+bonificacion12m+comision12m+extradiurna12m+extradiurnafestivo12m+extranocturna12m+extranocturnafestivo12m+recargonocturno12m+recargodiurnofestivo12m+recargonocturnofestivo12m

            #ws.write(fila, 21, 0, format_number1) if not total_dias else ws.write(fila, 11, salario12m, format_number1)

            ws.write(fila, 11, salario12m, format_number1)


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
