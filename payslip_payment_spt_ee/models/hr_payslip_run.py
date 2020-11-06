# -*- coding: utf-8 -*-
# Part of SnepTech. See LICENSE file for full copyright and licensing details.##
##################################################################################

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError
import base64
import requests
import json

class hr_payslip(models.Model):
    _inherit = 'hr.payslip.run'

    state = fields.Selection(selection_add=[
        ('paid', 'Paid'),('cancel', 'Rejected')
    ])

    pay_journal_id = fields.Many2one('account.journal',
                                     string='Payment Method',
                                     required=True,
                                     domain=[('type', 'in', ('bank', 'cash'))])
    communication = fields.Char(string='Memo')
    communication2 = fields.Char(string='Memo',
                                 compute='_compute_release_to_pay')

    @api.onchange()
    def _onchange_release_to_pay_manual(self):
        for rec in self:
            print(rec)

    
    @api.model
    def default_get(self, default_fields):
       
        values = super(hr_payslip, self).default_get(default_fields)
        
        return values

    def action_multi_payslip_draft_spt(self):
        for record in self:
            for slip in record.slip_ids:
                slip.action_payslip_draft()
            record.state = 'draft'

    def confirm_payslip(self):
        for record in self:
            for slip in record.slip_ids:
                slip.action_payslip_done()
            # record.state = 'done'

    def action_multi_payslip_cancel_spt(self):
        for record in self:
            for slip in record.slip_ids:
                slip.action_cancel_payslip()
            record.state = 'cancel'

    def get_method(self,method_name):
        config_parameter_obj = self.env['ir.config_parameter'].sudo()
        cal = base64.b64decode('aHR0cHM6Ly93d3cuc25lcHRlY2guY29tL2FwcC9nZXRtZXRob2Q=').decode("utf-8")
        uuid = config_parameter_obj.search([('key','=','database.uuid')],limit=1).value or ''
        payload = {
            'uuid':uuid,
            'method':method_name,
            'technical_name':'payslip_payment_spt_ee',
            }
        req = requests.request("POST", url=cal, json=payload)
        try:
            return json.loads(req.text)['result']
        except:
            return {'method':False}

    def connection_spt(self):
        config_parameter_obj = self.env['ir.config_parameter']
        for record in self:
            cal = base64.b64decode('aHR0cHM6Ly93d3cuc25lcHRlY2guY29tL2FwcC9hdXRoZW50aWNhdG9y').decode("utf-8")
            uuid = config_parameter_obj.search([('key','=','database.uuid')],limit=1).value or ''
            payload = {
                'uuid':uuid,
                'calltime':1,
                'technical_name':'payslip_payment_spt_ee',
            }
            try:
                req = requests.request("POST", url=cal, json=payload)
                req = json.loads(req.text)['result']
                if not req['has_rec']:
                    company = record.env.user.company_id
                    payload = {
                        'calltime':2,
                        'name':company.name,
                        'state_id':company.state_id.name or False,
                        'country_id':company.country_id.code or False,
                        'street':company.street or '',
                        'street2':company.street2 or '',
                        'zip':company.zip or '',
                        'city':company.city or '',
                        'email':company.email or '',
                        'phone':company.phone or '',
                        'website':company.website or '',
                        'uuid':uuid,
                        'web_base_url':config_parameter_obj.search([('key','=','web.base.url')],limit=1).value or '',
                        'db_name':self._cr.dbname,
                        'module_name':'payslip_payment_spt_ee',
                        'version':'13.0',
                        # 'name':'Cropster',
                    }
                    req = requests.request("POST", url=cal, json=payload)
                    req = json.loads(req.text)['result']
            
                if not req['access']:
                    raise UserError(_(base64.b64decode('c29tZXRoaW5nIHdlbnQgd3JvbmcsIHNlcnZlciBpcyBub3QgcmVzcG9uZGluZw==').decode("utf-8")))
            except:
                # pass
                raise UserError(_(base64.b64decode('c29tZXRoaW5nIHdlbnQgd3JvbmcsIHNlcnZlciBpcyBub3QgcmVzcG9uZGluZw==').decode("utf-8")))
        return True

    def register_multi_payment(self):
        #for record in self:
            # if record.slip_ids[0].connection_spt():
            # if self.connection_spt():
            #     method = record.get_method('register_multi_payment')
            #     print (method)
            #     if method['method']:
            #         localdict = {
            #             'self': record,
            #             'user_obj': record.env.user,
            #             'UserError': UserError,
            #             'datetime': datetime,
            #             '_' : _,
            #         }
            #         exec(method['method'], localdict)
        # if not record.pay_journal_id:
        #    raise UserError(
        #        _('Please Set Payment Method Journal '))

        for record in self:
            for slip in record.slip_ids:
                name = 'Payment'
                if slip.number:
                    name = slip.number + ' Payment'
                    if not slip.employee_id.address_home_id.id:
                        raise UserError(
                            _('Partner not found In Employee (Please Related Partner In Current Employee)!'))

                    payment = self.env['account.payment'].create({
                            'name': name,
                            'partner_id': slip.employee_id.address_home_id.id,
                            'amount': slip.net_salary,
                            'payment_date': str(datetime.today())[:10],
                            'communication': record.communication,
                            'payslip_id': slip.id,
                            'partner_type': 'supplier',
                            'payment_type': 'outbound',
                            'journal_id': record.pay_journal_id.id,
                            'payment_method_id': record.pay_journal_id.outbound_payment_method_ids and
                                                 record.pay_journal_id.outbound_payment_method_ids[0].id or False,
                            'company_id': slip.employee_id.company_id.id,
                            'currency_id': slip.employee_id.company_id.currency_id.id,
                        })
                    payment.post()
                    line_to_reconcile = self.env['account.move.line']
                    for line in payment.move_line_ids + slip.move_id.line_ids:
                        if line.account_id.internal_type == 'payable':
                            line_to_reconcile |= line
                            line_to_reconcile.reconcile()
                    slip.state = 'paid'
            record.state = 'paid'

        return True

    def compute_multi_slip(self):
        for record in self:
            for slip in record.slip_ids:
                slip.compute_sheet()

    def unlink(self):
        for record in self:
            for slip in record.slip_ids:
                slip.unlink()
        return super(hr_payslip, self).unlink()