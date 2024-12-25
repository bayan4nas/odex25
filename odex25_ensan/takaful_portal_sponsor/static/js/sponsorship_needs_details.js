$(document).ready(function () {
    const urlSearchParams = new URLSearchParams(window.location.search);
    const benefit_type = urlSearchParams.get("benefit_type");
    const benefit_id = urlSearchParams.get("benefit_id");
    // benefit details 
    $.ajax({
        url: `/portal/sponsor/benefit/info?benefit_type=${benefit_type}&benefit_id=${benefit_id}`,
        type: 'GET',
        dataType: 'json',
        success: function (data) {
            result = data.benefit;
            if(benefit_type == 'widow'){
                windowOrphans = result.orphan_ids
            }
            console.log(result);
            var html = '';
            if (data.status) {
                console.log(result);
                html +=
                    `
                            <div class="data_wrapper d-flex flex-lg-wrap">
                                <div class="right_part ">
                                    <div class="header">
                                        <img
                                            src="/takaful_portal_sponsor/static/img/document.png"
                                            alt="document" />
                                        <span>بيانات اليتيم </span>
                                    </div>
                                    <div class="data_content">
                                        <ul class="p-0 list-unstyled">
                                            <li class="d-flex align-items-center">
                                                <h5>الاسم</h5>
                                                <span> ${result.name}</span>
                                            </li>
                                            <li class="d-flex align-items-center">
                                                <h5>الجنس</h5>
                                                <span> ${result.gender} </span>
                                            </li>
                                            <li class="d-flex align-items-center">
                                                <h5>السن </h5>
                                                <span> ${result.age} </span>
                                            </li>
                                            <li class="d-flex align-items-center">
                                                <h5>المدينة </h5>
                                                <span> ${result.city_id} </span>
                                            </li>
                                            <li class="d-flex align-items-center">
                                                <h5>رقم اليتيم </h5>
                                                <span> ${result.number} </span>
                                            </li>
                                            <li class="d-flex align-items-center">
                                                <h5>نوع الحالة </h5>
                                                <span> ${result.benefit_type} </span>
                                            </li>
                                        </ul>
                                    </div>
                                </div>
                                <div class="left_part ">
                                    <div class="header">
                                        <img src="/takaful_portal_sponsor/static/img/file.png"
                                        alt="file" />
                                        <span> بيانات شخصية و إجتماعية </span>
                                    </div>
                                    <div class="data_content">
                                        <ul class="p-0 list-unstyled">
                                            <li class="d-flex align-items-center">
                                                <h5>العائل الحالي</h5>
                                                <span> ${result.responsible} </span>
                                            </li>
                                            <li class="d-flex align-items-center">
                                                <h5>حالة السكن </h5>
                                                <span> ${result.housing_status} </span>
                                            </li>
                                            <li class="d-flex align-items-center">
                                                <h5>التعليم </h5>
                                                <span> ${result.education_status} </span>
                                            </li>
                                            <li class="d-flex align-items-center">
                                                <h5>المرحلة الدراسية </h5>
                                                <span> ${result.education_level} </span>
                                            </li>
                                            <li class="d-flex align-items-center">
                                                <h5> الصف الدراسي  </h5>
                                                <span> ${result.class_room} </span>
                                            </li>
                                            <li class="d-flex align-items-center">
                                                <h5> الحالة الصحية  </h5>
                                                <span>${result.health_status} </span>
                                            </li>
                                            <li class="d-flex align-items-center">
                                                <h5> كم يحفظ من القران  </h5>
                                                <span>${result.quran_parts} </span>
                                            </li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                            <div style="border-radius: 0;"
                                class="data_wrapper d-flex flex-lg-wrap">
                                <div class="right_part ">
                                    <div class="header">
                                        <img
                                            src="/takaful_portal_sponsor/static/img/document.png"
                                            alt="document" />
                                        <span > احتياجات اليتيم  </span>
                                    </div>
                                    <div class="data_content">
                                        <ul class="p-0 list-unstyled">
                                            <li class="d-flex align-items-center">
                                                <h5>نسبة الإحتياج</h5>
                                                <span> ${result.benefit_needs_percent} % </span>
                                            </li>
                                            <li class="d-flex align-items-center">
                                                <h5>احتياجات طارئة</h5>
                                                <span> ${result.benefit_available_need} </span>
                                            </li>
                                            <li class="d-flex align-items-center">
                                                <h5>متأخرات مالية </h5>
                                                <span> ${result.benefit_arrears_value} </span>
                                            </li>
                                            <li class="d-flex align-items-center">
                                                <h5>الاحتياج الشهري  </h5>
                                                <span> ${result.benefit_total_need} </span>
                                            </li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        `
                $('.makfoul_data .need_sponsorship_details').html(html);
                $("#gift_modal #name, #contribution_modal #name, #SingleKafala #name").val(result.name)
                $("#gift_modal #number, #contribution_modal #number, #SingleKafala #number").val(result.number)
                $("#gift_modal #benefit_type, #contribution_modal #benefit_type, #SingleKafala #benefit_type").val(result.benefit_type)
                $(".need_sponsorship_name").append( ` <span> اليتيم ${result.name} </span> ` )
                $('#SingleKafala #month_amount').val(result.benefit_total_need)

                windowOrphans.forEach((element, i) => {
                    $('#orphan_ids').append(

                        `
                            <option value=${i+1}> ${element.first_name} </option>
                        `
                    )
                    
                });
            }
            else {
                console.log(data.msg);
            }
        },
        error: function (error) {
            console.log(error);
        }
    });
})