# -*- coding: utf-8 -*-
# Part of SnepTech. See LICENSE file for full copyright and licensing details.##
##################################################################################

from odoo import api, fields, models, _

class hr_contract(models.Model):
    _inherit = 'hr.contract'
    _description = 'Employee Contract'

    journal_id = fields.Many2one('account.journal', 'Salary Journal')