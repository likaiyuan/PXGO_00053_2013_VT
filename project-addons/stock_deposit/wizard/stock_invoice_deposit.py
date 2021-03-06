# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pexego All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api, exceptions, _


class StockInvoiceDeposit(models.TransientModel):
    _name = 'stock.invoice.deposit'

    def _get_journal(self):
        journal_obj = self.env['account.journal']
        journals = journal_obj.search([('type', '=', 'sale')])
        return journals and journals[0] or False

    journal_id = fields.Many2one('account.journal', 'Destination Journal', required=True, default=_get_journal)

    @api.multi
    def create_invoice(self):
        deposit_obj = self.env['stock.deposit']
        deposit_ids = self.env.context.get('active_ids', [])
        deposits = deposit_obj.search([('id', 'in', deposit_ids), ('state', '=', 'sale')])
        invoice_ids = []
        if not deposits:
            raise exceptions.Warning(_('No deposit'), _('No deposit selected'))
        sales = list(set([x.sale_id for x in deposits]))
        for sale in sales:
            sale_deposit = deposit_obj.search(
                [('id', 'in', deposit_ids), ('sale_id', '=', sale.id)])

            sale_lines = self.env['sale.order.line']
            for deposit in sale_deposit:
                sale_lines += deposit.move_id.procurement_id.sale_line_id
            my_context = dict(self.env.context)
            my_context['invoice_deposit'] = True
            lines = sale_lines.with_context(my_context).invoice_line_create()
            inv_vals = self.env['sale.order']._prepare_invoice(sale, lines)
            inv_vals['journal_id'] = self.journal_id.id
            invoice = self.env['account.invoice'].create(inv_vals)
            invoice_ids.append(invoice.id)
            sale_deposit.write({'invoice_id': invoice.id})
        deposits.write({'state': 'invoiced'})
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        action['domain'] = "[('id','in', ["+','.join(map(str,invoice_ids))+"])]"
        return action
