# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re

from odoo import api, fields, models, tools, _
from odoo.osv import expression


class Product(models.Model):
    _inherit = 'product.product'

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100,
                     name_get_uid=None):
        if not args:
            args = []
        if name:
            positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
            product_ids = []
            if operator in positive_operators:
                product_ids = self._search(
                    [('default_code', '=', name)] + args, limit=limit,
                    access_rights_uid=name_get_uid)
                if not product_ids:
                    product_ids = self._search([('barcode', '=', name)] + args,
                                               limit=limit,
                                               access_rights_uid=name_get_uid)
            if not product_ids and operator not in expression.NEGATIVE_TERM_OPERATORS:
                product_ids = self._search(
                    args + [('default_code', operator, name)], limit=limit)
                if not limit or len(product_ids) < limit:
                    limit2 = (limit - len(product_ids)) if limit else False
                    product2_ids = self._search(
                        args + [('name', operator, name),
                                ('id', 'not in', product_ids)], limit=limit2,
                        access_rights_uid=name_get_uid)
                    product_ids.extend(product2_ids)
            elif not product_ids and operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = expression.OR([
                    ['&', ('default_code', operator, name),
                     ('name', operator, name)],
                    ['&', ('default_code', '=', False),
                     ('name', operator, name)],
                ])
                domain = expression.AND([args, domain])
                product_ids = self._search(domain, limit=limit,
                                           access_rights_uid=name_get_uid)
            if not product_ids and operator in positive_operators:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    product_ids = self._search(
                        [('default_code', '=', res.group(2))] + args,
                        limit=limit, access_rights_uid=name_get_uid)
            # still no results, partner in context: search on supplier info as last hope to find something
            if not product_ids and self._context.get('partner_id'):
                suppliers_ids = self.env['product.supplierinfo']._search([
                    ('name', '=', self._context.get('partner_id')),
                    '|',
                    ('product_code', operator, name),
                    ('product_name', operator, name)],
                    access_rights_uid=name_get_uid)
                if suppliers_ids:
                    product_ids = self._search(
                        [('product_tmpl_id.seller_ids', 'in', suppliers_ids)],
                        limit=limit, access_rights_uid=name_get_uid)
            if not product_ids:
                product_ids = self.env['stock.production.lot'].search(
                    [('barcode', '=', name)], limit=limit).product_id.id
        else:
            product_ids = self._search(args, limit=limit,
                                       access_rights_uid=name_get_uid)
        return models.lazy_name_get(
            self.browse(product_ids).with_user(name_get_uid))

    lot_ids = fields.One2many(
        "stock.production.lot", "product_id", string="Lotes"
    )