odoo.define('property_management.website_sale', function (require) {

    require('web.dom_ready');
    var base = require("web_editor.base");
    var ajax = require('web.ajax');
    var utils = require('web.utils');
    var core = require('web.core');
    var config = require('web.config');
    var ProductConfiguratorMixin = require('sale.ProductConfiguratorMixin');
    var sAnimations = require('website.content.snippets.animation');
    require("website.content.zoomodoo");
    require("website_sale.website_sale");
    var _t = core._t;
    var _t = core._t;
    var sAnimations = require('website.content.snippets.animation');
    $(".select_chosen").chosen();
    sAnimations.registry.WebsiteSaleOptions.include({

        _onClickAdd: function (ev) {

            this.$form = $(ev.currentTarget).closest('form');
            var CustomerPrice = this.$form.find('.js_main_product input[name="customer_price"]').first().val();
            var LimitPrice = this.$form.find('.js_main_product input[name="product_limit_qty"]').first().val();
            var $PriceSection = this.$form.find('.js_main_product #customer_price_div').first();
            if (parseFloat(CustomerPrice) < parseFloat(LimitPrice)) {
                var price_alert = $PriceSection.parent().find('#data_price_warning');
                if (price_alert.length === 0) {
                    $PriceSection.prepend('<div class="alert alert-danger" role="alert" id="data_price_warning">' +
                        '<p>Sorry You Exceed Limit Price :' + LimitPrice + '</p></div>');
                }
                return false;
            }
            else {
                ev.preventDefault();
                return this._handleAdd($(ev.currentTarget).closest('form'));
            }
        },

        /*events: {
            'change input.js_customer_price': 'onChangeCustomerPrice',
        },

        onChangeCustomerPrice: function (ev) {
            console.log("On Customer Price Change>>>>>>>>>>>>");
            //this.triggerVariantChange($parent);
        },*/
    });
});
