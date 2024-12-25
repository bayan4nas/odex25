$(document).ready(function () {




    const getProfileData = () => {
        let url = "/benefit/profile";
        fetch(url)
            .then(response => response.json())
            .then(res => {
                data = res.data;
                console.log(data);
                const dataObject = {
                    name: data.name,
                    id_number: data.id_number,
                    id_number_attach: data.id_number_attach,
                    id_expiry: data.id_expiry,
                    gender: data.gender,
                    marital_status: data.marital_status,
                    birth_date: data.birth_date,
                    bank_id: data.bank_id[0],
                    bank_name: data.bank_id[1],
                    iban: data.iban,
                    iban_attach: data.iban_attach,
                    email: data.email,
                    phone: data.phone,
                    country_id: data.country_id,
                    city_id: data.city_id,
                    street: data.street,
                    location: data.location,

                }
                //general information inputs values 
                $("input[name=name]").val(dataObject.name);
                $("input[name=id_number]").val(dataObject.id_number);
                $("input[name=id_expiry]").val(dataObject.id_expiry);
                if (dataObject.gender == 'male') {
                    $('#gender-male').prop('checked', true)
                    $('#gender-female').prop('checked', false)
                } else {
                    $('#gender-female').prop('checked', true)
                    $('#gender-male').prop('checked', false)
                }
                $('#marital_status option[value="' + dataObject.marital_status + '"]').prop('selected', true);
                $("input[name=birth_date]").val(dataObject.birth_date);
                $('#bank_id option[value="' + dataObject.bank_id + '"]').prop('selected', true);
                $("input[name=iban]").val(dataObject.iban);
                //main information inputs values 
                $("input[name=email]").val(dataObject.email);
                $("input[name=phone]").val(dataObject.phone);
                $("input[name=country_id]").val(dataObject.country_id);
                $("input[name=city_id]").val(dataObject.city_id);
                $("input[name=street]").val(dataObject.street);
                if (dataObject.location) {
                    $("input[name=location]").val(dataObject.location);
                } else {
                    $("input[name=location]").val('لايوجد');

                }

                //attached_files 

                if (dataObject.id_number_attach[1]) {
                    $('#id_file_preview').val(dataObject.id_number_attach[1])

                } else {
                    $('#id_file_preview').val('غير مرفق ')
                }

                if (dataObject.iban_attach.length > 0) {
                    $('#iban_file_preview').val(dataObject.iban_attach[1])

                } else {
                    $('#iban_file_preview').val('غير مرفق ')
                }
                //followers data 
                const followerArray = data.follower;
                console.log(followerArray);
                followerArray.forEach((element, i) => {
                    $('.followers_tbl tbody').append(
                        `<tr>
                            <td> ${i + 1} </td>
                            <td> ${element.name} </td>
                            <td> ${element.gender} </td>
                            <td> ${element.responsible} </td>
                            <td> ${element.birth_date} </td>
                            <td> ${element.id_number} </td>
                            <td> ${element.id_number_attach[0] ? `<a href="/web/content/${element.id_number_attach[0]}?download=true"> تحميل  </a>` : 'لايوجد'} </td>
                            <td class="delete_follower">
                                <img src="/takaful_portal_benefit/static/img/trash_ben.png" alt="trash_ben" />
                            </td>
                        </tr>`);
                })
            })
            .catch(err => {
                console.log(err);
            })
    }
    getProfileData();

    //profile update values 
    let update_profile = "/benefit/profile/update";
    const form = $('.general_data_form')
    const updateHandler = () => {
        form.on('submit', function (e) {
            e.preventDefault();
            $.ajax({
                method: 'PUT',
                url: update_profile,
                data: {
                    name: $("input[name=name]").val(),
                    id_number: $("input[name=id_number]").val(),
                    id_expiry: $("input[name=id_expiry]").val(),
                    gender: $("input[name=gender]").val(),
                    marital_status: $("input[name=marital_status]").val(),
                    birth_date: $("input[name=birth_date]").val(),
                    bank_id: $("input[name=bank_id]").val(),
                    bank_name: $("input[name=bank_name]").val(),
                    iban: $("input[name=iban]").val(),
                    family: $("input[name=family]").val()
                },
                dataType: "json",
                success: function (response) {
                    if (response !== undefined && response !== null) {
                        if (response.status) {
                            $('.main_data_btn').hide();
                            $('#enableInputs').show();
                            $('.response_msg').html(`<div class="alert text-center alert-success"> تم تحديث البيانات بنجاح ! </div>`);
                            setTimeout(function () {
                                $('.response_msg').hide();
                            }, 3000);
                        } else {
                            $('.response_msg').html(`<div class="alert alert-danger">${response.msg}</div>`);
                        }
                    }
                    setTimeout(function () {
                        $('.step-loader').removeClass('show');
                    }, 3000);
                },
                error: function (error) {
                    $('.response_msg').html(`<div class="alert alert-danger">${error.responseJSON.msg}</div>`);
                    setTimeout(function () {
                        $('.step-loader').removeClass('show');
                    }, 3000);
                }
            });
            return false;
        }
        );
    }

    updateHandler();


    //create support

    let create_support = "/benefit/create_support";
    $('form#add_support').on('submit', function (evt) {
        evt.preventDefault();
        var form_data = new FormData(this);
        $.ajax({
            url: create_support,
            method: 'POST',
            data: form_data,
            dataType: 'json',
            processData: false,
            contentType: false,
            success: function (response) {
                if (response.status) {
                    $('.new_support').append(`<p class="alert alert-success"> ${response.msg} </p>`)
                    setTimeout(function () {
                        $('.new_support').hide();
                        location.reload();
                    }, 3000);
                } else {
                    console.log('Error');
                    $('.new_support').append(`<p class="alert alert-danger"> ${response.msg}  </p>`)
                    setTimeout(function () {
                        $('.new_support').hide();
                        // location.reload();
                    }, 3000);
                }
            },
            error: function (err) {
                console.log(err);
            }
        });
    });



    // show expense type 

    $('.medical_expenses').hide();
    $('.transport_expenses').hide();
    $('.debt_expenses').hide();
    $('.pandemics_expenses').hide();
    $('.living_expenses').hide();
    $('.learning_expense').hide();
    $("#expenses_type").change(function () {
        if ($(this).val() === 'medical') {
            $('.medical_expenses').show();
            $('.transport_expenses').hide();
            $('.debt_expenses').hide();
            $('.pandemics_expenses').hide();
            $('.living_expenses').hide();
            $('.learning_expense').hide();
        } else if ($(this).val() === 'transportation') {
            $('.medical_expenses').hide();
            $('.transport_expenses').show();
            $('.debt_expenses').hide();
            $('.pandemics_expenses').hide();
            $('.living_expenses').hide();
            $('.learning_expense').hide();
        } else if ($(this).val() === 'debts') {
            $('.medical_expenses').hide();
            $('.transport_expenses').hide();
            $('.debt_expenses').show();
            $('.pandemics_expenses').hide();
            $('.living_expenses').hide();
            $('.learning_expense').hide();

        } else if ($(this).val() === 'pandemics') {
            $('.medical_expenses').hide();
            $('.transport_expenses').hide();
            $('.debt_expenses').hide();
            $('.pandemics_expenses').show();
            $('.living_expenses').hide();
            $('.learning_expense').hide();
        } else if ($(this).val() === 'living') {
            $('.medical_expenses').hide();
            $('.transport_expenses').hide();
            $('.debt_expenses').hide();
            $('.pandemics_expenses').hide();
            $('.living_expenses').show();
            $('.learning_expense').hide();
        } else if ($(this).val() === 'educational') {
            $('.medical_expenses').hide();
            $('.transport_expenses').hide();
            $('.debt_expenses').hide();
            $('.pandemics_expenses').hide();
            $('.living_expenses').hide();
            $('.learning_expense').show();
        } else {
            $('.medical_expenses').hide();
            $('.transport_expenses').hide();
            $('.debt_expenses').hide();
            $('.pandemics_expenses').hide();
            $('.living_expenses').hide();
            $('.learning_expense').hide();
        }
    });


    // get all expenses 


    $.ajax({
        url: '/benefit/get_benefit_expenses/',
        type: 'GET',
        dataType: 'json',
        processData: false,
        success: function (response) {
            myData = response.data;
            console.log(myData);
            if (response.status) {
                $('.expenses_table tbody').empty();
                myData.forEach((element, i) => {
                    $('.expenses_table tbody').append(`
                    <tr>
                        <td> ${i + 1} </td>
                        <td> ${element.name} </td>
                        <td> ${element.expenses_type} </td>
                        <td> ${element.expenses_fees_type} </td>
                        <td> ${element.amount ? element.amount : '0'} </td>
                        <td> ${element.medicine_type ? element.medicine_type : 'لايوجد'} </td>
                        <td> ${element.diseases_type ? element.diseases_type : 'لايوجد'} </td>
                        <td> ${element.trans_type ? element.trans_type : 'لايوجد'} </td>
                        <td> ${element.debt_type ? element.debt_type : 'لايوجد'} </td>
                        <td> ${element.debt_reason ? element.debt_reason : 'لايوجد'} </td>
                        <td> ${element.pandemics_explain ? element.pandemics_explain : 'لايوجد'} </td>
                        <td> ${element.state} </td>
                        <td> ${element.attach ? `<a href="data:application/octet-stream;base64,${element.attach}"> تحميل </a>` : 'لايوجد'}</td>
                    </tr>
                        `)
                });
            }
            else {
                $('.expenses_table tbody').empty();
                $('.expenses_table tbody').append(` <tr> لايوجد بيانات  </tr> `)

            }
        },
        error: function (error) {
            $('.expenses_table tbody').empty();
            $('.expenses_table tbody').append(` <tr> ${error.msg} </tr> `)
        }
    });




    // post a new expense 

    $('form#expenses_form').on('submit', function (evt) {
        evt.preventDefault();
        var form_data = $(this).serialize();
        // var id = $("#id_holder_input").val();
        var expenses_api = `/benefit/add_benefit_expenses/`;
        $.ajax({
            url: expenses_api,
            type: "POST",
            data: form_data,
            dataType: 'json',
            success: function (response) {
                if (response.status) {
                    $('.add_expense_feedback').show();
                    $(".add_expense_feedback").text(response.msg).removeClass('alert-danger').addClass('alert alert-success')
                    setTimeout(function () {
                        $('.add_expense_feedback').hide();
                        location.reload();
                        // $('.zakat_modal').modal('hide');
                    }, 3000);
                } else {
                    $('.add_expense_feedback').show();
                    $(".add_expense_feedback").text(response.msg).removeClass('alert-success').addClass('alert alert-danger')
                    setTimeout(function () {
                        $('.add_expense_feedback').hide();
                        // location.reload();
                    }, 3000);
                }
            },
            error: function (err) {
                $('.add_expense_feedback').show();
                $(".add_expense_feedback").text(err.msg).removeClass('alert-success').addClass('alert alert-danger')
                setTimeout(function () {
                    $('.add_expense_feedback').hide();
                    // location.reload();
                }, 3000);
            }
        });
    });
})


$(document).ready(function () {
    // Disable all inputs initially
    $('#main_data_form input').prop('readonly', true);
    $('.main_data_btn').hide();
    // Enable inputs when the specified element is clicked
    $('#enableInputs').on('click', function () {
        $(this).hide();
        $('#main_data_form input').prop('readonly', false);
        $('.main_data_btn').show();
    });
});

$(document).ready(function () {
    // Disable all inputs initially
    $('#main_info_form input').prop('readonly', true);
    $('.mainInfo_Btn').hide();
    // Enable inputs when the specified element is clicked
    $('#mainInfo').on('click', function () {
        $(this).hide();
        $('#main_info_form input').prop('readonly', false);
        $('.mainInfo_Btn').show();
    });
});
$(document).ready(function () {
    // Disable all inputs initially
    $('#attachments_form input').prop('readonly', true);
    $('.attach_btn').hide();
    // Enable inputs when the specified element is clicked
    $('#attachEdit').on('click', function () {
        $(this).hide();
        $('#attachments_form input').prop('readonly', false);
        $('.attach_btn').show();
    });
});



