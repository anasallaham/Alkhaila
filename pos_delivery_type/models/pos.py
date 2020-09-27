# -*- coding: utf-8 -*-

from odoo import models, fields ,api


class PosDeliveryType(models.Model):
    _name = 'pos.delivery.type'

    name = fields.Char(string="Type", required=True)


class pos_config(models.Model):
    _inherit = 'pos.config' 
    
    delivery_type_ids = fields.Many2many('pos.delivery.type', 'pos_cofing_delivery_type','delivery_type_pos_cofing', string="Delivery Types")



class PosOrder(models.Model):
    _inherit = "pos.order"

    pos_delivery_type = fields.Many2one("pos.delivery.type","Delivery Type")

    @api.model
    def _order_fields(self,ui_order):
        fields = super(PosOrder,self)._order_fields(ui_order)
        fields['pos_delivery_type'] = ui_order.get('pos_delivery_type',0)
        return fields



