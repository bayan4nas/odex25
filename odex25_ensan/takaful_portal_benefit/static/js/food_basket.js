// $(document).ready(function () {


//     // get all food basket in reciving mood 

//     $.ajax({
//         url: '/services/food_basket',
//         type: 'GET',
//         dataType: 'json',
//         processData: false,
//         success: function (response) {
//             food_basket = response.data[0].basket;
//             console.log(food_basket);
//             if (response.status) {
//                 food_basket.forEach((element, i) => {
//                     $('.food_basket_row').append(`
//                         <div class="col-lg-6">
//                                 <div class="zakat_content" id=${element.id}>
//                                     <h5>
//                                         ${element.name}
//                                     </h5>
//                                     <ul class="list-unstyled p-0">
//                                         ${element.description ?

//                             `
//                                             <li>
//                                                 <img src="/takaful_portal_benefit/static/img/Icon awesome-info-circle.png" alt="info" />
//                                                 <span> ${element.description} </span>
//                                             </li>
//                                             `
//                             :

//                             ''
//                         }
                                        
//                                         <li>
//                                             <img src="/takaful_portal_benefit/static/img/Icon material-date-range.png" alt="date" />
//                                             <span>${element.date_start} حتى  ${element.date_end} </span>
//                                         </li>
//                                     </ul>
//                                     <span data-id="${element.id}"
//                                         class="donation food_basket_link main_link"> تبرع الان 
//                                     </span>
//                                 </div>
//                             </div>
//                         `)
//                 });
//             }
//             else {
//                 $('.food_basket_row').append(` <p> لايوجد زكاة لعرضها  </p> `)

//             }
//         },
//         error: function (error) {
//             $(".zakat_fitr_feedback").text(error.msg).addClass('alert alert-danger')
//         }
//     });


//     var zakat_sacrifices_text = "";

//     $(".food_basket_row").on('click','.food_basket_link', function(){
//         console.log("hello");
//         var data_id = $(this).data("id")
//         console.log(data_id);
//         const targetDiv = $('#' + data_id);
//         console.log(targetDiv);
//         if (targetDiv.length > 0) {
//         const h5Element = targetDiv.find('h5');
//         console.log(h5Element);

//         if (h5Element.length > 0) {
//             zakat_sacrifices_text = h5Element.text();
//         }
//       }
//     })

//     $("#food_basket_form").on("submit", function (event) {
//         event.preventDefault(); 

//         var amount = $("#amount").val();

//         var name_op = zakat_sacrifices_text;

//         var encodedAmount = encodeURIComponent(amount);
//         var encodedNameOp = encodeURIComponent(name_op);

//         var redirectURL = "/dashboard/payment/paycard?name_op=" + encodedNameOp + "&required_amount=" + encodedAmount;

//         window.location.href = redirectURL;
//     });



//     //set the zakat id 
//     $('.food_basket_row').on('click', '.food_basket_link', function () {
//         $('.food_basket_modal').modal('show');
//         $("#basket_id_holder_input").val($(this).data('id'))
//         console.log($("#basket_id_holder_input").val());
//     });
//     // send zakat fitr handler

//     $('.new_donor').hide(); //hie the feedback div

//     $('form#food_basket_form').on('submit', function (evt) {
//         evt.preventDefault();
//         var form_data = $(this).serialize();
//         var id = $("#basket_id_holder_input").val();
//         var food_basket_api = `/services/add_food_basket?id=${id}`;
//         console.log(food_basket_api);
//         $.ajax({
//             url: food_basket_api,
//             type: "POST",
//             data: form_data,
//             dataType: 'json',
//             success: function (response) {
//                 if (response.status) {
//                     $('.new_donor').show();
//                     $(".new_donor").text(response.msg).addClass('alert alert-success')
//                     setTimeout(function () {
//                         $('.new_donor').hide();
//                         location.reload();
//                         // $('.zakat_modal').modal('hide');
//                     }, 3000);
//                 } else {
//                     $('.new_donor').show();
//                     $(".new_donor").text(response.msg).addClass('alert alert-danger')
//                     setTimeout(function () {
//                         $('.new_donor').hide();
//                         // location.reload();
//                     }, 3000);
//                 }
//             },
//             error: function (err) {
//                 $('.new_donor').show();
//                 $(".new_donor").text(err.msg).addClass('alert alert-danger')
//                 setTimeout(function () {
//                     $('.new_donor').hide();
//                     // location.reload();
//                 }, 3000);
//             }
//         });
//     });


