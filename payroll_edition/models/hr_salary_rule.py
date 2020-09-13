# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _

class HrSalaryRule(models.Model):
    _inherit = "hr.salary.rule"


    is_eos = fields.Boolean(string="IS EOS?")


