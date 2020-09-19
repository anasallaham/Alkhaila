# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from odoo import api, fields, models, tools, _
import math

class AdvancedSalaryMonthly(models.Model):
    _name = "advanced.salary.monthly"
    _rec_name = "order_number"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    order_number  = fields.Char(string="Number",readonly=True)
    note = fields.Char(string="الوصف",required=True)
    advanced_salary = fields.One2many('advanced.salary','advanced_salary_monthly', string="السلف")
    hr_employee = fields.Many2one('hr.employee', string="الموظف",required=True)
    date = fields.Date(string=" تاريخ",required=True)
    count_cut = fields.Integer(string="عدد الاقساط")
    amount = fields.Float(string="القيمة الكلية",required=True)
    journal_id = fields.Many2one('account.journal', string="اليوميه")
    account_id = fields.Many2one('account.account', string="الحساب")
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', )

    move_id = fields.Many2one('account.move', string="القيد",readonly=True)
    holiday_id = fields.Many2one('hr.leave',string="مرتبط باجازة")
    contract_id = fields.Many2one('hr.contract',string="العقد")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('hr_manager_accept', 'Hr Mananger Accept'),
        ('finance_manager', 'Finance Manager'),
        ('director', 'Director'),
        ('accepted', 'Final Accept'),
        ("refuse", "Refuse"),
    ],
        string="State",
        default="draft",
    )

    @api.model
    def create(self, vals):
        if 'order_number' not in vals:
            vals['order_number'] = self.env['ir.sequence'].next_by_code('advanced.salary.monthly')
        return super(AdvancedSalaryMonthly, self).create(vals)


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
    def action_director(self):
        if self.env.user.has_group('base.group_system'):

            return self.write({'state': 'director'})
        else:
            raise UserError(
                _(
                    "لا يمكنك الموافقة صلاحية الادارة فقط"
                )

            )

    def action_accepted(self):
        if self.env.user.has_group('account.group_account_manager'):
            if self.holiday_id:
                date = self.holiday_id.request_date_from
            else:
                date = self.date
            if not self.contract_id:
                amount_monthly = round(self.amount / self.count_cut, 3)
                for c in range(1, self.count_cut+1):
                    advanced = self.env['advanced.salary'].create({
                        'advanced_salary_monthly': self.id,
                        'hr_employee': self.hr_employee.id,
                        'amount': amount_monthly,
                        'date': date,
                    })
                    advanced.state = 'accepted'
                    date = date + relativedelta(months=1)
            else:
                salary = self.contract_id.wage
                salary_per_day = round(salary/30,2)
                holidays = self.holiday_id.number_of_days
                holidays_per_30 = math.floor(holidays/30)
                amount_holidays = holidays * salary_per_day
                current_amount = amount_holidays
                if  amount_holidays <= salary:
                    advanced = self.env['advanced.salary'].create({
                        'advanced_salary_monthly': self.id,
                        'hr_employee': self.hr_employee.id,
                        'amount': amount_holidays,
                        'date': date,
                    })
                    advanced.state = 'accepted'

                elif amount_holidays > salary:
                    for num in range(0, holidays_per_30+1):
                        if current_amount >= salary:
                            advanced = self.env['advanced.salary'].create({
                                'advanced_salary_monthly': self.id,
                                'hr_employee': self.hr_employee.id,
                                'amount': salary,
                                'date': date,
                            })
                            advanced.state = 'accepted'

                            current_amount = current_amount - salary
                        elif current_amount < salary and current_amount >= 0.0:
                            advanced = self.env['advanced.salary'].create({
                                'advanced_salary_monthly': self.id,
                                'hr_employee': self.hr_employee.id,
                                'amount': current_amount,
                                'date': date,
                            })
                            advanced.state = 'accepted'
                            current_amount = current_amount - salary
                        date = date + relativedelta(months=1)


            AccountMove = self.env['account.move'].with_context(default_type='entry')
            if not self.move_id:
                moves = AccountMove.create(self.return_movelines())
                moves.post()
                self.move_id = moves.id
            else:
                self.move_id.button_draft()
                move_line_vals = []
                line1 = (0, 0, {'name': self.order_number, 'debit': self.amount, 'credit': 0,
                                'account_id': self.account_id.id,'partner_id':self.hr_employee.address_id.id,
                                'analytic_account_id': self.analytic_account_id.id
                                })
                line2 = (0, 0, {'name': self.order_number, 'debit': 0, 'credit': self.amount,
                                'account_id': self.journal_id.default_credit_account_id.id,'partner_id':self.hr_employee.address_id.id,
                                'analytic_account_id': self.analytic_account_id.id
                                })
                move_line_vals.append(line1)
                move_line_vals.append(line2)
                self.move_id.line_ids = move_line_vals
                self.move_id.post()


            self.state = "accepted"







        else:
            raise UserError(
                _(
                    "لا يمكنك الموافقة صلاحية مسؤول المحاسبة"
                )

            )

    def return_movelines(self):
        all_move_vals = []
        for rec in self:

            move_vals = {
                'date': rec.date,
                'ref': rec.order_number,
                'journal_id': rec.journal_id.id,
                'line_ids': [
                    (0, 0, {
                        'name': rec.order_number,
                        'debit': rec.amount,
                        'credit': 0.0,
                        'account_id': rec.account_id.id,
                        'analytic_account_id': rec.analytic_account_id.id,
                        'partner_id':rec.hr_employee.address_id.id,
                    }),
                    (0, 0, {
                        'name': rec.order_number,
                        'debit': 0.0,
                        'credit': rec.amount,
                        'account_id': rec.journal_id.default_credit_account_id.id,
                        'analytic_account_id': rec.analytic_account_id.id,
                        'partner_id': rec.hr_employee.address_id.id,
                    }),
                ],
            }
            all_move_vals.append(move_vals)
            return all_move_vals


    def action_cancel(self):
        return self.write({'state': 'cancel'})


    def draft_advanced(self):
        for line in self.advanced_salary:
            line.draft_advanced()
            line.unlink()
        self.state = "draft"

    def unlink(self):
        for me in self:
            if me.state != "draft":
                raise UserError(
                    _(
                        "لا يمكنك الحذف لان الحالة ليست مسودة"
                    )

                )
            return super(AdvancedSalaryMonthly, me).unlink()


