# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AYSWizard(models.TransientModel):

    _name = "hr.contract.wizard"
    
    @api.multi
    def action_are_you_sure(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        active_id = context.get('active_ids', False)
        obj_hr_contract = self.env['hr.contract']
        rec_hr_contract = obj_hr_contract.browse(active_id)
        if rec_hr_contract.state=='validado':
            rec_hr_contract.validado_borrador()
        elif rec_hr_contract.state=='activo':
            rec_hr_contract.activo_borrador()
        elif rec_hr_contract.state=='liquidado':
            rec_hr_contract.liquidado_borrador()
        return {'type': 'ir.actions.act_window_close'}