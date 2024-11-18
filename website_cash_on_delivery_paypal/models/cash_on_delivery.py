# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare

class CreditPaymentAcquirer(models.Model):
    _inherit = 'payment.provider'

    paypal_extra_fees = fields.Integer('Extra Fees')

    def cod_paypal_get_form_action_url(self):
        return '/paypal/payment/feedback'
    