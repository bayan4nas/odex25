odoo.define('simplify_access_management.hide_export', function (require) {
    "use strict";

    var ListRenderer = require('web.ListRenderer');
    var session = require("web.Session");
    var rpc = require('web.rpc');

    ListRenderer.include({

        _render: function () {
            const res = this._super.apply(this, arguments);
            const self = this;
            this._super.apply(this, arguments);
            
            var hash = window.location.hash.replace("#", '').split("&");
            let cids;
            if(hash.findIndex(ele => ele.includes("cid")) == -1)
                cids = session.company_id;
            else {
                cids = hash.filter(ele => ele.includes("cid"))[0].split("=")[1].split(",");
                cids = cids.length > 0? parseInt(cids[0]): session.company_id;
            }
            let model = hash.filter(ele=>ele.includes("model"))?.[0];
            model = model? model.split("=")?.[1].split(",")?.[0]: model;
            if(cids && model) {
                rpc.query({
                    model:'access.management',
                    method: 'is_export_hide',
                    args: [cids, model]
                }).then(function(result){
                    if(result) {
                        var btn1 = setInterval(function() {
                        if ($('.o_list_export_xlsx').length) {
                                $('.o_list_export_xlsx').remove();
                                clearInterval(btn1);
                        }
                        }, 50);
                    }
                });
            }
            return res;

        },

    });

});