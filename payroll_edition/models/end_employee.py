# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, time
from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools.float_utils import float_round


class EndEmployee(models.Model):
    _name = 'end.employee'
    _rec_name = 'employee_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    order_number = fields.Char(string="Number", readonly=True)
    date = fields.Date(string=" تاريخ التحرير", required=True)
    employee_id = fields.Many2one('hr.employee', string="الموظف", required=True)
    payslip_id = fields.Many2one('hr.payslip', string="احتساب الرواتب")



    ensbeh_eos = fields.Float(string="نسبة EOS",readonly=True, related='employee_id.ensbeh_eos')
    sum_lastes = fields.Float(string="مكافئة انتهاء الخدمة",readonly=True, compute='_compute_years_in', store=True)
    date_stop  = fields.Date(string="تاريخ الانهاء ",required=True)
    type_end = fields.Selection([('Resignation','مستقيل'),('end_of_contract','End of contract'),('termination2','Termination')],string="انهاء الموظف",required=True)
    date_in  = fields.Date(string="تاريخ التعيين ",related="employee_id.joining_date")
    years_in  = fields.Integer(string="السنوات ", compute='_compute_years_in', store=True)
    months_in  = fields.Integer(string="الاشهر ", compute='_compute_years_in', store=True)
    days_in  = fields.Integer(string="الايام ", compute='_compute_years_in', store=True)
    days_paid_holidays = fields.Float(string="عدد الايام المدفوعة",readonly=True, compute='_compute_years_in', store=True)
    amount_days_paid_holidays = fields.Float(string="قيمة الايام المدفوعة",readonly=True, compute='_compute_years_in', store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('hr_manager_accept', 'Hr Mananger Accept'),
        ('finance_manager', 'Finance Manager'),
        ('director', 'Director'),
        ('accepted', 'Final Accept'),
        ('cancel', 'Cancelled'),
        ("refuse", "Refuse"),
    ], string='Status', default='draft')



    @api.depends('date_stop','employee_id','type_end','date_in')
    def _compute_years_in(self):
        if self.employee_id:
            contract_id = self.env["hr.contract"].search(
                [
                    ("employee_id", "=", self.employee_id.id), ("date_start", "<=", self.date_stop), ("date_end", ">=", self.date_stop),
                ]
            )

            remaining = self.employee_id._get_paid_remaining_leaves()
            self.days_paid_holidays = float_round(remaining.get(self.employee_id.id, 0.0), precision_digits=2)
            difference_in_years = relativedelta(self.date_stop, self.date_in)
            self.years_in = difference_in_years.years
            self.months_in = difference_in_years.months
            self.days_in = difference_in_years.days
            if contract_id:
                self.amount_days_paid_holidays = round(
                    ((contract_id[0].wage + contract_id[0].amount_hous) / 30) * self.days_paid_holidays, 2)
            else:
                self.amount_days_paid_holidays = 0.0

            if self.type_end == 'Resignation':
                try:
                    if self.years_in < 2:
                        self.sum_lastes = 0.0
                    elif self.years_in >= 2 and self.years_in < 5:
                        self.sum_lastes = (33 / 100) * self.years_in * (contract_id[0].wage / 2)
                    elif self.years_in >= 5 and self.years_in < 10:
                        self.sum_lastes = (66 / 100) * self.years_in * (contract_id[0].wage / 2)
                    elif self.years_in >= 10:
                        res1 = 5 * (contract_id[0].wage / 2)
                        res3 = self.years_in - 5 * (contract_id[0].wage)
                        self.sum_lastes = res1 + res3
                except:
                    self.sum_lastes = 0.0

            else:
                try:

                    res3 = self.years_in * (contract_id[0].wage) / 2
                    self.sum_lastes = res3
                except:
                    self.sum_lastes = 0.0

    def draft_advanced(self):
        self.state = "draft"

    def refuse_go(self):
        if self.state == "draft":
            if self.env.user.has_group('hr.group_hr_manager'):
                self.state = "refuse"
            else:
                raise UserError(
                    _(
                        "لا يمكنك الموافقة صلاحية مدير الموارد البشرية فقط"
                    )

                )

        elif self.state == "hr_manager_accept":
            if self.env.user.has_group('account.group_account_manager'):
                self.state = "refuse"
            else:
                raise UserError(
                    _(
                        "لا يمكنك الموافقة صلاحية مسؤول المحاسبة"
                    )

                )

        elif self.state == "finance_manager":
            if self.env.user.has_group('base.group_system'):
                self.state = "refuse"
            else:
                raise UserError(
                    _(
                        "لا يمكنك الموافقة صلاحية الادارة فقط"
                    )

                )

    @api.model
    def create(self, vals):
        if 'order_number' not in vals:
            vals['order_number'] = self.env['ir.sequence'].next_by_code('exit.entry')
        return super(EndEmployee, self).create(vals)


    def action_finance_manager(self):
        if self.env.user.has_group('account.group_account_manager'):

            return self.write({'state': 'finance_manager'})
        else:
            raise UserError(
                _(
                    "لا يمكنك الموافقة صلاحية مسؤول المحاسبة"
                )

            )

    def action_director(self):
        if self.env.user.has_group('base.group_system'):

            return self.write({'state': 'director'})
        else:
            raise UserError(
                _(
                    "لا يمكنك الموافقة صلاحية الادارة فقط"
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
        if self.env.user.has_group('account.group_account_manager'):
            self.employee_id.type_employee_end = self.type_end
            self.employee_id.date_stop = self.date_stop
            self.employee_id.active = False
            return self.write({'state': 'accepted'})

        else:
            raise UserError(
                _(
                    "لا يمكنك الموافقة صلاحية الادارة فقط"
                )
            )

    def action_cancel(self):
        return self.write({'state': 'cancel'})

    def to_street(self):
        AccountMove = self.env['account.move'].with_context(default_type='entry')
        for rec in self:

            if not self.move_id:
                moves = AccountMove.create(rec.return_movelines())
                moves.post()
                self.move_id = moves.id
            else:
                if self.type_exit_entry == "single":
                    if self.amount >= 200:
                        amount = 200
                    else:
                        amount = self.amount
                else:
                    amount = self.amount

                self.move_id.button_draft()
                move_line_vals = []
                line1 = (0, 0, {'name': self.order_number, 'debit': amount, 'credit': 0,
                                'account_id': self.account_id.id, 'partner_id': self.employee_id.address_id.id,
                                'analytic_account_id': self.analytic_account_id.id
                                })
                line2 = (0, 0, {'name': self.order_number, 'debit': 0, 'credit': amount,
                                'account_id': self.journal_id.default_credit_account_id.id,
                                'partner_id': self.employee_id.address_id.id,
                                'analytic_account_id': self.analytic_account_id.id
                                })
                move_line_vals.append(line1)
                move_line_vals.append(line2)
                self.move_id.line_ids = move_line_vals
                self.move_id.post()
        return True
