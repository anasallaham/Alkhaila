# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HrContract(models.Model):
    _inherit = 'hr.contract'

    addition_ture = fields.Boolean(string="احتساب اضافي؟")
    addition_nsbeh = fields.Float(string="نسبة الاضافي%",default=1)

    delay_ture = fields.Boolean(string="احتساب الخصومات؟")
    delay_nsbeh = fields.Float(string="نسبة الخصومات%",default=1)

    hous = fields.Integer(string="نسبة بدل السكن",default=25,readonly=True)
    amount_hous = fields.Integer(string="قيمة بدل السكن", compute='_compute_amount_hous', store=True)


    trasportation = fields.Integer(string="نسبة بدل المواصلات",default=10,readonly=True)
    amount_trasportation = fields.Integer(string="قيمة بدل المواصلات", compute='_compute_amount_trasportation', store=True)

    amount_mobile = fields.Integer(string="قيمة بدل الهاتف")


    amount_anuther_allow = fields.Integer(string="قيمة العلاوات الاخرى")


    @api.depends('hous','wage')
    def _compute_amount_hous(self):
        for me in self:
            me.amount_hous = me.hous/100 * me.wage

    @api.depends('trasportation','wage')
    def _compute_amount_trasportation(self):
        for me in self:
            me.amount_trasportation = me.trasportation/100 * me.wage


