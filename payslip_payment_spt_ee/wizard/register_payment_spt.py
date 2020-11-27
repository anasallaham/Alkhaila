# -*- coding: utf-8 -*-
# Part of SnepTech. See LICENSE file for full copyright and licensing details.##
##################################################################################

from odoo import models, fields, api,_
from odoo.exceptions import UserError

class register_payment_spt(models.TransientModel):
    _name = 'register.payment.spt'

    name = fields.Char('Name')
    journal_id = fields.Many2one('account.journal', string='Payment Method', required=True, domain=[('type', 'in', ('bank', 'cash'))])
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Type', required=True)
    amount = fields.Monetary(string='Payment Amount', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.user.company_id.currency_id)
    payment_date = fields.Date(string='Payment Date', default=fields.Date.context_today, required=True)
    communication = fields.Char(string='Memo')
    payslip_id = fields.Many2one('hr.payslip',string='Pay Slip', required=True)

    @api.onchange('journal_id')
    def _onchange_journal(self):
        if self.journal_id:
            # Set default payment method (we consider the first to be the default one)
            payment_methods = self.journal_id.outbound_payment_method_ids
            self.payment_method_id = payment_methods and payment_methods[0] or False

    def payment_payslip_spt(self):
        for record in self:
            if record.payslip_id.connection_spt():
                # method = record.payslip_id.get_method('payment_payslip_spt')
                # if method['method']:
                #     localdict = {'self':record,'user_obj':record.env.user,'UserError': UserError,'_':_}
                #     exec(method['method'], localdict)
                if not self.payslip_id.employee_id.address_home_id.id:
                    raise UserError(_('Partner not found In Employee (Please Related Partner In Current Employee)!'))
                payment = self.env['account.payment'].create({
                    'name': self.name,
                    'partner_id': self.payslip_id.employee_id.address_home_id.id,
                    'amount': self.payslip_id.net_salary,
                    'payment_date': self.payment_date,
                    'communication': self.communication,
                    'payslip_id': self.payslip_id.id,
                    'partner_type': 'supplier',
                    'payment_type': 'outbound',
                    'journal_id': self.journal_id.id,
                    'payment_method_id': self.payment_method_id.id,
                    'company_id': self.payslip_id.employee_id.company_id.id,
                    'currency_id': self.payslip_id.employee_id.company_id.currency_id.id,
                })
                payment.post()
                line_to_reconcile = self.env['account.move.line']
                for line in payment.move_line_ids + self.payslip_id.move_id.line_ids:
                    if line.account_id.internal_type == 'payable':
                        line_to_reconcile |= line
                line_to_reconcile.reconcile()
                self.payslip_id.state = 'paid'

     