//     $('.material_btn').hide();
//     $('.price_quantity').hide();

//     $("#donation_type").change(function () {
//         if ($(this).val() === 'cash') {
//             $('.material_btn').hide();
//             $('.cash_btn').show();
//             $('.price_amount').show();
//             $('.payment_method').show();
//             $('.price_quantity').hide();

//         } else if ($(this).val() === 'material') {
//             $('.material_btn').show();
//             $('.cash_btn').hide();
//             $('.price_amount').hide();
//             $('.payment_method').hide();
//             $('.price_quantity').show();

//         } else {
//             $('.material_btn').show();
//             $('.cash_btn').hide();
//             $('.price_amount').show();
//             $('.payment_method').show();
//             $('.price_quantity').show();
//         }
//     })
// })


$(document).ready(function () {

    // get all food basket in reciving mood 

    $.ajax({
        url: '/services/food_basket',
        type: 'GET',
        dataType: 'json',
        processData: false,
        success: function (response) {
            // console.log(response);
            if (response && response.data && response.data.length > 0) {
                food_basket = response.data[0].basket;
                // console.log(food_basket);
                if (response.status) {
                    food_basket.forEach((element, i) => {
                        $('.food_basket_row').append(`
                            <div class="col-lg-6">
                                    <div class="zakat_content" id=${element.id}>
                                        <h5>
                                            ${element.name}
                                        </h5>
                                        <ul class="list-unstyled p-0">
                                            ${element.description ?
    
                                `
                                                <li>
                                                    <img src="/takaful_portal_benefit/static/img/Icon awesome-info-circle.png" alt="info" />
                                                    <span> ${element.description} </span>
                                                </li>
                                                `
                                :
    
                                ''
                            }
                                            
                                            <li>
                                                <img src="/takaful_portal_benefit/static/img/Icon material-date-range.png" alt="date" />
                                                <span>${element.date_start} حتى  ${element.date_end} </span>
                                            </li>
                                        </ul>
                                        <span data-id="${element.id}"
                                            class="donation food_basket_link main_link"> تبرع الان 
                                        </span>
                                    </div>
                                </div>
                            `)
                    });
                }
                else {
                    $('.food_basket_row').append(` <p> لايوجد زكاة لعرضها  </p> `)
    
                }
            }
        },
        error: function (error) {
            $(".zakat_fitr_feedback").text(error.msg).addClass('alert alert-danger')
        }
    });


    var zakat_sacrifices_text = "";

    $(".food_basket_row").on('click','.food_basket_link', function(){
        console.log("hello");
        var data_id = $(this).data("id")
        console.log(data_id);
        const targetDiv = $('#' + data_id);
        console.log(targetDiv);
        if (targetDiv.length > 0) {
        const h5Element = targetDiv.find('h5');
        console.log(h5Element);

        if (h5Element.length > 0) {
            zakat_sacrifices_text = h5Element.text();
        }
      }
    })

    $("#food_basket_form").on("submit", function (event) {
        event.preventDefault(); 

        var amount = $("#amount").val();

        var name_op = zakat_sacrifices_text;

        var encodedAmount = encodeURIComponent(amount);
        var encodedNameOp = encodeURIComponent(name_op);

        var redirectURL = "/dashboard/payment/paycard?name_op=" + encodedNameOp + "&required_amount=" + encodedAmount;

        window.location.href = redirectURL;
    });



    //set the zakat id 
    $('.food_basket_row').on('click', '.food_basket_link', function () {
        $('.food_basket_modal').modal('show');
        $("#basket_id_holder_input").val($(this).data('id'))
        console.log($("#basket_id_holder_input").val());
    });
    // send zakat fitr handler

    $('.new_donor').hide(); //hie the feedback div

    $('form#food_basket_form').on('submit', function (evt) {
        evt.preventDefault();
        var form_data = $(this).serialize();
        var id = $("#basket_id_holder_input").val();
        var food_basket_api = `/services/add_food_basket?id=${id}`;
        console.log(food_basket_api);
        $.ajax({
            url: food_basket_api,
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