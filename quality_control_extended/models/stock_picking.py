from ast import literal_eval
from datetime import date
from itertools import groupby
from operator import attrgetter, itemgetter
from collections import defaultdict
import time

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES

class StockPicking(models.Model):

    _inherit = 'stock.picking'

    
    def button_validate(self):
        for record in self:
            super(StockPicking, record).button_validate()
            if record.picking_type_id.sequence_code == 'IN':
                for move_line_ids in record.move_line_nosuggest_ids:
                    check_points = record.env['quality.point'].search([('product_tmpl_id', '=', move_line_ids.product_id.name),
                                                                       ('picking_type_id', '=', 'Materia Prima: Transferencias internas')], limit=1)

                    if check_points:
                        lot = False
                        stock_production_lot = record.env['stock.production.lot'].search([('name', '=', move_line_ids.lot_name)], limit=1)
                        if stock_production_lot:
                            lot = stock_production_lot.id

                        record.env['quality.check'].create({
                            'product_id': move_line_ids.product_id.id,
                            'lot_id': lot,
                            'picking_id': record.id,
                            'team_id': 1,
                            'test_type_id': check_points.test_type_id.id,

                        })
                    else:
                        pass


            if record.picking_type_id.sequence_code == 'INT':
                for move_line_ids in record.move_line_ids_without_package:
                    quality_check = record.env['quality.check'].search([('product_id', '=', move_line_ids.product_id.name),
                                                                        ('quality_state', '=', 'none')])

                    if quality_check:
                        raise UserError('El producto ' + move_line_ids.product_id.name + ' No ha sido aprobado en el documento control de calidad')
