class AdvancedSalary(models.Model):
    _name = "advanced.salary"
    _rec_name = "order_number"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    order_number  = fields.Char(string="Number",readonly=True)
    note = fields.Char(string="الوصف",required=True)

    advanced_salary_monthly = fields.Many2one('advanced.salary.monthly', string="الموظف")
    exit_entry_id = fields.Many2one('exit.entry', string="exit entry")
    hr_employee = fields.Many2one('hr.employee', string="الموظف",required=True)
    date = fields.Date(string="التاريخ",required=True)
    amount = fields.Float(string="قيمة السلفة",required=True)

    journal_id = fields.Many2one('account.journal', string="اليوميه")
    account_id = fields.Many2one('account.account', string="الحساب")
    move_id = fields.Many2one('account.move', string="القيد",readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('hr_manager_accept', 'Hr Mananger Accept'),
        ('finance_manager', 'Finance Manager'),
        ('director', 'Director'),
        ('accepted', 'Final Accept'),
        ("refuse", "Refuse"),
    ],
        string="State",
        default="draft",
    )




    def return_movelines(self):
        all_move_vals = []
        for rec in self:

            move_vals = {
                'date': rec.date,
                'ref': rec.order_number,
                'journal_id': rec.journal_id.id,
                'line_ids': [
                    (0, 0, {
                        'name': rec.order_number,
                        'debit': rec.amount,
                        'credit': 0.0,
                        'account_id': rec.account_id.id,
                        'analytic_account_id': rec.analytic_account_id.id,
                        'partner_id':rec.hr_employee.address_id.id,
                    }),
                    (0, 0, {
                        'name': rec.order_number,
                        'debit': 0.0,
                        'credit': rec.amount,
                        'account_id': rec.journal_id.default_credit_account_id.id,
                        'analytic_account_id': rec.analytic_account_id.id,
                        'partner_id': rec.hr_employee.address_id.id,
                    }),
                ],
            }
            all_move_vals.append(move_vals)
            return all_move_vals


    @api.model
    def create(self, vals):
        if 'order_number' not in vals:
            vals['order_number'] = self.env['ir.sequence'].next_by_code('advanced.salary')
        return super(AdvancedSalary, self).create(vals)

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
            AccountMove = self.env['account.move'].with_context(default_type='entry')
            if not self.move_id:
                moves = AccountMove.create(self.return_movelines())
                moves.post()
                self.move_id = moves.id
            else:
                self.move_id.button_draft()
                move_line_vals = []
                line1 = (0, 0, {'name': self.order_number, 'debit': self.amount, 'credit': 0,
                                'account_id': self.account_id.id,'partner_id':self.hr_employee.address_id.id,
                                'analytic_account_id': self.analytic_account_id.id
                                })
                line2 = (0, 0, {'name': self.order_number, 'debit': 0, 'credit': self.amount,
                                'account_id': self.journal_id.default_credit_account_id.id,'partner_id':self.hr_employee.address_id.id,
                                'analytic_account_id': self.analytic_account_id.id
                                })
                move_line_vals.append(line1)
                move_line_vals.append(line2)
                self.move_id.line_ids = move_line_vals
                self.move_id.post()

            self.state = "accepted"
        else:
            raise UserError(
                _(
                    "لا يمكنك الموافقة صلاحية مسؤول المحاسبة"
                )

            )


    def action_cancel(self):
        return self.write({'state': 'cancel'})


    def draft_advanced(self):
        self.move_id.button_draft()
        lines = self.env['account.move.line'].search([('move_id', '=', self.move_id.id)])
        lines.unlink()
        self.state = "draft"

    def unlink(self):
        for me in self:
            if me.state != "draft":
                raise UserError(
                    _(
                        "لا يمكنك الحذف لان الحالة ليست مسودة"
                    )

                )
            return super(AdvancedSalary, me).unlink()




