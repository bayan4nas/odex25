$(document).ready(function () {
    $(".widow_type").hide()
    const urlSearchParams = new URLSearchParams(window.location.search);
    const benefit_type = urlSearchParams.get("benefit_type");
    console.log(benefit_type);
    const benefit_id = urlSearchParams.get("benefit_id");
    let benefit_type_input = $("#benefit_type_sponsorship")
    let benefit_id_input = $("#benefit_id_sponsorship")
    benefit_type_input.val(benefit_type);
    benefit_id_input.val(benefit_id);
    if (benefit_type_input.val() == 'orphan') {
        $(".widow_type").hide()
    }
    else {
        $(".widow_type").show()
    }


    $('#orphan_ids').on('change', function () {
        var selectedOptions = $('#orphan_ids option:selected');
        $('#selected_options').empty(); // Clear the previous content
        selectedOptions.each(function () {
            var fullName = $(this).text().trim();
            var firstName = fullName.split(' ')[0];
            var spanElement = `<span class="wdiow_orphans"> ${firstName} <i class="fa fa-times remove_btn"></i> </span>`
            $('#selected_options').append(spanElement);
        });
    });

    $(document).on('click', '.remove_btn', function () {
        $(this).parent('span').remove();
    });

    //show and hide gifter data depend on is_gift input 
    $('.gifter_data').hide();
    $('input[name="is_gift"]').change(function () {
        if ($(this).val() === 'yes') {
            $('.gifter_data').show();
        } else if ($(this).val() === 'no') {

            $('.gifter_data').hide();
        }
    });
    $('.months_num').hide();
    $('#sponsorship_duration').change(function () {
        if ($(this).val() === 'permanent') {
            $('.months_num').hide();
        } else {
            $('.months_num').show();
        }
    });
    $('#months_number').on('input', function () {
        var input1 = $(this).val();
        var input2 = $('#month_amount').val();
        $('#kafala_total').val(input1 * input2)
    });

    $('input[name="with_orphan"]').change(function () {
        if ($(this).val() === 'yes') {
            $('.isOrphan').show();
        } else if ($(this).val() === 'no') {
            $('.isOrphan').hide();
        }
    });


    let sponsorships_api = "/portal/sponsor/sponsorships/create/";
    $('form#single_sponsorship_form').on('submit', function (evt) {
        evt.preventDefault();
        var form_data = $(this).serialize();
        $.ajax({
            type: "POST",
            url: sponsorships_api,
            data: form_data,
            dataType: 'json',
            processData: false,
            success: function (response) {
                console.log(response);
                if (response.status === true) {
                    $('.sponsorship_creation_feedback').show();
                    $('.sponsorship_creation_feedback').html(`<p class="alert alert-success text-center">  ${response.msg} </p>`);
                    setTimeout(function () {
                        $('.sponsorship_creation_feedback').hide();
                        // location.reload();
                        $('#SingleKafala').modal('hide');

                    }, 3000);
                } else {
                    $('.sponsorship_creation_feedback').show();
                    $('.sponsorship_creation_feedback').html(`<p class="alert alert-danger text-center">  ${response.msg} </p>`);
                    setTimeout(function () {
                        // $('.sponsorship_creation_feedback').hide();
                        // location.reload();
                    }, 3000);
                }
            },
            error: function (err) {
                $('.sponsorship_creation_feedback').append(`<p class="alert alert-dander text-center">  يوجد مشكلة !!   </p>`)
            }
        });
    });
});
