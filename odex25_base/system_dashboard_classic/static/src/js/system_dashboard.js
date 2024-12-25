odoo.define('system_dashboard_classic.dashboard', function(require) {
    "use strict";

    var core = require('web.core');
    var session = require('web.session');
    var ajax = require('web.ajax');
    var ActionManager = require('web.ActionManager');
    var view_registry = require('web.view_registry');
    var Widget = require('web.Widget');
    var AbstractAction = require('web.AbstractAction');

    var QWeb = core.qweb;

    var _t = core._t;
    var _lt = core._lt;
    var functions = [];
    window.click_actions = [];

    var SystemDashboardView = AbstractAction.extend({
        template: 'system_dashboard_classic.dashboard',
        init: function(parent, context) {
            this._super(parent, context);
            var data = [];
            var self = this;
            window.selfOb = this;
            if (context.tag == 'system_dashboard_classic.dashboard') {
                self._rpc({
                        model: 'system_dashboard_classic.dashboard',
                        method: 'get_data',
                    }, []).then(function(result) {
                        console.log(result)
                        window.resultX = result;
                        if (result.employee !== undefined && result.employee !== '' && result.employee[0].length !== 0) {
                            $('#main-cards').css('display', 'flex');
                            $('.fn-id,.fn-department,.fn-job').show();
                            // SET EMPLOYEE DATA
                            if (result.employee[0][0] !== undefined) {
                                $(".img-box").css('background-image', 'url(data:image/png;base64,' + result.employee[0][0].image_128 + ')')
                                $("p.fn-section").html(result.employee[0][0].name);
                                $("p.fn-id").html(result.employee[0][0].emp_no);
                                if (result.employee[0][0].job_id.length !== 0) {
                                    $("p.fn-job").html(result.employee[0][0].job_id[1]);
                                }
                            } else {
                                $(".img-box").css('background-image', 'url(data:image/png;base64,' + result.user[0][0].image_128 + ')')
                                $("p.fn-section").html(result.user[0][0].display_name);
                                $("p.fn-id").html(result.user[0][0].id);
                            }
                            // SET MAIN CARD DATA (LEAVES - TIMESHEET - PAYSLIPS)
                            $(".leaves_count span.value").html(parseFloat(result['employee'][0][0].remaining_leaves).toFixed(2));
                            $(".timesheet_count span.value").html(result['employee'][0][0].timesheet_count);
                            $(".paylips_count span.value").html(result['employee'][0][0].payslip_count);
                            // LEAVES DO ACTION
                            $("#leaves_btn").on('click', function(event) {
                                event.stopPropagation();
                                event.preventDefault();
                                return self.do_action({
                                    name: _t("Leaves"),
                                    type: 'ir.actions.act_window',
                                    res_model: 'hr.holidays',
                                    src_model: 'hr.employee',
                                    view_mode: 'tree,form',
                                    view_type: 'form',
                                    views: [
                                        [false, 'list'],
                                        [false, 'form']
                                    ],
                                    context: {
                                        'search_default_employee_id': [result['employee'][0][0].id],
                                        'default_employee_id': result['employee'][0][0].id,
                                    },
                                    domain: [
                                        ['holiday_type', '=', 'employee'],
                                        ['holiday_status_id.limit', '=', false],
                                        ['state', '!=', 'refuse']
                                    ],
                                    target: 'main',
                                    flags:{
                                        reload: true,
                                    }
                                }, { on_reverse_breadcrumb: self.on_reverse_breadcrumb })
                            });

                            // TIMESHEET DO ACTION
                            $("#timesheet_btn").on('click', function(event) {
                                event.stopPropagation();
                                event.preventDefault();
                                return self.do_action({
                                    name: _t("Timesheets"),
                                    type: 'ir.actions.act_window',
                                    res_model: 'account.analytic.line',
                                    view_mode: 'tree,form',
                                    view_type: 'form',
                                    views: [
                                        [false, 'list'],
                                        [false, 'form']
                                    ],
                                    context: {
                                        'search_default_employee_id': [result['employee'][0][0].id],
                                    },
                                    domain: [
                                        ['user_id', '=', result['user'][0]]
                                    ],
                                    target: 'main',
                                    flags:{
                                        reload: true,
                                    }
                                }, { on_reverse_breadcrumb: self.on_reverse_breadcrumb })
                            });

                            // PAYSLIPS DO ACTION
                            $("#paylips_btn").on('click', function(event) {
                                event.stopPropagation();
                                event.preventDefault();
                                return self.do_action({
                                    name: _t("Payslips"),
                                    type: 'ir.actions.act_window',
                                    res_model: 'hr.payslip',
                                    view_mode: 'tree,form',
                                    view_type: 'form',
                                    views: [
                                        [false, 'list'],
                                        [false, 'form']
                                    ],
                                    context: {
                                        'search_default_employee_id': [result['employee'][0][0].id],
                                        'default_employee_id': result['employee'][0][0].id,
                                    },
                                    target: 'main',
                                    flags:{
                                        reload: true,
                                    }
                                }, { on_reverse_breadcrumb: self.on_reverse_breadcrumb })
                            });
                        } else {
                            if (result.user !== undefined && result.user !== '' && result.user[0].length !== 0) {
                                // SET EMPLOYEE DATA
                                $(".img-box").css('background-image', 'url(data:image/png;base64,' + result.user[0][0].image_128 + ')')
                                $("p.fn-section").html(result.user[0][0].name);
                                $("p.fn-id").html('ID: ' + result.user[0][0].id);
                            }
                        }

                        // Dynamic Cards (DO ACTIONS)
                        if (result.cards !== undefined && result.cards.length > 0) {
                            $.each(result.cards, function(index) {
                                if (result.cards[index].type == "approve") {
                                    window.card_data = result.cards[index];
                                    var card_title = (card_data.name_english.replace(/\s/g, '').toLocaleLowerCase());
                                    var btn = 'click button#' + (card_title + index);
                                    // BUILD APPROVE CARD
                                    window.card = buildCard(result.cards[index], index, 'table1');
                                    $(card).find('.card-header h4 span').html(_t(result.cards[index].name));
                                    // BUILD FOLLOW CARD
                                    window.card2 = buildCard(result.cards[index], index, 'table2');
                                    $(card2).find('.card-header h4 span').html(_t(result.cards[index].name));
                                    // APPENDING APPROVE CARD TO APPROVE TAB/SECTION
                                    self.$el.find('div.card-section1').append(card);
                                    // APPENDING FOLLOW CARD TO FOLLOW TAB/SECTION
                                    self.$el.find('div#details .card-section').append(card2);
                                }
                            });

                            // TRIGGERING BUTTONS IN THE APPROVE & FOLLOW CARD TO SHOW DETAILS
                            self.$el.find('tr[data-target="record-button"]').on('click', function(event) {
                                event.stopPropagation();
                                event.preventDefault();
                                // GET DATA OF BUTTON TO HANDEL IT
                                var model = $(this).attr('data-model');
                                var name = $(this).attr('data-name');
                                var domain = $(this).attr('data-domain');
                                var form_view = parseInt($(this).attr('form-view'));
                                var list_view = parseInt($(this).attr('list-view'));
                                var type = $(this).attr('data-type');

                                // CHECK DOMAIN
                                if (domain === undefined || domain === '') {
                                    domain = false;
                                } else {
                                    domain = JSON.parse(domain);
                                }
                                // CHECK FORM VIEW VALUE
                                if (isNaN(form_view)) {
                                    form_view = false;
                                }
                                // CHECK LIST VIEW VALUE
                                if (isNaN(list_view)) {
                                    list_view = false;
                                }

                                //FIRING DO ACTION
                                return self.do_action({
                                    name: _t(name),
                                    type: 'ir.actions.act_window',
                                    res_model: model,
                                    view_mode: 'tree,form',
                                    view_type: 'list',
                                    views: [
                                        [list_view, 'list'],
                                        [form_view, 'form']
                                    ],
                                    domain: domain,
                                    target: 'main',
                                    flags:{
                                        reload: true,
                                    }
                                }, { on_reverse_breadcrumb: function() { return self.reload(); } })
                            });

                        }
                        // Chart Settings
                        setTimeout(function() {
                            window.check = false;
                            //result.attendance[0].is_attendance = true;
                            var name = "";
                            if (result.employee[0][0] !== undefined) {
                                name = result.employee[0][0].name;
                            } else {
                                name = result.user[0][0].display_name;
                            }
                            if (result.attendance !== undefined) {
                                setupAttendanceArea(result.attendance[0], name);
                                // check button submission
                                $('button#check_button').on('click', function(event) {
                                    //var check = result.attendance[0].is_attendance; //false or true
                                    self._rpc({
                                        model: 'system_dashboard_classic.dashboard',
                                        method: 'checkin_checkout',
                                        context: { 'check': check },
                                    }, []).then(function(result) {
                                        $('.last-checkin-section').html('');
                                        $('.attendance-img-section').html('');
                                        $('#check_button').html('');
                                        setupAttendanceArea(result, resultX.employee[0][0].name);
                                    });
                                });
                            } else {
                                $('.attendance-section-body').hide();
                            }

                            // Charts Labels
                            if ($('body').hasClass('o_rtl') === true) {
                                var total_leaves_title = "الرصيد الكلي ";
                                var remaining_leaves_title = "رصيد الأيام المتبقية ";
                                var taken_leaves_title = "رصيد الأيام المأخوذة ";

                                var total_payroll_title = "إجمالي القسائم السنوية";
                                var remaining_payroll_title = "قسائم الراتب المتبقية ";
                                var taken_payroll_title = "القسائم المأخوذة ";

                                var total_timesheet_title = "إجمالي ساعات الأسبوع ";
                                var remaining_timesheet_title = "الساعات المتبقية ";
                                var taken_timesheet_title = "الساعات المنجزة ";
                            } else {
                                var total_leaves_title = "Total Balance ";
                                var remaining_leaves_title = "Left Balance ";
                                var taken_leaves_title = "Total remaining days ";

                                var total_payroll_title = "Total annual slips";
                                var remaining_payroll_title = "Remaining salary slips ";
                                var taken_payroll_title = "Left salary slips ";

                                var total_timesheet_title = "Total hours of week";
                                var remaining_timesheet_title = "Remaining hours ";
                                var taken_timesheet_title = "Left hours ";
                            }

                            if (result.leaves !== undefined) {
                                if (result.leaves[0].taken > 0 || result.leaves[0].remaining_leaves > 0) {
                                    var total_leaves = (result.leaves[0].taken + result.leaves[0].remaining_leaves);
                                    var remaining_leaves_percent = ((result.leaves[0].remaining_leaves / total_leaves) * 100).toFixed(2);
                                    var taken_leaves_percent = ((result.leaves[0].taken / total_leaves) * 100).toFixed(2);
                                    //set data
                                    $('.leave-total-amount').html(total_leaves_title + " " + Math.round(parseFloat(result.leaves[0].taken + result.leaves[0].remaining_leaves)));
                                    $('.leave-left-amount').html(remaining_leaves_title + " " + Math.round(parseFloat(result.leaves[0].remaining_leaves)));
                                    if ($('body').hasClass('o_rtl') === true) {
                                        $('.leave-data-percent').html('%' + taken_leaves_percent);
                                    } else {
                                        $('.leave-data-percent').html(taken_leaves_percent + '%');
                                    }
                                    $('#chartContainer').html('');
                                    pluscharts.draw({
                                        drawOn: "#chartContainer",
                                        type: "donut",
                                        dataset: {
                                            data: [{
                                                    label: remaining_leaves_title,
                                                    value: ((result.leaves[0].taken / total_leaves) * 100).toFixed(2)
                                                },
                                                {
                                                    label: taken_leaves_title,
                                                    value: ((result.leaves[0].remaining_leaves / total_leaves) * 100).toFixed(2)
                                                }
                                            ],
                                            backgroundColor: ["#003056", "#2ead97"],
                                            borderColor: "#ffffff",
                                            borderWidth: 0,
                                        },
                                        options: {
                                            width: 15,
                                            text: {
                                                display: false,
                                                color: "#f6f6f6"
                                            },
                                            legends: {
                                                display: false,
                                                width: 20,
                                                height: 20
                                            },
                                            size: {
                                                width: '140', //give 'container' if you want width and height of initiated container
                                                height: '140'
                                            }
                                        }
                                    });
                                    // display section
                                    $('#leave-section').fadeIn();
                                }
                            }

                            if (result.payroll !== undefined) {
                                if (result.payroll[0].taken > 0 || result.payroll[0].payslip_remaining > 0) {
                                    // Configure Salary Slips Chart
                                    var total_payroll = (result.payroll[0].taken + result.payroll[0].payslip_remaining);
                                    var remaining_payroll_percent = ((result.payroll[0].payslip_remaining / total_payroll) * 100).toFixed(2);
                                    var taken_payroll_percent = ((result.payroll[0].taken / total_payroll) * 100).toFixed(2);
                                    $('.payroll-total-amount').html(total_payroll_title + " " + parseFloat(total_payroll));
                                    $('.payroll-left-amount').html(remaining_payroll_title + " " + parseFloat(result.payroll[0].payslip_remaining));
                                    if ($('body').hasClass('o_rtl') === true) {
                                        $('.payroll-data-percent').html('%' + taken_payroll_percent);
                                    } else {
                                        $('.payroll-data-percent').html(taken_payroll_percent + '%');
                                    }
                                    $('#chartPaylips').html('');
                                    pluscharts.draw({
                                        drawOn: "#chartPaylips",
                                        type: "donut",
                                        dataset: {
                                            data: [{
                                                    label: remaining_payroll_title,
                                                    value: ((result.payroll[0].payslip_remaining / total_payroll) * 100).toFixed(2)
                                                },
                                                {
                                                    label: taken_payroll_title,
                                                    value: ((result.payroll[0].taken / total_payroll) * 100).toFixed(2)
                                                }
                                            ],
                                            backgroundColor: ["#003056", "#2ead97"],
                                            borderColor: "#ffffff",
                                            borderWidth: 0,
                                        },
                                        options: {
                                            width: 15,
                                            text: {
                                                display: false,
                                                color: "#f6f6f6"
                                            },
                                            legends: {
                                                display: false,
                                                width: 20,
                                                height: 20
                                            },
                                            size: {
                                                width: '140', //give 'container' if you want width and height of initiated container
                                                height: '140'
                                            }
                                        }
                                    });
                                    // display section
                                    $('#salary-section').fadeIn();
                                }
                            }

                            if (result.timesheet !== undefined) {
                                if (result.timesheet[0].taken > 0 || result.timesheet[0].timesheet_remaining > 0) {
                                    // Configure Weekly Timesheet Chart
                                    var total_timesheet = (result.timesheet[0].taken + result.timesheet[0].timesheet_remaining);
                                    var remaining_timesheet_percent = ((result.timesheet[0].timesheet_remaining / total_timesheet) * 100).toFixed(2);
                                    var taken_timesheet_percent = ((result.timesheet[0].taken / total_timesheet) * 100).toFixed(2);
                                    $('.timesheet-total-amount').html(total_timesheet_title + " " + parseFloat(total_timesheet));
                                    $('.timesheet-left-amount').html(remaining_timesheet_title + " " + parseFloat(result.timesheet[0].timesheet_remaining));
                                    $('.timesheet-data-percent').html(taken_timesheet_percent + '%');
                                    if ($('body').hasClass('o_rtl') === true) {
                                        $('.timesheet-data-percent').html('%' + taken_timesheet_percent);
                                    } else {
                                        $('.timesheet-data-percent').html(taken_timesheet_percent + '%');
                                    }
                                    $('#chartTimesheet').html('');
                                    pluscharts.draw({
                                        drawOn: "#chartTimesheet",
                                        type: "donut",
                                        dataset: {
                                            data: [{
                                                    label: taken_timesheet_title,
                                                    value: ((result.timesheet[0].taken / total_timesheet) * 100).toFixed(2)
                                                },
                                                {
                                                    label: remaining_timesheet_title,
                                                    value: ((result.timesheet[0].timesheet_remaining / total_timesheet)).toFixed(2)
                                                }
                                            ],
                                            backgroundColor: ["#003056", "#2ead97"],
                                            borderColor: "#ffffff",
                                            borderWidth: 0,
                                        },
                                        options: {
                                            width: 15,
                                            text: {
                                                display: false,
                                                color: "#f6f6f6"
                                            },
                                            legends: {
                                                display: false,
                                                width: 20,
                                                height: 20
                                            },
                                            size: {
                                                width: '140', //give 'container' if you want width and height of initiated container
                                                height: '140'
                                            }
                                        }
                                    });

                                    // display section
                                    $('#timesheet-section').fadeIn();
                                }
                            }
                            // hide charts loader
                            $('.charts-over-layer').fadeOut();
                        }, 1000);

                    })
                    // .done(function() {
                    //     self.render();
                    //     self.href = window.location.href;
                    // });
            }
            var attrs = [{
                    value: 50,
                    label: 'Total Amount 30',
                    color: '#003056'
                },
                {
                    value: 50,
                    label: 'Left Amount',
                    color: '#2ead97'
                },
            ];


            function explodePie(e) {
                if (typeof(e.dataSeries.dataPoints[e.dataPointIndex].exploded) === "undefined" || !e.dataSeries.dataPoints[e.dataPointIndex].exploded) {
                    e.dataSeries.dataPoints[e.dataPointIndex].exploded = true;
                } else {
                    e.dataSeries.dataPoints[e.dataPointIndex].exploded = false;
                }
                e.chart.render();
            }
        },
        willStart: function() {
            return $.when(ajax.loadLibs(this), this._super());
        },
        start: function() {
            var self = this;
            return this._super();
        },
        render: function() {
            var super_render = this._super;
            $(".o_control_panel").addClass("o_hidden");
            var self = this;
        },
        reload: function() {
            window.location.href = this.href;
        }
    });
    core.action_registry.add('system_dashboard_classic.dashboard', SystemDashboardView);
    return SystemDashboardView
});

