# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    lot_ids = fields.One2many(
        "stock.production.lot", "product_id", string="Lotes"
    )

    def search(self, args, offset=0, limit=None, order=None, count=False):
        res = super().search(args, offset, limit, order, count)
        if not res and args:
            for item in args:
                if len(item) > 1 and "barcode" in item:
                    args.insert(0, "|")
                    args.append(['barcode', 'ilike', str(item[2][0:6]) + '%'])
                    break
            res = super().search(args, offset, limit, order, count)
        return res