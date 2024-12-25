odoo.define('odex_grant_management.odex_attches', function (require) {
    "use strict";
    $(document).ready(function () {

        $('form#entity_account_update-form')
            .on('submit', function (e) {
                var form = $(this);
                var formData = new FormData();
                var formParams = form.serializeArray();
                $.each(form.find('input[type="file"]'), function (i, tag) {
                    $.each($(tag)[0].files, function (i, file) {
                        formData.append(tag.name, file);
                    });
                });

                $.each(formParams, function (i, val) {
                    formData.append(val.name, val.value);
                });
                $.blockUI({message: "جاري رفع التعديلات ..."});
                $.ajax({
                    type: 'POST',
                    url: '/page/entity_profile/edit/update',
                    data: formData,
                    dataType: "json",
                    success: function (d) {
                        window.location.href = '/page/entity_profile';
                        $.unblockUI();
                    },
                    error: function () {
                        window.location.href = '/page/entity_profile';
                        $.unblockUI();
                    },
                });
                return false;
            });
        $('form#upload_grant_attachments').on('submit', function (evt) {
            evt.preventDefault();
            var form_data = new FormData();
            form_data.append("file", $("#attach_desc_file")[0].files[0]);
            form_data.append("description", $("#attach_desc").val());
            form_data.append("grant_id", $("#grant_data").val());
            form_data.append("file_name", $("#attach_desc_file")[0].files[0].name);
            $.blockUI({message: "جاري اتمام تحميل المرفقات ..."});
            $.ajax({
                url: "/upload/grant/attaches", // NB: Use the correct action name
                type: "POST",
                data: form_data,
                processData: false,
                contentType: false,
                success: function (response) {

                    var base_url = window.location.origin;
                    response = $.parseJSON(response);
                    if (response.status === 'ok') {
                        var attach = response.attachment;
                        var name = response.name;
                        var description = response.description
                        var date = response.date;
                        var item = "<a href=" + base_url + "/web/content/" + attach + "/" + String(name) + "  target=\"_blank\">" + "<span class=\"fa fa-download\">" + name + "</span></a>";
                        var markup = "<tr>" +
                            "<td>" +
                            "<input type='checkbox' value='" + attach + "' name='record'>" +
                            "</td>" +
                            "<td>" + date + "</td>" +
                            "<td>" + description + "</td>" +
                            "<td>" + item + "</td>" +
                            "</tr>";
                        $(".attach_table tbody").append(markup);
                        $.unblockUI();
                        $("form#upload_grant_attachments").trigger("reset");
                    } else {
                        var message = response.msg;
                        alert(message)
                        $.unblockUI();
                    }

                },
                error: function (response) {

                    $.unblockUI();
                }
            });
        });

        $('form#upload_voucher_attachments').on('submit', function (evt) {
            evt.preventDefault();
            var form_data = new FormData();
            form_data.append("file", $("#attach_voucher_file")[0].files[0]);
            form_data.append("grant_id", $("#grant_voucher_data").val());
            form_data.append("file_name", $("#attach_voucher_file")[0].files[0].name);
            $.blockUI({message: "جاري اتمام تحميل المرفقات ..."});
            $.ajax({
                url: "/upload/voucher/attaches", // NB: Use the correct action name
                type: "POST",
                data: form_data,
                processData: false,
                contentType: false,
                success: function (response) {
                    response = $.parseJSON(response);
                    var base_url = window.location.origin;
                    if (response.status === 'ok') {
                        var attach = response.attachment;
                        var name = response.name;
                        var description = response.description
                        var date = response.date;
                        var item = "<a href=" + base_url + "/web/content/" + attach + "/" + String(name) + "  target=\"_blank\">" + "<span class=\"fa fa-download\">" + name + "</span></a>";
                        var markup = "<tr>" +
                            "<td>" +
                            "<input type='checkbox' value='" + attach + "' name='record'>" +
                            "</td>" +
                            "<td>" + date + "</td>" +
                            "<td>" + description + "</td>" +
                            "<td>" + item + "</td>" +
                            "</tr>";
                        $(".attach_table tbody").append(markup);
                        $.unblockUI();
                        $("form#upload_voucher_attachments").trigger("reset");
                    } else {
                        var message = response.msg;
                        alert(message)
                        $.unblockUI();
                    }

                },
                error: function (response) {
                    $.unblockUI();
                }
            });
        });

        $('form#upload_report_attachments').on('submit', function (evt) {
            evt.preventDefault();
            var form_data = new FormData();
            form_data.append("file", $("#attach_report_file")[0].files[0]);
            form_data.append("grant_id", $("#grant_report_data").val());
            form_data.append("file_name", $("#attach_report_file")[0].files[0].name);
            $.blockUI({message: "جاري اتمام تحميل المرفقات ..."});
            $.ajax({
                url: "/upload/report/attaches", // NB: Use the correct action name
                type: "POST",
                data: form_data,
                processData: false,
                contentType: false,
                success: function (response) {
                    response = $.parseJSON(response);
                    var base_url = window.location.origin;
                    if (response.status === 'ok') {
                        var attach = response.attachment;
                        var name = response.name;
                        var description = response.description
                        var date = response.date;
                        var item = "<a href=" + base_url + "/web/content/" + attach + "/" + String(name) + "  target=\"_blank\">" + "<span class=\"fa fa-download\">" + name + "</span></a>";
                        var markup = "<tr>" +
                            "<td>" +
                            "<input type='checkbox' value='" + attach + "' name='record'>" +
                            "</td>" +
                            "<td>" + date + "</td>" +
                            "<td>" + description + "</td>" +
                            "<td>" + item + "</td>" +
                            "</tr>";
                        $(".attach_table tbody").append(markup);
                        $.unblockUI();
                        $("form#upload_report_attachments").trigger("reset");
                    } else {
                        var message = response.msg;
                        alert(message)
                        $.unblockUI();
                    }

                },
                error: function (response) {

                    $.unblockUI();
                }
            });
        });

        $(".check_all").click(function () {

            if (this.checked) {
                $("#record").each(function () {
                    $('input[name=record]').prop('checked', true);
                });
            } else {
                $("#record").each(function () {
                    $('input[name=record]').prop('checked', false);
                });
            }
        });

        $(".delete-row").click(function () {
            $(".attach_table tbody").find('input[name="record"]').each(function () {
                var self = this;
                if ($(self).is(":checked")) {
                    var data = new FormData();
                    data.append("attach", $(self).val());
                    data.append("grant_id", $("#grant_data").val());
                    $.blockUI({message: "جاري حذف المرفقات ..."});
                    $.ajax({
                        url: "/remove/grant/attaches", // NB: Use the correct action name
                        type: "POST",
                        data: data,
                        processData: false,
                        contentType: false,
                        success: function (response) {
                            $(self).parents("tr").remove();
                            $.unblockUI();
                        },
                        error: function (response) {
                            $.unblockUI();
                        }
                    });
                }
            });
        });
    });
});
