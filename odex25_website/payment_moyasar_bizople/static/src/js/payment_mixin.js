odoo.define('payment_moyasar_bizople.payment_form_mixin_moyasar', require => {
    'use strict';
    var ajax = require('web.ajax');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var PaymentForm = require('payment.payment_form');

    PaymentForm.include({
        payEvent: function (ev) {
            ev.preventDefault();
            var $checkedRadio = this.$('input[type="radio"]:checked');
            if ($checkedRadio.length === 1 && $checkedRadio.data('provider') === 'moyasar') {
                return this._createMoyasarToken(ev, $checkedRadio);
            } else {
                return this._super.apply(this, arguments);
            }
        },
        _createMoyasarToken: function(ev){
            ev.preventDefault();
            var form = this.el;
            var checked_radio = this.$('input[type="radio"]:checked');
            var self = this;
            if (ev.type === 'submit') {
                var button = $(ev.target).find('*[type="submit"]')[0]
            }else {
                var button = ev.target;
            }
            if (checked_radio.length === 1) {
                checked_radio = checked_radio[0];
                var acquirer_id = this.getAcquirerIdFromRadio(checked_radio);
                var acquirer_form = false;
                if (this.isNewPaymentRadio(checked_radio)) {
                    acquirer_form = this.$('#o_payment_add_token_acq_' + acquirer_id);
                } else {
                    acquirer_form = this.$('#o_payment_form_acq_' + acquirer_id);
                }
                var inputs_form = $('input', acquirer_form);
                var ds = $('input[name="data_set"]', acquirer_form)[0];

                var $tx_url = this.$el.find('input[name="prepare_tx_url"]');
                if ($tx_url.length === 1) {
                    var form_save_token = acquirer_form.find('input[name="o_payment_form_save_token"]').prop('checked');
                    return this._rpc({
                        route: $tx_url[0].value,
                        params: {
                            'acquirer_id': parseInt(acquirer_id),
                            'save_token': form_save_token,
                            'access_token': self.options.accessToken,
                            'success_url': self.options.successUrl,
                            'error_url': self.options.errorUrl,
                            'callback_method': self.options.callbackMethod,
                            'order_id': self.options.orderId,
                            'invoice_id': self.options.invoiceId,
                        },
                    }).then(function (result) {
                        if (result) {
                            $('#moyasarpayment').modal({ show: true, keyboard: false, backdrop: "static" });
                            $('#wrapwrap').css('z-index',1051)
                        }
                    })
                }
            }
        }
    })
})