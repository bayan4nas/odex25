from odoo import models, fields, api, _
from odoo.exceptions import ValidationError , AccessError
from odoo.tools.safe_eval import safe_eval
import ast
from datetime import datetime, date
from dateutil.relativedelta import relativedelta, SA, SU, MO
import calendar
import pytz



class SystemDashboard(models.Model):
    _name = 'system_dashboard_classic.dashboard'
    _description = 'System Dashboard'
    name = fields.Char("")
    
    def is_user(self, groups, user):
        # this method is used to check whether current user in a certin group
        for group in groups:
            if user.id in group.users.ids:
                return True
        return False

    @api.model
    def get_data(self):
        '''
        we call the mothod from js do_action function, when a user access the system
        we first check if user belongs to one of the groups on the configuration model lines,
        then draw cards depends on states or stage they should see
        '''

        # employee and user date and vars defined to be used inside this method
        values = {'user': [], 'timesheet': [], 'leaves': [], 'payroll': [], 'attendance': [], 'employee': [],
                  'cards': []}
        base = self.env['base.dashbord'].search([])

        user = self.env.user
        user_id = self.env['res.users'].sudo().search_read(
            [('id', '=', user.id)], limit=1)
        employee_id = self.env['hr.employee'].sudo().search_read(
            [('user_id', '=', user.id)], limit=1)

        employee_object = self.env['hr.employee'].sudo().search(
            [('user_id', '=', user.id)], limit=1)

        job_english = employee_object.job_id.english_name

        t_date = date.today()
        attendance_date = {}
        leaves_data = {}
        payroll_data = {}
        timesheet_data = {}
        ###################################################

        # check whether last action sign in or out and its date
        is_hr_attendance_module = self.env['ir.module.module'].sudo().search([('name', '=', 'hr_attendance')])
        if is_hr_attendance_module and is_hr_attendance_module.state == 'installed':
            attendance = self.env['attendance.attendance'].sudo().search(
                [('employee_id', '=', employee_object.id), ('action_date', '=', t_date)])
            is_attendance = True
            if not attendance:
                is_attendance = False
            if attendance and attendance[-1].action == 'sign_out':
                is_attendance = False
            user_tz = pytz.timezone(self.env.context.get('tz', 'Asia/Riyadh') or self.env.user.tz)
            if attendance:
                time_object = fields.Datetime.from_string(attendance[-1].name)
                time_in_timezone = pytz.utc.localize(time_object).astimezone(user_tz)
            attendance_date.update({'is_attendance': is_attendance,
                                    'time': time_in_timezone if attendance else False
                                    })
            # if noc is found case shoud be handeld
        ###############################################

        # compute leaves taken and remaing leaves
        is_leave_module = self.env['ir.module.module'].sudo().search([('name', '=', 'hr_holidays_community')])
        if is_leave_module and is_leave_module.state == 'installed':
            leaves = self.env['hr.holidays'].sudo().search(
                [('employee_id', '=', employee_object.id), ('holiday_status_id.leave_type', '=', 'annual'),
                 ('type', '=', 'add'), ('check_allocation_view', '=', 'balance')], limit=1)
            taken = leaves.leaves_taken
            remaining_leaves = leaves.remaining_leaves
            leaves_data.update({'taken': taken,
                                'remaining_leaves': remaining_leaves

                                })
        ###################################################

        # compute payroll taken and remaing payslips
        first_day = date(date.today().year, 1, 1)
        last_day = date(date.today().year, 12, 31)

        is_payslip_module = self.env['ir.module.module'].sudo().search([('name', '=', 'exp_hr_payroll')])
        if is_payslip_module and is_payslip_module.state == 'installed':
            payslip = self.env['hr.payslip'].sudo().search_count(
                [('employee_id', '=', employee_object.id), ('date_from', '>=', first_day), ('date_to', '<=', last_day)])
            payroll_data.update({'taken': payslip,
                                 'payslip_remaining': 12 - payslip
                                 })
        ##############################################

        # compute timesheet taken and remaing timesheet
        is_analytic_module = self.env['ir.module.module'].sudo().search([('name', '=', 'analytic')])
        if is_analytic_module and is_analytic_module.state == 'installed':
            calender = employee_object.resource_calendar_id
            days_off_name = []
            days_special_name = []
            days_of_week = 7
            working_hours = 0.0
            sepcial_working_hours = 0

            # get working hours and days_off and special days if emp is a full day working
            if calender.is_full_day:
                working_hours = calender.working_hours
                for off in calender.shift_day_off:
                    days_off_name.append(off.name)
                for special in calender.special_days:
                    if not special.date_from and not special.date_to:
                        sepcial_working_hours += special.working_hours
                        days_special_name.append(special.name)
                    elif not special.date_from and str(t_date) <= special.date_to:
                        sepcial_working_hours += special.working_hours
                        days_special_name.append(special.name)
                    elif not special.date_to and str(t_date) >= special.date_from:
                        sepcial_working_hours += special.working_hours
                        days_special_name.append(special.name)
                    elif special.date_from and special.date_to and str(t_date) >= special.date_from and str(
                            t_date) <= special.date_to:
                        sepcial_working_hours += special.working_hours
                        days_special_name.append(special.name)

            # get working hours and days_off and special days if emp is shit hours working
            # else:
            #     working_hours = calender.shift_one_working_hours + calender.shift_two_working_hours
            #     for off in calender.full_day_off:
            #         days_off_name.append(off.name)
            #     if calender.special_days_partcial:
            #         for special in calender.special_days_partcial:
            #             if not special.date_from and not special.date_to:
            #                 sepcial_working_hours += special.working_hours
            #                 days_special_name.append(special.name)
            #             elif not special.date_from and str(t_date) < special.date_to:
            #                 sepcial_working_hours += special.working_hours
            #                 days_special_name.append(special.name)
            #             elif not special.date_to and str(t_date) > special.date_from:
            #                 sepcial_working_hours += special.working_hours
            #                 days_special_name.append(special.name)
            #             elif special.date_from and special.date_to and str(t_date) >= special.date_from and str(
            #                     t_date) <= special.date_to:
            #                 sepcial_working_hours += special.working_hours
            #                 days_special_name.append(special.name)

            # get start of the week according to days off
            star_of_week = None
            if 'saturday' in days_off_name:
                star_of_week = SU
            elif 'friday' in days_off_name:
                star_of_week = SA
            elif 'sunday' in days_off_name:
                star_of_week = MO
            else:
                star_of_week = SA

                # calcultion of all working hours and return done working hours and remaining
            lenght_days_off = len(days_off_name)
            lenght_special_days_off = len(days_special_name)
            lenght_work_days = (days_of_week - lenght_days_off) - lenght_special_days_off
            total_wroking_hours = (working_hours * lenght_work_days) + sepcial_working_hours
            domain = [('employee_id', '=', employee_object.id), '&', (
            'date', '>=', (date.today() + relativedelta(weeks=-1, days=1, weekday=star_of_week)).strftime('%Y-%m-%d')),
                      ('date', '<=', (date.today() + relativedelta(weekday=6)).strftime('%Y-%m-%d')), ]
            timesheet = self.env['account.analytic.line'].sudo().search(domain)
            day_name_list = ['saturday', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', ]
            done_hours = 0
            for sheet in timesheet:
                day = datetime.strptime(str(sheet.date), '%Y-%m-%d').weekday()
                day_name = day_name_list[day]
                if day_name not in days_off_name:
                    done_hours = done_hours + sheet.unit_amount

            don_hours = sum(item.unit_amount for item in timesheet)
            timesheet_data.update({'taken': don_hours,
                                   'timesheet_remaining': total_wroking_hours - don_hours
                                   })

        ##############################################

        if base:
            for models in base:
                for model in models:
                    #we use try and except access error if user has no read access on a model 
                    try:
                        # print(model)
                        # print(model.with_user(user).check_access_rights('read'))
                        # print("user", user)
                        model.with_user(user).check_access_rights('read')
                        mod = {'name': '', 'model': '', 'icon': '', 'lines': [], 'type': 'approve', 'domain_to_follow': []}
                        for line in model.line_ids:
                            if self.is_user(line.group_ids,
                                            user):  # call method to return if user is in one of the groups in current line
                                # static vars for the card
                                # TODO: find a way to fix translation,
                                # the filed is name is translateable,
                                # but its not loaded when change lang,
                                # so we handel it by searching on translation object.
                                model_name_to_serach = model.name if model.name else model.model_id.name
                                #value = self.env['ir.translation'].sudo().search([('source', '=', model_name_to_serach)], limit=1).value
                                value = "text"
                                card_name =  model.name if model.name else model.model_id.name
                                # if self.env.user.lang == 'en_US':
                                #     card_name = model.name if model.name else model.model_id.name
                                # else:
                                #     card_name = value
                                mod['name'] = card_name
                                mod['name_arabic'] = card_name
                                mod['name_english'] = card_name
                                mod['model'] = model.model_name
                                mod['image'] = model.card_image
                                
                                # var used in domain to serach with either state or state
                                state_or_stage = 'state' if line.state_id else 'stage_id'

                                state_click = line.state_id.state if line.state_id else int(line.stage_id.stage_id)
                                state_follow = line.state_id.state if line.state_id else int(line.stage_id.stage_id)

                                ''' below lists to passed for search count 
                                    it contains the domain from action_id if it contains domain and the domain in the action,
                                    dosnt contains state field,if it does remove the state.
                                    and the actual domain of state
                                    '''
                                action_domain_click = []
                                action_domain_follow = []
                                if model.action_domain:
                                    try:  # because we can use literal eval only with string if the action domain contains active word not str it throw an error

                                        dom_act = ast.literal_eval(model.action_domain)
                                        for i in dom_act:
                                            if i[0] != 'state':
                                                action_domain_click.append(i)
                                                action_domain_follow.append(i)
                                    except ValueError:
                                        pass

                                '''
                                if model is hr.holdiays and hr_holidays_workflow moduel is installed ,
                                we need to search with state or stage,
                                because the moduel adds stages for some recods
                                '''
                                if model.model_name == 'hr.holidays':
                                    hr_holidays_workflow = self.env['ir.module.module'].sudo().search(
                                        [('name', '=', 'hr_holidays_workflow')])
                                    if hr_holidays_workflow and hr_holidays_workflow.state == 'installed':
                                        action_domain_click.append('|')
                                        action_domain_click.append(('stage_id.name', '=', line.state_id.state))
                                action_domain_click.append(('state', '=', line.state_id.state) if line.state_id else (
                                'stage_id', '=', int(line.stage_id.stage_id)))

                                # we use str to be able to use replace method, and make domain valid for search orm method then converted back to list
                                domain_click = str(action_domain_click).replace('(', '[').replace(')', ']')
                                domain_click = ast.literal_eval(domain_click)

                                domain_follow = str(action_domain_follow).replace('(', '[').replace(')', ']')
                                domain_follow = ast.literal_eval(domain_follow)

                                state_to_click = self.env[model.model_name].search_count(action_domain_click)

                                mod['domain_to_follow'].append(state_follow)
                                action_domain_follow.append((state_or_stage, 'not in', mod['domain_to_follow']))
                                state_to_follow = self.env[model.model_name].search_count(action_domain_follow)

                                # below domains to be passed to do action in js
                                domain_follow_js = str(action_domain_follow).replace('(', '[').replace(')', ']')
                                domain_follow_js = ast.literal_eval(domain_follow_js)

                                # for translation
                                # TODO: find a way to fix translations,we load states in ar lang it create states in ar lang in the table and vise versa

                                state = ""
                                if line.state_id:
                                    if self.env.user.lang == 'en_US':
                                        state = line.state_id.state
                                    else:
                                        state = line.state_id.name
                                if line.stage_id:
                                    if self.env.user.lang == 'en_US':
                                        state = state = line.stage_id.name
                                    else:
                                        state = line.stage_id.value

                                '''for every line in states form th config model ,we add a card with its data
                                so we could have a card with "record to confirm  count is 5"
                                '''
                                mod['lines'].append({
                                    'id': line.state_id.id if line.state_id else line.stage_id.id,
                                    'count_state_click': state_to_click,  # count of state to click on card
                                    'count_state_follow': state_to_follow,  # count of state to follow on card

                                    'state_approval': _('') + '' + _(line.state_id.name),
                                    # title of card ex:records to confirm in approve tab
                                    'state_folow': _('All Records'),  # title of card in track tap

                                    'domain_to_follow': state_follow,  # domain

                                    'form_view': model.form_view_id.id,  # to open specific list
                                    'list_view': model.list_view_id.id,  # to open specific from

                                    'domain_click': domain_click,  # to open specific records in approval tab
                                    'domain_follow': domain_follow_js,  # to open specific records in track tab

                                    'context': model.action_context,

                                })
                                # sort the cards according to states or stages (draft,confirm,etc..)
                                mod['lines'] = sorted(mod['lines'], key=lambda i: i['id'])

                        '''if user in tow or more cards we wont create another card,
                            but append the new data in the old card
                            so one card could have two ex:records to confirm and new line records to approve'''

                        if mod['name'] != '':
                            values['cards'].append(mod)

                        ''' if we check the is_self_service field new card will be added to sef service screen 
                            and it depnds on current user ,
                            because search method apply security and access right,records rules'''
                        if model.is_self_service:
                            card_name =  model.name if model.name else model.model_id.name
                            mod = self.env[model.model_name]
                            js_domain = []
                            service_action_domain = []

                            ''' check if user_id = user.id to search for user own records 
                            if there is domain in the action which open the view 
                            get the domain and append the old one to new one
                            '''
                            if model.action_domain:
                                js_domain = model.action_domain
                                try:  # because we can use literal eval only with string if the action domain contains active word not str it throw an error
                                    
                                    service_action = ast.literal_eval(model.action_domain)
                                    for i in service_action:
                                        if i[0] != 'state':
                                            service_action_domain.append(i)
                                            
                                except ValueError:
                                    pass

                                # service_action_domain.append('|')
                                if 'employee_id' in mod._fields and 'user_id' in mod._fields:
                                    service_action_domain.append('|')
                                    service_action_domain.append(('user_id', '=', user.id))
                                    service_action_domain.append(('employee_id.user_id', '=', user.id))

                                if 'employee_id' in mod._fields:
                                    service_action_domain.append(('employee_id.user_id', '=', user.id))

                                if 'user_id' in mod._fields:
                                    service_action_domain.append(('user_id', '=', user.id))
                                # service_action_domain.append(('employee_id.user_id','=',user.id))

                            else:
                                if 'employee_id' in mod._fields and 'user_id' in mod._fields:
                                    service_action_domain.append('|')
                                    service_action_domain.append(('user_id', '=', user.id))
                                    service_action_domain.append(('employee_id.user_id', '=', user.id))
                                # service_action_domain.append('|')
                                if 'employee_id' in mod._fields:
                                    service_action_domain.append(('employee_id.user_id', '=', user.id))
                                if 'user_id' in mod._fields:
                                    service_action_domain.append(('user_id', '=', user.id))
                                # service_action_domain.append(('employee_id.user_id','=',user.id))
                            # value = self.env['ir.translation'].sudo().search([('source', '=', model.name)], limit=1).value
                            values['cards'].append({
                                'type': 'selfs',
                                'name': card_name,
                                'name_english': card_name,
                                'name_arabic': card_name,
                                'model': model.model_name,
                                'state_count': self.env[model.model_name].search_count(service_action_domain),
                                'image': model.card_image,
                                'form_view': model.form_view_id.id,
                                'list_view': model.list_view_id.id,
                                'js_domain': service_action_domain,
                                'context': model.action_context if model.action_context else {},
                            })
                    except AccessError:
                        continue
                        
        # append user record 
        values['user'].append(user_id)
        # append employee data record
        values['employee'].append(employee_id)
        values['leaves'].append(leaves_data)
        values['payroll'].append(payroll_data)
        values['attendance'].append(attendance_date)
        values['timesheet'].append(timesheet_data)

        values['job_english'] = job_english
        return values

    @api.model
    def checkin_checkout(self):
        ctx = self._context
        t_date = date.today()
        user = self.env.user
        user_id = self.env['res.users'].sudo().search_read(
            [('id', '=', user.id)], limit=1)

        employee_object = self.env['hr.employee'].sudo().search(
            [('user_id', '=', user.id)], limit=1)
        now = fields.Datetime.now
        attendance = self.env['attendance.attendance']
        vals_in = {'employee_id': employee_object.id,
                   'action': 'sign_in',
                   'action_type': 'manual',
                   }
        vals_out = {'employee_id': employee_object.id,
                    'action': 'sign_out',
                    'action_type': 'manual',
                    }

        if ctx.get('check', False):
            result = attendance.create(vals_out)
            # check whether last action sign in or out and its date
            attendance = self.env['attendance.attendance'].sudo().search(
                [('employee_id', '=', employee_object.id), ('action_date', '=', t_date)])
            is_attendance = True
            if not attendance:
                is_attendance = False
            if attendance and attendance[-1].action == 'sign_out':
                is_attendance = False
            user_tz = pytz.timezone(self.env.context.get('tz', 'Asia/Riyadh') or self.env.user.tz)
            if attendance:
                time_object = fields.Datetime.from_string(attendance[-1].name)
                time_in_timezone = pytz.utc.localize(time_object).astimezone(user_tz)
            attendance_date = {'is_attendance': is_attendance,
                               'time': time_object if attendance else False
                               }
            return attendance_date
        else:

            result = attendance.create(vals_in)
            # check whether last action sign in or out and its date
            attendance = self.env['attendance.attendance'].sudo().search(
                [('employee_id', '=', employee_object.id), ('action_date', '=', t_date)])
            user_tz = pytz.timezone(self.env.context.get('tz', 'Asia/Riyadh') or self.env.user.tz) #add
            time_object = fields.Datetime.from_string(attendance[-1].name) #add
            time_in_timezone = pytz.utc.localize(time_object).astimezone(user_tz) #add
            is_attendance = True
            if not attendance:
                is_attendance = False
            if attendance and attendance[-1].action == 'sign_out':
                is_attendance = False
            attendance_date = {'is_attendance': is_attendance,
                               'time': time_in_timezone if attendance else False
                               }
            return attendance_date
