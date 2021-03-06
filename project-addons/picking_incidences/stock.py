# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pexego Sistemas Informáticos All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@pexego.es>$
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

from openerp import fields, models, api, _, exceptions
import openerp.addons.decimal_precision as dp
from openerp.tools.float_utils import float_compare, float_round


class StockMove(models.Model):

    _inherit = "stock.move"

    qty_ready = fields.Float('Qty ready', readonly=True,
                             digits=dp.get_precision('Product Unit of'
                                                     ' Measure'))


class StockPicking(models.Model):

    _inherit = "stock.picking"

    with_incidences = fields.Boolean('With incidences', readonly=True)

    @api.one
    def action_accept_ready_qty(self):
        self.with_incidences = False
        new_moves = []
        for move in self.move_lines:
            if move.state in ('done', 'cancel'):
                # ignore stock moves cancelled or already done
                continue
            precision = move.product_uom.rounding
            remaining_qty = move.product_uom_qty - move.qty_ready
            remaining_qty = float_round(remaining_qty,
                                        precision_rounding=precision)
            if float_compare(remaining_qty, 0,
                             precision_rounding=precision) > 0 and \
                float_compare(remaining_qty, move.product_qty,
                              precision_rounding=precision) < 0:
                new_move = move.split(move, remaining_qty)
                new_moves.append(new_move)
        if new_moves:
            new_moves = self.env['stock.move'].browse(new_moves)
            self._create_backorder(self, backorder_moves=new_moves)
            new_moves.write({'qty_ready': 0.0})
            self.do_unreserve()
            self.recheck_availability()
        self.message_post(body=_("User %s accepted ready quantities.") %
                          (self.env.user.name))

    @api.multi
    def action_assign(self):
        res = super(StockPicking, self).action_assign()
        for pick in self:
            pick.write({'with_incidences': False})
        return res

    @api.cr_uid_ids_context
    def do_enter_transfer_details(self, cr, uid, picking, context=None):
        for pick in self.pool['stock.picking'].browse(cr, uid, picking,
                                                      context=context):
            if pick.with_incidences:
                raise exceptions.Warning(_("Cannot process picking with "
                                           "incidences. Please fix or "
                                           "ignore it."))
        return super(StockPicking, self).do_enter_transfer_details(cr, uid,
                                                                   picking,
                                                                   context)

    @api.multi
    def action_done(self):
        for pick in self:
            if pick.with_incidences:
                raise exceptions.Warning(_("Cannot process picking with "
                                           "incidences. Please fix or "
                                           "ignore it."))
        return super(StockPicking, self).action_done()
