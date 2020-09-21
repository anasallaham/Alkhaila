# -*- coding: utf-8 -*-
# Part of SnepTech. See LICENSE file for full copyright and licensing details.##
##################################################################################

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError

class account_payment(models.Model):           
    _inherit = 'account.payment'
    
    payslip_id = fields.Many2one('hr.payslip',"Payslip")
    


    def get_payslip(self):
        try:
            form_view = self.env.ref('hr_payroll.view_hr_payslip_form')
        except ValueError:
            form_view = False
        if not self.payslip_id.id:
            raise UserError(_('Payslip not found for this payment!'))

        return {
            'name': 'Payment',
            'view_mode': 'form',
            'res_model': 'hr.payslip',
            'res_id':self.payslip_id.id,
            'view_id': form_view.id,
            'views': [(form_view.id, 'form')],
            'type': 'ir.actions.act_window',
            'target':'curret',
        }