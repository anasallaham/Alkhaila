# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

class HrLeave(models.Model):
    _inherit = "hr.leave"

    def action_approve(self):
        res = super(HrLeave, self).action_approve()
        if not (self.env.user.id == self.employee_id.parent_id.user_id.id):
            raise UserError(
                _(
                    "صلاحية المسئول المباشر %s فقط"%(self.employee_id.parent_id.user_id.name)
                ))
        return res



    def action_validate(self):
        res = super(HrLeave, self).action_validate()
        if not self.env.user.has_group('hr.group_hr_manager'):
            raise UserError(
                _(
                    "لا يمكنك الموافقة صلاحية مدير الموارد البشرية فقط"
                ))
        return res



