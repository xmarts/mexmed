# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api
from odoo.exceptions import ValidationError


class Product(models.Model):
    _inherit = 'product.product'

    # def get_all_products_by_barcode_button(self):
    #     products = self.env['stock.production.lot'].search_read(
    #         [('barcode', '!=', None), ('product_id.type', '!=', 'service')],
    #         ['barcode', 'product_id']
    #     )
    #     packagings = self.env['product.packaging'].search_read(
    #         [('barcode', '!=', None), ('product_id', '!=', None)],
    #         ['barcode', 'product_id', 'qty']
    #     )
    #     # for each packaging, grab the corresponding product data
    #     to_add = []
    #     to_read = []
    #     products_by_id = {product['id']: product for product in products}
    #     for packaging in packagings:
    #         if products_by_id.get(packaging['product_id']):
    #             product = products_by_id[packaging['product_id']]
    #             to_add.append(dict(product, **{'qty': packaging['qty']}))
    #         # if the product doesn't have a barcode, you need to read it directly in the DB
    #         to_read.append((packaging, packaging['product_id'][0]))
    #     products_to_read = self.env['product.product'].browse(
    #         list(set(t[1] for t in to_read))).sudo().read(
    #         ['display_name', 'uom_id', 'tracking'])
    #     products_to_read = {product['id']: product for product in
    #                         products_to_read}
    #     to_add.extend([dict(t[0], **products_to_read[t[1]]) for t in to_read])
    #     # self.env["stock.production.lot"].search([("product_id", "=", )])
    #     raise ValidationError(products)
    #     return {product.pop('barcode'): product for product in
    #             products + to_add}

    @api.model
    def get_all_products_by_barcode(self):
        products = self.env['stock.production.lot'].search_read(
            [('barcode', '!=', None), ('product_id.type', '!=', 'service')],
            ['barcode', 'product_id']
        )
        packagings = self.env['product.packaging'].search_read(
            [('barcode', '!=', None), ('product_id', '!=', None)],
            ['barcode', 'product_id', 'qty']
        )
        # for each packaging, grab the corresponding product data
        to_add = []
        to_read = []
        products_by_id = {product['id']: product for product in products}
        for packaging in packagings:
            if products_by_id.get(packaging['product_id']):
                product = products_by_id[packaging['product_id']]
                to_add.append(dict(product, **{'qty': packaging['qty']}))
            # if the product doesn't have a barcode, you need to read it directly in the DB
            to_read.append((packaging, packaging['product_id'][0]))
        products_to_read = self.env['stock.production.lot'].browse(list(set(t[1] for t in to_read))).sudo().read(['product_id'])
        products_to_read = {product['product_id']: product for product in products_to_read}
        to_add.extend([dict(t[0], **products_to_read[t[1]]) for t in to_read])
        #self.env["stock.production.lot"].search([("product_id", "=", )])
        return {product.pop('barcode'): product for product in products + to_add}

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
                if not product_ids:
                    product_ids = self.env['stock.production.lot'].search(
                        [('barcode', '=', name)] + args,
                        limit=limit, access_rights_uid=name_get_uid).product_id

            if not product_ids and operator not in expression.NEGATIVE_TERM_OPERATORS:
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                product_ids = self._search(
                    args + [('default_code', operator, name)], limit=limit)
                if not limit or len(product_ids) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
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
        else:
            product_ids = self._search(args, limit=limit,
                                       access_rights_uid=name_get_uid)
        return models.lazy_name_get(
            self.browse(product_ids).with_user(name_get_uid))