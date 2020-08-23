# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields


class AccountJournal(models.Model):
    _inherit = "account.journal"

    rule_users = fields.Many2many('res.users',string="صلاحية القيود")