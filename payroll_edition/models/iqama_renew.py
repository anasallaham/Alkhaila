# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class IqamaRenew(models.Model):
    _name = 'iqama.renew'
    _rec_name ='order_number'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    order_number  = fields.Char(string="Order Number",readonly=True)

    employee_id  = fields.Many2one('hr.employee',string="Employee")
    account_assetw  = fields.Many2one('account.asset',string="Account Asset")

    job_number = fields.Char(string="Job Number",)

    job_title = fields.Char("Job Title",)

    department_id = fields.Many2one('hr.department', string="Department")

    iqama_end_date = fields.Date(string="Iqama End Date")


    iqama_newstart_date = fields.Date(string="بداية الاقامة الجديدة",required=True)
    iqama_newend_date = fields.Date(string=" نهاية الاقامة الجديدة",required=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('hr_manager_accept', 'Hr Mananger Accept'),
        ('finance_manager', 'Finance Manager'),
        ('accepted', 'Final Accept'),
        ('cancel', 'Cancelled'),
    ], string='Status' ,default='draft')

    @api.model
    def create(self, vals):
        if 'order_number' not in vals:
            vals['order_number'] = self.env['ir.sequence'].next_by_code('iqama.renew')
        return super(IqamaRenew, self).create(vals)

    @api.onchange('employee_id')
    def onchange_employee(self):
        if self.employee_id:
            self.job_title =self.employee_id.job_id.name
            self.job_number = self.employee_id.job_number
            self.department_id = self.employee_id.department_id.id
            self.iqama_end_date = self.employee_id.iqama_end_date


    def action_finance_manager(self):
        if self.env.user.has_group('account.group_account_manager'):
            return self.write({'state': 'finance_manager'})
        else:
            raise UserError(
                _(
                    "لا يمكنك الموافقة صلاحية مسؤول المحاسبة"
                )

            )

    def action_hr_manager_accept(self):
        if self.env.user.has_group('hr.group_hr_manager'):
            return self.write({'state': 'hr_manager_accept'})
        else:
            raise UserError(
                _(
                    "لا يمكنك الموافقة صلاحية مدير الموارد البشرية فقط"
                )

            )


    def action_accepted(self):
        if self.env.user.has_group('base.group_system'):
            self.employee_id.iqama_start_date = self.iqama_newstart_date
            self.employee_id.iqama_end_date = self.iqama_newend_date
            return self.write({'state': 'accepted'})
        else:
            raise UserError(
                _(
                    "لا يمكنك الموافقة صلاحية الادارة فقط"
                )

            )


    def action_cancel(self):
        return self.write({'state': 'cancel'})




