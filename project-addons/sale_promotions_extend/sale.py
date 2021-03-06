# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Marta Vázquez Rodríguez$ <marta@pexego.es>
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
from openerp.osv import osv, fields


class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'

    def _get_tag_recursivity(self, cr, uid, ids, context=None):

        tags = []
        tagsa = []
        tagsb = []

        for t in self.pool.get('product.tag').browse(cr, uid, ids, context):
            tagsb.append(t.id)
            print t
            if t.parent_id:
                tagsa = self._get_tag_recursivity(cr, uid, [t.parent_id.id],
                                             context)
                if tagsa:
                    tags = list(set(tagsa + tagsb))
        if tags:
            return tags
        else:
            return tagsb

    def _get_tags_product(self, cr, uid, ids, field_name, arg,
                                  context=None):
        result = {}
        for line in self.browse(cr, uid, ids, context=context):
            result[line.id] = ''
            tag_obj = self.pool.get('product.tag')
            stream = []
            tags = []
            if line.product_id and line.product_id.tag_ids:
                tag_ids = [x.id for x in line.product_id.tag_ids]
                tags = self._get_tag_recursivity(cr, uid,
                                                 tag_ids,
                                                 context)
                print tags
                if tags:
                    for tag in tag_obj.browse(cr, uid, tags):
                        stream.append(tag.name)
            if stream:
                result[line.id] = u", ".join(stream)
        return result

    _columns = {
        'product_tags': fields.function(_get_tags_product, string='Tags',
                                        type='char',
                                        size=255, store=True)
    }
