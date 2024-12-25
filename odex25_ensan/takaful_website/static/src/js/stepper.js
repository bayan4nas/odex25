
$(document).ready(function () {

    $.validator.addMethod("usernameRegex", function (value, element) {
        return this.optional(element) || /^[a-zA-Z0-9]*$/i.test(value) || /[\u0600-\u06FF]/.test(value);
    }, "الاسم لابد أن يحتوي على حروف و أرقام فقط ");

    $(".next").click(function () {
        var form = $("#myform");
        form.validate({
            errorElement: 'span',
            errorClass: 'help-block',
            highlight: function (element, errorClass, validClass) {
                $(element).closest('.form-group').addClass("has-error");
            },
            unhighlight: function (element, errorClass, validClass) {
                $(element).closest('.form-group').removeClass("has-error");
            },
            rules: {
                work: {
                    required: true,
                    usernameRegex: true,
                    minlength: 6,
                },
                workPlace: {
                    required: true,
                },
                indetity: {
                    required: true,
                },
                bank: {
                    required: true,
                },
            },
            messages: {
                work: {
                    required: "هذا الحقل مطلوب ",
                    minlength: "من فضلك أدخل على الاقل 6 حروف "
                },
                workPlace: {
                    required: "هذا الحقل مطلوب ",
                },
                indetity: {
                    required: "هذا الحقل مطلوب ",
                },
                bank: {
                    required: "هذا الحقل مطلوب "
                },
            }
        });
        if (form.valid() === true) {
            $(".step_field.active").fadeOut(100, function () {
                $(this)
                    .removeClass("active")
                    .next(".step_field")
                    .addClass("active")
                    .fadeIn();
            });
        }
    });

    $('#previous').click(function () {
        if ($('#company_information').is(":visible")) {
            current_fs = $('#company_information');
            next_fs = $('#account_information');
        } else if ($('#personal_information').is(":visible")) {
            current_fs = $('#personal_information');
            next_fs = $('#company_information');
        }
        next_fs.show();
        current_fs.hide();
    });

    //@naresh action dynamic childs
    var next_exp = 0;
    $("#add-more1").click(function (e) {
        e.preventDefault();
        var addto = "#fielda" + next_exp;
        var addRemove = "#fielda" + (next_exp);
        next_exp = next_exp + 1;
        var newInp = ' <div id="fielda' + next_exp + '" name="field1' + next_exp + '"><div class="form-group"><label class="col-md-3">Job Title</label><div class="col-md-7"><input type="text"  name="job_tit[]" id="job_tit" class="form-control" placeholder="e.g. Java/php Developer" required> </div><br><br><br><!-- Text input--><div class="form-group"><label class="col-md-3">Company</label><div class="col-md-7"><input type="text"  name="company[]" id="company" class="form-control" placeholder="" required> </div> <div><br><br><!-- Text input--><div class="form-group"><label class="col-md-3">City</label> <div class="col-md-7"><input type="text"  name="city[]" id="city" class="form-control" placeholder="" required></div></div><br><br><!-- Text input--><div class="form-group"><label class="col-md-3">Time period</label><div class="col-md-8"><div class="col-md-3"><select class="form-control"  name="work_from[]" ><option value="1995">    1995	</option><option value="1996">	1996	</option><option value="1997">	1997	</option><option value="1998">	1998	</option><option value="1999">	1999	</option><option value="2000">	2000	</option><option value="2001">	2001	</option><option value="2002">	2002	</option><option value="2003">	2003	</option><option value="2004">	2004	</option><option value="2005">	2005	</option><option value="2006">	2006	</option><option value="2007">	2007	</option><option value="2008">	2008	</option><option value="2009">	2009	</option><option value="2010">	2010	</option><option value="2011">	2011	</option><option value="2012">	2012	</option><option value="2013">	2013	</option><option value="2014">	2014	</option><option value="2015">	2015	</option><option value="2016">	2016	</option></select></div><div class="col-md-1"><label>To</label></div><div class="col-md-3"><select class="form-control"  name="work_to[]" ><option value="1980">	1980	</option><option value="2000">	2000	</option><option value="2001">	2001	</option><option value="2002">	2002	</option><option value="2003">	2003	</option><option value="2004">	2004	</option><option value="2005">	2005	</option><option value="2006">	2006	</option><option value="2007">	2007	</option><option value="2008">	2008	</option><option value="2009">	2009	</option><option value="2010">	2010	</option><option value="2011">	2011	</option><option value="2012">	2012	</option><option value="2013">	2013	</option><option value="2014">	2014	</option><option value="2015">	2015	</option><option value="2016">	2016	</option><option value="2017">	2017	</option><option value="2018">	2018	</option><option value="2019">	2019	</option><option value="2020">	2020	</option></select></div></div></div><br><br><div class="form-group"><input type="checkbox" name="cur_work[]" value="cur_work"> I currently work here<br></div><br><hr></div>';
        var newInput = $(newInp);

        var removeBtn = '<button id="remove' + (next_exp - 1) + '" class="btn btn-danger remove-me" >Remove</button></div></div><div id="field"><br>';
        var removeButton = $(removeBtn);
        $(addto).after(newInput);
        $(addRemove).after(removeButton);
        $("#fielda" + next_exp).attr('data-source', $(addto).attr('data-source'));
        $("#count").val(next_exp);

        $('.remove-me').click(function (e) {
            e.preventDefault();
            var fieldNum = this.id.charAt(this.id.length - 1);
            var fieldID = "#fielda" + fieldNum;
            $(this).remove();
            $(fieldID).remove();
        });
    });


    //@naresh action dynamic childs
    var nextedu = 0;
    $("#add-more").click(function (e) {
        e.preventDefault();
        var addto = "#field" + nextedu;
        var addRemove = "#field" + (nextedu);
        nextedu = nextedu + 1;
        var newIn = ' <div id="field' + nextedu + '" name="field' + nextedu + '"><div class="form-group"><label class="col-md-3">Education level</label><div class="col-md-7"><select class="form-control"  name="edu_level[]" ><option value="1">High school or equivalent</option><option value="2">Diploma</option><option value="3">Higher National Diploma</option><option value="4">Bachelos</option><option value="5">Masters</option><option value="6">Doctorate</option></select></div></div><br><br><br><!-- Text input--><div class="form-group"><label class="col-md-3">Field of Study</label><div class="col-md-7"><input type="text"  name="field_stu[]" id="field_stu" class="form-control" placeholder="e.g. Computer Science, Intellectual Property,Psychology." required> </div></div><br><br><!-- Text input--><div class="form-group"><label class="col-md-3">University</label><div class="col-md-7"><input type="text"  name="university[]" id="university" class="form-control" placeholder="" required></div></div><br><br><!-- Text input--><div class="form-group"><label class="col-md-3">Time period</label><div class="col-md-8"><div class="col-md-3"><select class="form-control"  name="edu_from[]" ><option value="1995">    1995    </option><option value="1996">	1996	</option><option value="1997">	1997	</option><option value="1998">	1998	</option><option value="1999">	1999	</option><option value="2000">	2000	</option><option value="2001">	2001	</option><option value="2002">	2002	</option><option value="2003">	2003	</option><option value="2004">	2004	</option><option value="2005">	2005	</option><option value="2006">	2006	</option><option value="2007">	2007	</option><option value="2008">	2008	</option><option value="2009">	2009	</option><option value="2010">	2010	</option><option value="2011">	2011	</option><option value="2012">	2012	</option><option value="2013">	2013	</option><option value="2014">	2014	</option><option value="2015">	2015	</option><option value="2016">	2016	</option></select></div><div class="col-md-1"><label>To</label></div><div class="col-md-3"><select class="form-control"  name="edu_to[]" ><option value="1980">	1980	</option><option value="2000">	2000	</option><option value="2001">	2001	</option><option value="2002">	2002	</option><option value="2003">	2003	</option><option value="2004">	2004	</option><option value="2005">	2005	</option><option value="2006">	2006	</option><option value="2007">	2007	</option><option value="2008">	2008	</option><option value="2009">	2009	</option><option value="2010">	2010	</option><option value="2011">	2011	</option><option value="2012">	2012	</option><option value="2013">	2013	</option><option value="2014">	2014	</option><option value="2015">	2015	</option><option value="2016">	2016	</option><option value="2017">	2017	</option><option value="2018">	2018	</option><option value="2019">	2019	</option><option value="2020">	2020	</option></select></div></div></div> <br><hr></div>';
        var newInput = $(newIn);

        var removeBtn = '<button id="remove' + (nextedu - 1) + '" class="btn btn-danger remove-me" >Remove</button></div></div><div id="field">';
        var removeButton = $(removeBtn);
        $(addto).after(newInput);
        $(addRemove).after(removeButton);
        $("#field" + nextedu).attr('data-source', $(addto).attr('data-source'));
        $("#count").val(nextedu);

        $('.remove-me').click(function (e) {
            e.preventDefault();
            var fieldNum = this.id.charAt(this.id.length - 1);
            var fieldID = "#field" + fieldNum;
            $(this).remove();
            $(fieldID).remove();
        });
    });


});
