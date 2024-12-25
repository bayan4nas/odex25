$(document).ready(function () {
    var currentPage = 1;
    var benefitType = 'orphan'; // Default value
    var nextorphan
    var prev
    var next

    function orphan_widows_needs(page) {
        $.ajax({
            url: '/portal/sys/benefits/page/' + page,
            type: 'GET',
            data: { benefit_type: benefitType },
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
                            <tr data-type="orphan" data-id="${element.id}" class="expired">
                                <td> ${i + 1} </td>
                                <td> ${element.first_name} </td>
                                <td> ${element.gender} </td>
                                <td> ${element.age} </td>
                                <td> ${element.city_id} </td>
                                <td> ${element.benefit_type} </td>
                                <td> ${element.benefit_needs_percent} % </td>
                                <td class="expired_td">
                                    <div class="d-flex align-items-center">
                                        <a href="#" class="sadad_link"> ساهم الان </a>
                                    </div>
                                </td>
                            </tr>
                        `
                    });
                    $('.orphan_widows_needs tbody').html(html);
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
    orphan_widows_needs(1);
    function updateButtons(next, prev) {
        $('#benefits-next').attr('disabled', (next == null));
        $('#benefits-prev').attr('disabled', (prev == null));
    }

    $('#benefit-type').change(function () {
        benefitType = $(this).val();
        $('.financial_donation tbody tr').data("type", benefitType)
        orphan_widows_needs(1);

    });
    $('#benefits-prev').click(function () {
        orphan_widows_needs(currentPage - 1);
        updateButtons(next, prev)

    });
    $('#benefits-next').click(function () {
        orphan_widows_needs(currentPage + 1);
        updateButtons(next, prev)
    });
})