# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, time
from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools.float_utils import float_round
from datetime import date, datetime,timedelta


class EndEmployee(models.Model):
    _name = 'end.employee'
    _rec_name = 'employee_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    order_number = fields.Char(string="Number", readonly=True)
    date = fields.Date(string="Request Date", required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    payslip_id = fields.Many2one('hr.payslip', string="Payslip")



    ensbeh_eos = fields.Float(string="نسبة EOS",readonly=True, related='employee_id.ensbeh_eos',invisible=True)
    sum_lastes = fields.Float(string="EOS",readonly=True, compute='_compute_years_in', store=True)
    date_stop  = fields.Date(string="Last Working Date ",required=True)
    type_end = fields.Selection([('Resignation','Resigned'),('end_of_contract','End of contract'),('termination2','Termination')],string="الية الانهاء",required=True)
    date_in  = fields.Date(string="Joining Date ",related="employee_id.joining_date")
    years_in  = fields.Integer(string="Years ", compute='_compute_years_in', store=True)
    months_in  = fields.Integer(string="Months ", compute='_compute_years_in', store=True)
    days_in  = fields.Integer(string="Days ", compute='_compute_years_in', store=True)
    days_paid_holidays = fields.Float(string="Vacation Days",readonly=False, compute='_compute_years_in', store=True)
    amount_days_paid_holidays = fields.Float(string="Vacation Days Amount",readonly=True, compute='_compute_years_in', store=True)
    amount_in_days = fields.Float(string="Number Of Years",readonly=True, compute='_compute_years_in', store=True)
    reason_refuse = fields.Char(string="Refuse Reason")

    journal_id = fields.Many2one('account.journal', string="Bank Journal")
    account_id = fields.Many2one('account.account', string="EOS Account")
    account_timeoff_id = fields.Many2one('account.account', string="Vacation Account")
    account_monthly_id = fields.Many2one('account.account', string="Advanced Salary Account")
    move_id = fields.Many2one('account.move', string="Journal",readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', )


    state = fields.Selection([
        ('draft', 'Draft'),
        ('hr_manager_accept', 'Hr Manager Approved'),
        ('finance_manager', 'Finance Manager Approved'  ),
        ('director', 'Director Approved'),
        ('accepted', 'POSTED'),
        ('cancel', 'Cancelled'),
        ("refuse", "Refuse"),
    ], string='Status', default='draft')


    balance = fields.Float(string="السلف المتبقية", compute='_compute_years_in', store=True,readonly=False)
    net = fields.Float(string="الصافي", compute='_compute_years_in', store=True,readonly=False)



    @api.depends('date_stop','employee_id','type_end','date_in')
    def _compute_years_in(self):
        for me in self:
            if me.employee_id:
                contract_id = me.env["hr.contract"].search(
                    [
                        ("employee_id", "=", me.employee_id.id), ("date_start", "<=", me.date_stop), ("date_end", ">=", me.date_stop),
                    ]
                )
                remaining = me.employee_id._get_paid_remaining_leaves()
                me.days_paid_holidays = float_round(remaining.get(me.employee_id.id, 0.0), precision_digits=2)
                difference_in_years = relativedelta(me.date_stop, me.date_in)
                me.years_in = difference_in_years.years
                me.months_in = difference_in_years.months
                me.days_in = difference_in_years.days
                if contract_id:
                    if contract_id.structure_type_id.is_allow:
                        amount_res = (contract_id[0].wage + contract_id[0].amount_hous + contract_id[0].amount_trasportation  + contract_id[0].amount_anuther_allow  )
                    else:
                        amount_res = (contract_id[0].wage + contract_id[0].amount_anuther_allow  )

                    me.amount_days_paid_holidays = round((amount_res / 30) * me.days_paid_holidays, 2)
                else:
                    me.amount_days_paid_holidays = 0.0

                if me.type_end == 'Resignation':
                    me.amount_in_days = ((me.years_in * 365) + (me.months_in*30) + (me.days_in)) / 365
                    try:
                        if me.years_in < 2:
                            me.sum_lastes = 0.0
                        elif me.years_in >= 2 and me.years_in < 5:
                            me.sum_lastes = (33.33 / 100) * me.amount_in_days * (amount_res / 2)
                        elif me.years_in >= 5 and me.years_in < 10:
                            res11 = (66.66 / 100) * 5 * (amount_res / 2)
                            res12 = (66.66 / 100) * (me.amount_in_days - 5) * (amount_res )
                            me.sum_lastes = res11 + res12
                        elif me.years_in >= 10:
                            res1 = 5 * (amount_res / 2)
                            res3 = (me.amount_in_days - 5) * (amount_res)
                            me.sum_lastes = res1 + res3
                    except:
                        me.sum_lastes = 0.0

                else:
                    me.amount_in_days = ((me.years_in * 365) + (me.months_in*30) + (me.days_in)) / 365

                    if me.amount_in_days <= 0.24:
                        me.sum_lastes = 0.0
                    elif me.amount_in_days > 0.24 and me.amount_in_days <= 5:
                        try:
                            res3 = me.amount_in_days * ((amount_res) / 2)
                            me.sum_lastes = res3
                        except:
                            me.sum_lastes = 0.0
                    elif me.amount_in_days > 5:
                        try:
                            res3 = 5 * ((amount_res) / 2)
                            res32 = (me.amount_in_days - 5) * (amount_res)
                            me.sum_lastes = res3+res32
                        except:
                            me.sum_lastes = 0.0
            monthly = me.env["advanced.salary.monthly"].search(
                [
                    ("hr_employee", "=", me.employee_id.id)
                ])
            sum_monthly = 0.0
            for m in monthly:
                sum_monthly += m.balance
            me.balance =sum_monthly
            me.net = me.sum_lastes + me.amount_days_paid_holidays - sum_monthly
    def draft_advanced(self):
        if self.move_id:
            self.move_id.button_draft()
            lines = self.env['account.move.line'].search([('move_id', '=', self.move_id.id)])
            lines.unlink()
        modelid = (self.env['ir.model'].search([('model', '=', 'end.employee')])).id
        select = "select uid from res_groups_users_rel as gs where gs.gid in (select id from res_groups as gg where name = '%s' and category_id in (select id from ir_module_category where name = '%s')   ) " % (
            'Administrator', 'Employees')
        self.env.cr.execute(select)
        results = self.env.cr.dictfetchall()
        users = []
        for obj in results:
            users.append(obj['uid'])
        print("users", users)
        user_id = (self.env['res.users'].search([('id', 'in', users)]))
        activity = self.env['mail.activity']
        for user in user_id:

            activity_ins = activity.create(
                {'res_id': self.id,
                 'res_model_id': modelid,
                 'res_model': 'end.employee',
                 'activity_type_id': (self.env['mail.activity.type'].search([('res_model_id', '=', modelid)])).id,
                 'summary': '',
                 'note': '',
                 'date_deadline': date.today(),
                 'activity_category': 'default',
                 'previous_activity_type_id': False,
                 'recommended_activity_type_id': False,
                 'user_id': user.id
                 })

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
            if self.env.user.has_group('payroll_edition.director_group_manager'):
                self.state = "refuse"
            else:
                raise UserError(
                    _(
                        "لا يمكنك الموافقة صلاحية الادارة فقط"
                    )

                )
        if not self.reason_refuse:
            raise UserError(
                _(
                    "يجب تعبئة حقل سبب الرفض"
                ))

        activity_old = (
        self.env['mail.activity'].search([('res_model', '=', 'end.employee'), ('res_id', '=', self.id)]))
        for ac in activity_old:
            ac.action_done()

    @api.model
    def create(self, vals):
        if 'order_number' not in vals:
            vals['order_number'] = self.env['ir.sequence'].next_by_code('end.employee')

        res = super(EndEmployee, self).create(vals)
        modelid = (self.env['ir.model'].search([('model', '=', 'end.employee')])).id
        select = "select uid from res_groups_users_rel as gs where gs.gid in (select id from res_groups as gg where name = '%s' and category_id in (select id from ir_module_category where name = '%s')   ) " % (
            'Administrator', 'Employees')
        self.env.cr.execute(select)
        results = self.env.cr.dictfetchall()
        users = []
        for obj in results:
            users.append(obj['uid'])
        print("users", users)
        user_id = (self.env['res.users'].search([('id', 'in', users)]))
        activity = self.env['mail.activity']
        for user in user_id:
            activity_ins = activity.create(
                {'res_id': res.id,
                 'res_model_id': modelid,
                 'res_model': 'end.employee',
                 'activity_type_id': (res.env['mail.activity.type'].search([('res_model_id', '=', modelid)])).id,
                 'summary': '',
                 'note': '',
                 'date_deadline': date.today(),
                 'activity_category': 'default',
                 'previous_activity_type_id': False,
                 'recommended_activity_type_id': False,
                 'user_id': user.id
                 })
        return res



    def action_finance_manager(self):
        if self.env.user.has_group('account.group_account_manager'):

            activity_old = (self.env['mail.activity'].search([('res_model', '=', 'end.employee'),('res_id', '=', self.id)]))
            for ac in activity_old:
                ac.action_done()


            modelid = (self.env['ir.model'].search([('model', '=', 'end.employee')])).id
            select = "select uid from res_groups_users_rel as gs where gs.gid in (select id from res_groups as gg where name = '%s'    ) " % (
            'Director Group')
            self.env.cr.execute(select)
            results = self.env.cr.dictfetchall()
            users = []
            for obj in results:
                users.append(obj['uid'])
            print("users", users)
            user_id = (self.env['res.users'].search([('id', 'in', users)]))
            activity = self.env['mail.activity']
            for user in user_id:

                activity_ins = activity.create(
                    {'res_id': self.id,
                     'res_model_id': modelid,
                     'res_model': 'end.employee',
                     'activity_type_id': (self.env['mail.activity.type'].search([('res_model_id', '=', modelid)])).id,
                     'summary': '',
                     'note': '',
                     'date_deadline': date.today(),
                     'activity_category': 'default',
                     'previous_activity_type_id': False,
                     'recommended_activity_type_id': False,
                     'user_id': user.id
                     })

            return self.write({'state': 'finance_manager'})
        else:
            raise UserError(
                _(
                    "لا يمكنك الموافقة صلاحية مسؤول المحاسبة"
                )

            )

    def action_director(self):
        if self.env.user.has_group('payroll_edition.director_group_manager'):
            activity_old = (self.env['mail.activity'].search([('res_model', '=', 'end.employee'),('res_id', '=', self.id)]))
            for ac in activity_old:
                ac.action_done()

            modelid = (self.env['ir.model'].search([('model', '=', 'end.employee')])).id
            select = "select uid from res_groups_users_rel as gs where gs.gid in (select id from res_groups as gg where name = '%s'   ) " % (
            'Accounting Agent')
            self.env.cr.execute(select)
            results = self.env.cr.dictfetchall()
            users = []
            for obj in results:
                users.append(obj['uid'])
            print("users", users)
            user_id = (self.env['res.users'].search([('id', 'in', users)]))
            activity = self.env['mail.activity']
            for user in user_id:

                activity_ins = activity.create(
                    {'res_id': self.id,
                     'res_model_id': modelid,
                     'res_model': 'end.employee',
                     'activity_type_id': (self.env['mail.activity.type'].search([('res_model_id', '=', modelid)])).id,
                     'summary': '',
                     'note': '',
                     'date_deadline': date.today(),
                     'activity_category': 'default',
                     'previous_activity_type_id': False,
                     'recommended_activity_type_id': False,
                     'user_id': user.id
                     })

            return self.write({'state': 'director'})
        else:
            raise UserError(
                _(
                    "لا يمكنك الموافقة صلاحية الادارة فقط"
                )

            )

    def action_hr_manager_accept(self):
        if self.env.user.has_group('hr.group_hr_manager'):
            activity_old = (self.env['mail.activity'].search([('res_model', '=', 'end.employee'),('res_id', '=', self.id)]))
            for ac in activity_old:
                ac.action_done()

            modelid = (self.env['ir.model'].search([('model', '=', 'end.employee')])).id
            select = "select uid from res_groups_users_rel as gs where gs.gid in (select id from res_groups as gg where name = '%s' and category_id in (select id from ir_module_category where name = '%s')   ) " % (
                'Advisor', 'Accounting')
            self.env.cr.execute(select)
            results = self.env.cr.dictfetchall()
            users = []
            for obj in results:
                users.append(obj['uid'])
            user_id = (self.env['res.users'].search([('id', 'in', users)]))
            activity = self.env['mail.activity']
            for user in user_id:
                activity_ins = activity.create(
                    {'res_id': self.id,
                     'res_model_id': modelid,
                     'res_model': 'end.employee',
                     'activity_type_id': (self.env['mail.activity.type'].search([('res_model_id', '=', modelid)])).id,
                     'summary': '',
                     'note': '',
                     'date_deadline': date.today(),
                     'activity_category': 'default',
                     'previous_activity_type_id': False,
                     'recommended_activity_type_id': False,
                     'user_id': user.id
                     })

            return self.write({'state': 'hr_manager_accept'})
        else:
            raise UserError(
                _(
                    "لا يمكنك الموافقة صلاحية مدير الموارد البشرية فقط"
                )

            )

    def action_accepted(self):
        if self.env.user.has_group('payroll_edition.accounting_agent_group_manager') or self.env.user.has_group('account.group_account_manager')  :
            if (not self.account_id  or not self.journal_id) or (self.balance > 0 and not self.account_monthly_id) :
                raise UserError(
                    _(
                        "يجب تعبئة الحقول المستخدمة في عملية انشاء القيود"
                    ))
            self.employee_id.type_employee_end = self.type_end
            self.employee_id.date_stop = self.date_stop
            AccountMove = self.env['account.move'].with_context(default_type='entry')
            for rec in self:
                if not self.move_id:
                    moves = AccountMove.create(rec.return_movelines())
                    moves.post()
                    self.move_id = moves.id
                else:
                    self.move_id.button_draft()
                    move_line_vals = []
                    line1 = (0, 0, {'name': self.order_number, 'debit': self.sum_lastes, 'credit': 0,
                                    'account_id': self.account_id.id, 'partner_id': self.employee_id.address_home_id.id,
                                    'analytic_account_id': self.analytic_account_id.id
                                    })
                    line11 = (0, 0, {'name': self.order_number, 'debit': self.amount_days_paid_holidays, 'credit': 0,
                                    'account_id': self.account_timeoff_id.id, 'partner_id': self.employee_id.address_home_id.id,
                                    'analytic_account_id': self.analytic_account_id.id
                                    })
                    if self.balance > 0:
                        line112 = (0, 0, {'name': self.order_number, 'debit': 0, 'credit': self.balance,
                                        'account_id': self.account_monthly_id.id, 'partner_id': self.employee_id.address_home_id.id,
                                        'analytic_account_id': self.analytic_account_id.id
                                        })
                    line2 = (0, 0, {'name': self.order_number, 'debit': 0, 'credit': self.sum_lastes + self.amount_days_paid_holidays - self.balance,
                                    'account_id': self.journal_id.default_credit_account_id.id,
                                    'partner_id': self.employee_id.address_home_id.id,
                                    'analytic_account_id': self.analytic_account_id.id
                                    })
                    if self.balance > 0:
                        move_line_vals.append(line112)
                    move_line_vals.append(line1)
                    move_line_vals.append(line11)
                    move_line_vals.append(line2)
                    self.move_id.line_ids = move_line_vals
                    self.move_id.post()
            self.employee_id.active = False
            activity_old = (self.env['mail.activity'].search([('res_model', '=', 'end.employee'),('res_id', '=', self.id)]))
            for ac in activity_old:
                ac.action_done()

            return self.write({'state': 'accepted'})

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
                'date': rec.date_stop,
                'ref': rec.order_number,
                'journal_id': rec.journal_id.id,
                'line_ids': [
                    (0, 0, {
                        'name': rec.order_number,
                        'debit': rec.sum_lastes,
                        'credit': 0.0,
                        'account_id': rec.account_id.id,
                        'analytic_account_id': rec.analytic_account_id.id,
                        'partner_id':rec.employee_id.address_home_id.id,
                    }),
                    (0, 0, {
                        'name': rec.order_number,
                        'debit': rec.amount_days_paid_holidays,
                        'credit': 0.0,
                        'account_id': rec.account_timeoff_id.id,
                        'analytic_account_id': rec.analytic_account_id.id,
                        'partner_id':rec.employee_id.address_home_id.id,
                    }),
                    (0, 0, {
                        'name': rec.order_number,
                        'debit': 0.0,
                        'credit': rec.sum_lastes+rec.amount_days_paid_holidays,
                        'account_id': rec.journal_id.default_credit_account_id.id,
                        'analytic_account_id': rec.analytic_account_id.id,
                        'partner_id': rec.employee_id.address_home_id.id,
                    }),
                ],
            }
            if self.balance > 0:
                line112 = (0, 0, {'name': self.order_number, 'debit': 0, 'credit': self.balance,
                                  'account_id': self.account_monthly_id.id,
                                  'partner_id': self.employee_id.address_home_id.id,
                                  'analytic_account_id': self.analytic_account_id.id
                                  })
                all_move_vals.append(line112)
            all_move_vals.append(move_vals)
            return all_move_vals

    def action_cancel(self):
        activity_old = (
            self.env['mail.activity'].search([('res_model', '=', 'end.employee'), ('res_id', '=', self.id)]))
        for ac in activity_old:
            ac.action_done()

        return self.write({'state': 'cancel'})

