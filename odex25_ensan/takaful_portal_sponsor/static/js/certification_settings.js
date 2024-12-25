$(document).ready(function () {
    $.ajax({
        url: '/portal/sponsor/certificate_setting',
        type: 'GET',
        dataType: 'json',
        processData: false,
        success: function (data) {
            settings = data.certificate_setting;
            console.log(settings);
            if (data.status) {
                $('input[name="name_in_certificate"]').prop('checked', settings.name_in_certificate);
                $('input[name="type_in_certificate"]').prop('checked', settings.type_in_certificate);
                $('input[name="duration_in_certificate"]').prop('checked', settings.duration_in_certificate);
                $(".certificate_setting_feedback").text(settings.msg).addClass('alert alert-success')
            }
            else {
                $(".certificate_setting_feedback").text(data.msg).addClass('alert alert-danger')
            }
        },
        error: function (error) {
            $(".certificate_setting_feedback").text(error.msg).addClass('alert alert-danger')
        }
    });

    var settings_data = {}

    // Add event listener to input fields to detect changes
    $('input[type="checkbox"]').change(function () {
        settings_data = {
            name_in_certificate: $('input[name="name_in_certificate"]').prop('checked'),
            type_in_certificate: $('input[name="type_in_certificate"]').prop('checked'),
            duration_in_certificate: $('input[name="duration_in_certificate"]').prop('checked'),
        }
    });

    // Add event listener to save button to trigger AJAX request
    $('#certificate_settings_form').on("submit", (e) => {
        e.preventDefault();
        $.ajax({
            url: '/portal/sponsor/certificate_setting/update',
            type: 'POST',
            data: settings_data,
            dataType: 'json',
            success: function (response) {
                if (response.status) {
                    console.log(response);
                    $(".certificate_setting_feedback").show()
                    $(".certificate_setting_feedback").text(response.msg)
                } else {
                    $(".certificate_setting_feedback").show()
                    $(".certificate_setting_feedback").text(response.msg)
                }
            },
            error: function (error) {
                $(".certificate_setting_feedback").show()
                $(".certificate_setting_feedback").text(error.msg)
            }
        });
        
    });
})