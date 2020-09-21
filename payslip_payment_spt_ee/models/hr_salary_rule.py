# -*- coding: utf-8 -*-
# Part of SnepTech. See LICENSE file for full copyright and licensing details.##
##################################################################################

from odoo import models, fields, api, _

class hr_salary_rule(models.Model):
    _inherit = 'hr.salary.rule'

    account_tax_id = fields.Many2one('account.tax', 'Tax')
