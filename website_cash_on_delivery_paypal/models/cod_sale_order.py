# -*- cod_paypaling: utf-8 -*-

from odoo import fields, models, api

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_cod_paypal = fields.Boolean(string="Is a cod_paypal", default=False)

    def _show_in_cart(self):
        # Exclude delivery line from showing up in the cart
        return not self.is_cod_paypal and super()._show_in_cart()

class SaleOrder(models.Model):
    _inherit = "sale.order"

    amount_cod_paypal = fields.Monetary(
        compute='_compute_amount_cod_paypal',
        string='cod_paypal Amount',
        help="The amount without tax.", store=True, tracking=True)

    @api.depends('order_line.price_unit', 'order_line.tax_id', 'order_line.discount', 'order_line.product_uom_qty')
    def _compute_amount_cod_paypal(self):
        for order in self:
            if True:
                order.amount_cod_paypal = sum(order.order_line.filtered('is_cod_paypal').mapped('price_subtotal'))