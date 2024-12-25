$(document).ready(function () {
    // Show and hide data depend on a checkbox value 
    $('input[name="isAssociated"]').change(function () {
        if ($(this).val() === 'true') {
            $('.grant_data').show();
        } else if ($(this).val() === 'no') {
            $('.grant_data').hide();
        }
    });

    $('.not_educated_data').hide();
    $('.is_want_education ').hide();
    $('input[name="education_status"]').change(function () {
        if ($(this).val() === 'educated') {
            $('.educated_data').show();
            $('.not_educated_data').hide();
            $('.is_want_education ').hide();
        } else if ($(this).val() === 'illiterate') {
            $('.is_want_education').show();
            $('.educated_data').hide();
        }
    });

    // is want to educate ?
    $('input[name="is_want_education"]').change(function () {
        if ($(this).val() === 'true') {
            $('.not_educated_data').show();
        } else if ($(this).val() === 'false') {
            $('.not_educated_data').hide();
        }
    });


    // graduted or not 

    $('.intermittent_data').hide();
    $('.graduated_data').hide();
    $("#graduation_status").change(function () {
        if ($(this).val() === 'graduated') {
            $('.graduated_data').show();
            $('.intermittent_data').hide()
        } else if ($(this).val() === 'intermittent') {
            $('.intermittent_data').show();
            $('.graduated_data').hide();
        } else {
            $('.intermittent_data').hide();
            $('.graduated_data').hide();
        }
    });

    // is_quran_memorize
    $('input[name="is_quran_memorize"]').change(function () {
        if ($(this).val() === 'true') {
            $('.is_quran_memorize').show();
        } else if ($(this).val() === 'false') {
            $('.is_quran_memorize').hide();
        }
    });

    // other progs

    $('input[name="other_progs"]').change(function () {
        if ($(this).val() === 'true') {
            $('.other_progs').show();
        } else if ($(this).val() === 'false') {
            $('.other_progs').hide();
        }
    });


    // is_diseases

    $('input[name="is_diseases"]').change(function () {
        if ($(this).val() === 'true') {
            $('.is_deseased_data').show();
        } else if ($(this).val() === 'false') {
            $('.is_deseased_data').hide();
        }
    });

    $('input[name="is_treatment_amount_country"]').change(function () {
        if ($(this).val() === 'true') {
            $('.amount_country_data').show();
        } else if ($(this).val() === 'false') {
            $('.amount_country_data').hide();
        }
    });

    $('input[name="is_disability"]').change(function () {
        if ($(this).val() === 'true') {
            $('.is_disability').show();
        } else if ($(this).val() === 'false') {
            $('.is_disability').hide();
        }
    });

    // is_insurance

    $('input[name="is_insurance"]').change(function () {
        if ($(this).val() === 'true') {
            $('.is_insurance').show();
        } else if ($(this).val() === 'false') {
            $('.is_insurance').hide();
        }
    });

    // is_sport

    $('input[name="is_sport"]').change(function () {
        if ($(this).val() === 'true') {
            $('.is_sport').show();
        } else if ($(this).val() === 'false') {
            $('.is_sport').hide();
        }
    });




    // get all selections data from TYPE End point 

    // associations

    let associations = "/benefit/types/associations";
    fetch(associations).then(res => res.json()).then(response => {
        let allAssociations = response.result[0].other_associations;
        allAssociations.forEach((data, i) => {
            $('#associations_id').append(`<option value=${data.id}> ${data.name} </option>`)
        });
    })


    // specialization

    let specialization = "/benefit/types/specialization";
    fetch(specialization).then(res => res.json()).then(response => {
        let allSpecialization = response.result[0].specialization_specialization;
        allSpecialization.forEach((data, i) => {
            $('#specialization_ids').append(`<option value=${data.id}> ${data.name} </option>`)
        });
    })

    // insurance type
    let insurance_type = "/benefit/types/insurance";
    fetch(insurance_type).then(res => res.json()).then(response => {
        let insurance = response.result[0].insurance_type;
        insurance.forEach((data, i) => {
            $('#insurance_type').append(`<option value=${data.id}> ${data.name} </option>`)
        });
    })

    // insurance company
    let insurance_company = "/benefit/types/insurance_company";
    fetch(insurance_company).then(res => res.json()).then(response => {
        let companies = response.result[1].insurance_company;
        companies.forEach((data, i) => {
            $('#insurance_company').append(`<option value=${data.id}> ${data.name} </option>`)
        });
    })

    // cloth type
    let cloth_type = "/benefit/types/cloth_type";
    fetch(cloth_type).then(res => res.json()).then(response => {
        let clothes = response.result[0].cloth_type;
        clothes.forEach((data, i) => {
            $('#dressing_type').append(`<option value=${data.id}> ${data.name} </option>`)
        });
    })

    // cloth size
    let cloth_size = "/benefit/types/cloth_size";
    fetch(cloth_size).then(res => res.json()).then(response => {
        let sizes = response.result[0].cloth_size;
        sizes.forEach((data, i) => {
            $('#dressing_size').append(`<option value=${data.id}> ${data.name} </option>`)
        });
    })

    // sport
    let ssport = "/benefit/types/sport";
    fetch(ssport).then(res => res.json()).then(response => {
        let sports = response.result[0].sport_type;
        sports.forEach((sport, i) => {
            $('#sport_type').append(`<option value=${sport.id}> ${sport.name} </option>`)
        });
    })

    var specializationIdsSelect = $('.specialization_ids');
    var case_study = $('.case_study');
    var graduation_status = $('.graduation_status');

    specializationIdsSelect.hide();
    case_study.hide();
    graduation_status.hide();

    $(document).ready(function () {
        $('#education_level').change(function () {
            var selectedValue = $(this).val();
            if (selectedValue === "primary" || selectedValue === "middle" || selectedValue === "secondary") {
                specializationIdsSelect.show();
                case_study.show();
                graduation_status.hide();
            } else if (selectedValue === "university" || selectedValue === "postgraduate") {
                graduation_status.show();
                specializationIdsSelect.hide();
                case_study.hide();
            } else {
                graduation_status.hide();
                specializationIdsSelect.hide();
                case_study.hide();
            }
        });
    });

    var lat = $("#lat");
    var lon = $("#lon");
    var geoInput = $("#geolocation");

    function getLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(showPosition);
        } else {
            x.innerHTML = "Geolocation is not supported by this browser.";
        }
    }

    function showPosition(position) {
        lat.val(position.coords.latitude);
        lon.val(position.coords.longitude);
        geoInput.val(lat.val() + "," + lon.val());
    }

    $('.setGeo').click(function () {
        getLocation();
    })

    // complete benefit API integration 
    var step = 1;
    var benefit_data = "/benefit/complete_benefit";
    $('form.user_data_form fieldset').each(function () {
        var fieldset = $(this);
        var submitButton = fieldset.find('button[type="submit"]');
        submitButton.on('click', function (e) {
            e.preventDefault();
            var formData = new FormData();
            var formParams = fieldset.serializeArray();
            $.each(fieldset.find('input[type="file"]'), function (i, tag) {
                $.each($(tag)[0].files, function (i, file) {
                    formData.append(tag.name, file);
                });
            });
            $.each(formParams, function (i, val) {
                formData.append(val.name, val.value);
            });
            $.ajax({
                type: 'POST',
                url: `${benefit_data}?step=${step}`,
                data: formData,
                dataType: "json",
                processData: false,
                contentType: false,
                success: function (response) {
                    console.log(response);
                    if (response !== undefined && response !== null) {
                        if (response.status) {
                            console.log(response.data[0]);
                            localStorage.setItem('inputsValues', JSON.stringify(response.data[0]));
                            // Find the next fieldset and make it active
                            var nextFieldset = fieldset.next('fieldset');
                            if (nextFieldset.length > 0) {
                                fieldset.removeClass("active");
                                nextFieldset.addClass("active");
                                var currentBullet = $('.bullet-navigation .bullet.active');
                                var nextBullet = currentBullet.next('.bullet');
                                currentBullet.removeClass('active');
                                nextBullet.addClass('active');
                                step = $('.bullet-navigation .bullet.active').index() + 1;
                                console.log(step);
                                // Last fieldset 
                            } else {
                                $('#success_data_modal').modal('show');
                                setTimeout(function () {
                                    // window.location.href = "/benefit_profile"
                                }, 5000);


                            }
                        } else {
                            $('.message-block').show();
                            $('.message-block').html(`<div class="alert alert-danger">${response.msg}</div>`);
                            setTimeout(function () {
                                $('.message-block').hide();
                            }, 3000);
                        }
                    }
                },
                error: function (error) {
                    $('.message-block').show();
                    $('.message-block').html(`<div class="alert error_server alert-danger">${error.msg}</div>`);
                    setTimeout(function () {
                        $('.message-block').hide();
                    }, 3000);
                }
            });

            return false;
        });
    });


    // checking address api integraion
    $('#house_number').on('change', function () {
        var housingNumber = $(this).val();
        $.ajax({
            url: '/benefit/check_address',
            type: 'GET',
            data: {
                housing_number: housingNumber
            },
            dataType: 'json',
            success: function (response) {
                // Handle the response data here
                address = response.data[0];
                addressTwo = response.data;
                if (response.status && addressTwo.length > 0) {
                    console.log('Address exists:', response.data);
                    // Populate the form fields with the received data
                    $('#city_id option[value="' + address.city_id[0] + '"]').prop('selected', true);
                    $('#block').val(address.block);
                    $('#street').val(address.street);
                    $('#floor').val(address.floor);
                    $('#housing_type option[value="' + address.housing_type + '"]').prop('selected', true);
                    $('#property_type option[value="' + address.property_type + '"]').prop('selected', true);
                    $('#lon').val(address.lon);
                    $('#lat').val(address.lat);
                    $('#rooms_number').val(address.rooms_number);
                    $('#water_bill_account_number').val(address.water_bill_account_number);
                    $('#electricity_bill_account_number').val(address.electricity_bill_account_number);
                } else {
                    console.log('No address found');
                }
                $('#house_number').val(housingNumber);

            },
            error: function (error) {
                console.error('Error:', error);
            }
        });
    })

    var savedResponseJSON = localStorage.getItem('inputsValues');
    var inputsValues = JSON.parse(savedResponseJSON);
    // first step values 
    $('#job_position').val(inputsValues.job_position);
    $('#job_company').val(inputsValues.job_company);
    inputsValues.id_number_attach ? $('#id_number_attach').next().val('مرفق') : $('#id_number_attach').val('غير مرفق ');
    $('#id_expiry').val(inputsValues.id_expiry)
    $('#marital_status').val(inputsValues.marital_status);
    $('#marital_status option[value="' + inputsValues.marital_status + '"]').prop('selected', true);
    $('#bank_id').val(inputsValues.bank_id[0]);
    $('#bank_id option[value="' + inputsValues.bank_id[0] + '"]').prop('selected', true);
    $('#iban').val(inputsValues.iban)
    inputsValues.iban_attach ? $('#iban_attach').next().val('مرفق') : $('#iban_attach').val('غير مرفق ');
    $('#name_in_bank').val(inputsValues.name_in_bank)
    $('#followers_total').val(inputsValues.followers_total)
    $('#followers_out_total').val(inputsValues.followers_out_total)
    $('#instrument_number').val(inputsValues.instrument_number)
    inputsValues.instrument_attach ? $('#instrument_attach').next().val('مرفق') : $('#instrument_attach').val('غير مرفق ');

    // second step data 
    $('#city_id').val(inputsValues.city_id[0]);
    $('#city_id option[value="' + inputsValues.city_id[0] + '"]').prop('selected', true);
    $('#house_number').val(inputsValues.house_number);
    $('#block').val(inputsValues.block);
    $('#street').val(inputsValues.street);
    $('#floor').val(inputsValues.floor);
    $('#housing_type').val(inputsValues.housing_type);
    $('#housing_type option[value="' + inputsValues.housing_type + '"]').prop('selected', true);
    $('#property_type').val(inputsValues.property_type);
    $('#property_type option[value="' + inputsValues.property_type + '"]').prop('selected', true);
    $('#lat').val(inputsValues.lat);
    $('#lon').val(inputsValues.lon);
    $('#geolocation').val(inputsValues.lat + ',' + inputsValues.lon);
    inputsValues.image ? $('#house_images').next().val('مرفق') : $('#house_images').next().val('غير مرفق ');
    $('#rooms_number').val(inputsValues.rooms_number);
    $('#water_bill_account_number').val(inputsValues.water_bill_account_number);
    inputsValues.water_bill_account_attach ? $('#water_bill_account_attach').next().val('مرفق') : $('#water_bill_account_attach').next().val('غير مرفق ');
    $('#electricity_bill_account_number').val(inputsValues.electricity_bill_account_number);
    inputsValues.electricity_bill_account_attach ? $('#electricity_bill_account_attach').next().val('مرفق') : $('#water_bill_account_attach').next().val('غير مرفق ');
    // stp 4 inputs values 
    $('#salary_type').val(inputsValues.salary_ids[0]);
    inputsValues.water_bill_account_attach ? $('#water_bill_account_attach').next().val('مرفق') : $('#water_bill_account_attach').next().val('غير مرفق ');
    $('#education_status option[value="' + inputsValues.education_status + '"]').prop('checked', true);
    $('#education_level option[value="' + inputsValues.education_level + '"]').prop('checked', true);
    $('#classroom').val(inputsValues.classroom);
    $('#educational_institution_information').val(inputsValues.educational_institution_information);
    $('#specialization_ids option[value="' + inputsValues.specialization_ids[0] + '"]').prop('selected', true);
    $('#quran_memorize_name').val(inputsValues.quran_memorize_name);
    $('#number_parts').val(inputsValues.number_parts);

    // step 5 data 
    $('#diseases_type option[value="' + inputsValues.diseases_type + '"]').prop('selected', true);
    $('#treatment_used').val(inputsValues.treatment_used);
    $('#treatment_amount').val(inputsValues.treatment_amount);
    inputsValues.is_treatment_amount_country ? $('#is_treat').prop('checked', true) && $('#not_treat').prop('checked', false) : $('#is_treat').prop('checked', false) && $('#not_treat').prop('checked', true) 
    $('#treatment_amount_country_Monthly').val(inputsValues.treatment_amount_country_Monthly);
    $('#treatment_amount_country_description').val(inputsValues.treatment_amount_country_description);
    inputsValues.is_disability ? $('#is_dis').prop('checked', true) && $('#not_dis').prop('checked', false) : $('#is_dis').prop('checked', false) && $('#not_dis').prop('checked', true) 
    
    $('#disability_type').val(inputsValues.disability_type);
    $('#disability_accessories').val(inputsValues.disability_accessories);
    $('#disability_amount').val(inputsValues.disability_amount);
    $('#weight').val(inputsValues.weight);
    $('#height').val(inputsValues.height);


    // 6
    inputsValues.is_insurance ? $('#is_ins').prop('checked', true) && $('#not_ins').prop('checked', false) : $('#is_ins').prop('checked', false) && $('#not_ins').prop('checked', true) 
    $('#insurance_amount').val(inputsValues.insurance_amount);
    $('#sport_club').val(inputsValues.sport_club);

});


// show fieldsets by clicking the bullets 
$(document).ready(function () {
    var fieldsets = $('form.user_data_form fieldset');
    var bullets = $('.bullet-navigation .bullet');
    bullets.on('click', function () {
        var index = $(this).index();
        var currentFieldset = fieldsets.filter('.active');
        // Remove active class from current fieldset and bullet
        currentFieldset.removeClass('active');
        bullets.removeClass('active');
        // Add active class to selected fieldset and bullet
        fieldsets.eq(index).addClass('active');
        bullets.eq(index).addClass('active');
        step = $('.bullet-navigation .bullet.active').index() + 1;
        console.log(step);


    });
});