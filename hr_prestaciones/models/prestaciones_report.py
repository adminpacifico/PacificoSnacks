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
    date_creation = fields.Date('Fecha')

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

            # ---------------------- FECHA INICIAL PRIMA -----------------------

            if self.date_creation.month <= 6 and self.date_creation.day <= 31:
                init_date_prima = date(self.date_creation.year, 1, 1)

            elif self.date_creation.month <= 12 and self.date_creation.day <= 31:
                init_date_prima = date(self.date_creation.year, 7, 1)

            if c.date_start <= init_date_prima:
                date_init_prima = init_date_prima
            else:
                date_init_prima = c.date_start

            dias_labor_prima = days360(date_init_prima, self.date_creation) + 1

            dias_liq_prima = dias_labor_prima / 360

            # ---------------------- VALOR PROMEDIO SEMESTRAL -----------------

            salary = c.wage
            total_extra_hour = 0
            amountb = 0
            amountc = 0
            date_from = self.date_creation
            date_to = self.date_creation

            # Horas extras promedio semestral
            hora_extra_6month = self.env['hr.payslip'].get_inputs_hora_extra_6month(c, date_from, date_to)
            if hora_extra_6month:
                if date_from.month <= 6 and date_from.day <= 31:
                    hdate_init_6month = date(date_from.year, 1, 1)

                elif date_from.month <= 12 and date_from.day <= 31:
                    hdate_init_6month = date(date_from.year, 7, 1)

                if c.date_start <= hdate_init_6month:
                    hdate_init = hdate_init_6month
                else:
                    hdate_init = c.date_start

                if date_to.day == 31:
                    date_to = date_to - relativedelta(days=1)

                total_days = days360(hdate_init, date_to) + 1

                if total_days < 30:
                    day_base = total_days
                else:
                    day_base = 30

                extradiurna_amount = 0
                extradiurnafestivo_amount = 0
                extranocturna_amount = 0
                extranocturnafestivo_amount = 0
                recargonocturno_amount = 0
                recargodiurnofestivo_amount = 0
                recargonocturnofestivo_amount = 0
                for hora in hora_extra_6month:
                    if hora[1] == 'EXTRADIURNA':
                        extradiurna_amount = extradiurna_amount + hora[2]
                        extradiurna_type_id = hora[3]
                    if hora[1] == 'EXTRADIURNAFESTIVO':
                        extradiurnafestivo_amount = extradiurnafestivo_amount + hora[2]
                        extradiurnafestivo_type_id = hora[3]
                    if hora[1] == 'EXTRANOCTURNA':
                        extranocturna_amount = extranocturna_amount + hora[2]
                        extranocturna_type_id = hora[3]
                    if hora[1] == 'EXTRANOCTURNAFESTIVO':
                        extranocturnafestivo_amount = extranocturnafestivo_amount + hora[2]
                        extranocturnafestivo_type_id = hora[3]
                    if hora[1] == 'RECARGONOCTURNO':
                        recargonocturno_amount = recargonocturno_amount + hora[2]
                        recargonocturno_type_id = hora[3]
                    if hora[1] == 'RECARGODIURNOFESTIVO':
                        recargodiurnofestivo_amount = recargodiurnofestivo_amount + hora[2]
                        recargodiurnofestivo_type_id = hora[3]
                    if hora[1] == 'RECARGONOCTURNOFESTIVO':
                        recargonocturnofestivo_amount = recargonocturnofestivo_amount + hora[2]
                        recargonocturnofestivo_type_id = hora[3]

                if not extradiurna_amount == 0:
                    extradiurna_amount = (extradiurna_amount / total_days) * day_base
                if not extradiurnafestivo_amount == 0:
                    extradiurnafestivo_amount = (extradiurnafestivo_amount / total_days) * day_base
                if not extranocturna_amount == 0:
                    extranocturna_amount = (extranocturna_amount / total_days) * day_base
                if not extranocturnafestivo_amount == 0:
                    extranocturnafestivo_amount = (extranocturnafestivo_amount / total_days) * day_base
                if not recargonocturno_amount == 0:
                    recargonocturno_amount = (recargonocturno_amount / total_days) * day_base
                if not recargodiurnofestivo_amount == 0:
                    recargodiurnofestivo_amount = (recargodiurnofestivo_amount / total_days) * day_base
                if not recargonocturnofestivo_amount == 0:
                    recargonocturnofestivo_amount = (recargonocturnofestivo_amount / total_days) * day_base

                total_extra_hour = extradiurna_amount + extradiurnafestivo_amount + extranocturna_amount + extranocturnafestivo_amount + recargonocturno_amount + recargodiurnofestivo_amount + recargonocturnofestivo_amount

            # Bonificaciones y comisiones semestral
            loans_6month = self.env['hr.payslip'].get_inputs_loans_6month(c, date_from, date_to)
            if loans_6month:
                if date_from.month <= 6 and date_from.day <= 31:
                    ldate_init_6month = date(date_from.year, 1, 1)

                elif date_from.month <= 12 and date_from.day <= 31:
                    ldate_init_6month = date(date_from.year, 7, 1)

                if c.date_start <= ldate_init_6month:
                    ldate_init = ldate_init_6month
                else:
                    ldate_init = c.date_start
                if date_to.day == 31:
                    date_to = date_to - relativedelta(days=1)

                ltotal_days = days360(ldate_init, date_to) + 1

                if ltotal_days < 30:
                    day_base = ltotal_days
                else:
                    day_base = 30

                countb = 0
                amountb = 0
                inputb_type_id = 0
                countc = 0
                amountc = 0
                inputc_type_id = 0
                for loans in loans_6month:
                    if loans[1] == 'BONIFICACION':
                        countb = countb + 1
                        amountb = amountb + loans[2]
                        inputb_type_id = loans[3]
                    if loans[1] == 'COMISION':
                        countc = countc + 1
                        amountc = amountc + loans[2]
                        inputc_type_id = loans[3]
                if not amountb == 0:
                    amountb = (amountb / ltotal_days) * day_base
                if not amountc == 0:
                    amountc = (amountc / ltotal_days) * day_base

            # ------------------------------ VALOR DERIVADO DEL PROMEDIO ANUAL  -----------------------------------------

            valor_prima = salary + total_extra_hour + amountb + amountc

            valor_unit_prima = valor_prima / 30

            total_prima = valor_unit_prima * dias_liq_prima

            # ---------------------- FECHA INICIAL CESANTIAS -----------------------
            init_year = date(date_from.year, 1, 1)
            if c.date_start <= init_year:
                date_init_ces = init_year
            else:
                date_init_ces = c.date_start


            dias_labor_ces = days360(date_init_ces, self.date_creation) + 1

            dias_liq_ces = dias_labor_ces / 360


            # ---------------------- VALOR CESANTIAS PROMEDIO ANUAL -----------------

            salary = c.wage
            total_extra_hour = 0
            amountb = 0
            amountc = 0
            date_from = self.date_creation
            date_to = self.date_creation


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

                if total_days12y < 30:
                    day_base = total_days12y
                else:
                    day_base = 30

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
                    extradiurna_amount = (extradiurna_amount / total_days12y) * day_base
                if not extradiurnafestivo_amount == 0:
                    extradiurnafestivo_amount = (extradiurnafestivo_amount / total_days12y) * day_base
                if not extranocturna_amount == 0:
                    extranocturna_amount = (extranocturna_amount / total_days12y) * day_base
                if not extranocturnafestivo_amount == 0:
                    extranocturnafestivo_amount = (extranocturnafestivo_amount / total_days12y) * day_base
                if not recargonocturno_amount == 0:
                    recargonocturno_amount = (recargonocturno_amount / total_days12y) * day_base
                if not recargodiurnofestivo_amount == 0:
                    recargodiurnofestivo_amount = (recargodiurnofestivo_amount / total_days12y) * day_base
                if not recargonocturnofestivo_amount == 0:
                    recargonocturnofestivo_amount = (recargonocturnofestivo_amount / total_days12y) * day_base

                total_extra_hour = extradiurna_amount + extradiurnafestivo_amount + extranocturna_amount + extranocturnafestivo_amount + recargonocturno_amount + recargodiurnofestivo_amount + recargonocturnofestivo_amount

            inputs_loans_year_now = self.env['hr.payslip'].get_inputs_loans_year_now(c, date_from,date_to)
            if inputs_loans_year_now:
                lm12_date_ini = date_to - relativedelta(months=12)
                lm12_date_ini = lm12_date_ini + relativedelta(days=1)
                if c.date_start <= lm12_date_ini:
                    lm12_date_init = lm12_date_ini
                else:
                    lm12_date_init = c.date_start
                if date_to.day == 31:
                    date_to = date_to - relativedelta(days=1)
                total_dayl12 = days360(lm12_date_init, date_to) + 1

                if total_dayl12 < 30:
                    day_base = total_dayl12
                else:
                    day_base = 30

                amountb = 0
                amountc = 0
                for loans in inputs_loans_year_now:
                    if loans[1] == 'BONIFICACION':
                        amountb = amountb + loans[2]
                    if loans[1] == 'COMISION':
                        amountc = amountc + loans[2]
                if not amountb == 0:
                    amountb = (amountb / total_dayl12) * day_base
                if not amountc == 0:
                    amountc = (amountc / total_dayl12) * day_base


            # ------------------------------ VALOR DERIVADO DEL PROMEDIO CESANTIAS  -----------------------------------------

            valor_ces = salary + total_extra_hour + amountb + amountc

            valor_unit_ces = valor_ces / 30

            total_ces = valor_unit_ces * dias_liq_ces

            # ------------------------------ VALOR DERIVADO DEL PROMEDIO INT CESANTIAS  -----------------------------------------

            valor_ces_int = (salary + total_extra_hour + amountb + amountc) * 0.12

            valor_unit_ces_int = valor_ces_int / 30

            total_ces_int = valor_unit_ces_int * dias_liq_ces


            # ---------------------- VALOR VACACIONES PROMEDIO 12 MESES ATRAS -----------------

            dias_labor_vaca = days360(c.vacations_date, self.date_creation) + 1

            dias_liq_vaca = c.vacations_available

            total_extra_hour_12m = 0
            amountb_12m = 0
            amountc_12m = 0
            date_from = self.date_creation
            date_to = self.date_creation

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

                if total_days12y < 30:
                    day_base = total_days12y
                else:
                    day_base = 30

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
                    extradiurna_amount = (extradiurna_amount / total_days12y) * day_base
                if not extradiurnafestivo_amount == 0:
                    extradiurnafestivo_amount = (extradiurnafestivo_amount / total_days12y) * day_base
                if not extranocturna_amount == 0:
                    extranocturna_amount = (extranocturna_amount / total_days12y) * day_base
                if not extranocturnafestivo_amount == 0:
                    extranocturnafestivo_amount = (extranocturnafestivo_amount / total_days12y) * day_base
                if not recargonocturno_amount == 0:
                    recargonocturno_amount = (recargonocturno_amount / total_days12y) * day_base
                if not recargodiurnofestivo_amount == 0:
                    recargodiurnofestivo_amount = (recargodiurnofestivo_amount / total_days12y) * day_base
                if not recargonocturnofestivo_amount == 0:
                    recargonocturnofestivo_amount = (recargonocturnofestivo_amount / total_days12y) * day_base

                total_extra_hour_12m = extradiurna_amount + extradiurnafestivo_amount + extranocturna_amount + extranocturnafestivo_amount + recargonocturno_amount + recargodiurnofestivo_amount + recargonocturnofestivo_amount

            inputs_loans_12month_before = self.env['hr.payslip'].get_inputs_loans_12month_before(c, date_from, date_to)
            if inputs_loans_12month_before:
                lm12_date_ini = date_to - relativedelta(months=12)
                lm12_date_ini = lm12_date_ini + relativedelta(days=1)
                if c.date_start <= lm12_date_ini:
                    lm12_date_init = lm12_date_ini
                else:
                    lm12_date_init = c.date_start
                if date_to.day == 31:
                    date_to = date_to - relativedelta(days=1)
                total_dayl12 = days360(lm12_date_init, date_to) + 1

                if total_dayl12 < 30:
                    day_base = total_dayl12
                else:
                    day_base = 30

                amountb_12m = 0
                amountc_12m = 0
                for loans in inputs_loans_12month_before:
                    if loans[1] == 'BONIFICACION':
                        amountb_12m = amountb_12m + loans[2]
                    if loans[1] == 'COMISION':
                        amountc_12m = amountc_12m + loans[2]
                if not amountb_12m == 0:
                    amountb_12m = (amountb_12m / total_dayl12) * day_base
                if not amountc_12m == 0:
                    amountc_12m = (amountc_12m / total_dayl12) * day_base

            # ------------------------------ VALOR DERIVADO DEL PROMEDIO 12 MESES ATRAS  -----------------------------------------

            valor_vaca = salary + total_extra_hour_12m + amountb_12m + amountc_12m

            valor_unit_vaca = valor_vaca / 30

            total_vaca = valor_unit_vaca * dias_liq_vaca

            #---------------------------------------------- PRIMA --------------------------------------------------------------------
            ws.write(fila, col, '') if not c.name else ws.write(fila, col, c.name)
            col += 1

            ws.write(fila, col, '') if not c.employee_id.identification_id else ws.write(fila, col, c.employee_id.identification_id)
            col += 1

            ws.write(fila, col, '') if not c.employee_id.name else ws.write(fila, col, c.employee_id.name)
            col += 1

            ws.write(fila, col, 'Prima Legal')
            col += 1

            ws.write(fila, col, '') if not init_date_prima else ws.write(fila, col, init_date_prima, format_date)
            col += 1

            ws.write(fila, col, self.date_creation, format_date)
            col += 1

            ws.write(fila, col, valor_prima, format_number)
            col += 1

            ws.write(fila, col, dias_labor_prima)
            col += 1

            ws.write(fila, col, round(dias_liq_prima, 2))
            col += 1

            ws.write(fila, col, valor_unit_prima, format_number)
            col += 1

            ws.write(fila, col, total_prima, format_number)
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

            ws.write(fila, col, '') if not date_init_ces else ws.write(fila, col, date_init_ces, format_date)
            col += 1

            ws.write(fila, col, self.date_creation, format_date)
            col += 1

            ws.write(fila, col, valor_ces, format_number)
            col += 1

            ws.write(fila, col, dias_labor_ces)
            col += 1

            ws.write(fila, col, round(dias_liq_ces, 2))
            col += 1

            ws.write(fila, col, valor_unit_ces, format_number)
            col += 1

            ws.write(fila, col, total_ces, format_number)
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

            ws.write(fila, col, '') if not date_init_ces else ws.write(fila, col, date_init_ces, format_date)
            col += 1

            ws.write(fila, col, self.date_creation, format_date)
            col += 1

            ws.write(fila, col, valor_ces_int, format_number)
            col += 1

            ws.write(fila, col, dias_labor_ces)
            col += 1

            ws.write(fila, col, round(dias_liq_ces, 2))
            col += 1

            ws.write(fila, col, valor_unit_ces_int, format_number)
            col += 1

            ws.write(fila, col, total_ces_int, format_number)
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

            ws.write(fila, col, '') if not c.vacations_date else ws.write(fila, col, c.vacations_date, format_date)
            col += 1

            ws.write(fila, col, self.date_creation, format_date)
            col += 1

            ws.write(fila, col, valor_vaca, format_number)
            col += 1

            ws.write(fila, col, dias_labor_vaca)
            col += 1

            ws.write(fila, col, dias_liq_vaca)
            col += 1

            ws.write(fila, col, valor_unit_vaca, format_number)
            col += 1

            ws.write(fila, col, total_vaca , format_number)
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
