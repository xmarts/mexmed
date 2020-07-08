# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    barcode = fields.Char(compute="get_barcode", store=True)

    @api.depends("name", "product_id.barcode", "life_date")
    def get_barcode(self):
        for lot in self:
            if lot.name and lot.product_id.barcode and lot.life_date:
                date = fields.Datetime.to_string(lot.life_date)
                date_code = "{}{}{}".format(date[8:10], date[5:7], date[2:4])
                lot.barcode = "{}{}{}".format(
                    lot.product_id.barcode[0:6],
                    date_code,
                    lot.name[0:6]
                )