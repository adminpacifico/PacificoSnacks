from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime

class HrContract(models.Model):
    _inherit = 'hr.contract'
    
    tarifa_riesgos = fields.Selection([
        ('0.522', 'I'),
        ('1.044', 'II'),
        ('2.436', 'III'),
        ('4.35', 'IV'),
        ('6.96', 'V'),
        ('0', 'No Aplica')
    ], string='Tarifa Riesgos', required=True, default='0.522')
    
    arl_id = fields.Many2one('res.partner', string='Administradora de Riesgos Laborales', domain=[('tipo_entidad_ss','=','arl')])
    afp_id = fields.Many2one('res.partner', string='Administradora de Fondos de Pension', domain=[('tipo_entidad_ss','=','afp')])
    afc_id = fields.Many2one('res.partner', string='Administradora de Fondos de Cesantias', domain=[('tipo_entidad_ss','=','afc')])
    eps_id = fields.Many2one('res.partner', string='Entidad Promotora de Salud', domain=[('tipo_entidad_ss','=','eps')])
    ccf_id = fields.Many2one('res.partner', string='Caja de Compensacion Familiar', domain=[('tipo_entidad_ss','=','ccf')])
    
class HrSSEntidad(models.Model):
    _inherit = 'res.partner'
    
    tipo_entidad_ss = fields.Selection([
        ('eps', 'Entidad Promotora de Salud'),
        ('arl', 'Administradora de Riesgos Laborales'),
        ('afp', 'Administradora de Fondos de Pension'),
        ('afc', 'Administradora de Fondos de Cesantias'),
        ('ccf', 'Caja de Compensacion Familiar'),
        ('na', 'No Aplica')
    ], string='Tipo Entidad Seguridad Social', required=True, default='na')
    
class HrSalaryRuleSS(models.Model):
    _inherit = 'hr.salary.rule'   
    
    tipo_entidad_asociada = fields.Selection([
            ('arl', 'Administradora de Riesgos Laborales'),
            ('afp', 'Administradora de Fondos de Pension'),
            ('afc', 'Administradora de Fondos de Cesantias'),
            ('eps', 'Entidad Promotora de Salud'),
            ('ccf', 'Caja de Compensacion Familiar'),
            ('na', 'No Aplica'),
            ]
            , string='Tipo Entidad Asociada', help="Identifica a que tipo de entidad según el Sistema de Seguridad Social Colombiano está asociada la regla salarial.", 
            required=True, default='na')
