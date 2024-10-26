# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#    Copyright (C) 2024 Cesar Ortiz  Para ti.co SAS
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import logging

_logger = logging.getLogger(__name__)


class PtHrContract(models.Model):
    _inherit = 'hr.contract'

    otros_uno_id = fields.Many2one('res.partner',
                                                  string="Proveedor uno",
                                                  help="Nombre del campo - otros_uno_id")
    otros_dos_id = fields.Many2one('res.partner',
                                                  string="Proveedor dos",
                                                  help="Nombre del campo - otros_dos_id")
    otros_tres_id = fields.Many2one('res.partner',
                                                  string="Proveedor tres",
                                                  help="Nombre del campo - otros_tres_id")
    otros_cuatro_id = fields.Many2one('res.partner',
                                                  string="Proveedor cuatro",
                                                  help="Nombre del campo - otros_cuatro_id")
    otros_cinco_id = fields.Many2one('res.partner',
                                                  string="Proveedor cinco",
                                                  help="Nombre del campo - otros_cinco_id")
    otros_seis_id = fields.Many2one('res.partner',
                                                  string="Proveedor seis",
                                                  help="Nombre del campo - otros_seis_id")
    otros_siete_id = fields.Many2one('res.partner',
                                                  string="Proveedor siete",
                                                  help="Nombre del campo - otros_siete_id")
    otros_ocho_id = fields.Many2one('res.partner',
                                                  string="Proveedor ocho",
                                                  help="Nombre del campo - otros_ocho_id")
    otros_nueve_id = fields.Many2one('res.partner',
                                                  string="Proveedor nueve",
                                                  help="Nombre del campo - otros_nueve_id")
    otros_diez_id = fields.Many2one('res.partner',
                                                  string="Proveedor diez",
                                                  help="Nombre del campo - otros_diez_id")
    monto_uno = fields.Float(string='Monto Uno', help="En caso que sea un monto fijo para el proveedor uno - campo - monto_uno")
    monto_dos = fields.Float(string='Monto Dos', help="En caso que sea un monto fijo para el proveedor dos - campo - monto_dos")
    monto_tres = fields.Float(string='Monto Tres', help="En caso que sea un monto fijo para el proveedor tres - campo - monto_tres")
    monto_cuatro = fields.Float(string='Monto Cuatro', help="En caso que sea un monto fijo para el proveedor cuatro - campo - monto_cuatro")
    monto_cinco = fields.Float(string='Monto Cinco', help="En caso que sea un monto fijo para el proveedor cinco - campo - monto_cinco")
    monto_seis = fields.Float(string='Monto Seis', help="En caso que sea un monto fijo para el proveedor seis - campo - monto_seis")
    monto_siete = fields.Float(string='Monto Siete', help="En caso que sea un monto fijo para el proveedor siete - campo - monto_siete")
    monto_ocho = fields.Float(string='Monto Ocho', help="En caso que sea un monto fijo para el proveedor ocho - campo - monto_ocho")
    monto_nueve = fields.Float(string='Monto Nueve', help="En caso que sea un monto fijo para el proveedor nueve - campo - monto_nueve")
    monto_diez = fields.Float(string='Monto Diez', help="En caso que sea un monto fijo para el proveedor diez - campo - monto_diez")
    tipo_retencion = fields.Selection([('1', 'Método Uno'), ('2', 'Método Dos'), ('3', 'No aplica')], string='Tipo de Retención', help="Tipo de retención salarial", default='3')
    procentaje_metodo_dos = fields.Float(string='Porcentaje Método Dos', help="Porcentaje de retención para el método dos - campo - procentaje_metodo_dos")
    intereses_vivienda = fields.Float(string='Intereses Vivienda', help="Intereses de Vivienda")
    prepagada = fields.Float(string='Prepagada', help="Medicina Prepagada")
    dependiente = fields.Boolean(string='Dependiente', help="Dependiente Económico")
    excentas = fields.Float(string='Renta excenta', help="Rentas Excentas")
    tipo_incapacidad = fields.Selection([('1', 'Normal'), ('2', 'Todo .5'), ('3', 'Todo .66') ,('4', 'Todo 100')], string='Tipo de Retención', help="Tipo de Incapacidad", default='1')
