odoo.define('web_watermark.Watermark', function (require) {
    "use strict";

    var session = require('web.session');
    var WebClient = require('web.WebClient');
    var rpc = require('web.rpc');

    WebClient.include({
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self._applyWatermark();
            });
        },

        _applyWatermark: function () {
            var self = this;
            var userId = session.uid;

            // Fetch the language of the current user
            rpc.query({
                model: 'res.users',
                method: 'read',
                args: [[userId], ['lang']],
            }).then(function (userData) {
                var langCode = userData[0].lang || 'en_US';
                var isRtl = ['ar', 'he'].includes(langCode.split('_')[0]);

                // Fetch employee information based on the current user's user_id
                rpc.query({
                    model: 'hr.employee',
                    method: 'search_read',
                    domain: [['user_id', '=', userId]],
                    fields: ['name', 'emp_no', 'work_email'],
                    limit: 1,
                }).then(function (employees) {
                    if (employees.length > 0) {
                        var username = session.username;
                        var employee = employees[0];
                        var employeeNumber = employee.emp_no || 'N/A';
                        var username = employee.work_email || 'N/A';
                        var date = new Date().toLocaleDateString();

                        var watermarkText;
                        if (isRtl) {
                            watermarkText = "المستخدم: " + username  + "<br>التاريخ: " + date;
                        } else {
                            watermarkText = "User: " + username + "<br>Date: " + date;
                        }

                        var watermarkDiv = document.createElement('div');
                        watermarkDiv.className = 'watermark-container';

                        // Create fewer watermark elements to reduce visual clutter
                        for (var i = 0; i < 4; i++) {
                            for (var j = 0; j < 3; j++) {
                                var watermarkElement = document.createElement('div');
                                watermarkElement.className = 'watermark';
                                watermarkElement.innerHTML = watermarkText;
                                watermarkElement.style.top = (i * 400) + 'px';
                                watermarkElement.style.left = (j * 800) + 'px';
                                watermarkElement.style.transform = 'rotate(-30deg)';
                                watermarkDiv.appendChild(watermarkElement);
                            }
                        }

                        document.body.appendChild(watermarkDiv);
                    }
                });
            });
        },
    });

    // CSS for the watermark
    var css = `
        .watermark-container {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 1000;
            overflow: hidden;
        }
        .watermark {
            position: absolute;
            font-size: 20px; /* Slightly reduced font size */
            font-family: 'Arial', sans-serif;
            color: rgba(0, 0, 0, 0.15); /* Reduced color intensity */
            opacity: 1.0; /* Reduced opacity */
            white-space: nowrap;
            user-select: none;
            text-align: center;
            line-height: 1.5;
        }
    `;

    var style = document.createElement('style');
    style.type = 'text/css';
    if (style.styleSheet){
        style.styleSheet.cssText = css;
    } else {
        style.appendChild(document.createTextNode(css));
    }

    document.head.appendChild(style);
});