# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date, datetime,timedelta


class IqamaRenew(models.Model):
    _name = 'iqama.renew'
    _rec_name ='order_number'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    order_number  = fields.Char(string="Order Number",readonly=True)
    employee_id  = fields.Many2one('hr.employee',string="Employee")
    job_number = fields.Char(string="Job Number",)
    job_title = fields.Char("Job Title",)
    department_id = fields.Many2one('hr.department', string="Department")
    iqama_end_date = fields.Date(string="Old Iqama End Date " )
    iqama_newstart_date = fields.Date(string="بداية الاقامة الجديدة",required=True)
    iqama_newend_date = fields.Date(string=" نهاية الاقامة الجديدة",required=True)
    reason_refuse = fields.Char(string="سبب الرفض")


    deferred_expense_models  = fields.Many2one('account.asset',string="Deferred Expense Models")
    deferred_expense  = fields.Many2one('account.asset',string="Deferred Expense")


    date_payed = fields.Date(string="تاريخ الدفع")
    amount = fields.Float(string="القيمة",required=True)
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
        ('cancel', 'Cancelled'),
        ("refuse", "Refuse"),
    ], string='Status' ,default='draft')


    @api.model
    def create_activity_type(self):
        modelid = (self.env['ir.model'].search([('model', '=', 'iqama.renew')])).id
        advanced_salary = (self.env['ir.model'].search([('model', '=', 'advanced.salary')])).id
        advanced_salary_monthly = (self.env['ir.model'].search([('model', '=', 'advanced.salary.monthly')])).id
        penalty_salary = (self.env['ir.model'].search([('model', '=', 'penalty.salary')])).id
        exit_entry = (self.env['ir.model'].search([('model', '=', 'exit.entry')])).id
        end_employee = (self.env['ir.model'].search([('model', '=', 'end.employee')])).id

        activity = self.env['mail.activity.type']
        activity.create(
            {
             'name': 'Iqama Renew',
             'res_model_id': modelid,
             'delay_unit': 'days',
             'delay_from': 'previous_activity',
             })
        activity.create(
            {
                'name': 'Advanced Salary ',
             'res_model_id': advanced_salary,
             'delay_unit': 'days',
             'delay_from': 'previous_activity',
             })
        activity.create(
            {
                'name': 'Advanced Salary monthly',
             'res_model_id': advanced_salary_monthly,
             'delay_unit': 'days',
             'delay_from': 'previous_activity',
             })
        activity.create(
            {
                'name': 'Penalty Salary',
             'res_model_id': penalty_salary,
             'delay_unit': 'days',
             'delay_from': 'previous_activity',
             })
        activity.create(
            {
                'name': 'Exit entry',
             'res_model_id': exit_entry,
             'delay_unit': 'days',
             'delay_from': 'previous_activity',
             })
        activity.create(
            {
                'name': 'End employee',
             'res_model_id': end_employee,
             'delay_unit': 'days',
             'delay_from': 'previous_activity',
             })

    def draft_advanced(self):
        self.deferred_expense.set_to_draft()
        self.deferred_expense.unlink()

        self.move_id.button_draft()
        lines = self.env['account.move.line'].search([('move_id', '=', self.move_id.id)])
        lines.unlink()

        modelid = (self.env['ir.model'].search([('model', '=', 'iqama.renew')])).id
        select = "select uid from res_groups_users_rel as gs where gs.gid in (select id from res_groups as gg where name = '%s' and category_id in (select id from ir_module_category where name = '%s')   ) " % (
            'Administrator', 'Employees')
        self.env.cr.execute(select)
        results = self.env.cr.dictfetchall()
        print("wwresults", results)
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
                 'res_model': 'iqama.renew',
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

    @api.model
    def create(self, vals):
        if 'order_number' not in vals:
            vals['order_number'] = self.env['ir.sequence'].next_by_code('iqama.renew')
        res = super(IqamaRenew, self).create(vals)
        modelid = (self.env['ir.model'].search([('model', '=', 'iqama.renew')])).id
        select = "select uid from res_groups_users_rel as gs where gs.gid in (select id from res_groups as gg where name = '%s' and category_id in (select id from ir_module_category where name = '%s')   ) " % (
            'Administrator', 'Employees')
        self.env.cr.execute(select)
        results = self.env.cr.dictfetchall()
        print("wwresults", results)
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
                 'res_model': 'iqama.renew',
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

    @api.onchange('employee_id')
    def onchange_employee(self):
        if self.employee_id:
            self.job_title =self.employee_id.job_id.name
            self.job_number = self.employee_id.job_number
            self.department_id = self.employee_id.department_id.id
            self.iqama_end_date = self.employee_id.iqama_end_date


    def action_finance_manager(self):
        if self.env.user.has_group('account.group_account_manager'):
            activity_old = (self.env['mail.activity'].search([('res_model', '=', 'iqama.renew'),('res_id', '=', self.id)]))
            for ac in activity_old:
                ac.action_done()


            modelid = (self.env['ir.model'].search([('model', '=', 'iqama.renew')])).id
            select = "select uid from res_groups_users_rel as gs where gs.gid in (select id from res_groups as gg where name = '%s' and category_id in (select id from ir_module_category where name = '%s')   ) " % (
                'Advisor', 'Accounting')
            self.env.cr.execute(select)
            results = self.env.cr.dictfetchall()
            print("wwresults", results)
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
                     'res_model': 'iqama.renew',
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

    def action_hr_manager_accept(self):
        if self.env.user.has_group('hr.group_hr_manager'):
            activity_old = (self.env['mail.activity'].search([('res_model', '=', 'iqama.renew'),('res_id', '=', self.id)]))
            for ac in activity_old:
                ac.action_done()

            modelid = (self.env['ir.model'].search([('model', '=', 'iqama.renew')])).id
            select = "select uid from res_groups_users_rel as gs where gs.gid in (select id from res_groups as gg where name = '%s' and category_id in (select id from ir_module_category where name = '%s')   ) " % (
                'Advisor', 'Accounting')
            self.env.cr.execute(select)
            results = self.env.cr.dictfetchall()
            print("wwresults", results)
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
                     'res_model': 'iqama.renew',
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
        activity_old = (self.env['mail.activity'].search([('res_model', '=', 'iqama.renew'), ('res_id', '=', self.id)]))
        for ac in activity_old:
            ac.action_done()

    def action_director(self):
        if self.env.user.has_group('base.group_system'):
            activity_old = (self.env['mail.activity'].search([('res_model', '=', 'iqama.renew'),('res_id', '=', self.id)]))
            for ac in activity_old:
                ac.action_done()
            return self.write({'state': 'director'})
        else:
            raise UserError(
                _(
                    "لا يمكنك الموافقة صلاحية الادارة فقط"
                )

            )
    def return_movelines(self):
        all_move_vals = []
        for rec in self:

            move_vals = {
                'date': rec.date_payed,
                'ref': rec.order_number,
                'journal_id': rec.journal_id.id,
                'line_ids': [
                    (0, 0, {
                        'name': rec.order_number,
                        'debit': rec.amount,
                        'credit': 0.0,
                        'account_id': rec.account_id.id,
                        'analytic_account_id': rec.analytic_account_id.id,
                        'partner_id':rec.employee_id.address_home_id.id,
                    }),
                    (0, 0, {
                        'name': rec.order_number,
                        'debit': 0.0,
                        'credit': rec.amount,
                        'account_id': rec.journal_id.default_credit_account_id.id,
                        'analytic_account_id': rec.analytic_account_id.id,
                        'partner_id': rec.employee_id.address_home_id.id,
                    }),
                ],
            }
            all_move_vals.append(move_vals)
            return all_move_vals

    def action_accepted(self):
        if self.env.user.has_group('account.group_account_user'):
            account_asset = self.env['account.asset']
            res_asset = account_asset.create(
                {
                    'asset_type': 'expense',
                    'state': 'draft',
                    'name': self.deferred_expense_models.name,
                    'original_value': self.amount,
                    'acquisition_date': self.date_payed,
                    'method_number': self.deferred_expense_models.method_number,
                    'method_period': self.deferred_expense_models.method_period,
                    'account_depreciation_id': self.deferred_expense_models.account_depreciation_id.id,
                    'account_depreciation_expense_id': self.deferred_expense_models.account_depreciation_expense_id.id,
                    'journal_id': self.deferred_expense_models.journal_id.id,
                })
            self.deferred_expense  = res_asset.id
            self.deferred_expense.compute_depreciation_board()
            self.deferred_expense.validate()


            self.employee_id.iqama_start_date = self.iqama_newstart_date
            self.employee_id.iqama_end_date = self.iqama_newend_date
            AccountMove = self.env['account.move'].with_context(default_type='entry')
            if not self.move_id:
                moves = AccountMove.create(self.return_movelines())
                moves.post()
                self.move_id = moves.id
            else:
                self.move_id.button_draft()
                self.move_id.date = self.date_payed
                move_line_vals = []
                line1 = (0, 0, {'name': self.order_number, 'debit': self.amount, 'credit': 0,
                                'account_id': self.account_id.id,'partner_id':self.employee_id.address_home_id.id,
                                'analytic_account_id': self.analytic_account_id.id
                                })
                line2 = (0, 0, {'name': self.order_number, 'debit': 0, 'credit': self.amount,
                                'account_id': self.journal_id.default_credit_account_id.id,'partner_id':self.employee_id.address_home_id.id,
                                'analytic_account_id': self.analytic_account_id.id
                                })
                move_line_vals.append(line1)
                move_line_vals.append(line2)
                self.move_id.line_ids = move_line_vals
                self.move_id.post()

            return self.write({'state': 'accepted'})
        else:
            raise UserError(
                _(
                    "لا يمكنك الموافقة صلاحية الادارة فقط"
                )

            )
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
        if not self.reason_refuse:
            raise UserError(
                _(
                    "يجب تعبئة حقل سبب الرفض"
                ))

        activity_old = (self.env['mail.activity'].search([('res_model', '=', 'exit.entry'), ('res_id', '=', self.id)]))
        for ac in activity_old:
            ac.action_done()


    def action_cancel(self):
        activity_old = (self.env['mail.activity'].search([('res_model', '=', 'iqama.renew'), ('res_id', '=', self.id)]))
        for ac in activity_old:
            ac.action_done()

        return self.write({'state': 'cancel'})




