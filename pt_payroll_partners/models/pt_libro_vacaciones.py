# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#    Copyright (C) 2024 Cesar Ortiz  Para ti.co SAS
#
##############################################################################

from odoo import api, fields, models, _


class PtLibroVacaciones(models.Model):
    _name = 'pt.libro.vacaciones'
    _description = 'Libro de vacaciones'

    name = fields.Char(string='Año', required=True)
    fecha_inicio = fields.Date(string='Fecha de inicio', required=True)
    fecha_fin = fields.Date(string='Fecha de fin', required=True)
    empleado_id = fields.Many2one('hr.employee', string='Empleado')
    dias_vacaciones = fields.Integer(string='Días de vacaciones') # dias ganados en el año
    dias_tomados = fields.Integer(string='Días tomados') # dias tomados en el año
    dias_restantes = fields.Integer(string='Días restantes', compute='_compute_dias_restantes') # dias restantes en el año
    dias_pasan = fields.Integer(string='Días que pasan del año anterior', required=True, default=0)

    @api.depends('dias_vacaciones', 'dias_tomados')
    def _compute_dias_restantes(self):
        for record in self:
            record.dias_restantes = record.dias_vacaciones + record.dias_pasan - record.dias_tomados


class PTVacacionesTomadas(models.Model):
    _name = 'pt.vacaciones.tomadas'
    _description = 'Vacaciones tomadas'

    name = fields.Char(string='Año', required=True)
    fecha_inicio = fields.Date(string='Fecha de inicio', required=True)
    fecha_fin = fields.Date(string='Fecha de fin', required=True)
    empleado_id = fields.Many2one('hr.employee', string='Empleado')
    dias_tomados = fields.Integer(string='Días tomados')
    registrado = fields.Boolean(string='Registrado', default=False)

    def registrar_vacaciones(self):
        if not self.registrado:
            # find the employee's vacation book
            libro_vacaciones = self.env['pt.libro.vacaciones'].search([('empleado_id', '=', self.empleado_id.id), ('name', '=', self.name)])
            # if not fouend create a new one
            if not libro_vacaciones:
                libro_vacaciones = self.env['pt.libro.vacaciones'].create({
                    'name': self.name,
                    'empleado_id': self.empleado_id.id,
                    'dias_vacaciones': 0, # default value
                    'dias_tomados': 0, # default value
                    'dias_pasan': 0, # default value
                })
            # update the vacation book
            libro_vacaciones.dias_tomados += self.dias_tomados
            self.registrado = True


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    libro_vacaciones_ids = fields.One2many('pt.libro.vacaciones', 'empleado_id', string='Libro de vacaciones')
    vacaciones_tomadas_ids = fields.One2many('pt.vacaciones.tomadas', 'empleado_id', string='Vacaciones tomadas')
