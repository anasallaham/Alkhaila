# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HrContract(models.Model):
    _inherit = 'hr.contract'

    addition_ture = fields.Boolean(string="احتساب اضافي؟")
    delay_ture = fields.Boolean(string="احتساب الخصومات؟")
    hous = fields.Integer(string="نسبة بدل سكن",default=25,readonly=True)
    amount_hous = fields.Integer(string="قيمة بدل السكن", compute='_compute_amount_hous', store=True)

    moving = fields.Integer(string="نسبة بدل المواصلات",default=10,readonly=True)
    amount_moving = fields.Integer(string="قيمة بدل المواصلات", compute='_compute_amount_moving', store=True)


    @api.depends('hous','wage')
    def _compute_amount_hous(self):
        for me in self:
            me.amount_hous = me.hous/100 * me.wage

    @api.depends('moving','wage')
    def _compute_amount_moving(self):
        for me in self:

            me.amount_moving = me.moving/100 * me.wage