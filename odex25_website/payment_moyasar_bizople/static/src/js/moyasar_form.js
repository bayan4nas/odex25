odoo.define('payment_moyasar_bizople.payment_moyasara_js', require => {
    'use strict';

    const core = require('web.core');
	var publicWidget = require('web.public.widget');
    const ajax = require('web.ajax');

    publicWidget.registry.MoyasarModal = publicWidget.Widget.extend({
        selector: '.moyasar-modal',
        events: {
            'click .close-moyasar-form' : '_CloseMoyasarForm',
        },
        _CloseMoyasarForm : function(){
            console.log("CLOSED")
            $('#wrapwrap').css('z-index',1051)
            window.location.reload();
        },
    });
	
    publicWidget.registry.MoyasarFormRender = publicWidget.Widget.extend({
	    selector: '#payment_method',

	    start : function(){
            this._super(...arguments);
            var portal_order = $('#quote_content').find('#portal_order_id').val()

            ajax.jsonRpc("/get/moyasar/order",'call',{
                'data':true,
                'portal_order': portal_order,
            }).then(function(data){
                var amount = data['amount']
                var public_key = data['public_key']
                var callback_url = data['callback_url']
                var currency = data['currency']
                var description = data['description']

                if(currency == 'SAR'){
                    amount = amount*100
                }else if(currency == 'USD'){
                    amount = amount*100
                }else if(currency == 'KWD'){
                    amount = amount*1000
                }else if (currency == 'JPY'){
                    amount = amount
                }else{
                    amount = amount*100
                }
                Moyasar.init({
                    element: '.mysr-form',
                    // Amount in the smallest currency unit
                    // For example:
                    // 10 SAR = 10 * 100 Halalas
                    // 10 KWD = 10 * 1000 Fils
                    // 10 JPY = 10 JPY (Japanese Yen does not have fractions)
                    amount: amount.toFixed(),
                    currency: currency,
                    description: description,
                    publishable_api_key: public_key,
                    callback_url: callback_url+'/payment-status-return',

                    methods: [
                        'creditcard',
                        'stcpay',
                        'applepay'
                    ],
                    apple_pay: {
                        country: 'SA',
                        label: 'Test Merchant',
                        supported_countries: ['SA', 'US'],
                        validate_merchant_url: 'https://api.moyasar.com/v1/applepay/initiate',
                        validation_url: 'https://apple-pay-gateway.apple.com/paymentservices/paymentSession',
                    }
                });
            })
        },
	});

});