class PenaltyName(models.Model):
    _name = "penalty.name"
    name = fields.Char(string="اسم العقوية",required=True)
    account_debit_id = fields.Many2one('account.account', string="حساب المدين",required=True)
    account_credit_id = fields.Many2one('account.account', string="حساب الدائن",required=True)

    def unlink(self):
        for me in self:
            penalty_ids = self.env["penalty.salary"].search(
                [
                    ("penalty_name", "=", me.id),
                ]
            )
            if penalty_ids:
                raise UserError(
                    _(
                        "لا يمكنك الحذف لانه تم انشاء عقوبة مرتبطه"
                    )

                )
            return super(PenaltySalary, me).unlink()

class PenaltySalary(models.Model):
    _name = "penalty.salary"
    _rec_name = "order_number"
    _inherit = ['mail.thread', 'mail.activity.mixin']


    order_number  = fields.Char(string="Number",readonly=True)
    note = fields.Char(string="الوصف",required=True)

    penalty_name = fields.Many2one('penalty.name', string="العقوبة",required=True)
    hr_employee = fields.Many2one('hr.employee', string="الموظف",required=True)
    date = fields.Date(string="التاريخ",required=True)
    amount = fields.Float(string="القيمة",required=True)

    journal_id = fields.Many2one('account.journal', string="يومية القيود")
    account_debit_id = fields.Many2one('account.account', string="حساب المدين")
    account_credit_id = fields.Many2one('account.account', string="حساب الدائن")
    move_id = fields.Many2one('account.move', string="القيد",readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('hr_manager_accept', 'Hr Mananger Accept'),
        ('finance_manager', 'Finance Manager'),
        ('director', 'Director'),
        ('accepted', 'Final Accept'),
        ("refuse", "Refuse"),
    ],
        string="State",
        default="draft",
    )



    def return_movelines(self):
        all_move_vals = []
        for rec in self:

            move_vals = {
                'date': rec.date,
                'ref': rec.order_number,
                'journal_id': rec.journal_id.id,
                'line_ids': [
                    (0, 0, {
                        'name': rec.order_number,
                        'debit': rec.amount,
                        'credit': 0.0,
                        'account_id': rec.account_debit_id.id,
                        'analytic_account_id': rec.analytic_account_id.id,
                        'partner_id':rec.hr_employee.address_id.id,
                    }),
                    (0, 0, {
                        'name': rec.order_number,
                        'debit': 0.0,
                        'credit': rec.amount,
                        'account_id': rec.account_credit_id.id,
                        'analytic_account_id': rec.analytic_account_id.id,
                        'partner_id': rec.hr_employee.address_id.id,
                    }),
                ],
            }
            all_move_vals.append(move_vals)
            return all_move_vals

    @api.model
    def create(self, vals):
        if 'order_number' not in vals:
            vals['order_number'] = self.env['ir.sequence'].next_by_code('penalty.salary')
        return super(PenaltySalary, self).create(vals)

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

    def action_director(self):
        if self.env.user.has_group('base.group_system'):
            self.account_credit_id = self.penalty_name.account_credit_id.id
            self.account_debit_id = self.penalty_name.account_debit_id.id
            return self.write({'state': 'director'})
        else:
            raise UserError(
                _(
                    "لا يمكنك الموافقة صلاحية الادارة فقط"
                )

            )

    def action_accepted(self):
        if self.env.user.has_group('account.group_account_manager'):
            AccountMove = self.env['account.move'].with_context(default_type='entry')
            if not self.move_id:
                moves = AccountMove.create(self.return_movelines())
                moves.post()
                self.move_id = moves.id
            else:
                self.move_id.button_draft()
                move_line_vals = []
                line1 = (0, 0, {'name': self.order_number, 'debit': self.amount, 'credit': 0,
                                'account_id': self.account_debit_id.id,'partner_id':self.hr_employee.address_id.id,
                                'analytic_account_id': self.analytic_account_id.id
                                })
                line2 = (0, 0, {'name': self.order_number, 'debit': 0, 'credit': self.amount,
                                'account_id': self.account_credit_id.id,'partner_id':self.hr_employee.address_id.id,
                                'analytic_account_id': self.analytic_account_id.id
                                })
                move_line_vals.append(line1)
                move_line_vals.append(line2)
                self.move_id.line_ids = move_line_vals
                self.move_id.post()

            self.state = "accepted"
        else:
            raise UserError(
                _(
                    "لا يمكنك الموافقة صلاحية مسؤول المحاسبة"
                )

            )

    def post_advanced(self):
        self.state = "accepted"
    def draft_advanced(self):
        self.move_id.button_draft()
        lines = self.env['account.move.line'].search([('move_id', '=', self.move_id.id)])
        lines.unlink()
        self.state = "draft"


    def unlink(self):
        for me in self:
            if me.state != "draft":
                raise UserError(
                    _(
                        "لا يمكنك الحذف لان الحالة ليست مسودة"
                    )

                )
            return super(PenaltySalary, me).unlink()

