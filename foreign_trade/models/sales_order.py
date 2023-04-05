from datetime import date, timedelta, datetime
from odoo import fields, models, api



class Sales_development (models.Model):
    _inherit = 'sale.order'
    _description = 'Campos adicionales ventas'

    exportacion_ids = fields.One2many(comodel_name='x_exportacion',inverse_name='x_studio_field_Xjy46',string='Orden Exportacion')
    x_studio_exportacion_ = fields.Many2one(comodel_name='x_exportacion',compute='compute_exportacion_id',inverse='exportacion_id_inverse', string='OP')
    #responsible = fields.Many2one(comodel_name='hr.employee', string='Responsable')
    #other_format = fields.Char(string='Otros formatos')
    #responsible_position = fields.Char(compute='compute_cargo_responsable',string='Cargo del responsable')

    @api.depends('exportacion_ids')
    def compute_exportacion_id(self):
        for record in self:
            if len(record.exportacion_ids) > 0:
                record.x_studio_exportacion_ = record.exportacion_ids[0]
            else:
                record.x_studio_exportacion_ = False


    def exportacion_id_inverse(self):
        for record in self:

            if len(record.exportacion_ids) > 0:
                # delete previous reference
                exportacion = record.env['x_exportacion'].browse(record.exportacion_ids[0].id)
                exportacion.x_studio_field_Xjy46 = False
            # set new reference
            record.x_studio_exportacion_.x_studio_field_Xjy46 = record
##############################################################################################
    #@api.depends('responsible')
    #def compute_cargo_responsable(self):
    #    for record in self:
    #        if record.responsible:
    #            record.responsible_position= record.responsible.job_id.name
    #        else:
    #            record.responsible_position = False
#############################################
