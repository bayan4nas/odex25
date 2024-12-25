$(document).ready(function () {
    $.ajax({
        url: '/portal/sponsor/notify_setting',
        type: 'GET',
        dataType: 'json',
        processData: false,
        success: function (data) {
            settings = data.notify_setting;
            console.log(settings);
            if (data.status) {
                $('input[name="notify_by_app"]').prop('checked', settings.notify_by_app);
                $('input[name="notify_by_sms"]').prop('checked', settings.notify_by_sms);
                $('input[name="notify_month_day"]').val(settings.notify_month_day);
                $('input[name="notify_pay_by_app"]').prop('checked', settings.notify_pay_by_app);
                $('input[name="notify_pay_by_sms"]').prop('checked', settings.notify_pay_by_sms);
                $(".notifications_update_feedback").text(data.msg).addClass('alert alert-success')

            }
            else {
                console.log(data.msg);
                $(".notifications_update_feedback").text(data.msg).addClass('alert alert-danger')
            }
        },
        error: function (error) {
            $(".notifications_update_feedback").text(error.msg).addClass('alert alert-danger')
        }
    });

    var settings_data = {}

    // Add event listener to input fields to detect changes
    $('input[type="checkbox"]').change(function () {
        settings_data = {
            notify_by_app: $('input[name="notify_by_app"]').prop('checked'),
            notify_by_sms: $('input[name="notify_by_sms"]').prop('checked'),
            notify_month_day: $('input[name="notify_month_day"]').val(),
            notify_pay_by_app: $('input[name="notify_pay_by_app"]').prop('checked'),
            notify_pay_by_sms: $('input[name="notify_pay_by_sms"]').prop('checked'),
        }
    });

    // Add event listener to save button to trigger AJAX request
    $('#notifications_update_form').on("submit", (e) => {
        e.preventDefault();
        $.ajax({
            url: '/portal/sponsor/notify_setting/update',
            type: 'POST',
            data: settings_data,
            dataType: 'json',
            success: function (response) {
                if (response.status) {
                    console.log(response);
                    $(".notifications_update_feedback").show()
                    $(".notifications_update_feedback").text(response.msg)
                } else {
                    $(".notifications_update_feedback").show()
                    $(".notifications_update_feedback").text(response.msg)
                }
            },
            error: function (error) {
                $(".notifications_update_feedback").show()
                $(".notifications_update_feedback").text(error.msg)
            }
        });

    });
})


