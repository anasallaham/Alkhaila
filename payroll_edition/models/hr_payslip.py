# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
from dateutil.relativedelta import relativedelta


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    hr_attendance_save_ids = fields.One2many('hr.attendance.save', 'hr_payslip_id', string="الدوام")
    addition_sum = fields.Float(string=" ساعات الاضافي", compute='_compute_addition_sum', store=True, readonly=True)
    delay_sum = fields.Float(string=" ساعات الخصومات", compute='_compute_delay_sum', store=True, readonly=True)
    addition_amount = fields.Float(string="قيمة الاضافي", compute='_compute_addition_amount', store=True, readonly=True)
    delay_amount = fields.Float(string="قيمة الخصومات", compute='_compute_delay_amount', store=True, readonly=True)

    advanced_salary_ids = fields.Many2many('advanced.salary', string="السلف", readonly=True)
    amount_advanced_salary = fields.Float(string="مجموع السلف", readonly=True)

    penalty_salary_ids = fields.Many2many('penalty.salary', string="العقوبات", readonly=True)
    amount_penalty_salary = fields.Float(string="مجموع العقوبات", readonly=True)

    @api.depends('hr_attendance_save_ids')
    def _compute_addition_sum(self):
        for s in self:
            if s.contract_id.addition_ture:
                select = "select COALESCE( sum(addition),0) as sum from hr_attendance_save where hr_payslip_id = %s " % (
                    s.id)
                s.env.cr.execute(select)
                results = s.env.cr.dictfetchall()[0]['sum']
                s.addition_sum = results
            else:
                s.addition_sum = 0.0

    @api.depends('hr_attendance_save_ids')
    def _compute_delay_sum(self):
        for s in self:
            if s.contract_id.delay_ture:
                if type(s.id) == int:
                    select = "select COALESCE( sum(delays),0) as sum from hr_attendance_save where hr_payslip_id = %s " % (
                        s.id)
                    s.env.cr.execute(select)
                    results = s.env.cr.dictfetchall()[0]['sum']
                    s.delay_sum = results
            else:
                s.delay_sum = 0.0

    @api.depends('addition_sum')
    def _compute_addition_amount(self):
        for s in self:
            if s.contract_id.addition_ture:
                sum_of_days = 0
                for line in s.worked_days_line_ids:
                    sum_of_days += line.number_of_days

                if s.contract_id.structure_type_id.is_allow:
                    s.addition_amount = ((s.addition_sum * 60) * (
                        (s.contract_id.wage+s.contract_id.amount_hous+s.contract_id.amount_trasportation+s.contract_id.amount_mobile+s.contract_id.amount_anuther_allow) / sum_of_days / s.contract_id.resource_calendar_id.hours_per_day / 60)) * (
                                                    s.contract_id.addition_nsbeh / 100.0)
                else:
                    s.addition_amount = ((s.addition_sum * 60) * (
                        (s.contract_id.wage) / sum_of_days / s.contract_id.resource_calendar_id.hours_per_day / 60)) * (
                                                    s.contract_id.addition_nsbeh / 100.0)

            else:
                s.addition_amount = 0.0

    @api.depends('delay_sum')
    def _compute_delay_amount(self):
        for s in self:
            if s.contract_id.delay_ture:
                sum_of_days = 0
                for line in s.worked_days_line_ids:
                    sum_of_days += line.number_of_days

                if s.contract_id.structure_type_id.is_allow:

                    s.delay_amount = ((s.delay_sum * 60) * (
                            (s.contract_id.wage+s.contract_id.amount_hous+s.contract_id.amount_trasportation+s.contract_id.amount_mobile+s.contract_id.amount_anuther_allow)  / sum_of_days / s.contract_id.resource_calendar_id.hours_per_day / 60)) * (
                                                 s.contract_id.delay_nsbeh / 100.0)
                else:
                    s.delay_amount = ((s.delay_sum * 60) * (
                            (s.contract_id.wage)  / sum_of_days / s.contract_id.resource_calendar_id.hours_per_day / 60)) * (
                                                 s.contract_id.delay_nsbeh / 100.0)

            else:
                s.delay_amount = 0.0

    def compute_sheet(self):
        for me in self:

            penalty_salary_ids = me.env["penalty.salary"].search(
                [
                    ("hr_employee", "=", me.employee_id.id),
                    ("state", "=", "accepted"),
                    ("date", ">=", me.date_from), ("date", "<=", me.date_to),
                ]
            )
            sum_salarypenalty = 0.0
            for line in penalty_salary_ids:
                sum_salarypenalty += line.amount
            me.penalty_salary_ids = [(6, 0, penalty_salary_ids.ids)]
            me.amount_penalty_salary = sum_salarypenalty

            advanced_salary_ids = me.env["advanced.salary"].search(
                [
                    ("hr_employee", "=", me.employee_id.id),
                    ("state", "=", "accepted"),
                    ("date", ">=", me.date_from), ("date", "<=", me.date_to),
                ]
            )
            sum_salary = 0.0
            for line in advanced_salary_ids:
                sum_salary += line.amount
            me.advanced_salary_ids = [(6, 0, advanced_salary_ids.ids)]
            me.amount_advanced_salary = sum_salary

            date_diff = relativedelta(datetime.today(), me.employee_id.joining_date)
            day = date_diff.days
            month = date_diff.months
            year = date_diff.years
            if year < 5:
                me.employee_id.ensbeh_eos = 0.5
            else:
                me.employee_id.ensbeh_eos = 1

            super(HrPayslip, me).compute_sheet()
            me.hr_attendance_save_ids.unlink()

            me.model = me.env["hr.attendance.save"]

            current_date = me.date_from
            while (current_date <= me.date_to):
                # IDS = me.env['hr.attendance']._search(
                #     [('employee_id', '=', me.employee_id.id), ('check_in', '>=', current_date), ('check_in', '<',  (datetime.strptime(str(current_date), '%Y-%m-%d').date() + relativedelta(days= + 1))) ])
                # employee_attendance_ids = me.env['hr.attendance'].browse(IDS)

                select = "select COALESCE( sum(worked_hours),0) as sum from hr_attendance where employee_id = %s and check_in >= %r and check_in < %r" % (
                    me.employee_id.id, str(current_date),
                    str(datetime.strptime(str(current_date), '%Y-%m-%d').date() + relativedelta(days=+ 1)))
                me.env.cr.execute(select)
                results = me.env.cr.dictfetchall()[0]['sum']
                second = (results * 60 * 60) - (me.contract_id.resource_calendar_id.hours_per_day * 60 * 60)
                if second > 0.0:
                    edafy_second = second / 60 / 60
                    edafy_delay = 0.0
                else:
                    edafy_second = 0.0
                    edafy_delay = (second * -1) / 60 / 60

                hr_work_entry_ids = me.env["hr.work.entry"].search(
                    [
                        ("employee_id", "=", me.employee_id.id),("date_start", "<=", current_date), ("date_stop", ">=", current_date),("work_entry_type_id.name", "=", "Attendance"),
                    ])
                if hr_work_entry_ids:
                    me.model.create({'date': current_date, "employee_id": me.employee_id.id, "hr_payslip_id": me.id,
                                       "hours_per_day": me.contract_id.resource_calendar_id.hours_per_day,
                                       "time_work": results, "addition": edafy_second, "delays": edafy_delay})
                current_date = (datetime.strptime(str(current_date), '%Y-%m-%d').date() + relativedelta(days=+ 1))
        res = super(HrPayslip, self).compute_sheet()

        return res


class HrAttendanceSave(models.Model):
    _name = 'hr.attendance.save'

    date = fields.Date(string="التاريخ", readonly=False)
    hr_payslip_id = fields.Many2one('hr.payslip', string="hr.payslip")
    employee_id = fields.Many2one('hr.employee', string="الموظف")

    hours_per_day = fields.Float(string="ساعات الدوام المطلوب")
    time_work = fields.Float(string="ساعات الدوام الفعلي")

    addition = fields.Float(string="الاضافي")
    delays = fields.Float(string="غرامات")