window.text = [{
    'btn': {
        'ar': 'مشاهدة التفاصيل <i class="mdi mdi-chevron-double-left"></i>',
        'en': 'Show Details <i class="mdi mdi-chevron-double-right"></i>'
    }
}];

/*
    NAME: buildCard
    DESC: Using to create (APPROVE/FOLLOW) card base on sent data and it return DOM OBJECT
    RETURN: DOM OBJECT
*/
function buildCard(data, index, card_type) {
    var card = document.createElement('div');
    var card_container = document.createElement('div');
    var card_header = document.createElement('div');
    var card_body = document.createElement('div');

    $(card).addClass('col-md-3 col-sm-6 col-xs-12 card2');
    $(card_container).addClass('col-md-12 col-sm-12 col-xs-12 card-container');

    //card header
    var h4 = document.createElement('h4');
    $(card_header).addClass('col-md-12 col-sm-12 col-xs-12 card-header');
    $(h4).html('<img src="data:image/png;base64,' + data.image + '"/> <span>' + data.name + '</span>').attr('title', data.name);
    $(card_header).append(h4);
    $(card_container).append(card_header);

    // card body
    $(card_body).addClass('col-md-12 col-sm-12 col-xs-12 card-body');
    if (card_type == "table1") {
        var table = buildTableApprove(data);
    } else if (card_type == "table2") {
        var table = buildTableFollow(data);
    }
    $(card_body).append(table);
    $(card_container).append(card_body);

    // card
    $(card).append(card_container);
    return card;
}

