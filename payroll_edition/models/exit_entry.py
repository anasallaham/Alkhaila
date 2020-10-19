# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, time
from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from datetime import date, datetime,timedelta


class ExitEntry(models.Model):
    _name = 'exit.entry'
    _rec_name ='employee_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    order_number  = fields.Char(string="Number",readonly=True)
    date = fields.Date(string=" تاريخ",required=True)
    date_payed = fields.Date(string=" تاريخ الدفع")
    reason_refuse = fields.Char(string="سبب الرفض")

    employee_id  = fields.Many2one('hr.employee',string="الموظف",required=True)
    amount = fields.Float(string="القيمة كاملة", compute='_compute_amount', store=True)
    count = fields.Integer(string="عدد الاشهر",readonly=True)
    advanced_salary = fields.One2many('advanced.salary','exit_entry_id', string="السلف")
    journal_id = fields.Many2one('account.journal', string="اليوميه")
    account_id = fields.Many2one('account.account', string="الحساب")
    account_advanced_id = fields.Many2one('account.account', string="حساب السلف")
    move_id = fields.Many2one('account.move', string="القيد",readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', )

    type_exit_entry = fields.Selection([
        ('single', 'Single'),
        ('multi', 'Multi'),
    ], string='النوع' ,required=True,default="single")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('hr_manager_accept', 'Hr Mananger Accept'),
        ('finance_manager', 'Finance Manager'),
        ('director', 'Director'),
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


        modelid = (self.env['ir.model'].search([('model', '=', 'exit.entry')])).id
        select = "select uid from res_groups_users_rel as gs where gs.gid in (select id from res_groups as gg where name = '%s' and category_id in (select id from ir_module_category where name = '%s')   ) " % ('Administrator','Employees')
        self.env.cr.execute(select)
        results = self.env.cr.dictfetchall()
        print ("wwresults",results)
        users = []
        for obj in results:
            users.append(obj['uid'])
        print ("users",users)
        user_id = (self.env['res.users'].search([('id', 'in', users)]))

        activity = self.env['mail.activity']
        for user in user_id:

            activity_ins = activity.create(
                {'res_id': self.id,
                 'res_model_id': modelid,
                 'res_model': 'exit.entry',
                 'activity_type_id': (self.env['mail.activity.type'].search([('res_model_id', '=', modelid)])).id,
                 'summary': '',
                 'note': '',
                 'date_deadline': date.today() ,
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

    @api.model
    def create(self, vals):
        if 'order_number' not in vals:
            vals['order_number'] = self.env['ir.sequence'].next_by_code('exit.entry')
        res = super(ExitEntry, self).create(vals)


        modelid = (self.env['ir.model'].search([('model', '=', 'exit.entry')])).id


        select = "select uid from res_groups_users_rel as gs where gs.gid in (select id from res_groups as gg where name = '%s' and category_id in (select id from ir_module_category where name = '%s')   ) " % ('Administrator','Employees')
        self.env.cr.execute(select)
        results = self.env.cr.dictfetchall()
        print ("wwresults",results)
        users = []
        for obj in results:
            users.append(obj['uid'])
        print ("users",users)
        user_id = (self.env['res.users'].search([('id', 'in', users)]))


        activity = self.env['mail.activity']
        for user in user_id:

            activity_ins = activity.create(
                {'res_id': res.id,
                 'res_model_id': modelid,
                 'res_model': 'exit.entry',
                 'activity_type_id': (res.env['mail.activity.type'].search([('res_model_id', '=', modelid)])).id,
                 'summary': '',
                 'note': '',
                 'date_deadline': date.today() ,
                 'activity_category': 'default',
                 'previous_activity_type_id': False,
                 'recommended_activity_type_id': False,
                 'user_id': user.id
                 })
        return res
    @api.depends('count')
    def _compute_amount(self):
        for me in self:
            if me.type_exit_entry == "single":
                if me.count > 12:
                    raise UserError(
                        _("الحد الاقصى 12 شهر")

                    )
                me.amount = 100 * me.count



    def action_finance_manager(self):
        if self.env.user.has_group('account.group_account_manager'):
            activity_old = (self.env['mail.activity'].search([('res_model', '=', 'exit.entry'),('res_id', '=', self.id)]))
            for ac in activity_old:
                ac.action_done()


            modelid = (self.env['ir.model'].search([('model', '=', 'exit.entry')])).id
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
                     'res_model': 'exit.entry',
                     'activity_type_id': (self.env['mail.activity.type'].search([('res_model_id', '=', modelid)])).id,
                     'summary': '',
                     'note': '',
                     'date_deadline': date.today() ,
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
        if self.env.user.has_group('base.group_system'):
            activity_old = (self.env['mail.activity'].search([('res_model', '=', 'exit.entry'),('res_id', '=', self.id)]))
            for ac in activity_old:
                ac.action_done()


            modelid = (self.env['ir.model'].search([('model', '=', 'exit.entry')])).id
            select = "select uid from res_groups_users_rel as gs where gs.gid in (select id from res_groups as gg where name = '%s' and category_id in (select id from ir_module_category where name = '%s')   ) " % (
            'Settings', 'Administration')
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
                     'res_model': 'exit.entry',
                     'activity_type_id': (self.env['mail.activity.type'].search([('res_model_id', '=', modelid)])).id,
                     'summary': '',
                     'note': '',
                     'date_deadline': date.today() ,
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
            activity_old = (self.env['mail.activity'].search([('res_model', '=', 'exit.entry'),('res_id', '=', self.id)]))
            for ac in activity_old:
                ac.action_done()

            modelid = (self.env['ir.model'].search([('model', '=', 'exit.entry')])).id
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
                     'res_model': 'exit.entry',
                     'activity_type_id': (self.env['mail.activity.type'].search([('res_model_id', '=', modelid)])).id,
                     'summary': '',
                     'note': '',
                     'date_deadline': date.today() ,
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
        if self.env.user.has_group('account.group_account_user'):
            self.employee_id.type_exit_entry = self.type_exit_entry
            self.to_street()
            testamount = self.amount - 200
            if self.type_exit_entry == "single" and testamount > 0:
                advanced = self.env['advanced.salary'].create({
                            'exit_entry_id': self.id,
                            'hr_employee': self.employee_id.id,
                            'amount': testamount,
                            'journal_id': self.journal_id.id,
                            'account_id': self.account_advanced_id.id,
                            'analytic_account_id': self.analytic_account_id.id,
                            'date': self.date,
                            'date_payed': self.date_payed,
                        })
                advanced.action_accepted()
            activity_old = (self.env['mail.activity'].search([('res_model', '=', 'exit.entry'),('res_id', '=', self.id)]))
            for ac in activity_old:
                ac.action_done()



            return self.write({'state': 'accepted'})
        else:
            raise UserError(
                _(
                    "لا يمكنك الموافقة صلاحية الادارة فقط"
                )

    # def action_accepted(self):
    #     if self.env.user.has_group('base.group_system'):
    #         self.employee_id.type_exit_entry = self.type_exit_entry
    #         self.to_street()
    #         if self.count > 2:
    #             date = self.date
    #             for r in range(2,self.count):
    #                 advanced = self.env['advanced.salary'].create({
    #                     'exit_entry_id': self.id,
    #                     'hr_employee': self.employee_id.id,
    #                     'amount': 100,
    #                     'journal_id': self.journal_id.id,
    #                     'analytic_account_id': self.analytic_account_id.id,
    #                     'date': date,
    #                 })
    #                 advanced.action_accepted()
    #                 date = date + relativedelta(months=1)
    #         return self.write({'state': 'accepted'})
    #     else:
    #         raise UserError(
    #             _(
    #                 "لا يمكنك الموافقة صلاحية الادارة فقط"
    #             )
    #
            )


    def action_cancel(self):
        activity_old = (self.env['mail.activity'].search([('res_model', '=', 'exit.entry'), ('res_id', '=', self.id)]))
        for ac in activity_old:
            ac.action_done()

        return self.write({'state': 'cancel'})



    def return_movelines(self):
        all_move_vals = []
        for exitentry in self:

            if self.type_exit_entry == 'single':
                if exitentry.amount  >= 200 :
                    amount = 200
                else:
                    amount = exitentry.amount
            else:
                amount = exitentry.amount

            move_vals = {
                'date': exitentry.date_payed,
                'ref': exitentry.order_number,
                'journal_id': exitentry.journal_id.id,
                'line_ids': [
                    (0, 0, {
                        'name': exitentry.order_number,
                        'debit': amount,
                        'credit': 0.0,
                        'account_id': exitentry.account_id.id,
                        'analytic_account_id': exitentry.analytic_account_id.id,
                        'partner_id':exitentry.employee_id.address_id.id,
                    }),
                    (0, 0, {
                        'name': exitentry.order_number,
                        'debit': 0.0,
                        'credit': amount,
                        'account_id': exitentry.journal_id.default_credit_account_id.id,
                        'analytic_account_id': exitentry.analytic_account_id.id,
                        'partner_id': exitentry.employee_id.address_id.id,
                    }),
                ],
            }
            all_move_vals.append(move_vals)
            return all_move_vals

    def to_street(self):
        AccountMove = self.env['account.move'].with_context(default_type='entry')
        for rec in self:

            if not rec.move_id:
                moves = AccountMove.create(rec.return_movelines())
                moves.post()
                rec.move_id = moves.id
            else:
                if rec.type_exit_entry == "single":
                    if rec.amount >= 200:
                        amount = 200
                    else:
                        amount = rec.amount
                else:
                    amount = rec.amount

                rec.move_id.button_draft()
                rec.move_id.date = rec.date_payed
                move_line_vals = []
                line1 = (0, 0, {'name': rec.order_number, 'debit': amount, 'credit': 0,
                                'analytic_account_id': rec.analytic_account_id.id,'account_id': rec.account_id.id,'partner_id':rec.employee_id.address_id.id,
                                })
                line2 = (0, 0, {'name': rec.order_number, 'debit': 0, 'credit': amount,
                                'account_id': rec.journal_id.default_credit_account_id.id,'partner_id':rec.employee_id.address_id.id,
                                'analytic_account_id': rec.analytic_account_id.id
                                })
                move_line_vals.append(line1)
                move_line_vals.append(line2)
                rec.move_id.line_ids = move_line_vals
                rec.move_id.post()
        return True

