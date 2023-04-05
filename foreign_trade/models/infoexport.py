from odoo import models, fields,api


class infoexport(models.Model):
    _name = 'infoexport'
    _description = 'Datos Informe'
    _rec_name = 'name'


    name = fields.Char(string='Configuracion', required=True)
    empty_percentage = fields.Float(string='Porcentaje Vacio')
    origin_freight = fields.Float(string='Flete Origen (COP)')
    sea_freight = fields.Float('Flete marítimo + flete terrestre en destino) (USD)')
    other_origin_expenses = fields.Float(string='Otros gastos Origen (COP)')
    other_expenses = fields.Float('Otros gastos destino (USD)')
    sure = fields.Float(string='seguros (USD)')
    reach_vuce = fields.Selection(selection=[('SI','SI'),('No','No')],string='Alcance por la vuce')
    responsible_name = fields.Many2one(comodel_name='hr.employee', string='Nombre responsable de operacion')
    position = fields.Many2one(comodel_name='hr.job',string='Cargo')
    responsible_certificate = fields.Char(string='Cedula')
    expedition_place = fields.Many2one(comodel_name='res.city',string='Lugar de expedicion')


    @api.onchange('responsible_name')
    def compute_cedula(self):
        for record in self:
            if record.responsible_name:
                record.responsible_certificate = record.responsible_name.identification_id
            else:
                record.responsible_certificate = False

    @api.onchange('responsible_name')
    def compute_cargo(self):
        for record in self:
            if record.responsible_name:
                record.position = record.responsible_name.job_id
            else:
                record.position = False



