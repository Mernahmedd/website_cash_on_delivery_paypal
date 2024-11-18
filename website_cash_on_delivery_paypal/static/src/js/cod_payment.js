/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from '@web/core/network/rpc_service';
import { KeepLast } from "@web/core/utils/concurrency";

const PaymentOptionWidgetPaypal = publicWidget.Widget.extend({
    selector: '.oe_website_sale',
    events:  {
           'click .o_payment_option': '_onClickPaymentOptionCodPaypal',
        },


    start: function () {
        var self = this;
        this.KeepLast = new KeepLast();
        this.KeepLast.add(jsonrpc(
                '/shop/update/provider/paypal',{
                    provider_id: false,
            })).then(this._handleProviderUpdateResult.bind(this));
        return this._super.apply(this, arguments);
    },

    _handleProviderUpdateResult: function (result) {
            var $amountCod = $('#order_cod_paypal .monetary_field');
            var $amountUntaxed = $('#order_total_untaxed .monetary_field');
            var $amountTax = $('#order_total_taxes .monetary_field');
            var $amountTotal = $('#order_total .monetary_field, #amount_total_summary.monetary_field');

            if (result.status === true) {
                $amountCod.html(result.new_amount_cod);
                $amountUntaxed.html(result.new_amount_untaxed);
                $amountTax.html(result.new_amount_tax);
                $amountTotal.html(result.new_amount_total);

            } else {
                $amountCod.html(result.new_amount_cod);
                $amountUntaxed.html(result.new_amount_untaxed);
                $amountTax.html(result.new_amount_tax);
                $amountTotal.html(result.new_amount_total);
            }
    },

    _onClickPaymentOptionCodPaypal: function (ev) {
        var $providerOption = $(ev.currentTarget).find('input[name="o_payment_radio"]').attr('data-provider-code');
        this.KeepLast.add(jsonrpc(
            '/shop/update/provider/paypal',{
                provider_id: $providerOption,
        })).then(this._handleProviderUpdateResult.bind(this));
    },


    });

publicWidget.registry.PaymentOptionWidgetPaypal = PaymentOptionWidgetPaypal;
export default PaymentOptionWidgetPaypal