from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def _action_create_account_move(self):
        precision = self.env['decimal.precision'].precision_get('Payroll')

        # Add payslip without run
        payslips_to_post = self.filtered(lambda slip: not slip.payslip_run_id)

        # Adding pay slips from a batch and deleting pay slips with a batch that is not ready for validation.
        payslip_runs = (self - payslips_to_post).mapped('payslip_run_id')
        for run in payslip_runs:
            if run._are_payslips_ready():
                payslips_to_post |= run.slip_ids

        # A payslip need to have a done state and not an accounting move.
        payslips_to_post = payslips_to_post.filtered(lambda slip: slip.state == 'done' and not slip.move_id)

        # Check that a journal exists on all the structures
        if any(not payslip.struct_id for payslip in payslips_to_post):
            raise ValidationError(_('One of the contract for these payslips has no structure type.'))
        if any(not structure.journal_id for structure in payslips_to_post.mapped('struct_id')):
            raise ValidationError(_('One of the payroll structures has no account journal defined on it.'))

        # Map all payslips by structure journal and pay slips month.
        # {'journal_id': {'month': [slip_ids]}}
        slip_mapped_data = {slip.struct_id.journal_id.id: {fields.Date().end_of(slip.date_to, 'month'): self.env['hr.payslip']} for slip in payslips_to_post}
        for slip in payslips_to_post:
            slip_mapped_data[slip.struct_id.journal_id.id][fields.Date().end_of(slip.date_to, 'month')] |= slip

        for journal_id in slip_mapped_data: # For each journal_id.
            for slip_date in slip_mapped_data[journal_id]: # For each month.
                line_ids = []
                debit_sum = 0.0
                credit_sum = 0.0
                date = slip_date
                move_dict = {
                    'narration': '',
                    'ref': date.strftime('%B %Y'),
                    'journal_id': journal_id,
                    'date': date,
                }

                for slip in slip_mapped_data[journal_id][slip_date]:
                    move_dict['narration'] += slip.number or '' + ' - ' + slip.employee_id.name or ''
                    move_dict['narration'] += '\n'
                    for line in slip.line_ids.filtered(lambda line: line.category_id):
                        amount = -line.total if slip.credit_note else line.total
                        if line.code == 'NET': # Check if the line is the 'Net Salary'.
                            for tmp_line in slip.line_ids.filtered(lambda line: line.category_id):
                                if tmp_line.salary_rule_id.not_computed_in_net: # Check if the rule must be computed in the 'Net Salary' or not.
                                    if amount > 0:
                                        amount -= abs(tmp_line.total)
                                    elif amount < 0:
                                        amount += abs(tmp_line.total)
                        if float_is_zero(amount, precision_digits=precision):
                            continue
                        debit_account_id = line.salary_rule_id.account_debit.id
                        credit_account_id = line.salary_rule_id.account_credit.id

                        if debit_account_id: # If the rule has a debit account.
                            debit = amount if amount > 0.0 else 0.0
                            credit = -amount if amount < 0.0 else 0.0

                            debit_line = self._prepare_line_values(line, debit_account_id, date, debit, credit)
                            line_ids.append(debit_line)

                        if credit_account_id: # If the rule has a credit account.
                            debit = -amount if amount < 0.0 else 0.0
                            credit = amount if amount > 0.0 else 0.0

                            credit_line = self._prepare_line_values(line, credit_account_id, date, debit, credit)
                            line_ids.append(credit_line)

                for line_id in line_ids: # Get the debit and credit sum.
                    debit_sum += line_id['debit']
                    credit_sum += line_id['credit']

                # The code below is called if there is an error in the balance between credit and debit sum.
                if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
                    acc_id = slip.journal_id.default_credit_account_id.id
                    if not acc_id:
                        raise UserError(_('The Expense Journal "%s" has not properly configured the Credit Account!') % (slip.journal_id.name))
                    existing_adjustment_line = (
                        line_id for line_id in line_ids if line_id['name'] == _('Adjustment Entry')
                    )
                    adjust_credit = next(existing_adjustment_line, False)

                    if not adjust_credit:
                        adjust_credit = {
                            'name': _('Adjustment Entry'),
                            'partner_id': False,
                            'account_id': acc_id,
                            'journal_id': slip.journal_id.id,
                            'date': date,
                            'debit': 0.0,
                            'credit': debit_sum - credit_sum,
                        }
                        line_ids.append(adjust_credit)
                    else:
                        adjust_credit['credit'] = debit_sum - credit_sum

                elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
                    acc_id = slip.journal_id.default_debit_account_id.id
                    if not acc_id:
                        raise UserError(_('The Expense Journal "%s" has not properly configured the Debit Account!') % (slip.journal_id.name))
                    existing_adjustment_line = (
                        line_id for line_id in line_ids if line_id['name'] == _('Adjustment Entry')
                    )
                    adjust_debit = next(existing_adjustment_line, False)

                    if not adjust_debit:
                        adjust_debit = {
                            'name': _('Adjustment Entry'),
                            'partner_id': False,
                            'account_id': acc_id,
                            'journal_id': slip.journal_id.id,
                            'date': date,
                            'debit': credit_sum - debit_sum,
                            'credit': 0.0,
                        }
                        line_ids.append(adjust_debit)
                    else:
                        adjust_debit['debit'] = credit_sum - debit_sum

                # Add accounting lines in the move
                move_dict['line_ids'] = [(0, 0, line_vals) for line_vals in line_ids]
                move = self.env['account.move'].create(move_dict)
                for slip in slip_mapped_data[journal_id][slip_date]:
                    slip.write({'move_id': move.id, 'date': date})
        return True

    def _prepare_line_values(self, line, account_id, date, debit, credit):

        analytic_tag_ids = False
        analytic_account_id = False

        if line.code == 'ARL':
            partner = line.slip_id.contract_id.entity_ids.search([("entity", "=", 'arl'), ("contract_id", "=", line.slip_id.contract_id.id)], limit=1).partner_id.id
        elif line.code == 'CAJACOMPENSACION':
            partner = line.slip_id.contract_id.entity_ids.search([("entity", "=", 'ccf'), ("contract_id", "=", line.slip_id.contract_id.id)], limit=1).partner_id.id
        elif line.code == 'SALUDEMPRESA':
            partner = line.slip_id.contract_id.entity_ids.search([("entity", "=", 'eps'), ("contract_id", "=", line.slip_id.contract_id.id)], limit=1).partner_id.id
        elif line.code == 'SALUDEMPLEADO':
            partner = line.slip_id.contract_id.entity_ids.search([("entity", "=", 'eps'), ("contract_id", "=", line.slip_id.contract_id.id)], limit=1).partner_id.id
        elif line.code == 'PENSIONEMPLEADO':
            partner = line.slip_id.contract_id.entity_ids.search([("entity", "=", 'afp'), ("contract_id", "=", line.slip_id.contract_id.id)], limit=1).partner_id.id
        elif line.code == 'PENSIONEMPRESA':
            partner = line.slip_id.contract_id.entity_ids.search([("entity", "=", 'afp'), ("contract_id", "=", line.slip_id.contract_id.id)], limit=1).partner_id.id
        elif line.code == 'FSP':
            partner = line.slip_id.contract_id.entity_ids.search([("entity", "=", 'fsp'), ("contract_id", "=", line.slip_id.contract_id.id)], limit=1).partner_id.id
        elif line.code == 'ICBF':
            partner = line.slip_id.contract_id.entity_ids.search([("entity", "=", 'icbf'), ("contract_id", "=", line.slip_id.contract_id.id)], limit=1).partner_id.id
        elif line.code == 'SENA':
            partner = line.slip_id.contract_id.entity_ids.search([("entity", "=", 'sena'), ("contract_id", "=", line.slip_id.contract_id.id)], limit=1).partner_id.id
        elif line.code == 'CESANTIAS':
            partner = line.slip_id.contract_id.entity_ids.search([("entity", "=", 'fc'), ("contract_id", "=", line.slip_id.contract_id.id)], limit=1).partner_id.id
        elif line.code == 'CESANTIAS_LIQ':
            partner = line.slip_id.contract_id.entity_ids.search([("entity", "=", 'fc'), ("contract_id", "=", line.slip_id.contract_id.id)], limit=1).partner_id.id
        elif line.code == 'INTCESANTIAS':
            partner = line.slip_id.contract_id.entity_ids.search([("entity", "=", 'fc'), ("contract_id", "=", line.slip_id.contract_id.id)], limit=1).partner_id.id
        else:
            partner = line.employee_id.partner_id.id

        if line.salary_rule_id.analytic_account_id.id:
            analytic_account_id = line.salary_rule_id.analytic_account_id.id
            if line.salary_rule_id.analytic_account_id.tag_id.id and not line.salary_rule_id.tag_id:
                tag_id = self.env['account.analytic.tag'].search([("id", "=", line.salary_rule_id.analytic_account_id.tag_id.id)]).id
                analytic_tag_ids = (tag_id, tag_id)
            else:
                if line.salary_rule_id.tag_id.id:
                    tag_id = self.env['account.analytic.tag'].search([("id", "=", line.salary_rule_id.tag_id.id)]).id
                    analytic_tag_ids = (tag_id, tag_id)

        else:
            if line.slip_id.contract_id.analytic_account_id.id:
                analytic_account_id = line.slip_id.contract_id.analytic_account_id.id
                if line.slip_id.contract_id.analytic_account_id.tag_id.id and not line.salary_rule_id.tag_id:
                    tag_id = self.env['account.analytic.tag'].search([("id", "=", line.slip_id.contract_id.analytic_account_id.tag_id.id)]).id
                    analytic_tag_ids = (tag_id, tag_id)
                else:
                    if line.salary_rule_id.tag_id.id:
                        tag_id = self.env['account.analytic.tag'].search( [("id", "=", line.salary_rule_id.tag_id.id)]).id
                        analytic_tag_ids = (tag_id, tag_id)

        if line.slip_id.contract_id.tag_id.id:
            tag_id = self.env['account.analytic.tag'].search([("id", "=", line.slip_id.contract_id.tag_id.id)]).id
            analytic_tag_ids = (tag_id, tag_id)

        account = self.env['account.account'].search([("id", "=", account_id)])
        if account:
            if account.blocking_analytic_payroll == True:
                analytic_tag_ids = False
                analytic_account_id = False
            if account.partner_employee_payroll == True:
                partner = line.employee_id.partner_id.id

        return {
            'name': line.name,
            'partner_id': partner,
            'account_id': account_id,
            'journal_id': line.slip_id.struct_id.journal_id.id,
            'date': date,
            'debit': debit,
            'credit': credit,
            'analytic_account_id': analytic_account_id,
            'analytic_tag_ids': analytic_tag_ids
        }