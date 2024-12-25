
// $(document).ready(function () {

//     // get all food food surplus 
//     $.ajax({
//         url: '/services/food',
//         type: 'GET',
//         dataType: 'json',
//         processData: false,
//         success: function (response) {
//             food_surplus = response.data[0].foods;
//             console.log(food_surplus);
//             if (response.status) {
//                 food_surplus.forEach((element, i) => {
//                     $('.food_surplus_row').append(`
//                     <div class="col-lg-6">
//                         <div class="zakat_content">
//                             <h5>
//                                 ${element.name} : ${element.name_food}
//                             </h5>
//                             <ul class="list-unstyled p-0">
//                                 ${element.description ?

//                             `
//                                     <li>
//                                         <img src="/takaful_portal_benefit/static/img/Icon awesome-info-circle.png" alt="info" />
//                                         <span> ${element.description} </span>
//                                     </li>
//                                     `
//                             :

//                             ''
//                         }
                                
//                                 <li>
//                                     <img src="/takaful_portal_benefit/static/img/metro-user.png" alt="user" />
//                                     <span>  المستفيدين : ${element.surplus_count} </span>
//                                 </li>
//                                 <li>
//                                     <img src="/takaful_portal_benefit/static/img/awesome-mug-hot.png" alt="mug" />
//                                     <span> الكمية : ${element.quantity} </span>
//                                 </li>
//                                 <li>
//                                     <img src="/takaful_portal_benefit/static/img/material-location-on.png" alt="location" />
//                                     <span> ${element.address}  </span>
//                                 </li>
//                                 <li>
//                                     <img src="/takaful_portal_benefit/static/img/Icon material-date-range.png" alt="date" />
//                                     <span>${element.date_start} حتى  ${element.date_end} </span>
//                                 </li>
//                             </ul>
//                             <span data-id="${element.id}"
//                                 class="donation food_surplus_link main_link"> تقديم طلب  
//                             </span>
//                         </div>
//                     </div>
//                 `)
//                 });
//             }
//             else {
//                 $('.food_surplus_row').append(` <p class="text-center  w-100 m-0"> لايوجد فائض طعام  لعرضها  </p> `)

//             }
//         },
//         error: function (error) {
//             $(".food_surplus_feedback").text(error.msg).addClass('alert alert-danger')
//         }
//     });



//     //set the zakat id 
//     $('.food_surplus_row').on('click', '.food_surplus_link', function () {
//         $('.food_surplus_modal').modal('show');
//         $("#food_id").val($(this).data('id'))
//         console.log($("#food_id").val());
//     });
//     // send zakat fitr handler

//     $('.new_donor').hide(); //hie the feedback div
//     $('form#food_surplus_form').on('submit', function (evt) {
//         evt.preventDefault();
//         var form_data = $(this).serialize();
//         var id = $("#surplus_id_holder_input").val();
//         var food_surplus_api = `/services/restaurant/request_food`;
//         console.log(food_surplus_api);
//         $.ajax({
//             url: food_surplus_api,
//             type: "POST",
//             data: form_data,
//             dataType: 'json',
//             success: function (response) {
//                 if (response.status) {
//                     $('.new_donor').show();
//                     $(".new_donor").text(response.msg).addClass('alert alert-success')
//                     setTimeout(function () {
//                         $('.new_donor').hide();
//                         // location.reload();
//                         $('.food_surplus_modal').modal('hide');
//                     }, 3000);
//                 } else {
//                     $('.new_donor').show();
//                     $(".new_donor").text(response.msg).addClass('alert alert-danger form_error')
//                     // setTimeout(function () {
//                     //     $('.new_donor').hide();
//                     //     // location.reload();
//                     // }, 3000);
//                 }
//             },
//             error: function (err) {
//                 $('.new_donor').show();
//                 $(".new_donor").text(err.msg).addClass('alert alert-danger server_error')
//                 // setTimeout(function () {
//                 //     $('.new_donor').hide();
//                 //     // location.reload();
//                 // }, 3000);
//             }
//         });
//     });
// })


$(document).ready(function () {

    // get all food food surplus 
    $.ajax({
        url: '/services/food',
        type: 'GET',
        dataType: 'json',
        processData: false,
        success: function (response) {
            if (response.data && response.data.length > 0) {
                food_surplus = response.data[0].foods;
                console.log(food_surplus);
                food_surplus.forEach((element, i) => {
                    $('.food_surplus_row').append(`
                    <div class="col-lg-6">
                        <div class="zakat_content">
                            <h5>
                                ${element.name} : ${element.name_food}
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
                                    <img src="/takaful_portal_benefit/static/img/metro-user.png" alt="user" />
                                    <span>  المستفيدين : ${element.surplus_count} </span>
                                </li>
                                <li>
                                    <img src="/takaful_portal_benefit/static/img/awesome-mug-hot.png" alt="mug" />
                                    <span> الكمية : ${element.quantity} </span>
                                </li>
                                <li>
                                    <img src="/takaful_portal_benefit/static/img/material-location-on.png" alt="location" />
                                    <span> ${element.address}  </span>
                                </li>
                                <li>
                                    <img src="/takaful_portal_benefit/static/img/Icon material-date-range.png" alt="date" />
                                    <span>${element.date_start} حتى  ${element.date_end} </span>
                                </li>
                            </ul>
                            <span data-id="${element.id}"
                                class="donation food_surplus_link main_link"> تقديم طلب  
                            </span>
                        </div>
                    </div>
                `)
                });
            } else {
                $('.food_surplus_row').append(`<p class="text-center w-100 m-0">لايوجد فائض طعام لعرضها</p>`);
            }
        },
        error: function (error) {
            $(".food_surplus_feedback").text(error.msg).addClass('alert alert-danger')
        }
    });



    //set the zakat id 
    $('.food_surplus_row').on('click', '.food_surplus_link', function () {
        $('.food_surplus_modal').modal('show');
        $("#food_id").val($(this).data('id'))
        console.log($("#food_id").val());
    });
    // send zakat fitr handler

    $('.new_donor').hide(); //hie the feedback div
    $('form#food_surplus_form').on('submit', function (evt) {
        evt.preventDefault();
        var form_data = $(this).serialize();
        var id = $("#surplus_id_holder_input").val();
        var food_surplus_api = `/services/restaurant/request_food`;
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
                        // location.reload();
                        $('.food_surplus_modal').modal('hide');
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
})