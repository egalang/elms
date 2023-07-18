# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import humanize

class LoanType(models.Model):
     _name='loans.type'
     _description='Loan Types'

     name = fields.Char(string='Loan Type')

class LoansStage(models.Model):
    _name = 'loans.stage'
    _description = 'Stages of loans'

    name = fields.Char(string='Stage')

class loans(models.Model):
     _name = 'loans.main'
     _description = 'Company loans'
     _order = 'id desc'
     _inherit = ['mail.thread','mail.activity.mixin']

     PAYMENT_TYPE_SELECTION = [
        ('full_payment', 'Full Payment Required'),
        ('interest_only', 'Interest Only'),
        ('amortization', 'Amortization'),
        ('full_payment_new_contract', 'Full Payment Unless New Contract'),
        ('pn_renewal', 'PN Renewal/Extension'),
        ('partial_payment', 'Partial Payment'),
        ('rental_pdc', 'Rental w/ PDCs'),
    ]

     company_name = fields.Many2one('res.partner', string="Company", tracking=True)
     loan_date=fields.Date('Date', required=True, tracking=True)
     bank_name=fields.Many2one('res.bank', string="Bank", required=True, tracking=True)
     loan_type=fields.Many2one('loans.type', string="Loan Type", default=lambda self: self._default_stage(), tracking=True)
     pn_number=fields.Char('PN Number', required=True, tracking=True)
     pn_count=fields.Integer('PN Count', required=True, default='1', tracking=True)
     remarks=fields.Text('REMARKS', tracking=True)
     term_loan=fields.Boolean('Term Loan?', tracking=True)
     amount = fields.Float('Amount', require=True, tracking=True)
     amount_type = fields.Selection([
          ('principal', 'Principal'),
          ('interest', 'Interest'),
          ('dst', 'DST'),
          ], string='Amount Type', default='principal', tracking=True)
     #type_1=fields.Char('Type I', tracking=True)
     #type_2=fields.Char('Type II', tracking=True)
     availment_entry=fields.Char('Availment Entry', tracking=True)
     settlement_entry=fields.Char('Settlement Entry', tracking=True, compute='_compute_settlement_entry', store=True, readonly=False)
     stage = fields.Many2one('loans.stage', string="Stage", default=lambda self: self._default_stage(), tracking=True)
     payment_type = fields.Selection([
          ('full_payment', 'Full Payment Required'),
          ('interest_only', 'Interest Only'),
          ('amortization', 'Amortization'),
          ('full_payment_new_contract', 'Full Payment Unless New Contract'),
          ('pn_renewal_extension', 'PN Renewal/Extension'),
          ('partial_payment', 'Partial Payment'),
          ('rental_pdc', 'Rental w/ PDCs')
    ], string='Action', default='full_payment', tracking=True)
     color = fields.Integer('Color', compute='_compute_color', tracking=True)
     
     def name_get(self):
           result = []
           for record in self:
                formatted_amount = humanize.intcomma(round(record.amount, 2))
                name = f"{formatted_amount}"
                result.append((record.id, name))
           return result
     
     def _default_stage(self):
          stage = self.env['loans.stage'].search([('name', '=', 'New')], limit=1)
          return stage
     
     @api.depends('payment_type')
     def _compute_color(self):
          color_mapping = {
               'full_payment': 0,
               'interest_only': 1,
               'amortization': 2,
               'full_payment_new_contract': 3,
               'pn_renewal_extension': 4,
               'partial_payment': 5,
               'rental_pdc': 6
          }
          for record in self:
               record.color = color_mapping.get(record.payment_type, 0)
     
     def action_loan_summary(self):
        action = self.env.ref('loans_summary.view_loan_summary_form').read()[0]
        action['domain'] = [('company_id', '=', self.company_name.id)]
        return action

     def _is_settlement_entry_required(self):
          return self.stage.name == 'Posted'
     
     @api.constrains('stage', 'settlement_entry')
     def _check_settlement_entry_required(self):
          for record in self:
               if record.stage.name == 'Posted' and not record.settlement_entry:
                    raise ValidationError("Settlement Entry is required when the stage is set to 'Posted'.")
