# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime
from dateutil.relativedelta import relativedelta


class HrPayrollStructureType(models.Model):
    _inherit = 'hr.payroll.structure.type'


    is_allow = fields.Boolean(string=" احتساب العلاوات في المخالصة")
