# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    barcode = fields.Char(compute="get_barcode", store=True)

    @api.depends("name", "product_id.barcode")
    def get_barcode(self):
        for lot in self:
            if lot.name and lot.product_id.barcode:
                lot.barcode = lot.product_id.barcode + "000000" + lot.name