from odoo import models, fields, api


class Exportacion(models.Model):
    #_inherit = 'x_exportacion'
    _name = 'x_exportacion'
    _description = 'actualizacion campos exportacion'
    _rec_name = 'x_name'


    profile = fields.Many2one(comodel_name='infoexport', string='Perfil')
    x_studio_field_Xjy46 = fields.Many2one(comodel_name='sale.order',inverse_name='exportacion_ids', string='Orden venta', copy=False)
    responsable_exp = fields.Many2one(comodel_name='hr.employee',string='Responsable')
    cargo_responsable_expo = fields.Many2one(comodel_name='hr.job', compute='compute_cargo_responsable_expo',string='Cargo')
    imp = fields.Char(compute='compute_imp',string='IMP')
    imp_id = fields.Many2one(comodel_name='x_importacion',compute='compute_imp_id',string='IMP')
    x_studio_valor_factura = fields.Float(string='Valor Factura',compute='compute_valor_factura')
    merchandise_description = fields.Text(string='Descripción de la mercancía')
    port_control_company = fields.Char(string='Compañía control porturario')


    @api.depends('x_studio_factura__1')
    def compute_valor_factura(self):
        for record in self:
            if record.x_studio_factura__1:
                record.x_studio_valor_factura = record.x_studio_factura__1.amount_total
            else:
                record.x_studio_valor_factura = ''
#______________________________________________________________________________________________________


            # __________________________________________________________________________________________________________________________________________
    @api.depends('imp')
    def compute_imp(self):
        for record in self:
            if record.x_name:
                cons = self.env['purchase.order'].search([('x_studio_op_', '=', record.x_name)])
                if cons.x_studio_imp__1.x_name == 'False':
                    record.imp= " "
                else:

                    record.imp = cons.x_studio_imp__1.x_name

            else:
                record.imp = ' '
#__________________________________________________________________________________________________________________________________________
    @api.depends('imp_id')
    def compute_imp_id(self):
        for record in self:
            if record.imp:
                record.imp_id = self.env['x_importacion'].search([('x_name', '=', record.imp)])
            else:
                record.imp_id = False


#__________________________________________________________________________________________________________________________________________
    @api.depends('responsable_exp')
    def compute_cargo_responsable_expo(self):
        for record in self:
            if record.responsable_exp:
                record.cargo_responsable_expo= record.responsable_exp.job_id
            else:
                record.cargo_responsable_expo = False

    @api.onchange('profile')
    def compute_porcentaje(self):
        for record in self:
            if record.profile:
                record.x_studio_porcentaje_vacio = record.profile.empty_percentage
            else:
                record.x_studio_porcentaje_vacio = False


    @api.onchange('profile')
    def compute_flete(self):
        for record in self:
            if record.profile:
                record.x_studio_flete_origen_cop = record.profile.origin_freight
            else:
                record.x_studio_flete_origen_cop = False

    @api.onchange('profile')
    def compute_gastos(self):
        for record in self:
            if record.profile:
                record.x_studio_otros_gastos_destino_usd = record.profile.other_origin_expenses
            else:
                record.x_studio_otros_gastos_destino_usd = False

    @api.onchange('profile')
    def compute_seguro(self):
        for record in self:
            if record.profile:
                record.x_studio_monto_seguro_usd_1 = record.profile.sure
            else:
                record.x_studio_monto_seguro_usd_1 = False

    @api.onchange('profile')
    def compute_nombre_responsable(self):
        for record in self:
            if record.profile:
                record.x_studio_field_W4KVK = record.profile.responsible_name
            else:
                record.x_studio_field_W4KVK = False

    @api.onchange('profile')
    def compute_cargo(self):
        for record in self:
            if record.profile:
                record.x_studio_cargo_2 = record.profile.position
            else:
                record.x_studio_cargo_2 = False

    @api.onchange('profile')
    def compute_cedula_responsable(self):
        for record in self:
            if record.profile:
                record.x_studio_cedula_responsable_1 = record.profile.responsible_certificate
            else:
                record.x_studio_cedula_responsable_1 = False

    @api.onchange('profile')
    def compute_lugar_exp(self):
        for record in self:
            if record.profile:
                record.x_studio_lugar_de_expedicion_1 = record.profile.expedition_place
            else:
                record.x_studio_lugar_de_expedicion_1 = False

    @api.onchange('profile')
    def compute_vuce(self):
        for record in self:
            if record.profile:
                record.x_studio_alcance_por_la_vuce = record.profile.reach_vuce
            else:
                record.x_studio_alcance_por_la_vuce = False

    @api.onchange('profile')
    def compute_flete_studio(self):
        for record in self:
            if record.profile:
                record.x_studio_monto_flete_maritimo_en_usd_1 = record.profile.sea_freight
            else:
                record.x_studio_monto_flete_maritimo_en_usd_1 = False

    @api.onchange('profile')
    def compute_flete_estudio(self):
        for record in self:
            if record.profile:
                record.x_studio_otros_cop = record.profile.other_expenses
            else:
                record.x_studio_otros_cop = False

