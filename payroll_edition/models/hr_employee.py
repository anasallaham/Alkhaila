# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, _
from odoo.tools.float_utils import float_round
from  datetime import  datetime
from dateutil.relativedelta import relativedelta

class Employee(models.Model):
    _inherit = "hr.employee"
    end_employee_ids = fields.One2many('end.employee','employee_id',string="انهاء الموظف")
    count_end_employee_ids = fields.Float(string="عدد الانهاء",compute="_compute_count_end_employee_ids")
    hr_payslip_ids = fields.One2many('hr.payslip','employee_id',string="ايصالات المرتبات")
    date_stop  = fields.Date(string="تاريخ الانهاء ")


    type_employee_end = fields.Selection([('Resignation','مستقيل'),('end_of_contract','End of contract'),('termination2','Termination')],string="الية الانهاء")


    advanced_salary_ids = fields.One2many('advanced.salary','hr_employee',string="السلف")
    count_advanced_salary_ids = fields.Float(string="عدد السلف",compute="_compute_count_advanced_salary_ids")

    penalty_salary_ids = fields.One2many('penalty.salary','hr_employee',string="العقوبات")
    count_penalty_salary_ids = fields.Float(string="عدد العقوبات",compute="_compute_count_penalty_salary_ids")



    job_number  = fields.Char(string="Job Number")

    identification_id = fields.Char(string='Personal Identification', tracking=True)
    medical_insurance = fields.Char(string='Medical Insurance', tracking=True)

    iqama_start_date = fields.Date(string="Iqama Start Date")

    iqama_end_date = fields.Date(string="Iqama End Date")
    ensbeh_eos = fields.Float(string="نسبة EOS",readonly=True, compute='_compute_ensbeh_eos', store=True)


    type_exit_entry = fields.Selection([
        ('single', 'Single'),
        ('multi', 'Multi'),
    ], string='النوع' )

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
    def _compute_count_penalty_salary_ids(self):
        for p in self:
            p.count_penalty_salary_ids = len(self.penalty_salary_ids)

    def _compute_count_end_employee_ids(self):
        for p in self:
            p.count_end_employee_ids = len(self.end_employee_ids)


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

    def action_view_end_employee(self):
        end_employee_ids = self.mapped('end_employee_ids')
        action = self.env.ref('payroll_edition.action_end_employee').read()[0]
        if len(end_employee_ids) > 1:
            action['domain'] = [('id', 'in', end_employee_ids.ids)]
        elif len(end_employee_ids) == 1:
            form_view = [(self.env.ref('payroll_edition.end_employee_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = end_employee_ids.id
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
