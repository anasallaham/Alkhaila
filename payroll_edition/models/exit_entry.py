# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, time
from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError


class ExitEntry(models.Model):
    _name = 'exit.entry'
    _rec_name ='employee_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    order_number  = fields.Char(string="Number",readonly=True)
    date = fields.Date(string=" تاريخ")

    employee_id  = fields.Many2one('hr.employee',string="الموظف",required=True)
    amount = fields.Float(string="القيمة كاملة", compute='_compute_amount', store=True,readonly=True)
    count = fields.Integer(string="عدد الاشهر",required=True)
    advanced_salary = fields.One2many('advanced.salary','exit_entry_id', string="السلف")
    journal_id = fields.Many2one('account.journal', string="اليوميه")
    move_id = fields.Many2one('account.move', string="القيد",readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', )

    type_exit_entry = fields.Selection([
        ('single', 'Single'),
        ('multi', 'Multi'),
    ], string='النوع' ,required=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('hr_manager_accept', 'Hr Mananger Accept'),
        ('finance_manager', 'Finance Manager'),
        ('accepted', 'Final Accept'),
        ('cancel', 'Cancelled'),
        ("refuse", "Refuse"),
    ], string='Status' ,default='draft')


    def draft_advanced(self):
        for line in self.advanced_salary:
            line.state  = 'draft'
            line.unlink()
        self.move_id.button_draft()
        lines = self.env['account.move.line'].search([('move_id', '=', self.move_id.id)])
        lines.unlink()
        for adv in self.advanced_salary:
            adv.draft_advanced()
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
            if self.env.user.id == self.hr_employee.department_id.manager_id.user_id.id:
                self.state = "refuse"
            else:
                raise UserError(
                    _(
                        "لا يمكنك الموافقة صلاحية مدير القسم فقط"
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
        return super(ExitEntry, self).create(vals)

    @api.depends('count')
    def _compute_amount(self):
        for me in self:
            me.amount = 100 * me.count


    def action_finance_manager(self):
        if self.env.user.id == self.employee_id.department_id.manager_id.user_id.id:
            return self.write({'state': 'finance_manager'})
        else:
            raise UserError(
                _(
                    "لا يمكنك الموافقة صلاحية مدير القسم فقط"
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
            self.employee_id.type_exit_entry = self.type_exit_entry
            self.to_street()
            if self.count > 2:
                date = self.date
                for r in range(2,self.count):
                    advanced = self.env['advanced.salary'].create({
                        'exit_entry_id': self.id,
                        'hr_employee': self.employee_id.id,
                        'amount': 100,
                        'journal_id': self.journal_id.id,
                        'analytic_account_id': self.analytic_account_id.id,
                        'date': date,
                    })
                    advanced.action_accepted()
                    date = date + relativedelta(months=1)
            return self.write({'state': 'accepted'})
        else:
            raise UserError(
                _(
                    "لا يمكنك الموافقة صلاحية الادارة فقط"
                )

            )


    def action_cancel(self):
        return self.write({'state': 'cancel'})



    def return_movelines(self):
        all_move_vals = []
        for exitentry in self:
            if exitentry.amount  >= 200 :
                amount = 200
            else:
                amount = exitentry.amount

            move_vals = {
                'date': exitentry.date,
                'ref': exitentry.order_number,
                'journal_id': exitentry.journal_id.id,
                'line_ids': [
                    (0, 0, {
                        'name': exitentry.order_number,
                        'debit': amount,
                        'credit': 0.0,
                        'account_id': exitentry.journal_id.default_debit_account_id.id,
                        'partner_id':self.employee_id.address_id.id,
                    }),
                    (0, 0, {
                        'name': exitentry.order_number,
                        'debit': 0.0,
                        'credit': amount,
                        'account_id': exitentry.journal_id.default_credit_account_id.id,
                        'analytic_account_id': exitentry.analytic_account_id.id,
                        'partner_id': self.employee_id.address_id.id,
                    }),
                ],
            }
            all_move_vals.append(move_vals)
            return all_move_vals

    def to_street(self):
        AccountMove = self.env['account.move'].with_context(default_type='entry')
        for rec in self:

            if not self.move_id:
                moves = AccountMove.create(rec.return_movelines())
                moves.post()
                self.move_id = moves.id
            else:
                if self.amount >= 200:
                    amount = 200
                else:
                    amount = self.amount

                self.move_id.button_draft()
                move_line_vals = []
                line1 = (0, 0, {'name': self.order_number, 'debit': amount, 'credit': 0,
                                'account_id': self.journal_id.default_debit_account_id.id,'partner_id':self.employee_id.address_id.id,
                                })
                line2 = (0, 0, {'name': self.order_number, 'debit': 0, 'credit': amount,
                                'account_id': self.journal_id.default_credit_account_id.id,'partner_id':self.employee_id.address_id.id,
                                'analytic_account_id': self.analytic_account_id.id
                                })
                move_line_vals.append(line1)
                move_line_vals.append(line2)
                self.move_id.line_ids = move_line_vals
                self.move_id.post()
        return True

