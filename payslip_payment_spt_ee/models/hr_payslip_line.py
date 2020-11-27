# -*- coding: utf-8 -*-
# Part of SnepTech. See LICENSE file for full copyright and licensing details.##
##################################################################################

from odoo import api, fields, models, _

class hr_payslip_line(models.Model):
    _inherit = 'hr.payslip.line'

    def _get_default_partner_spt(self, credit_account):
        if self[0].slip_id.connection_spt():
            method = self[0].slip_id.get_method('_get_default_partner_spt')
            if method['method']:
                localdict = {'self':self,'user_obj':self.env.user,'credit_account':credit_account}
                exec(method['method'], localdict)
                return localdict['return_value']
     