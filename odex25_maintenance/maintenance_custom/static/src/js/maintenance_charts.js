odoo.define('maintenance.charts', function (require) {
"use strict";

var AbstractField = require('web.AbstractField');
var registry = require('web.field_registry');

var FieldChart = AbstractField.extend({
    className: 'pichart',
    _render: function () {
        var self = this
        var fields = self.attrs.keys.split(';')       
        var labels = self.attrs.labels.split(';')
        var backgroundColors = self.attrs.backgroundColors.split(';')
        var borderColors = self.attrs.borderColors.split(';')
        var cutoutPercentage = 50
        if (self.attrs.cutoutPercentage){
            cutoutPercentage = self.attrs.cutoutPercentage
        }
            
        self._rpc({
            model: self.model,
            method: 'search_read',
            fields: fields,
            domain: [['id', '=', self.res_id]],
        }).then(function (result) {
            var vals = result[0]
            var data = []
            for (var f = 0 ; f < fields.length ; f++) {
                var fld = fields[f]
                data += [vals[fld]]
            }
            var ctx = document.createElement("canvas");
            var myChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels:labels ,
                    datasets: [{
                        label: '# Work Orders',
                        data: data,
                        backgroundColor : backgroundColors,
                        borderColor:borderColors,
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive : true,
                    cutoutPercentage : cutoutPercentage,
                    title: {
                        display: true,
                        text: self.value,
                    },
                    legend: {
                        display: true,
                        position : 'right',
                        labels : {
                            boxWidth : 15,
                            usePointStyle : false,
                        },
                    }
                }
            });  
            //this.$el.empty();
            self.$el.append(ctx)
        });
       
    },
    
});

registry.add('pichart', FieldChart)
});