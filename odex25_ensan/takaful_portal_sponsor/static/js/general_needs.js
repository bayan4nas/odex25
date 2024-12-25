
$(document).ready(function () {
    var currentPage = 1;
    var prev
    var next
    function generalNeeds(page) {
        $.ajax({
            url: '/portal/sys/need_types/page/' + page,
            type: 'GET',
            dataType: 'json',
            success: function (data) {
                results = data.results;
                console.log(results);
                var html = '';
                if (data.status) {
                    results.forEach((element, i) => {
                        console.log(element);
                        html +=
                            `
                            <tr data-type="${benefitType}" data-id="${element.id}" class="expired">
                                <td> ${i + 1} </td>
                                <td> ${element.name} </td>
                                <td> ${element.city_name} </td>
                                <td> ${element.benefit_count} </td>
                                <td> ${element.target_amount} </td>
                                <td> ${element.completion_ratio} % </td>
                                <td> ${element.remaining_amount}  </td>
                                <td class="expired_td">
                                    <div class="d-flex align-items-center">
                                        <a  href="#" class="sadad_link contribute"> ساهم الان</a>
                                    </div>
                                </td>
                            </tr>
                        `
                    });
                    $('.general_needs tbody').html(html);
                    next = data.next_page;
                    prev = (currentPage > 1) ? currentPage - 1 : null;
                    currentPage = page;
                }
                else {
                    console.log(data.msg);
                }
            },
            error: function (err) {
                console.log(err.msg);
            }
        });
    }
    generalNeeds(1);
    function updateButtons(next, prev) {
        $('#benefits-next').attr('disabled', (next == null));
        $('#benefits-prev').attr('disabled', (prev == null));
    }

    $('#benefits-prev').click(function () {
        generalNeeds(currentPage - 1);
        updateButtons(next, prev)

    });
    $('#benefits-next').click(function () {
        generalNeeds(currentPage + 1);
        updateButtons(next, prev)
    });
})