# -*- coding: utf-8 -*-
# Part of SnepTech. See LICENSE file for full copyright and licensing details.##
##################################################################################

from odoo import api, fields, models, _
from collections import defaultdict
from datetime import datetime, date, time
import pytz
from odoo.exceptions import UserError


class hr_payslip_employees(models.TransientModel):
    _inherit = 'hr.payslip.employees'
   
    payslip_run_id = fields.Many2one('hr.payslip.run')

   