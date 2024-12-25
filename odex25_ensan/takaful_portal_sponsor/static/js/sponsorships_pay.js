$(document).ready(function () {
    var currentPage = 1;
    var benefitType = 'orphan'; // Default value
    var prev
    function sponsorshipPay(page) {
        $.ajax({
            url: '/portal/sponsor/sponsorships/page/' + page,
            type: 'GET',
            data: { benefit_type: benefitType },
            dataType: 'json',
            success: function (data) {
                results = data.results;
                const filteredData = results.filter(item => item.month_count == 0);
                console.log(filteredData);
                var html = '';
                if (data.status) {
                    filteredData.forEach((element, i) => {
                        html +=
                            `
                            <tr data-type="orphan" data-id="${element.benefit_id.id}" class="expired">
                                <td> ${i + 1} </td>
                                <td> ${element.benefit_id.name} </td>
                                <td> ${element.benefit_id.gender} </td>
                                <td> ${element.benefit_id.age} </td>
                                <td> ${element.benefit_id.city_id} </td>
                                <td> ${element.benefit_id.benefit_type} </td>
                                <td> ${element.benefit_id.benefit_needs_percent} % </td>
                                <td> ${element.benefit_id.benefit_arrears_value} </td>
                                <td> ${element.start_date} </td>
                                <td class="expired_td">
                                    <div class="d-flex align-items-center">
                                        <span> بحاجة للتجديد </span>
                                        <a href="#" class="sadad_link"> سداد </a>
                                    </div>
                                </td>
                            </tr>
                        
                        `
                    });
                    $('.sponsorships_pay tbody').html(html);
                    next = data.next_page;
                    prev = (currentPage > 1) ? currentPage - 1 : null;
                    currentPage = page;
                }
                else {
                    console.log(data.msg);
                }
            },
            error: function (jqXHR, textStatus, errorThrown) {
                console.log(textStatus + ': ' + errorThrown);
            }
        });
    }
    sponsorshipPay(1);
    sponsorshipsCancelation(1)
    function updateButtons(next, prev) {
        $('#benefits-next').attr('disabled', (next == null));
        $('#benefits-prev').attr('disabled', (prev == null));
    }
    $('#benefit-type').change(function () {
        benefitType = $(this).val();
        $('.financial_donation tbody tr').data("type", benefitType)
        sponsorshipPay(1);
    });
    $('#benefits-prev').click(function () {
        sponsorshipPay(currentPage - 1);
        updateButtons(next, prev)

    });
    $('#benefits-next').click(function () {
        sponsorshipPay(currentPage + 1);
        updateButtons(next, prev)
    });

});