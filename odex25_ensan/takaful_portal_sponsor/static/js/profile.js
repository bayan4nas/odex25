$(document).ready(function () {



    const getProfileData = () => {
        let url = "/portal/sponsor/profile";
        fetch(url)
            .then(response => response.json())
            .then(res => {
                data = res.sponsor;
                console.log(data);
                const dataObject = {
                    name: data.name,
                    gender: data.gender,
                    id_number: data.id_number,
                    mobile: data.mobile,
                    email: data.email,
                    city_id: data.city_id,
                    company_type: data.company_type,
                    bank_entity_name: data.bank_entity_name,
                    account_number: data.account_number,
                    iban: data.iban,
                    bank_name: data.bank_id,
                }
                //general information inputs values 
                $("input[name=name]").val(dataObject.name);
                $("input[name=id_number]").val(dataObject.id_number);
                $("input[name=mobile]").val(dataObject.mobile);
                $("input[name=email]").val(dataObject.email);
                $('#city_id option[value="' + dataObject.city_id + '"]').prop('selected', true);
                $("input[name=company_type]").val(dataObject.company_type);
                if (dataObject.gender == 'male') {
                    $('#gender-male').prop('checked', true)
                    $('#gender-female').prop('checked', false)
                } else {
                    $('#gender-female').prop('checked', true)
                    $('#gender-male').prop('checked', false)
                }
                $("input[name=bank_entity_name]").val(dataObject.bank_entity_name);
                $("input[name=account_number]").val(dataObject.account_number);
                $("input[name=iban]").val(dataObject.iban);
                $('#bank_id option[value="' + dataObject.bank_id + '"]').prop('selected', true);
            })
            .catch(err => {
                console.log(err);
            })
    }
    getProfileData();

    //profile update values 
    let update_profile = "/portal/sponsor/profile/update";
    const form = $('.sponsor_profile_form')
    const updateHandler = () => {
        form.on('submit', function (e) {
            var formData = $(this).serialize();
            console.log(formData);
            e.preventDefault();
            $.ajax({
                method: 'PUT',
                url: update_profile,
                data: {
                    mobile: $("input[name=mobile]").val(),
                    city_id: $("#city_id").val(),
                    account_number: $("input[name=account_number]").val(),
                    iban: $("input[name=iban]").val(),
                    bank_id: $("#bank_id").val(),
                    bank_entity_name: $("input[name=bank_entity_name]").val(),
                },
                dataType: "json",
                success: function (response) {
                    if (response !== undefined && response !== null) {
                        if (response.status) {
                            console.log(response.data);
                            $('.success_res').show();
                            $('.error_res').hide();
                            $('.success_res').html(`<span> ${response.msg} </span>`);
                            setTimeout(function () {
                                $('.success_res').hide();
                            }, 3000);
                        } else {
                            $('.error_res').show();
                            $('.success_res').hide();
                            $('.error_res').html(`<span> ${response.msg} </span>`);
                            setTimeout(function () {
                                $('.success_res').hide();
                            }, 6000);
                        }
                    }
                },
                error: function (error) {
                    $('.success_res').hide();
                    $('.error_res').show();
                    $('.error_res').html(`<span> ${error.msg} </span>`);
                }
            });
            return false;
        }
        );
    }
    updateHandler();
})