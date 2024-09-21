# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime

class HrContract(models.Model):
    _inherit = 'hr.contract'
    
    def balance_account(self, account):
        print ("balance_account: ", self.employee_id.address_home_id.id, ' - ', account)
        self.env.cr.execute("""
            SELECT sum(balance) as sum
            from account_move_line as aml
            INNER JOIN account_account as aa on aml.account_id = aa.id
            INNER JOIN res_partner as rp on aml.partner_id = rp.id
            WHERE rp.id = %s AND aa.code = %s""",
            (str(self.employee_id.address_home_id.id), str(account)))
        return self.env.cr.fetchone()[0] or 0.0
        
class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'   
    
    liquidar_prima = fields.Boolean("Prima",default=False,
        help="Habilitar liquidacion de Prima en este documento.")
    liquidar_interes_cesantia = fields.Boolean("Interes Cesantias",default=False,
        help="Habilitar el pago de Intereses a las Cesantias en este documento.")
    liquidar_cesantia = fields.Boolean("Cesantias",default=False,
        help="Habilitar el pago adelantado de las Cesantias en este documento.")