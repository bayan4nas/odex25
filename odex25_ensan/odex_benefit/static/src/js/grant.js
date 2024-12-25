$(document).ready(function () {

    $('input[type="file"]').each(function () {
        if ($(this).val() != "") {
            $(this).css('color', '#333');
        } else {
            $(this).css('color', 'black');
        }
    });

    $('input[type="file"]').change(function () {
        if ($(this).val() != "") {
            $(this).css('color', '#333');
        } else {
            $(this).css('color', 'black');
        }
    });

    var loadCities = function () {
        var state_id = $('#state_id').val();
        $.ajax({
            url: '/grant/register/load_cities',
            type: 'POST',
            data: {
                'state_id': state_id
            },
            success: function (data) {
                $('#city_id').html(data);
            }
        });
    }
    var loadCities_s = function () {
        var state_id = $('#state_id_s').val();
        $.ajax({
            url: '/grant/register/load_cities_s',
            type: 'POST',
            data: {
                'state_id_s': state_id
            },
            success: function (data) {
                $('#city_id_s').html(data);
            }
        });
    }
    var check_load_entity = function () {
        var entity_id = $('#entity_type').val();
        $.ajax({
            url: '/grant/request/check_entity',
            type: 'POST',
            data: {
                'entity_id': entity_id
            },
            success: function (d) {
                entityValidation(d);
            },
            dataType: "json"
        });
    }

    var entityValidation = function (target) {
        $('.help-block').html('');

        var clean = false

        for (var key in target) {
            if (target.hasOwnProperty(key)) {
                clean = false;
                var msg = target[key];
                $('#' + key + '-help').html(msg);
                $('#' + key).focus();
            }
        }
    }

    var processValidation = function (target) {
        $('.help-block').html('');

        var clean = true

        for (var key in target) {
            if (target.hasOwnProperty(key)) {
                clean = false;
                var msg = target[key];
                $('#' + key + '-help').html(msg);
                $('#' + key).focus();
            }
        }
        if (clean) {
            $('form').off('submit');
            $('form').submit();
        } else {
            $.unblockUI();
        }
    }
    loadCities();
    $('#state_id').on('change', function () {
        loadCities();
    });
    $('#state_id_s').on('change', function () {
        loadCities_s();
    });
    var loadEntity = function () {
        var entity_id = $('#entity_id').val();
        $.ajax({
            url: '/grant/request/load_entity',
            type: 'POST',
            data: {
                'entity_id': entity_id
            },
            success: function (data) {
                $('#entity_id').html(data);
            }
        });
    }
    loadEntity();

    $('#entity_type').on('change', function () {
        check_load_entity();
    });

    $('form#register-form').on('submit', function (e) {
            e.preventDefault();
            var form = $('form')
            var data = form.serializeArray();
            $.each(form.find('input[type="file"]'), function (i, tag) {
                $.each($(tag)[0].files, function (i, file) {
                    data.push({name: tag.name + '#' + file.name, value:  file.size});
                });
            });
            $.blockUI({message: "جاري اتمام التسجيل ..."});
            $.ajax({
                type: 'POST',
                url: '/grant/validate_entity',
                data: data,
                success: function (d) {
                    processValidation(d);
                },
                error: function () {
                    $.unblockUI();
                },
                dataType: "json"
            });
            return false;
        }
    );

    $('form#request_grant-form').on('submit', function (e) {
        e.preventDefault();
        var data = $('form').serialize();
        $.ajax({
            type: 'POST',
            url: '/grant/validate_grant',
            data: data,
            success: function (d) {
                processValidation(d);
            },
            dataType: "json"
        });
        return false;
    });

    $(function () {
        $("#grant_start_date").datepicker({
            autoclose: true,
            todayHighlight: true
        }).datepicker('update', new Date());
    });

    $(function () {
        $("#record_start_date").datepicker({
            autoclose: true,
            todayHighlight: true
        });
    });
    $(function () {
        $("#record_start_date_r").datepicker({
            autoclose: true,
            todayHighlight: true
        });
    });
    $(function () {
        $("#expiry_board_directors_date").datepicker({
            autoclose: true,
            todayHighlight: true
        });
    });

    $(function () {
        $("#expiry_board_directors_date-1").datepicker({
            autoclose: true,
            todayHighlight: true
        }).datepicker('update', new Date());
    });

    $(function () {
        $("#record_end_date").datepicker({
            autoclose: true,
            todayHighlight: true
        });
    });

    function gmod(n, m) {
        return ((n % m) + m) % m;
    }

    function kuwaiticalendar(adjust) {
        var today = adjust;

        day = today.getDate();
        month = today.getMonth();
        year = today.getFullYear();

        m = month + 1;
        y = year;
        if (m < 3) {
            y -= 1;
            m += 12;
        }
        a = Math.floor(y / 100.);
        b = 2 - a + Math.floor(a / 4.);
        if (y < 1583) b = 0;
        if (y === 1582) {
            if (m > 10) b = -10;
            if (m === 10) {
                b = 0;
                if (day > 4) b = -10;
            }
        }

        jd = Math.floor(365.25 * (y + 4716)) + Math.floor(30.6001 * (m + 1)) + day + b - 1524;

        b = 0;
        if (jd > 2299160) {
            a = Math.floor((jd - 1867216.25) / 36524.25);
            b = 1 + a - Math.floor(a / 4.);
        }
        bb = jd + b + 1524;
        cc = Math.floor((bb - 122.1) / 365.25);
        dd = Math.floor(365.25 * cc);
        ee = Math.floor((bb - dd) / 30.6001);
        day = (bb - dd) - Math.floor(30.6001 * ee);
        month = ee - 1;
        if (ee > 13) {
            cc += 1;
            month = ee - 13;
        }
        year = cc - 4716;

        wd = gmod(jd + 1, 7) + 1;

        iyear = 10631. / 30.;
        epochastro = 1948084;
        epochcivil = 1948085;

        shift1 = 8.01 / 60.;

        z = jd - epochastro;
        cyc = Math.floor(z / 10631.);
        z = z - 10631 * cyc;
        j = Math.floor((z - shift1) / iyear);
        iy = 30 * cyc + j;
        z = z - Math.floor(j * iyear + shift1);
        im = Math.floor((z + 28.5001) / 29.5);
        if (im == 13) im = 12;
        id = z - Math.floor(29.5001 * im - 29);

        var myRes = new Array(8);

        myRes[0] = day; //calculated day (CE)
        myRes[1] = month - 1; //calculated month (CE)
        myRes[2] = year; //calculated year (CE)
        myRes[3] = jd - 1; //julian day number
        myRes[4] = wd - 1; //weekday number
        myRes[5] = id; //islamic date
        myRes[6] = im; //islamic month
        myRes[7] = iy; //islamic year

        return myRes;
    }

    function writeIslamicDate(adjustment) {
        var wdNames = new Array("الاحد", "الاثنين", "الثلاثاء", "الاربعاء", "الخميس", "الجمعة", "السبت");
        var iMonthNames = new Array("محرم", "صفر", "ربيع الاول", "ربيع الاخر",
            "جماد الاول", "جماد الاخر", "رجب", "شعبان",
            "رمضان", "شوال", "ذو القعدة", "ذو الحجة");
        var iDate = kuwaiticalendar(adjustment);
        var outputIslamicDate = iDate[7] + "-" + iDate[6] + "-" + iDate[5];
        return outputIslamicDate;
    }

    function formatDate(date) {
        var d = new Date(date),
            month = '' + (d.getMonth() + 1),
            day = '' + d.getDate(),
            year = d.getFullYear();

        if (month.length < 2) month = '0' + month;
        if (day.length < 2) day = '0' + day;

        return [year, month, day].join('-');
    }

    function reformatDate(record_start_date) {
        var date = record_start_date.split('-');
        var year = date[0];
        var day = date[2];
        var month = date[1];

        return [month, day, year].join('-');
    }

    function reformatDate(record_end_date) {
        var date = record_end_date.split('-');
        var year = date[0];
        var day = date[2];
        var month = date[1];

        return [month, day, year].join('-');
    }

    $(document).ready(function () {
        if (window.location.pathname ==='/page/entity_profile/edit/update/') {
            var record_start_date = $("input#record_start_date").val();
            if (record_start_date === undefined) {
                var record_start_date = $("input#record_start_date_2").val();
            }
            var record_end_date = $("input#record_end_date").val();
            if (record_end_date == undefined){
                var record_end_date = $("input#record_end_date_2").val();
            }
            var expiry_board_directors_date = $("input#expiry_board_directors_date").val();
            var expiry_date = expiry_board_directors_date.split('-');
            var expiry_year = expiry_date[0];
            var expiry_day = expiry_date[1];
            var expiry_month = expiry_date[2];
            var end_date = record_end_date.split('-');
            var end_year = end_date[0];
            var end_day = end_date[1];
            var end_month = end_date[2];
            var date = record_start_date.split('-');
            var year = date[0];
            var day = date[1];
            var month = date[2];
            year = parseInt(year);
            year=String(year);
            var new_date = year.concat('-', day, '-', month);
            $('input#hijri_record_start_date').val(writeIslamicDate(new Date(record_start_date)));
            $('input#hijri_record_start_date_2').val(writeIslamicDate(new Date(record_start_date)));
            var new_date = end_year.concat('-', end_day, '-', end_month);
            $('input#hijri_record_end_date_2').val(writeIslamicDate(new Date(new_date)));
            $('input#hijri_record_end_date').val(writeIslamicDate(new Date(new_date)));
            var new_date = expiry_year.concat('-', expiry_day, '-', expiry_month);
            $('input#hijri_expiry_board_directors_date_2').val(writeIslamicDate(new Date(new_date)));
            $('input#hijri_expiry_board_directors_date').val(writeIslamicDate(new Date(new_date)));
        }

        if (window.location.pathname === '/page/entity_profile') {
            var record_start_date = $("input#record_start_date_2").val();
            var record_end_date = $("input#record_end_date_2").val();
            var expiry_board_directors_date = $("input#expiry_board_directors_date").val();
            var expiry_date = expiry_board_directors_date.split('-');
            var expiry_year = expiry_date[0];
            var expiry_day = expiry_date[1];
            var expiry_month = expiry_date[2];
            var end_date = record_end_date.split('-');
            var end_year = end_date[0];
            var end_day = end_date[1];
            var end_month = end_date[2];
            var date = record_start_date.split('-');
            var year = date[0];
            var day = date[1];
            var month = date[2];
            var new_date = year.concat('-', day, '-', month);
            $('input#hijri_record_start_date_2').val(writeIslamicDate(new Date(record_start_date)));
            var new_date = end_year.concat('-', end_day, '-', end_month);
            $('input#hijri_record_end_date_2').val(writeIslamicDate(new Date(new_date)));
            var new_date = expiry_year.concat('-', expiry_day, '-', expiry_month);
            $('input#hijri_expiry_board_directors_date_2').val(writeIslamicDate(new Date(new_date)));

        }
        if (window.location.pathname === '/page/entity_profile/edit'){
            var record_start_date = $("input#record_start_date").val();
            var record_end_date = $("input#record_end_date").val();
            var expiry_board_directors_date = $("input#expiry_board_directors_date").val();
            var expiry_date = expiry_board_directors_date.split('-');
            var expiry_year = expiry_date[0];
            var expiry_day = expiry_date[1];
            var expiry_month = expiry_date[2];
            var date = record_start_date.split('-');
            var end_date = record_end_date.split('-');
            var year = date[0];
            var day = date[1];
            var month = date[2];
            var end_year = end_date[0];
            var end_day = end_date[1];
            var end_month = end_date[2];
            year = parseInt(year);
            end_year = parseInt(end_year);
            year=String(year);
            end_year = String(end_year);
            var new_date = year.concat('-', day, '-', month);
            if (record_start_date !=''){
                $('input#hijri_record_start_date').val(writeIslamicDate(new Date(record_start_date)));
            }
            var new_date = end_year.concat('-', end_day, '-', end_month);
            $('input#record_end_date').val(new_date);
            $('input#hijri_record_end_date').val(writeIslamicDate(new Date(new_date)));
            var new_date = expiry_year.concat('-', expiry_day, '-', expiry_month);
            $('input#hijri_expiry_board_directors_date').val(writeIslamicDate(new Date(new_date)));


        }});
    $('input#record_start_date').on('change', function () {
        var record_start_date = $("input#record_start_date").val();
        var record_start_datee = record_start_date.replace("-", "/")
        var record_start_dateee = record_start_datee.replace("-", "/")
        date = record_start_date.split('-');
        var year = date[2];
        var day = date[1];
        var month = date[0];
        year = parseInt(year);
        var new_date = month.concat('-', day, '-', year);
        $('input#hijri_record_start_date').val(writeIslamicDate(new Date(record_start_dateee)));

    });
    $('input#record_start_date_r').on('change', function () {
        var record_start_date = $("input#record_start_date_r").val();
        var record_start_datee = record_start_date.replace("-", "/")
        var record_start_dateee = record_start_datee.replace("-", "/")
        date = record_start_date.split('-');
        var year = date[2];
        var day = date[1];
        var month = date[0];
        year = parseInt(year);
        var new_date = month.concat('-', day, '-', year);
        $('input#hijri_record_start_date').val(writeIslamicDate(new Date(record_start_dateee)));
    });

    $('input#record_end_date').on('change', function () {
        var record_end_date = $("input#record_end_date").val();
        var record_end_datee = record_end_date.replace("-","/").replace("-", "/")
        date = record_end_date.split('-');
        var year = date[2];
        var day = date[1];
        var month = date[0];
        year = parseInt(year);
        var new_date = month.concat('-', day, '-', year);
        $('input#hijri_record_end_date').val(writeIslamicDate(new Date(record_end_datee)));
    });

    $('input#hijri_record_start_date').each(function () {
        function convert_to_hijri(date) {
            if (date.length == 0) {
                return false
            }
            var jd = $.calendars.instance('islamic').toJD(parseInt(date[0].year()), parseInt(date[0].month()), parseInt(date[0].day()));
            var date = $.calendars.instance('gregorian').fromJD(jd);
            var date_value = new Date(parseInt(date.year()), parseInt(date.month()) - 1, parseInt(date.day()) - 1);
            date_value = formatDate(date_value);

            var date_co = date_value.split('-');
            var year = date_co[0];
            var day = date_co[2];
            var month = date_co[1];
            var new_date = year.concat('-',month , '-',day );
            var final_date = reformatDate(date_value);
            $('input#record_start_date').val(new_date);
            if (window.location.pathname === '/grant/register/') {
                $('input#record_start_date_r').val(final_date);
            }

        }

        $(this).calendarsPicker({
            calendar: $.calendars.instance('islamic', 'ar'),
            dateFormat: 'yyyy-mm-dd',
            onSelect: convert_to_hijri,
            showOnFocus: true,
        });
    });

    $('input#hijri_record_end_date').each(function () {
        function convert_to_hijri(date) {
            if (date.length == 0) {
                return false
            }
            var jd = $.calendars.instance('islamic').toJD(parseInt(date[0].year()), parseInt(date[0].month()), parseInt(date[0].day()));
            var date = $.calendars.instance('gregorian').fromJD(jd);
            var date_value = new Date(parseInt(date.year()), parseInt(date.month()) - 1, parseInt(date.day()) - 1);
            date_value = formatDate(date_value);
            var final_date = reformatDate(date_value);

            var date_co = date_value.split('-');
            var year = date_co[0];
            var day = date_co[2];
            var month = date_co[1];
            var new_date = year.concat('-',month , '-',day );
            var final_date = reformatDate(date_value);
            $('input#record_end_date').val(new_date);
            if (window.location.pathname === '/grant/register/') {
                $('input#record_end_date').val(final_date);
            }
        }

        $(this).calendarsPicker({
            calendar: $.calendars.instance('islamic', 'ar'),
            dateFormat: 'yyyy-mm-dd',
            onSelect: convert_to_hijri,
            showOnFocus: true,
        });
    });

    $('input#grant_start_date').on('change', function () {
        var record_start_date = $("input#grant_start_date").val();
        var record_start_datee = record_start_date.replace("-", "/")
        var record_start_dateee = record_start_datee.replace("-", "/")
        $('input#hijri_grant_start_date').val(writeIslamicDate(new Date(record_start_dateee)));

    });

    $('input#hijri_grant_start_date').each(function () {

        function convert_to_hijri(date) {
            if (date.length == 0) {
                return false
            }
            var jd = $.calendars.instance('islamic').toJD(parseInt(date[0].year()), parseInt(date[0].month()), parseInt(date[0].day()));
            var date = $.calendars.instance('gregorian').fromJD(jd);
            var date_value = new Date(parseInt(date.year()), parseInt(date.month()) - 1, parseInt(date.day()) - 1);
            date_value = formatDate(date_value);

            var date_co = date_value.split('-');
            var year = date_co[0];
            var day = date_co[2];
            var month = date_co[1];
            year = parseInt(year);
            year = year + 4;
            new_date = month.concat('-', day, '-', year);

            var final_date = reformatDate(date_value);
            $('input#grant_start_date').val(final_date);

        }

        $(this).calendarsPicker({
            calendar: $.calendars.instance('islamic', 'ar'),
            dateFormat: 'yyyy-mm-dd',
            onSelect: convert_to_hijri,
            showOnFocus: true,
        });
    });

    $('input#expiry_board_directors_date').on('change', function () {
        var record_start_date = $("input#expiry_board_directors_date").val();
        var record_start_datee = record_start_date.replace("-", "/")
        var record_start_dateee = record_start_datee.replace("-", "/")
        date = record_start_date.split('-');
        var year = date[2];
        var day = date[1];
        var month = date[0];
        year = parseInt(year);
        var new_date = month.concat('-', day, '-', year);
        $('input#hijri_expiry_board_directors_date').val(writeIslamicDate(new Date(record_start_dateee)));
    });


    $('input#hijri_expiry_board_directors_date').each(function () {
        function convert_to_hijri(date) {
            if (date.length == 0) {
                return false
            }
            var jd = $.calendars.instance('islamic').toJD(parseInt(date[0].year()), parseInt(date[0].month()), parseInt(date[0].day()));
            var date = $.calendars.instance('gregorian').fromJD(jd);
            var date_value = new Date(parseInt(date.year()), parseInt(date.month()) - 1, parseInt(date.day()) - 1);
            date_value = formatDate(date_value);
            var final_date = reformatDate(date_value);

            var date_co = date_value.split('-');
            var year = date_co[0];
            var day = date_co[2];
            var month = date_co[1];
            var new_date = year.concat('-',month , '-',day );
            var final_date = reformatDate(date_value);
            $('input#expiry_board_directors_date').val(new_date);
            if (window.location.pathname === '/grant/register/') {
                $('input#expiry_board_directors_date').val(final_date);
            }
        }

        $(this).calendarsPicker({
            calendar: $.calendars.instance('islamic', 'ar'),
            dateFormat: 'yyyy-mm-dd',
            onSelect: convert_to_hijri,
            showOnFocus: true,
        });
    });

    $('form#myreset-form').on('submit', function (e) {
        e.preventDefault();
        var data = $('input').serialize();
        $.ajax({
            type: 'POST',
            url: '/reset_password/validate_pswd',
            data: data,
            success: function (d) {
                processValidation(d);
            },
            dataType: "json"
        });
        return false;
    });


});
