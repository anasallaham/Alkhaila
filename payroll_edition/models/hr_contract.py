# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HrContract(models.Model):
    _inherit = 'hr.contract'

    addition_ture = fields.Boolean(string="احتساب اضافي؟")
    addition_nsbeh = fields.Integer(string="نسبة الاضافي",default=1)

    delay_ture = fields.Boolean(string="احتساب الخصومات؟")
    delay_nsbeh = fields.Integer(string="نسبة الخصومات",default=1)

    hous = fields.Integer(string="نسبة العلاوات الاخرى",default=0,readonly=False)
    amount_hous = fields.Integer(string="قيمة العلاوات الاخرى", compute='_compute_amount_hous', store=True)



    @api.depends('hous','wage')
    def _compute_amount_hous(self):
        for me in self:
            me.amount_hous = me.hous/100 * me.wage

