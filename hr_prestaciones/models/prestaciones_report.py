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
from dateutil.relativedelta import relativedelta
_logger = logging.getLogger(__name__)

def days360(s, e):
    return ( ((e.year * 12 + e.month) * 30 + e.day) - ((s.year * 12 + s.month) * 30 + s.day))

class PrestacionesReport(models.TransientModel):
    _name = 'prestaciones.report'
    _description = 'Reporte prestaciones'

    data = fields.Binary("Archivo")
    data_name = fields.Char("nombre del archivo")
    date_creation = fields.Date('Created Date', default=fields.Date.today())

    def do_report(self):

        _logger.error("INICIA LA FUNCIÓN GENERAR EL REPORTE ")
        self.make_file()
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=prestaciones.report&field=data&id=%s&filename=%s' % (
            self.id, self.data_name),
            'target': 'new',
            'nodestroy': False,
        }

    def make_file(self):
        _logger.error("INICIA LA FUNCIÓN CONSTRUIR EL ARCHIVO ")

        contracts = self.env['hr.contract'].search([('state', '=', 'open'),('employee_id', '!=', False)])

        if not contracts:
            raise Warning(_('!No hay resultados para los datos seleccionados¡'))

        buf = BytesIO()
        wb = xlsxwriter.Workbook(buf)
        name = str(self.date_creation)
        ws = wb.add_worksheet(name)
        ws.set_column('A:A', 50)
        ws.set_column('B:B', 15)
        ws.set_column('C:C', 40)
        ws.set_column('D:D', 16)
        ws.set_column('E:K', 12)
        ws.set_column('L:ZZ', 16)

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

        ws.merge_range('A1:K1', 'PACIFICO SNACKS : Prestaciones', title_head)
        fila = 2
        col = 0

        if contracts:
            ws.write(fila, col, 'Contrato', title_head)
            col += 1
            ws.write(fila, col, 'Identificación', title_head)
            col += 1
            ws.write(fila, col, 'Nombres', title_head)
            col += 1
            ws.write(fila, col, 'Prestación', title_head)
            col += 1
            ws.write(fila, col, 'Fecha Inicio', title_head)
            col += 1
            ws.write(fila, col, 'Fecha Fin', title_head)
            col += 1
            ws.write(fila, col, 'Vr. Base', title_head)
            col += 1
            ws.write(fila, col, 'Dias Laboral', title_head)
            col += 1
            ws.write(fila, col, 'Dias Liquidar', title_head)
            col += 1
            ws.write(fila, col, 'Vr. Unitario', title_head)
            col += 1
            ws.write(fila, col, 'Vr. Total', title_head)
            col += 1

        fila += 1
        col = 0

        for c in contracts:

            # ---------------------- FECHA INICIAL -----------------------
            init_year = date(c.date_start.year, 1, 1)
            if c.date_start <= init_year:
                date_init = init_year
            else:
                date_init = c.date_start

            dias_labor = days360(date_init, self.date_creation) + 1

            dias_labor_vacaciones = days360(c.vacations_date, self.date_creation) + 1

            dias_liq = dias_labor / 360

            # ---------------------- VALOR PROMEDIO ANUAL -----------------

            salary = c.wage
            total_extra_hour = 0
            amountb = 0
            amountc = 0
            date_from = self.date_creation
            date_to = self.date_creation

            if date_to.day <= 15:
                date_to = date(date_to.year, date_to.month, 15)

            if date_to.day > 15 and date_to.day <= 31:
                date_to = date(date_to.year, date_to.month, 30)

            hora_extra_year_now = self.env['hr.payslip'].get_inputs_hora_extra_year_now(c,date_from,date_to)
            if hora_extra_year_now:
                hm12_date_ini = date_to - relativedelta(months=12)
                hm12_date_ini = hm12_date_ini + relativedelta(days=1)
                if c.date_start <= hm12_date_ini:
                    hm12_date_init = hm12_date_ini
                else:
                    hm12_date_init = c.date_start
                if date_to.day == 31:
                    date_to = date_to - relativedelta(days=1)
                total_days12y = days360(hm12_date_init, date_to) + 1
                extradiurna_amount = 0
                extradiurnafestivo_amount = 0
                extranocturna_amount = 0
                extranocturnafestivo_amount = 0
                recargonocturno_amount = 0
                recargodiurnofestivo_amount = 0
                recargonocturnofestivo_amount = 0
                for hora in hora_extra_year_now:
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

                if not extradiurna_amount == 0:
                    extradiurna_amount = (extradiurna_amount / total_days12y) * 30
                if not extradiurnafestivo_amount == 0:
                    extradiurnafestivo_amount = (extradiurnafestivo_amount / total_days12y) * 30
                if not extranocturna_amount == 0:
                    extranocturna_amount = (extranocturna_amount / total_days12y) * 30
                if not extranocturnafestivo_amount == 0:
                    extranocturnafestivo_amount = (extranocturnafestivo_amount / total_days12y) * 30
                if not recargonocturno_amount == 0:
                    recargonocturno_amount = (recargonocturno_amount / total_days12y) * 30
                if not recargodiurnofestivo_amount == 0:
                    recargodiurnofestivo_amount = (recargodiurnofestivo_amount / total_days12y) * 30
                if not recargonocturnofestivo_amount == 0:
                    recargonocturnofestivo_amount = (recargonocturnofestivo_amount / total_days12y) * 30

                total_extra_hour = extradiurna_amount + extradiurnafestivo_amount + extranocturna_amount + extranocturnafestivo_amount + recargonocturno_amount + recargodiurnofestivo_amount + recargonocturnofestivo_amount

            inputs_loans_year_now = self.env['hr.payslip'].get_inputs_loans_year_now(c, date_from,date_to)
            if inputs_loans_year_now:
                lm12_date_ini = date_to - relativedelta(months=12)
                lm12_date_ini = lm12_date_ini + relativedelta(days=1)
                if c.date_start <= lm12_date_ini:
                    lm12_date_init = lm12_date_ini
                else:
                    lm12_date_init = c.date_start
                # total_dayl12 = days_between(lm12_date_init, date_to)
                if date_to.day == 31:
                    date_to = date_to - relativedelta(days=1)
                total_dayl12 = days360(lm12_date_init, date_to) + 1
                amountb = 0
                amountc = 0
                for loans in inputs_loans_year_now:
                    if loans[1] == 'BONIFICACION':
                        amountb = amountb + loans[2]
                    if loans[1] == 'COMISION':
                        amountc = amountc + loans[2]
                if not amountb == 0:
                    amountb = (amountb / total_dayl12) * 30
                if not amountc == 0:
                    amountc = (amountc / total_dayl12) * 30


            # ------------------------------ VALOR DERIVADO DEL PROMEDIO ANUAL  -----------------------------------------

            valor_anual = salary + total_extra_hour + amountb + amountc

            valor_unit_anual = valor_anual / 30

            total_anual = valor_unit_anual * dias_liq

            # ---------------------- VALOR PROMEDIO 12 MESES ATRAS -----------------

            total_extra_hour_12m = 0
            amountb_12m = 0
            amountc_12m = 0
            date_from = self.date_creation
            date_to = self.date_creation

            if date_to.day <= 15:
                date_to = date(date_to.year, date_to.month, 15)

            if date_to.day > 15 and date_to.day <= 31:
                date_to = date(date_to.year, date_to.month, 30)

            horas_extras_12month_before = self.env['hr.payslip'].get_inputs_hora_extra_12month_before(c, date_from, date_to)
            if horas_extras_12month_before:
                hm12_date_ini = date_to - relativedelta(months=12)
                hm12_date_ini = hm12_date_ini + relativedelta(days=1)
                if c.date_start <= hm12_date_ini:
                    hm12_date_init = hm12_date_ini
                else:
                    hm12_date_init = c.date_start
                # total_days12y = days_between(hm12_date_init, date_to)
                if date_to.day == 31:
                    date_to = date_to - relativedelta(days=1)
                total_days12y = days360(hm12_date_init, date_to) + 1
                extradiurna_amount = 0
                extradiurnafestivo_amount = 0
                extranocturna_amount = 0
                extranocturnafestivo_amount = 0
                recargonocturno_amount = 0
                recargodiurnofestivo_amount = 0
                recargonocturnofestivo_amount = 0
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

                if not extradiurna_amount == 0:
                    extradiurna_amount = (extradiurna_amount / total_days12y) * 30
                if not extradiurnafestivo_amount == 0:
                    extradiurnafestivo_amount = (extradiurnafestivo_amount / total_days12y) * 30
                if not extranocturna_amount == 0:
                    extranocturna_amount = (extranocturna_amount / total_days12y) * 30
                if not extranocturnafestivo_amount == 0:
                    extranocturnafestivo_amount = (extranocturnafestivo_amount / total_days12y) * 30
                if not recargonocturno_amount == 0:
                    recargonocturno_amount = (recargonocturno_amount / total_days12y) * 30
                if not recargodiurnofestivo_amount == 0:
                    recargodiurnofestivo_amount = (recargodiurnofestivo_amount / total_days12y) * 30
                if not recargonocturnofestivo_amount == 0:
                    recargonocturnofestivo_amount = (recargonocturnofestivo_amount / total_days12y) * 30

                total_extra_hour_12m = extradiurna_amount + extradiurnafestivo_amount + extranocturna_amount + extranocturnafestivo_amount + recargonocturno_amount + recargodiurnofestivo_amount + recargonocturnofestivo_amount

            inputs_loans_12month_before = self.env['hr.payslip'].get_inputs_loans_12month_before(c, date_from, date_to)
            if inputs_loans_12month_before:
                lm12_date_ini = date_to - relativedelta(months=12)
                lm12_date_ini = lm12_date_ini + relativedelta(days=1)
                if c.date_start <= lm12_date_ini:
                    lm12_date_init = lm12_date_ini
                else:
                    lm12_date_init = c.date_start
                # total_dayl12 = days_between(lm12_date_init, date_to)
                if date_to.day == 31:
                    date_to = date_to - relativedelta(days=1)
                total_dayl12 = days360(lm12_date_init, date_to) + 1
                amountb_12m = 0
                amountc_12m = 0
                for loans in inputs_loans_12month_before:
                    if loans[1] == 'BONIFICACION':
                        amountb_12m = amountb_12m + loans[2]
                    if loans[1] == 'COMISION':
                        amountc_12m = amountc_12m + loans[2]
                if not amountb_12m == 0:
                    amountb_12m = (amountb_12m / total_dayl12) * 30
                if not amountc_12m == 0:
                    amountc_12m = (amountc_12m / total_dayl12) * 30

            # ------------------------------ VALOR DERIVADO DEL PROMEDIO ANUAL  -----------------------------------------

            valor_12m = salary + total_extra_hour_12m + amountb_12m + amountc_12m

            valor_unit_12m = valor_12m / 30

            total_12m = valor_unit_12m * dias_liq

            #---------------------------------------------- PRIMA --------------------------------------------------------------------
            ws.write(fila, col, '') if not c.name else ws.write(fila, col, c.name)
            col += 1

            ws.write(fila, col, '') if not c.employee_id.identification_id else ws.write(fila, col, c.employee_id.identification_id)
            col += 1

            ws.write(fila, col, '') if not c.employee_id.name else ws.write(fila, col, c.employee_id.name)
            col += 1

            ws.write(fila, col, 'Prima Legal')
            col += 1

            ws.write(fila, col, '') if not date_init else ws.write(fila, col, date_init, format_date)
            col += 1

            ws.write(fila, col, self.date_creation, format_date)
            col += 1

            ws.write(fila, col, valor_anual, format_number)
            col += 1

            ws.write(fila, col, dias_labor)
            col += 1

            ws.write(fila, col, round(dias_liq, 2))
            col += 1

            ws.write(fila, col, valor_unit_anual, format_number)
            col += 1

            ws.write(fila, col, total_anual, format_number)
            col += 1

            fila += 1
            col = 0

            # ---------------------------------------------- CESANTIAS --------------------------------------------------------------------
            ws.write(fila, col, '') if not c.name else ws.write(fila, col, c.name)
            col += 1

            ws.write(fila, col, '') if not c.employee_id.identification_id else ws.write(fila, col, c.employee_id.identification_id)
            col += 1

            ws.write(fila, col, '') if not c.employee_id.name else ws.write(fila, col, c.employee_id.name)
            col += 1

            ws.write(fila, col, 'Cesantias')
            col += 1

            ws.write(fila, col, '') if not date_init else ws.write(fila, col, date_init, format_date)
            col += 1

            ws.write(fila, col, self.date_creation, format_date)
            col += 1

            ws.write(fila, col, valor_anual, format_number)
            col += 1

            ws.write(fila, col, dias_labor)
            col += 1

            ws.write(fila, col, round(dias_liq, 2))
            col += 1

            ws.write(fila, col, valor_unit_anual, format_number)
            col += 1

            ws.write(fila, col, total_anual, format_number)
            col += 1

            fila += 1
            col = 0

            # ---------------------------------------------- INTERESES CESANTIAS --------------------------------------------------------------------
            ws.write(fila, col, '') if not c.name else ws.write(fila, col, c.name)
            col += 1

            ws.write(fila, col, '') if not c.employee_id.identification_id else ws.write(fila, col, c.employee_id.identification_id)
            col += 1

            ws.write(fila, col, '') if not c.employee_id.name else ws.write(fila, col, c.employee_id.name)
            col += 1

            ws.write(fila, col, 'Intereses Cesantias')
            col += 1

            ws.write(fila, col, '') if not date_init else ws.write(fila, col, date_init, format_date)
            col += 1

            ws.write(fila, col, self.date_creation, format_date)
            col += 1

            ws.write(fila, col, valor_anual, format_number)
            col += 1

            ws.write(fila, col, dias_labor)
            col += 1

            ws.write(fila, col, round(dias_liq, 2))
            col += 1

            ws.write(fila, col, valor_unit_anual, format_number)
            col += 1

            ws.write(fila, col, total_anual, format_number)
            col += 1

            fila += 1
            col = 0

            # ---------------------------------------------- VACACIONES --------------------------------------------------------------------
            ws.write(fila, col, '') if not c.name else ws.write(fila, col, c.name)
            col += 1

            ws.write(fila, col, '') if not c.employee_id.identification_id else ws.write(fila, col, c.employee_id.identification_id)
            col += 1

            ws.write(fila, col, '') if not c.employee_id.name else ws.write(fila, col, c.employee_id.name)
            col += 1

            ws.write(fila, col, 'Vacaciones')
            col += 1

            ws.write(fila, col, '') if not date_init else ws.write(fila, col, c.vacations_date, format_date)
            col += 1

            ws.write(fila, col, self.date_creation, format_date)
            col += 1

            ws.write(fila, col, valor_12m, format_number)
            col += 1

            ws.write(fila, col, dias_labor_vacaciones)
            col += 1

            ws.write(fila, col, c.vacations_available)
            col += 1

            ws.write(fila, col, valor_unit_12m, format_number)
            col += 1

            ws.write(fila, col, total_12m , format_number)
            col += 1

            fila += 1
            col = 0

        try:
            wb.close()
            out = base64.encodestring(buf.getvalue())
            buf.close()
            self.data = out
            self.data_name = 'prestaciones' + ".xls"
        except ValueError:
            raise Warning('No se pudo generar el archivo')

#
