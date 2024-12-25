$(document).ready(function () {


    // get all zakat in reciving mood 

    $.ajax({
        url: '/services/zkat_alfter',
        type: 'GET',
        dataType: 'json',
        processData: false,
        success: function (response) {
            myData = response.data;
            console.log(myData);
            if (response.status) {
                myData.forEach((element, i) => {
                    $('.zakat_fitr_row').append(`
                            <div class="col-lg-6">
                                <div class="zakat_content" id=${element[0]}>
                                    <h5 class="zakat-name"">
                                        ${element[1]}
                                    </h5>
                                    <ul class="list-unstyled p-0">
                                        <li>
                                            <img
                                                src="/takaful_portal_benefit/static/img/Icon material-attach-money.png"
                                                alt="money" />
                                            <span> ${element[3]} </span>
                                        </li>
                                        <li>
                                            <img
                                                src="/takaful_portal_benefit/static/img/Icon material-date-range.png"
                                                alt="date" />
                                            <span> ${element[4]} حتى ${element[5]} </span>
                                        </li>
                                    </ul>
                                    <span data-id="${element[0]}"
                                        class="donation zakat_fitr_link main_link"> تبرع الان </span>
                                </div>
                            </div>
                        `)
                });
            }
            else {
                $('.zakat_fitr_row').append(` <p> لايوجد زكاة لعرضها  </p> `)

            }
        },
        error: function (error) {
            $(".zakat_feedback").text(error.msg).addClass('alert alert-danger')
        }
    });

    var zakat_name_text = "";

    $(".zakat_fitr_row").on('click','.zakat_fitr_link', function(){
        console.log("hello");
        var data_id = $(this).data("id")
        console.log(data_id);
        const targetDiv = $('#' + data_id);
        console.log(targetDiv);
        if (targetDiv.length > 0) {
        const h5Element = targetDiv.find('h5');
        console.log(h5Element);

        if (h5Element.length > 0) {
            zakat_name_text = h5Element.text();
        }
      }
    })

    $("#zakat_fitr_form").on("submit", function (event) {
        event.preventDefault();

        var amount = $("#amount").val();
        var name_op = zakat_name_text; // Get the content from <h5>

        var encodedAmount = encodeURIComponent(amount);
        var encodedNameOp = encodeURIComponent(name_op);

        var redirectURL = "/dashboard/payment/paycard?name_op=" + encodedNameOp + "&required_amount=" + encodedAmount;

        window.location.href = redirectURL;
    });


    //set the zakat id 
    $('.zakat_fitr_row').on('click', '.zakat_fitr_link', function () {
        $('.zakat_modal').modal('show');
        $("#id_holder_input").val($(this).data('id'))
        console.log($("#id_holder_input").val());
    });
    // send zakat fitr handler

     $('.new_donor').hide(); //hie the feedback div

     $('form#zakat_fitr_form').on('submit', function (evt) {
         evt.preventDefault();
         var form_data = $(this).serialize();
         var id = $("#id_holder_input").val();
         var send_zakat_api = `/services/receive_zkat?id=${id}`;
         console.log(send_zakat_api);
         $.ajax({
             url: send_zakat_api,
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
                     $(".new_donor").text(response.msg).addClass('alert alert-danger')
                     setTimeout(function () {
                         $('.new_donor').hide();
                         // location.reload();
                     }, 3000);
                 }
             },
             error: function (err) {
                 $('.new_donor').show();
                 $(".new_donor").text(err.msg).addClass('alert alert-danger')
                 setTimeout(function () {
                     $('.new_donor').hide();
                     // location.reload();
                 }, 3000);
             }
         });
     });

    $('.material_btn').hide();
    $('.price_quantity').hide();

    $("#donation_type").change(function () {
        if ($(this).val() === 'cash') {
            $('.material_btn').hide();
            $('.cash_btn').show();
            $('.price_amount').show();
            $('.payment_method').show();
            $('.price_quantity').hide();

        } else if ($(this).val() === 'material') {
            $('.material_btn').show();
            $('.cash_btn').hide();
            $('.price_amount').hide();
            $('.payment_method').hide();
            $('.price_quantity').show();

        } else {
            $('.material_btn').show();
            $('.cash_btn').hide();
            $('.price_amount').show();
            $('.payment_method').show();
            $('.price_quantity').show();
        }
    })
})




//$(document).ready(function () {
//
//    // Validate and format the card expiry month
//    $('#cardExpiryMonth').on('input', function () {
//        var inputValue = $(this).val();
//        var formattedValue = inputValue.replace(/\D/g, '').slice(0, 2);
//
//        $(this).val(formattedValue);
//
//        if (formattedValue.length === 2) {
//            $('#cardExpiryYear').focus();
//        }
//    });
//
//    // Validate and format the card expiry year
//    $('#cardExpiryYear').on('input', function () {
//        var inputValue = $(this).val();
//        var formattedValue = inputValue.replace(/\D/g, '').slice(0, 2);
//
//        $(this).val(formattedValue);
//    });


//    $("#zakat_fitr_form").submit(function (event) {
//        event.preventDefault();
//        var form_data = $("#zakat_fitr_form").serialize();
//        // Send the POST request to Moyasar
//        $.ajax({
//            url: "https://api.moyasar.com/v1/payments",
//            type: "POST",
//            data: form_data,
//            dataType: "json",
//        })
//            .done(function (data) {
//                var paymentDate = data.created_at;
//                var date = new Date(paymentDate);
//                var options = { day: '2-digit', month: '2-digit', year: 'numeric' };
//                var formattedDate = date.toLocaleDateString('en-GB', options);
//                $('#pays_data #table_id tbody').append(
//                    `
//                        <tr>
//                            <td> ${data.metadata.user_name} </td>
//                            <td> ${data.amount} </td>
//                            <td> ${data.status} </td>
//                            <td> ${formattedDate} </td>
//                        </tr>
//                    `
//                )
//                window.location.href = data.source.transaction_url;
//            })
//            .fail(function (error) {
//                console.log(error);
//            });
//    });


//})