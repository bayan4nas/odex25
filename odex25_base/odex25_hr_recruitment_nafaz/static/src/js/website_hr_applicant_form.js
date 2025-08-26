odoo.define('website_hr_recruitment.apply', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var rpc = require('web.rpc');
    var core = require('web.core');
    var _t = core._t;

    publicWidget.registry.hrRecruitment = publicWidget.Widget.extend({
        selector: '#hr_recruitment_form',
        events: {
            'click #apply-btn': '_onClickApplyButton',
            'focusout #recruitment2': '_onFocusOutMail',
            'focusout #recruitment4': '_onFocusOutLinkedin',
        },

        start: function () {
            this._super.apply(this, arguments);
        },

        _onClickApplyButton: function (ev) {
            var linkedin_profile = $('#recruitment4').val();
            var resume = $('#recruitment6').val();
            if ($.trim(linkedin_profile) === '' && $.trim(resume) === '') {
                $('#recruitment4').attr('required', true);
                $('#recruitment6').attr('required', true);
            } else {
                $('#recruitment4').attr('required', false);
                $('#recruitment6').attr('required', false);
            }
        },

        _onFocusOutLinkedin: function (ev) {
            var linkedin = $(ev.currentTarget).val();
            if (!linkedin) {
                $(ev.currentTarget).removeClass('border-warning');
                $('#linkedin-message').removeClass('alert-warning').hide();
                return;
            }
            var linkedin_regex = /^(https?:\/\/)?([\w\.]*)linkedin\.com\/in\/(.*?)(\/.*)?$/;
            if (!linkedin_regex.test(linkedin)) {
                $('#linkedin-message').removeClass('alert-warning').hide();
                $(ev.currentTarget).addClass('border-warning');
                $('#linkedin-message').text(_t("The value entered doesn't seem like a LinkedIn profile.")).addClass('alert-warning').show();
            } else {
                $(ev.currentTarget).removeClass('border-warning');
                $('#linkedin-message').removeClass('alert-warning').hide();
            }
        },

        _onFocusOutMail: function (ev) {
            var self = this;
            var email = $(ev.currentTarget).val();
            if (!email) {
                $(ev.currentTarget).removeClass('border-warning');
                $('#email-message').removeClass('alert-warning').hide();
                return;
            }
            var job_id = $('#recruitment7').val();
            rpc.query({
                route: '/website_hr_recruitment/check_recent_application',
                params: {
                    email: email,
                    job_id: job_id,
                },
            }).then(function (data) {
                if (data.applied_same_job) {
                    $('#email-message').removeClass('alert-warning').hide();
                    $(ev.currentTarget).addClass('border-warning');
                    $('#email-message').text(_t('You already applied to this job position recently.')).addClass('alert-warning').show();
                } else if (data.applied_other_job) {
                    $('#email-message').removeClass('alert-warning').hide();
                    $(ev.currentTarget).addClass('border-warning');
                    $('#email-message').text(_t("You already applied to another position recently. You can continue if it's not a mistake.")).addClass('alert-warning').show();
                } else {
                    $(ev.currentTarget).removeClass('border-warning');
                    $('#email-message').removeClass('alert-warning').hide();
                }
            });
        },
    });
});
