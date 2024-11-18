# -*- coding: utf-8 -*-
import logging
import pprint
import werkzeug

from odoo import http, tools, SUPERUSER_ID, _
from odoo.http import request
from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing
_logger = logging.getLogger(__name__)

from odoo.addons.website_sale.controllers.main import WebsiteSale, PaymentPortal
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.fields import Command
from odoo.http import request
from odoo.addons.base.models.ir_qweb_fields import nl2br
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.payment import utils as payment_utils

class WebsiteCODPaypalPayment(http.Controller):

    _accept_url = '/cod_paypal/payment/feedback'

    @http.route(['/cod_paypal/payment/feedback'], type='http', auth='none', csrf=False)
    def cod_paypal_form_feedback(self, **post):
        post.update({ 'return_url':'/shop/payment/validate/paypal' })
        _logger.info('Beginning form_feedback with post data %s', pprint.pformat(post))  # debug
        tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data('cod_paypal', post)
        acquirer_sudo = tx_sudo.provider_id
        request.env['payment.transaction'].sudo()._handle_notification_data('cod_paypal', post)
        return werkzeug.utils.redirect(post.pop('return_url', '/'))

class WebsiteCODPaypalPayment(WebsiteSale):

    @http.route('/shop/payment/validate/paypal', type='http', auth="public", website=True, sitemap=False)
    def payment_validate_paypal(self, transaction_id=None, sale_order_id=None, **post):
        """ Method that should be called by the server when receiving an update
        for a transaction. State at this point :

         - UDPATE ME
        """
        if sale_order_id is None:
            order = request.website.sale_get_order()
            if not order and 'sale_last_order_id' in request.session:
                # Retrieve the last known order from the session if the session key `sale_order_id`
                # was prematurely cleared. This is done to prevent the user from updating their cart
                # after payment in case they don't return from payment through this route.
                last_order_id = request.session['sale_last_order_id']
                order = request.env['sale.order'].sudo().browse(last_order_id).exists()
        else:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            assert order.id == request.session.get('sale_last_order_id')

        if not order:
            transaction = request.session['__website_sale_last_tx_id']
            transaction_order = request.env['payment.transaction'].sudo().browse(transaction)
            sale_order_id = transaction_order.sale_order_ids
            order = transaction_order.sale_order_ids
        if not transaction_id:
            transaction = request.session['__website_sale_last_tx_id']
            transaction_id = request.env['payment.transaction'].sudo().browse(transaction)

        transaction = request.session['__website_sale_last_tx_id']
        transaction_order = request.env['payment.transaction'].sudo().browse(transaction)

        if transaction_id:
            tx = request.env['payment.transaction'].sudo().browse(transaction_id.id)
            # assert tx in order.transaction_ids()
        elif order:
            tx = order.get_portal_last_transaction()
        else:
            tx = None

        if not order or (order.amount_total and not tx):
            return request.redirect('/shop')

        if (not order.amount_total and not tx) or tx.state in ['pending', 'done', 'authorized']:
            if (not order.amount_total and not tx):
                # Orders are confirmed by payment transactions, but there is none for free orders,
                # (e.g. free events), so confirm immediately
                order.with_context(send_email=True).action_confirm()
        elif tx and tx.state == 'cancel':
            # cancel the quotation
            order.action_cancel()
        # clean context and session, then redirect to the confirmation page
        request.website.sale_reset()
        if tx and tx.state == 'draft':
            return request.redirect('/shop')

        if tx.provider_id.code == 'cod_paypal':
            payment_acquirer_obj = request.env['payment.provider'].sudo().search([('id','=', tx.provider_id.id)]) 
            # order.order_cod_paypal_available = True
            product_obj = request.env['product.product']
            extra_fees_product = request.env.ref('website_cash_on_delivery_paypal.product_product_fees').id
            product_ids = product_obj.sudo().search([('product_tmpl_id.id', '=', extra_fees_product)])
            order_line_obj = request.env['sale.order.line'].sudo().search([]) 
            order1 = order.sudo()         
    
            order.action_confirm()
            email_act = order.action_quotation_send()
            email_ctx = email_act.get('context', {})
    
            mail_template = order1._get_confirmation_template()
            order._send_order_notification_mail(mail_template)
            request.website.sale_reset()            
        return request.redirect('/shop/confirmation')
    
    @http.route(['/shop/confirmation'], type='http', auth="public", website=True, sitemap=False)
    def shop_payment_confirmation(self, **post):
        """ End of checkout process controller. Confirmation is basically seing
        the status of a sale.order. State at this point :

         - should not have any context / session info: clean them
         - take a sale.order id, because we request a sale.order and are not
           session dependant anymore
        """
        transaction = request.session['__website_sale_last_tx_id']
        transaction_order = request.env['payment.transaction'].sudo().browse(transaction)
        sale_order_id = transaction_order.sale_order_ids
        if sale_order_id:
            order = request.env['sale.order'].sudo().browse(sale_order_id.id)
            values = self._prepare_shop_payment_confirmation_values(order)
            return request.render("website_sale.confirmation", values)
        else:
            return request.redirect('/shop')
    
    @http.route(['/shop/update/provider/paypal'], type='json', auth='public', methods=['POST'], website=True, csrf=False)
    def update_eshop_provider_paypal(self, **post):
        
        order = request.website.sale_get_order()
        if order is None:
            if not order and 'sale_last_order_id' in request.session:
                last_order_id = request.session['sale_last_order_id']
                order = request.env['sale.order'].sudo().browse(last_order_id).exists()
        order_line_obj = request.env['sale.order.line']
        provider_id = post.get('provider_id')

        product_obj = request.env['product.product']
        extra_fees_product = request.env.ref('website_cash_on_delivery_paypal.product_product_fees').id
        product_ids = product_obj.sudo().search([('product_tmpl_id.id', '=', extra_fees_product)])
        payment_acquirer_obj = request.env['payment.provider'].sudo().search([('code','=', 'cod_paypal')],limit=1) 
        line_ids = request.env['sale.order.line'].sudo().search([('order_id','=',order.id),('is_cod_paypal','=',True)],limit=1)

        line_subtotal = 0.0

        for line in order.order_line:
            if 'is_cod_usdt' in line._fields and 'is_cod' in line._fields:
                if not line.is_cod_usdt and not line.is_cod_paypal and not line.is_cod:
                    line_subtotal += line.price_subtotal
            elif 'is_cod_usdt' in line._fields:         
                if not line.is_cod_paypal and not line.is_cod_usdt:
                    line_subtotal += line.price_subtotal
            elif 'is_cod' in line._fields:         
                if not line.is_cod_paypal and not line.is_cod:
                    line_subtotal += line.price_subtotal
            else:
                if not line.is_cod_paypal:
                    line_subtotal += line.price_subtotal

        cod_paypal_amount = ( line_subtotal * payment_acquirer_obj.paypal_extra_fees) /  100.0
        
        if provider_id == 'cod_paypal':
            if not order.id:
                pass
            if not line_ids:
                order_line_obj.sudo().create({
                            'product_id': product_ids.id,
                            'name': 'Discount',
                            'price_unit': cod_paypal_amount,
                            'order_id': order.id,
                            'product_uom':product_ids.uom_id.id,
                            'is_cod_paypal':True
                        })
            else:
                if line_ids.price_unit != cod_paypal_amount:
                    line_ids.sudo().update({'price_unit': cod_paypal_amount,})
        else:
            line_ids.sudo().unlink()

        return self._update_website_sale_cod_paypal_return(order, **post)

    def _update_website_sale_cod_paypal_return(self, order, **post):
        Monetary = request.env['ir.qweb.field.monetary']
        provider_id = (post.get('provider_id'))
        currency = order.currency_id
        if order:
            return {
                'provider_id': provider_id,
                'new_amount_cod': Monetary.value_to_html(order.amount_cod_paypal, {'display_currency': currency}),
                'new_amount_untaxed': Monetary.value_to_html(order.amount_untaxed, {'display_currency': currency}),
                'new_amount_tax': Monetary.value_to_html(order.amount_tax, {'display_currency': currency}),
                'new_amount_total': Monetary.value_to_html(order.amount_total, {'display_currency': currency}),
                'new_amount_total_raw': order.amount_total,
            }
        return {}
