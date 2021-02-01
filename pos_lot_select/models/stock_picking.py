# # -*- coding: utf-8 -*-
# from itertools import groupby
# from odoo.exceptions import ValidationError
# from odoo import api, fields, models , _
#
#
# class StockPicking(models.Model):
#     _inherit = 'stock.picking'
#
#     def read(self, fields=None, load='_classic_read'):
#         res = super(StockPicking, self).read(fields, load)
#         for this in self:
#             if this.origin:
#                 if 'S0' in this.origin:
#                     sale_order = this.env['sale.order'].search([('name','=',this.origin)])
#                     if sale_order:
#                         for this_lot_line in this.move_line_ids_without_package:
#                             for sale_lot_line in sale_order.order_line:
#                                 if this_lot_line.product_id == sale_lot_line.product_id:
#                                     this_lot_line.lot_id = sale_lot_line.lot_id.id
#         return res
#
#     invoice_unfixed = fields.Many2one('account.move')
#     sale_type = fields.Selection([('fixed', 'Fixed'),
#                                         ('unfixed', 'Unfixed')], string='sale type')
#
#     def action_done(self):
#         res = super(StockPicking, self).action_done()
#         for rec in self.filtered(lambda x: x.state == 'done'):
#             if 'S0' in rec.origin:
#                 rec.create_gold_journal_entry_sale()
#                 if rec.invoice_unfixed :
#                     rec.create_unfixed_journal_entry_sale()
#             if 'P0' in self.group_id.name:
#                 rec.create_gold_journal_entry_sale()
#                 if rec.bill_unfixed :
#                     rec.create_unfixed_journal_entry_sale()
#         return res
#     #
#     def create_gold_journal_entry_sale(self):
#         self.ensure_one()
#         if 'P0' in self.group_id.name:
#             purchase_obj = self.env['purchase.order'].search([('name','=',self.group_id.name)])
#             moves = self.move_lines.filtered(lambda x: x._is_in() and
#                                                         x.product_id and
#                                                         x.product_id.gold and
#                                                         x.product_id.categ_id and
#                                                         x.product_id.categ_id.is_gold and
#                                                         x.product_id.categ_id.gold_on_hand_account)
#             if moves:
#                 total_purity = 0
#                 product_dict = {}
#                 description = '%s' % self.name
#                 for product_id, move_list in groupby(moves, lambda x: x.product_id):
#                     description = '%s-%s' % (description, product_id.display_name)
#                     if product_id not in product_dict.keys():
#                         product_dict[product_id] = sum(
#                             x.pure_weight for x in move_list)
#                     else:
#                         product_dict[product_id] = product_dict[product_id] + sum(
#                             x.pure_weight for x in move_list)
#                 total_purity = sum(value for key, value in product_dict.items())
#                 if total_purity > 0.0 and product_dict and \
#                         self.partner_id :
#                     if not next(iter(product_dict)).categ_id.gold_journal.id:
#                         raise ValidationError(_('Please fill gold journal in product Category'))
#                     journal_id = next(iter(product_dict)).categ_id.gold_journal.id
#     #
#                     move_lines = self._prepare_account_move_line(product_dict)
#                     if move_lines:
#                         AccountMove = self.env['account.move'].with_context(
#                             default_journal_id=journal_id)
#                         date = self._context.get('force_period_date',
#                                                   fields.Date.context_today(self))
#                         type_of_action = ''
#                         if purchase_obj.order_type.is_fixed:
#                             type_of_action = 'fixed'
#                         elif  purchase_obj.order_type.gold:
#                             type_of_action = 'unfixed'
#                         else:
#                             pass
#                         new_account_move = AccountMove.sudo().create({
#                              'journal_id': journal_id,
#                              'line_ids': move_lines,
#                              'date': date,
#                              'ref': description,
#                              'type': 'entry',
#                              'type_of_action': type_of_action,
#                         })
#                         new_account_move.post()
#                         if purchase_obj:
#                             purchase_obj.write({'stock_move_id': new_account_move.id})
#         elif 'S0' in self.origin:
#             sale_obj = self.env['sale.order'].search([('name','=',self.origin)])
#             moves = self.move_lines.filtered(lambda x: x._is_out() and
#                                                         x.product_id and
#                                                         x.product_id.gold and
#                                                         x.product_id.categ_id and
#                                                         x.product_id.categ_id.is_gold and
#                                                         x.product_id.categ_id.gold_on_hand_account)
#             if moves:
#                 total_purity = 0
#                 product_dict = {}
#                 description = '%s' % self.name
#                 for product_id, move_list in groupby(moves, lambda x: x.product_id):
#                     description = '%s-%s' % (description, product_id.display_name)
#                     if product_id not in product_dict.keys():
#                         product_dict[product_id] = sum(
#                             x.pure_weight for x in move_list)
#                     else:
#                         product_dict[product_id] = product_dict[product_id] + sum(
#                             x.pure_weight for x in move_list)
#                 total_purity = sum(value for key, value in product_dict.items())
#                 if total_purity > 0.0 and product_dict and \
#                         self.partner_id :
#                     if not next(iter(product_dict)).categ_id.gold_journal.id:
#                         raise ValidationError(_('Please fill gold journal in product Category'))
#                     journal_id = next(iter(product_dict)).categ_id.gold_journal.id
#     #
#                     move_lines = self._prepare_account_move_line(product_dict)
#                     if move_lines:
#                         AccountMove = self.env['account.move'].with_context(
#                              default_journal_id=journal_id)
#                         date = self._context.get('force_period_date',
#                                                   fields.Date.context_today(self))
#                         type_of_action = ''
#                         if sale_obj.order_type.is_fixed:
#                             type_of_action = 'fixed'
#                         elif  sale_obj.order_type.gold:
#                             type_of_action = 'unfixed'
#                         else:
#                             pass
#                         new_account_move = AccountMove.sudo().create({
#                              'journal_id': journal_id,
#                              'line_ids': move_lines,
#                              'date': date,
#                              'ref': description,
#                              'type': 'entry',
#                              'type_of_action':type_of_action,
#                         })
#                         new_account_move.post()
#                         if sale_obj:
#                             sale_obj.write({'stock_move_id': new_account_move.id})
#     #
#     def _prepare_account_move_line(self, product_dict):
#         if 'P0' in self.group_id.name:
#             debit_lines = []
#             for product_id, value in product_dict.items():
#                 if not product_id.categ_id.gold_on_hand_account.id or not product_id.categ_id.gold_stock_input_account.id:
#                     raise ValidationError(_('Please fill gold accounts in product Category'))
#                 debit_lines.append({
#                     'name': '%s - %s' % (self.name, product_id.name),
#                     'product_id': product_id.id,
#                     'quantity': 1,
#                     'product_uom_id': product_id.uom_id.id,
#                     'ref': '%s - %s' % (self.name, product_id.name),
#                     'partner_id': self.partner_id.id,
#                     'debit': round(value, 3),
#                     'credit': 0,
#                     'account_id': product_id.categ_id.gold_on_hand_account.id,
#                 })
#             credit_line = [{
#                 'name': '%s - %s' % (self.name, product_id.name),
#                 'product_id': product_id.id,
#                 'quantity': 1,
#                 'product_uom_id': product_id.uom_id.id,
#                 'ref': '%s - %s' % (self.name, product_id.name),
#                 'partner_id': self.partner_id.id,
#                 'debit': 0,
#                 'credit': sum(x['debit'] for x in debit_lines),
#                 'account_id': product_id.categ_id.gold_stock_input_account.id,
#             }]
#             res = [(0, 0, x) for x in debit_lines + credit_line]
#             return res
#         elif 'S0' in self.origin:
#             credit_lines = []
#             for product_id, value in product_dict.items():
#                 if not product_id.categ_id.gold_on_hand_account.id or not product_id.categ_id.gold_stock_output_account.id:
#                     raise ValidationError(_('Please fill gold accounts in product Category'))
#                 credit_lines.append({
#                     'name': '%s - %s' % (self.name, product_id.name),
#                     'product_id': product_id.id,
#                     'quantity': 1,
#                     'product_uom_id': product_id.uom_id.id,
#                     'ref': '%s - %s' % (self.name, product_id.name),
#                     'partner_id': self.partner_id.id,
#                     'debit': 0,
#                     'credit': round(value, 3),
#                     'account_id': product_id.categ_id.gold_on_hand_account.id,
#                 })
#             debit_line = [{
#                 'name': '%s - %s' % (self.name, product_id.name),
#                 'product_id': product_id.id,
#                 'quantity': 1,
#                 'product_uom_id': product_id.uom_id.id,
#                 'ref': '%s - %s' % (self.name, product_id.name),
#                 'partner_id': self.partner_id.id,
#                 'debit': sum(x['credit'] for x in credit_lines),
#                 'credit': 0,
#                 'account_id': product_id.categ_id.gold_stock_output_account.id,
#             }]
#             res = [(0, 0, x) for x in credit_lines + debit_line]
#             return res
#     #
#     #
#     #
#     #
#     #
#     def create_unfixed_journal_entry_sale(self):
#         self.ensure_one()
#         if 'P0' in self.group_id.name:
#             account_move_obj = self.env['account.move'].search([('id','=',self.bill_unfixed.id)])
#             moves = self.move_lines.filtered(lambda x:
#                                                        x.product_id and
#                                                        x.product_id.gold and
#                                                        x.product_id.categ_id and
#                                                        x.product_id.categ_id.is_gold and
#                                                        x.product_id.categ_id.gold_on_hand_account)
#             if moves:
#                 total_purity = 0
#                 product_dict = {}
#                 description = account_move_obj.name
#                 for product_id, move_list in groupby(moves, lambda x: x.product_id):
#                     if product_id not in product_dict.keys():
#                         product_dict[product_id] = sum(
#                             x.pure_weight for x in move_list)
#                     else:
#                         product_dict[product_id] = product_dict[product_id] + sum(
#                             x.pure_weight for x in move_list)
#                 total_purity = sum(value for key, value in product_dict.items())
#                 if not  account_move_obj.partner_id.gold_account_payable_id:
#                         raise ValidationError(_('Please fill gold payable account for the partner'))
#                 if total_purity > 0.0 and product_dict and \
#                         account_move_obj.partner_id and account_move_obj.partner_id.gold_account_payable_id:
#                     if not next(iter(product_dict)).categ_id.gold_purchase_journal.id:
#                         raise ValidationError(_('Please fill gold purchase journal in product Category'))
#                     journal_id = next(iter(product_dict)).categ_id.gold_purchase_journal.id
#                     move_lines = self._prepare_account_move_line_unfixed(product_dict)
#                     if move_lines:
#                         AccountMove = self.env['account.move'].with_context(default_type='entry',
#                             default_journal_id=journal_id)
#                         date = self._context.get('force_period_date',
#                                                  fields.Date.context_today(self))
#                         type_of_action = ''
#                         if account_move_obj:
#                             type_of_action = account_move_obj.purchase_type
#                         else:
#                             pass
#                         new_account_move = AccountMove.sudo().create({
#                             'journal_id': journal_id,
#                             'line_ids': move_lines,
#                             'date': date,
#                             'ref': description,
#                             'type': 'entry',
#                             'type_of_action':type_of_action,
#                         })
#                         new_account_move.post()
#                         if account_move_obj:
#                             if account_move_obj.unfixed_move_id_two and not account_move_obj.unfixed_move_id_three:
#                                 account_move_obj.write({'unfixed_move_id_three': new_account_move.id})
#                             if account_move_obj.unfixed_move_id and not account_move_obj.unfixed_move_id_two and not account_move_obj.unfixed_move_id_three:
#                                 account_move_obj.write({'unfixed_move_id_two': new_account_move.id})
#                             if not account_move_obj.unfixed_move_id and not account_move_obj.unfixed_move_id_two and not account_move_obj.unfixed_move_id_three:
#                                 account_move_obj.write({'unfixed_move_id': new_account_move.id})
#         elif 'S0' in self.origin:
#             account_move_obj = self.env['account.move'].search([('id','=',self.invoice_unfixed.id)])
#             moves = self.move_lines.filtered(lambda x:
#                                                        x.product_id and
#                                                        x.product_id.gold and
#                                                        x.product_id.categ_id and
#                                                        x.product_id.categ_id.is_gold and
#                                                        x.product_id.categ_id.gold_on_hand_account)
#             if moves:
#                 total_purity = 0
#                 product_dict = {}
#                 description = account_move_obj.name
#                 for product_id, move_list in groupby(moves, lambda x: x.product_id):
#                     if product_id not in product_dict.keys():
#                         product_dict[product_id] = sum(
#                             x.pure_weight for x in move_list)
#                     else:
#                         product_dict[product_id] = product_dict[product_id] + sum(
#                             x.pure_weight for x in move_list)
#                 total_purity = sum(value for key, value in product_dict.items())
#                 if not  account_move_obj.partner_id.gold_account_receivable_id:
#                         raise ValidationError(_('Please fill gold receivable account for the partner'))
#                 if total_purity > 0.0 and product_dict and \
#                         account_move_obj.partner_id and account_move_obj.partner_id.gold_account_receivable_id:
#                     if not next(iter(product_dict)).categ_id.gold_sale_journal.id:
#                         raise ValidationError(_('Please fill gold sale journal in product Category'))
#                     journal_id = next(iter(product_dict)).categ_id.gold_sale_journal.id
#                     move_lines = self._prepare_account_move_line_unfixed(product_dict)
#                     if move_lines:
#                         AccountMove = self.env['account.move'].with_context(default_type='entry',
#                             default_journal_id=journal_id)
#                         date = self._context.get('force_period_date',
#                                                  fields.Date.context_today(self))
#                         type_of_action = ''
#                         if account_move_obj:
#                             type_of_action = account_move_obj.sale_type
#                         else:
#                             pass
#                         new_account_move = AccountMove.sudo().create({
#                             'journal_id': journal_id,
#                             'line_ids': move_lines,
#                             'date': date,
#                             'ref': description,
#                             'type': 'entry',
#                             'type_of_action':type_of_action,
#                         })
#                         new_account_move.post()
#                         if account_move_obj:
#                             if account_move_obj.unfixed_move_id_two and not account_move_obj.unfixed_move_id_three:
#                                 account_move_obj.write({'unfixed_move_id_three': new_account_move.id})
#                             if account_move_obj.unfixed_move_id and not account_move_obj.unfixed_move_id_two and not account_move_obj.unfixed_move_id_three:
#                                 account_move_obj.write({'unfixed_move_id_two': new_account_move.id})
#                             if not account_move_obj.unfixed_move_id and not account_move_obj.unfixed_move_id_two and not account_move_obj.unfixed_move_id_three:
#                                 account_move_obj.write({'unfixed_move_id': new_account_move.id})
#
#
#     def _prepare_account_move_line_unfixed(self, product_dict):
#         if 'P0' in self.group_id.name:
#             debit_lines = []
#             account_move_obj = self.env['account.move'].search([('id','=',self.bill_unfixed.id)])
#             for product_id, value in product_dict.items():
#                 if not product_id.categ_id.gold_on_hand_account.id :
#                     raise ValidationError(_('Please fill gold accounts in product Category'))
#                 debit_lines.append({
#                     'name': '%s - %s' % (self.name, product_id.name),
#                     'product_id': product_id.id,
#                     'quantity': 1,
#                     'product_uom_id': product_id.uom_id.id,
#                     'ref': '%s - %s' % (self.name, product_id.name),
#                     'partner_id': account_move_obj.partner_id.id,
#                     'debit': round(value, 3),
#                     'credit': 0,
#                     'account_id': account_move_obj.partner_id.gold_account_payable_id.id ,
#                 })
#             credit_line = [{
#                 'name': '%s - %s' % (self.name, product_id.name),
#                 'product_id': product_id.id,
#                 'quantity': 1,
#                 'product_uom_id': product_id.uom_id.id,
#                 'ref': '%s - %s' % (self.name, product_id.name),
#                 'partner_id': False,
#                 'debit': 0,
#                 'credit': sum(x['debit'] for x in debit_lines),
#                 'account_id': product_id.categ_id.gold_on_hand_account.id,
#             }]
#             res = [(0, 0, x) for x in debit_lines + credit_line]
#             return res
#         elif 'S0' in self.origin:
#             credit_lines = []
#             account_move_obj = self.env['account.move'].search([('id','=',self.invoice_unfixed.id)])
#             for product_id, value in product_dict.items():
#                 if not product_id.categ_id.gold_on_hand_account.id :
#                     raise ValidationError(_('Please fill gold accounts in product Category'))
#                 credit_lines.append({
#                     'name': '%s - %s' % (self.name, product_id.name),
#                     'product_id': product_id.id,
#                     'quantity': 1,
#                     'product_uom_id': product_id.uom_id.id,
#                     'ref': '%s - %s' % (self.name, product_id.name),
#                     'partner_id': account_move_obj.partner_id.id,
#                     'debit': 0,
#                     'credit': round(value, 3),
#                     'account_id': product_id.categ_id.gold_on_hand_account.id,
#                 })
#             debit_line = [{
#                 'name': '%s - %s' % (self.name, product_id.name),
#                 'product_id': product_id.id,
#                 'quantity': 1,
#                 'product_uom_id': product_id.uom_id.id,
#                 'ref': '%s - %s' % (self.name, product_id.name),
#                 'partner_id': False,
#                 'debit': sum(x['credit'] for x in credit_lines),
#                 'credit': 0,
#                 'account_id': account_move_obj.partner_id.gold_account_receivable_id.id ,
#             }]
#             res = [(0, 0, x) for x in credit_lines + debit_line]
#             return res
#
#
#
#     def _check_backorder(self):
#         """ This method will loop over all the move lines of self and
#         check if creating a backorder is necessary. This method is
#         called during button_validate if the user has already processed
#         some quantities and in the immediate transfer wizard that is
#         displayed if the user has not processed any quantities.
#
#         :return: True if a backorder is necessary else False
#         """
#         quantity_todo = {}
#         quantity_done = {}
#         for move in self.mapped('move_lines'):
#             quantity_todo.setdefault(move.product_id.id, 0)
#             quantity_done.setdefault(move.product_id.id, 0)
#             quantity_todo[move.product_id.id] += move.product_uom_qty
#             quantity_done[move.product_id.id] += move.quantity_done
#         for ops in self.mapped('move_line_ids').filtered(lambda x: x.package_id and not x.product_id and not x.move_id):
#             for quant in ops.package_id.quant_ids:
#                 quantity_done.setdefault(quant.product_id.id, 0)
#                 quantity_done[quant.product_id.id] += quant.qty
#         for pack in self.mapped('move_line_ids').filtered(lambda x: x.product_id and not x.move_id):
#             quantity_done.setdefault(pack.product_id.id, 0)
#             quantity_done[pack.product_id.id] += pack.product_uom_id._compute_quantity(pack.qty_done, pack.product_id.uom_id)
#         return any(quantity_done[x] < quantity_todo.get(x, 0) for x in quantity_done)
#
#
#     def _create_backorder(self):
#
#         """ This method is called when the user chose to create a backorder. It will create a new
#         picking, the backorder, and move the stock.moves that are not `done` or `cancel` into it.
#         """
#         backorders = self.env['stock.picking']
#         purchase_order = self.env['purchase.order'].search([('name','=',self.group_id.name)])
#         if purchase_order:
#             gross_wt = 0.00
#             pure_wt = 0.00
#             for rec in purchase_order.order_line:
#                 gross_wt = (gross_wt + rec.gross_wt) * (rec.product_uom_qty)
#                 pure_wt =  rec.pure_wt
#         sale_order = self.env['sale.order'].search([('name','=',self.origin)])
#         if sale_order:
#             gross_wt = 0.00
#             pure_wt = 0.00
#             for rec in sale_order.order_line:
#                 gross_wt = (gross_wt + rec.gross_wt) * (rec.product_uom_qty)
#                 pure_wt =  rec.pure_wt
#
#
#         for picking in self:
#             moves_to_backorder = picking.move_lines.filtered(lambda x: x.state not in ('done', 'cancel'))
#             if moves_to_backorder:
#                 backorder_picking = picking.copy({
#                     'name': '/',
#                     'move_lines': [],
#                     'move_line_ids': [],
#                     'backorder_id': picking.id
#                 })
#                 picking.message_post(
#                     body=_('The backorder <a href=# data-oe-model=stock.picking data-oe-id=%d>%s</a> has been created.') % (
#                         backorder_picking.id, backorder_picking.name))
#                 moves_to_backorder.write({'picking_id': backorder_picking.id})
#                 moves_to_backorder.mapped('package_level_id').write({'picking_id':backorder_picking.id})
#                 moves_to_backorder.mapped('move_line_ids').write({'picking_id': backorder_picking.id})
#                 backorder_picking.move_lines.write({'gross_weight': abs(gross_wt - backorder_picking.move_lines.gross_weight)})
#                 backorder_picking.move_lines.write({'pure_weight': abs(pure_wt - backorder_picking.move_lines.pure_weight)})
#                 backorder_picking.action_assign()
#                 backorders |= backorder_picking
#         return backorders
