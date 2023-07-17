from odoo import models, fields, api


class LoanSummary(models.Model):
    _name = 'loans.summary'
    _description = 'Loan Summary'
    
    company_id = fields.Many2one('res.partner', string='Company')
    bank_id = fields.Many2one('res.bank', string='Bank')
    principal = fields.Float('Total Principal Amount', compute='_compute_total_amount')
    credit_line = fields.Float('Credit Line')
    available_balance = fields.Float('Available Balance', compute='_compute_available_balance')
    type=fields.Many2one('loans.type', string='Loan Type', default=lambda self: self._default_type())

    def _compute_total_amount(self):
        for summary in self:
            loans = self.env['loans.main'].search([
                ('company_name', '=', summary.company_id.id),
                ('bank_name', '=', summary.bank_id.id),
                ('loan_type', '=', summary.type.id),
                ('amount_type', '=', 'principal'),
                ('stage', 'not in', ['Matured', 'Paid'])
            ])
            summary.principal = sum(loans.mapped('amount'))

    def _compute_available_balance(self):
        for summary in self:
            summary.available_balance = summary.credit_line - summary.principal

    def _default_type(self):
        type = self.env['loans.type'].search([('name', '=', 'New')], limit=1)
        return type

    
    
    def display_loan_records(self):
        self.ensure_one()
        loans = self.env['loans.main'].search([
            ('company_name', '=', self.company_id.id),
            ('bank_name', '=', self.bank_id.id),
            ('loan_type', '=', self.type.id)
        ])
        action = self.env.ref('elms.loans_main_action')  
        result = action.read()[0]
        result['domain'] = [('id', 'in', loans.ids)]
        return result
    