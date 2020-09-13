# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, _
from odoo.tools.float_utils import float_round
from  datetime import  datetime
from dateutil.relativedelta import relativedelta

class Employee(models.Model):
    _inherit = "hr.employee"


    sum_eos = fields.Float(string="تجميع EOS",readonly=True, compute='_compute_sum_eos', store=True)
    ensbeh_eos = fields.Float(string="نسبة EOS",readonly=True, compute='_compute_ensbeh_eos', store=True)
    sum_lastes = fields.Float(string="مكافئة انتهاء الخدمة",readonly=True)
    hr_payslip_ids = fields.One2many('hr.payslip','employee_id',string="ايصالات المرتبات")

    endemployee = fields.Selection([('Resignation','مستقيل'),('end_of_contract','End of contract'),('termination2','Termination')],string="انهاء الموظف")

    date_stop  = fields.Date(string="تاريخ الانهاء ")
    type_end = fields.Selection([('Resignation','مستقيل'),('end_of_contract','End of contract'),('termination2','Termination')],string="انهاء الموظف")
    doneend = fields.Boolean(string="تم انهاء الموظف")

    date_in  = fields.Date(string="تاريخ التعيين ")
    years_in  = fields.Integer(string="Years ")
    months_in  = fields.Integer(string="Months ")
    days_in  = fields.Integer(string="Days ")

    days_paid_holidays = fields.Float(string="عدد الايام المدفوعة",readonly=True)
    amount_days_paid_holidays = fields.Float(string="قيمة الايام المدفوعة",readonly=True)
    last_date_ehtsab  = fields.Datetime(string="تاريخ اخر احتساب ",readonly=True)


    advanced_salary_ids = fields.One2many('advanced.salary','hr_employee',string="السلف")
    count_advanced_salary_ids = fields.Float(string="عدد السلف",compute="_compute_count_advanced_salary_ids")

    penalty_salary_ids = fields.One2many('penalty.salary','hr_employee',string="العقوبات")
    count_penalty_salary_ids = fields.Float(string="عدد العقوبات",compute="_compute_count_penalty_salary_ids")



    job_number  = fields.Char(string="Job Number")

    identification_id = fields.Char(string='Personal Identification', tracking=True)
    medical_insurance = fields.Char(string='Medical Insurance', tracking=True)

    iqama_start_date = fields.Date(string="Iqama Start Date")

    iqama_end_date = fields.Date(string="Iqama End Date")



    type_exit_entry = fields.Selection([
        ('single', 'Single'),
        ('multi', 'Multi'),
    ], string='النوع' )


    def _compute_count_penalty_salary_ids(self):
        for p in self:
            p.count_penalty_salary_ids = len(self.penalty_salary_ids)


    def action_view_penalty_salary(self):
        penalty_salary_ids = self.mapped('penalty_salary_ids')
        action = self.env.ref('payroll_edition.penalty_salary_action').read()[0]
        if len(penalty_salary_ids) > 1:
            action['domain'] = [('id', 'in', penalty_salary_ids.ids)]
        elif len(penalty_salary_ids) == 1:
            form_view = [(self.env.ref('payroll_edition.penalty_salary_module_form_view').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = penalty_salary_ids.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
        }
        if len(self) == 1:
            context.update({
            })
        action['context'] = context
        return action



    def _compute_count_advanced_salary_ids(self):
        for p in self:
            p.count_advanced_salary_ids = len(self.advanced_salary_ids)


    def action_view_advanced_salary(self):
        advanced_salary_ids = self.mapped('advanced_salary_ids')
        action = self.env.ref('payroll_edition.advanced_salary_action').read()[0]
        if len(advanced_salary_ids) > 1:
            action['domain'] = [('id', 'in', advanced_salary_ids.ids)]
        elif len(advanced_salary_ids) == 1:
            form_view = [(self.env.ref('payroll_edition.advanced_salary_module_form_view').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = advanced_salary_ids.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
        }
        if len(self) == 1:
            context.update({
            })
        action['context'] = context
        return action


    @api.depends("hr_payslip_ids.line_ids","hr_payslip_ids.state","hr_payslip_ids")
    def _compute_sum_eos(self):
        for me in self:
            sum = 0.0
            for payslip in me.hr_payslip_ids.filtered(lambda r: r.state in ['verify','done']):
                for pl in payslip.line_ids:
                    if pl.salary_rule_id.is_eos:
                        sum += pl.amount
            me.sum_eos = sum
    @api.depends("joining_date","hr_payslip_ids")
    def _compute_ensbeh_eos(self):
        for me in self:
            date_diff = relativedelta(datetime.today(), me.joining_date)
            day = date_diff.days
            month = date_diff.months
            year = date_diff.years
            if year < 5:
                me.ensbeh_eos = 0.5
            else:
                me.ensbeh_eos = 1

    def sum_lastes_go(self):
        for me in self:
            contract_id = self.env["hr.contract"].search(
                [
                    ("employee_id", "=", me.id),("date_start", "<=", me.date_stop),("date_end", ">=", me.date_stop),
                ]
            )

            date_diff = relativedelta(me.date_stop, me.joining_date)
            year = date_diff.years
            if me.type_end == 'Resignation':
                if year < 2:
                    me.sum_lastes = 0.0
                elif year >= 2 and year < 5:
                    me.sum_lastes =  (33/100) * year * (contract_id.wage/2)
                elif year >= 5 and year < 10:
                    me.sum_lastes =  (66/100) * year * (contract_id.wage/2)
                elif year >= 10 :
                    res1 =  5 * (contract_id.wage/2)
                    res3 =   year-5 * (contract_id.wage)
                    me.sum_lastes = res1  + res3

            else:
                res3 = year  * (contract_id.wage)/2
                me.sum_lastes = res3
            remaining = self._get_paid_remaining_leaves()
            self.days_paid_holidays = float_round(remaining.get(self.id, 0.0), precision_digits=2)

            if contract_id:
                self.amount_days_paid_holidays = round(((contract_id[0].wage + contract_id[0].amount_hous + contract_id[0].amount_moving )/30 ) * self.days_paid_holidays,2)
            else:
                self.amount_days_paid_holidays = 0.0
            self.last_date_ehtsab = datetime.now()

    def go_end_employee(self):
        for me in self:
            remaining = self._get_paid_remaining_leaves()
            self.days_paid_holidays = float_round(remaining.get(self.id, 0.0), precision_digits=2)
            me.sum_lastes_go()
            self.date_in = self.joining_date
            difference_in_years = relativedelta(self.last_date_ehtsab, self.date_in)
            self.years_in = difference_in_years.years
            self.months_in = difference_in_years.months
            self.days_in = difference_in_years.days
            me.doneend = True
            me.active = False

    def back_go_end_employee(self):
        for me in self:
            me.sum_lastes = 0.0
            me.days_paid_holidays = 0.0
            me.amount_days_paid_holidays = 0.0
            self.date_in = False
            self.years_in = False
            self.months_in = False
            self.days_in = False

            me.doneend = False
            me.active = True


    def _get_paid_remaining_leaves(self):
        """ Helper to compute the remaining leaves for the current employees
            :returns dict where the key is the employee id, and the value is the remain leaves
        """
        self._cr.execute("""
            SELECT
                sum(h.number_of_days) AS days,
                h.employee_id
            FROM
                (
                    SELECT holiday_status_id, number_of_days,
                        state, employee_id
                    FROM hr_leave_allocation
                    UNION
                    SELECT holiday_status_id, (number_of_days * -1) as number_of_days,
                        state, employee_id
                    FROM hr_leave
                ) h
                join hr_leave_type s ON (s.id=h.holiday_status_id)
            WHERE
                h.state='validate' AND
                (s.allocation_type='fixed' OR s.allocation_type='fixed_allocation')AND s.unpaid=False AND
                h.employee_id in %s
            GROUP BY h.employee_id""", (tuple(self.ids),))
        return dict((row['employee_id'], row['days']) for row in self._cr.dictfetchall())
