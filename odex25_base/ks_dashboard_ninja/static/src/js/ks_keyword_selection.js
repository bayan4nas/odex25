odoo.define('ks_dashboard_ninja.ks_keyword_selection', function(require) {
    "use strict";

    var registry = require('web.field_registry');
    var AbstractField = require('web.AbstractField');
    var core = require('web.core');
    var ajax = require('web.ajax');

    var QWeb = core.qweb;

    //Widget for dashboard item theme using while creating dashboard item.
    var KsKeywordSelection = AbstractField.extend({

        supportedFieldTypes: ['char'],
        resetOnAnyFieldChange: true,

        events: _.extend({}, AbstractField.prototype.events, {
            'click .ks_input_custom': 'onclickvalues',
            'click .ks_response_container_list': 'onResponseSelect',
            'click .ks_response_container_list_zero': 'onResponseSelect',
            'keyup #ks_selection_field' :'onKeyup'
        }),


       init: function(parent, state, params) {
       this.ks_new_value = [];
       this.ks_data_model = [];
       this._super.apply(this, arguments);
       },



        _render: async function() {
            var self = this;
            self.ks_data_model = await ajax.jsonRpc('/web/dataset/call_kw', 'call',{
            model:'ks_dashboard_ninja.arti_int',
            method:'ks_get_keywords',
            args:[],
            kwargs: {},
        })
        self.ks_new_value = self.ks_data_model
            self.$el.empty();
            var $view = $(QWeb.render('KsKeywordSelection', {ks_values:self.ks_data_model,ks_fixed_value:self.value}));
            self.$el.append($view)
            if ($view.find("#ks_selection_field")[0].value == "false"){
                $view.find("#ks_selection_field")[0].value = ""
            }
        },

        onclickvalues: async function(ev){
        var self = this;
        if ($('.ks_response_container_list .d-block').length == 0){
        _.each($('.ks_response_container_list'), function(item) {
                $(item).removeClass('d-none');
                $(item).addClass('d-block');
            });
        }

        },

        onKeyup: function(ev) {
        var value = ev.target.value;
        var self=this;
        if (value.length){
            var ks_value = value.toUpperCase();
            self.ks_new_value =[];
            if ($('.ks_response_container_list').length){
                _.each($('.ks_response_container_list'),function(item){
                    if (item.innerText.toUpperCase().indexOf(ks_value) > -1){
                        $(item).addClass("d-block")
                        $(item).removeClass("d-none")
                    }else{
                    $(item).removeClass("d-block")
                        $(item).addClass("d-none")
                    }
                })
            }
            $('.ks_response_container_list_zero').removeClass("d-none")
//            $('.ks_response_container_list_zero').addClass("d-block")
            $('.ks_response_container_list_zero .ks_response span')[0].innerText = value

        }else{
            if ($('.ks_response_container_list .d-block').length == 0){
            _.each($('.ks_response_container_list'), function(item) {
                $(item).removeClass('d-none');
                $(item).addClass('d-block');
            });
        }

        }


    },

   onResponseSelect: function(ev) {
        var self = this;
        if ($(ev.currentTarget).hasClass("ks_response_container_list_zero")){
            var value = $(ev.currentTarget).find(".ks_response span")[0].innerText;
        }else{
        var value = $(ev.currentTarget).find(".ks_response")[0].innerText;
        }
        self._setValue(value);
    },

    });

    registry.add('ks_keyword_selection', KsKeywordSelection);

    return {
        KsKeywordSelection: KsKeywordSelection
    };

});