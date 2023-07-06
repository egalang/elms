from odoo import models, fields, api


class LoanSummary(models.Model):
    _name = 'loans.summary'
    _description = 'Loan Summary'
    
    company_id = fields.Many2one('res.partner', string='Company')
    bank_id = fields.Many2one('res.bank', string='Bank')
    principal = fields.Float('Total Principal Amount', compute='_compute_total_amount')
    credit_line = fields.Float('Credit Line')
    available_balance = fields.Float('Available Balance', compute='_compute_available_balance')

    def _compute_total_amount(self):
        for summary in self:
            loans = self.env['loans.main'].search([
                ('company_name', '=', summary.company_id.id),
                ('bank_name', '=', summary.bank_id.id),
                ('stage', '<>', 'Matured'), ('stage', '<>', 'Paid')
            ])
            summary.principal = sum(loans.mapped('principal'))

    def _compute_available_balance(self):
        for summary in self:
            summary.available_balance = summary.credit_line - summary.principal
    
    
    def display_loan_records(self):
        self.ensure_one()
        loans = self.env['loans.main'].search([
            ('company_name', '=', self.company_id.id),
            ('bank_name', '=', self.bank_id.id)
        ])
        action = self.env.ref('loans.loans_main_action')  # Replace 'module_name' with the actual module name
        result = action.read()[0]
        result['domain'] = [('id', 'in', loans.ids)]
        return result
    
