$(document).ready(function () {
    // get all food food surplus 
    $.ajax({
        url: '/services/loans',
        type: 'GET',
        dataType: 'json',
        processData: false,
        success: function (response) {
            if (response.status && response.data.length > 0) {
                loans = response.data[0].loans;
                console.log(loans);
                loans.forEach((element, i) => {
                    $('.families_loans_row').append(`
                    <div class="col-lg-6">
                        <div class="zakat_content">
                            <h5>
                                ${element.name}
                            </h5>
                            <ul class="list-unstyled p-0">
                                <li>
                                    <img
                                        src="/takaful_portal_benefit/static/img/Icon awesome-info-circle.png"
                                        alt="info" />
                                    <span>
                                        ${element.description}
                                    </span>
                                </li>
                                <li>
                                    <img
                                        src="/takaful_portal_benefit/static/img/Icon awesome-users.png"
                                        alt="money" />
                                    <span>
                                    ${element.benefits_total} أفراد 
                                    </span>
                                </li>
                                <li>
                                    <img
                                        src="/takaful_portal_benefit/static/img/Icon awesome-toolbox.png"
                                        alt="money" />
                                    <span>
                                        ${element.project_name}
                                    </span>
                                </li>
                                <li>
                                    <img
                                        src="/takaful_portal_benefit/static/img/Icon ionic-md-pricetag.png"
                                        alt="date" />
                                    <span>
                                        بحاجة ل ${element.loan_amount}
                                    </span>
                                </li>
                            </ul>
                            <span data-amount = ${element.loan_amount} data-id="${element.id}"
                                class="donation families_loan_link main_link"> 
                                تبرع بقرض للاسرة
                            </span>
                        </div>
                    </div>
                    
                `)
                });
            }
            else {
                $('.families_loans_row').append(` <p class="text-center w-100 m-0"> لايوجد  أسر  لعرضها  </p> `)

            }
        },
        error: function (error) {
            $(".families_feedback").text(error.msg).addClass('alert alert-danger')
        }
    });

    $("#good_loan_form").on("submit", function (event) {
        event.preventDefault();

        var amount = $("#loan_amount").val();

        var name_op = zakat_sacrifices_text;

        var encodedAmount = encodeURIComponent(loan_amount);
        var encodedNameOp = encodeURIComponent(name_op);

        var redirectURL = "/dashboard/payment/paycard?name_op=" + encodedNameOp + "&required_amount=" + encodedAmount;

        window.location.href = redirectURL;
    });




    //set the family id 
    $('.families_loans_row').on('click', '.families_loan_link', function () {
        $('.loans_modal').modal('show');
        $("#family_id").val($(this).data('id'));
        $("#loan_amount").val($(this).data('amount'));
        console.log($("#family_id").val());
    });

    $('.new_donor').hide(); //hide the feedback div
    $('form#good_loan_form').on('submit', function (evt) {
        evt.preventDefault();
        var form_data = $(this).serialize();
        var id = $("#family_id").val();
        var food_surplus_api = `/services/create_loan?id=${id}`;
        console.log(food_surplus_api);
        $.ajax({
            url: food_surplus_api,
            type: "POST",
            data: form_data,
            dataType: 'json',
            success: function (response) {
                if (response.status) {
                    $('.new_donor').show();
                    $(".new_donor").text(response.msg).addClass('alert alert-success')
                    setTimeout(function () {
                        $('.new_donor').hide();
                        location.reload();
                        // $('.zakat_modal').modal('hide');
                    }, 3000);
                } else {
                    $('.new_donor').show();
                    $(".new_donor").text(response.msg).addClass('alert alert-danger form_error')
                    // setTimeout(function () {
                    //     $('.new_donor').hide();
                    //     // location.reload();
                    // }, 3000);
                }
            },
            error: function (err) {
                $('.new_donor').show();
                $(".new_donor").text(err.msg).addClass('alert alert-danger server_error')
                // setTimeout(function () {
                //     $('.new_donor').hide();
                //     // location.reload();
                // }, 3000);
            }
        });
    });

    // installment_number 

    var loan_amount = $('#loan_amount');
    var installment_value = $('#installment_value');
    var installment_number = $('#installment_number');

    function calculateResult() {
        var value1 = loan_amount.val();
        var value2 = installment_value.val();

        // Perform division only if both values are provided and not zero
        if (value1 !== '' && value2 !== '' && parseFloat(value2) !== 0) {
            var divisionResult = parseFloat(value1) / parseFloat(value2);

            // Set the result value
            installment_number.val(divisionResult.toFixed(2));
        } else {
            installment_number.val('');
        }
    }

    loan_amount.on('input', calculateResult);
    installment_value.on('input', calculateResult);

    $('.user_name').hide()

    var userId = $('#userId').val();
    if(userId > 4){
        $('.user_name').hide()
    } else {
        $('.user_name').show()
    }

})

