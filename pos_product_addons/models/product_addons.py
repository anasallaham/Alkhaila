# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosProductAddonsConfig(models.Model):
    _inherit = 'product.template'

    has_addons = fields.Boolean('Has Add-ons')
    is_addons = fields.Boolean('Is Add-ons')
    addon_ids = fields.Many2many('product.product', string='Addons', domain="[('is_addons', '=', True)]")

    @api.onchange('is_addons', 'has_addons')
    def onchange_is_addons(self):
        """The function makes the corresponding product as 'Available In POS'
        if either 'is_addon' or 'has_addon' fields are true'"""
        if self.is_addons or self.has_addons:
            self.available_in_pos = True

