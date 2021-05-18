# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError

import logging

_logger = logging.getLogger(__name__)
           
class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'


    type_payslip_id = fields.Many2one('hr.type.payslip', string="Type")
    date = fields.Date('Date Account', states={'draft': [('readonly', False)]}, readonly=True,
                       help="Keep empty to use the period of the validation(Payslip) date.")
    journal_id = fields.Many2one('account.journal', string='Diario')


    def actualizar_entradas_run(self):
        self.ensure_one()
        if not self.slip_ids:
            raise exceptions.ValidationError(_("You must have at least one payroll so you can update days and others."))
            
        count = 1
        for slip in self.slip_ids:
            _logger.info("ACTUALIZANDO DATOS DE LA NOMINA "+ str(slip.number)+ " *** ID: "+ str(slip.id) + " *** "+ str(count)+ " de "+ str(len(self.slip_ids)))
            slip.actualizar_entradas()
            self._cr.commit()
            count += 1


    def compute_sheet_run(self):
        self.ensure_one()
        if not self.slip_ids:
            raise exceptions.ValidationError(_("You must have at least one payroll so you can update days and others."))
            
        count = 1
        for slip in self.slip_ids:
            _logger.info("ACTUALIZANDO DATOS DE LA NOMINA "+ str(slip.number)+ " *** ID: "+ str(slip.id) + " *** "+ str(count)+ " de "+ str(len(self.slip_ids)))
            slip.compute_sheet()
            self._cr.commit()
            count += 1


    def close_payslip_run(self):
        self.ensure_one()
        if not self.slip_ids:
            raise exceptions.ValidationError(_("You must have at least one payroll so you can update days and others."))
            
        count = 1
        for slip in self.slip_ids:
            _logger.info("ACTUALIZANDO DATOS DE LA NOMINA "+ str(slip.number)+ " *** ID: "+ str(slip.id) + " *** "+ str(count)+ " de "+ str(len(self.slip_ids)))
            slip.action_payslip_done()
            self._cr.commit()
            count += 1        
        return self.write({"state": "close"})


    def draft_payslip_run(self):
        self.ensure_one()
        if not self.slip_ids:
            raise exceptions.ValidationError(_("You must have at least one payroll so you can update days and others."))
            
        count = 1
        for slip in self.slip_ids:
            _logger.info("ACTUALIZANDO DATOS DE LA NOMINA "+ str(slip.number)+ " *** ID: "+ str(slip.id) + " *** "+ str(count)+ " de "+ str(len(self.slip_ids)))
            slip.action_payslip_cancel()
            slip.action_payslip_draft()
            self._cr.commit()
            count += 1        
        return self.write({"state": "draft"})        