/*
    NAME: buildTableApprove
    DESC: Using to create (APPROVE) rows/buttons base on sent data and it return DOM OBJECT
    RETURN: DOM OBJECT
*/
function buildTableApprove(data) {
    var table = document.createElement('table');
    var tbody = document.createElement('tbody');
    $(table).addClass('table');
    if (data.lines.length !== undefined && data.lines.length > 0) {
        $.each(data.lines, function(index) {
            var tr = document.createElement('tr');
            var td1 = document.createElement('td');
            var td2 = document.createElement('td');
            $(td1).html(data.lines[index].state_approval);
            $(td2).html('<div>' + data.lines[index].count_state_click + '</div>');
            $(tr).attr('data-target', 'record-button').attr('data-model', data.model).attr('data-name', data.name).
            attr('data-domain', JSON.stringify(data.lines[index].domain_click)).attr('form-view', data.lines[index].form_view).
            attr('list-view', data.lines[index].list_view).attr('data-action', JSON.stringify(data.lines[index].action_domain));
            $(tr).append(td1).append(td2);
            $(tbody).append(tr);
        });
    }
    $(table).append(tbody);
    return table;
}

/*
    NAME: buildTableFollow
    DESC: Using to create (FOLLOW) rows/buttons base on sent data and it return DOM OBJECT
    RETURN: DOM OBJECT
*/
function buildTableFollow(data) {
    var table = document.createElement('table');
    var tbody = document.createElement('tbody');
    $(table).addClass('table');
    if (data.lines.length !== undefined && data.lines.length > 0) {
        $.each(data.lines, function(index) {
            var tr = document.createElement('tr');
            var td1 = document.createElement('td');
            var td2 = document.createElement('td');
            $(td1).html(data.lines[index].state_folow);
            $(td2).html('<div>' + data.lines[index].count_state_follow + '</div>');
            $(tr).attr('data-target', 'record-button').attr('data-type', 'follow').attr('data-model', data.model).attr('data-name', data.name).
            attr('data-domain', JSON.stringify(data.lines[index].domain_follow)).attr('form-view', data.lines[index].form_view).
            attr('list-view', data.lines[index].list_view)
            $(tr).append(td1).append(td2);
            // to append
            //$(tbody).append(tr);
            // to override
            $(tbody).html(tr)

        });
    }
    // to append
    $(table).append(tbody);
    return table;
}

function setupAttendanceArea(data, name) {
    window.check = data.is_attendance;
    var button = '';
    if ($('body').hasClass('o_rtl')) {
        var checkout_title = "زمن تسجيل اخر دخول"
        var checkin_title = ",مرحباً بك"
        var checkin_button = "تسجيل الحضور";
        var checkout_button = "تسجيل الخروج";
    } else {
        var checkout_title = "Last check in"
        var checkin_title = "Welcome";
        var checkin_button = "Check In"
        var checkout_button = "Check Out";
    }
    if (data.is_attendance === true) {
        var check = checkout_title + " " + data.time;
        var image = '<img class="img-logout" src="/system_dashboard_classic/static/src/icons/logout.svg"/>';
        $('#check_button').html(checkout_button).removeClass('checkin-btn').addClass('checkout-btn');
        $('.last-checkin-section').html(check);
        $('.attendance-img-section').html(image);
    } else {
        var check = checkin_title + " " + name + ",";
        var image = '<img class="img-login" src="/system_dashboard_classic/static/src/icons/logout.svg"/>';
        $('#check_button').html(checkin_button).removeClass('checkout-btn').addClass('checkin-btn');
        $('.last-checkin-section').html(check);
        $('.attendance-img-section').html(image);
    }
}