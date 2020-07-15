# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    lot_ids = fields.One2many(
        "stock.production.lot", "product_id", string="Lotes"
    )

