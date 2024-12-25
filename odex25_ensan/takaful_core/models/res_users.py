# -*- coding: utf-8 -*-

from ..TaqnyatSms import client, make_http_response
from odoo import models, fields, api, _
from datetime import datetime, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from dateutil.relativedelta import relativedelta as rd

from odoo.exceptions import UserError, ValidationError, Warning

from datetime import timedelta
from dateutil import parser
import pytz

import math
import random
import re
import logging

_logger = logging.getLogger(__name__)

SAUDI_MOBILE_PATTERN = "(^(05|5)(5|0|3|6|4|9|1|8|7)([0-9]{7})$)"
OTP_HOUR_LIMIT = 7
OTP_COUNT_LIMIT = 3

def generateOTP() : 
    digits = "0123456789"
    OTP = "" 
    for i in range(4) : 
        OTP += digits[int(math.floor(random.random() * 10))] 
    return OTP 


class ResUser(models.Model):
    _inherit = 'res.users'

    otp = fields.Char(string="OTP", required=False, readonly=True)
    otp_password = fields.Char(string="OTP Reset Password", required=False, readonly=True)
    otp_count = fields.Integer(string='OTP Request Count', required=False, readonly=True)
    otp_date = fields.Datetime(string='OTP Date', required=False, readonly=True)

    # @api.multi
    def remove_access_groups(self):
        """ Remove any access group from a user """
        self.ensure_one()
        groups_list = self.env['res.groups'].sudo().search([])
        for group in groups_list:
            if self in (group.users):
                # Remove the access group
                self.sudo().write({'groups_id': [(3, group.id)]})

    # << Send OTP >>
    # @api.multi
    def send_otp(self, mobile):
        self.ensure_one()
        if not mobile:
            error_descrip = _('Missing mobile number')
            _logger.error(error_descrip)
            return { 
                'code': 400,
                'error': 'missing_data',
                'error_descrip': error_descrip,
            }

        if re.match(SAUDI_MOBILE_PATTERN, str(mobile)) == None:
            error_descrip = _('Invalid Saudi mobile number')
            _logger.error(error_descrip)
            return { 
                'code': 400,
                'error': 'invalid_mobile',
                'error_descrip': error_descrip,
            }

        company_id = self.env['res.company'].sudo().search([('id','=',1)])
        
        if company_id and company_id.use_otp_login:
            token = company_id.otp_provider_token or ''
            sender = company_id.otp_sender_name or ''
            if token and sender:
                otp = generateOTP()
                
                # Start demo for test
                self.otp = otp
                self.otp_password = otp
                self.otp_count = self.otp_count + 1
                if int(self.otp_count) == 1:
                    self.otp_date = fields.Datetime.now()

                return { 
                        'code': 200,
                        'results': {
                                'message': _('OTP code is successfully sent'),
                                "mobile": mobile, 
                                "otp": otp, 
                                'note': "OTP returned just for test, will be removed!",
                            }
                        }
                # End demo/test

                taqnyt = client(token)
                mobile = '966' + str(mobile).lstrip('0')
                body = _("""Dear Customer,
        %s is your one time password (OTP). Please enter the OTP to proceed.
        Thank you,
        Team Takaful""") % otp
                
                recipients = [mobile]
                scheduled=''
                # Sending a SMS for Verification using OTP
                message = taqnyt.sendMsg(body, recipients, sender,scheduled)
                
                result = make_http_response(message)
               
                code = int(result['statusCode'])
                total_count = int(result['totalCount'])
                msg = result['message']

                if code == 201 and total_count >=1:
                    self.otp = otp
                    self.otp_password = otp
                    self.otp_count = self.otp_count + 1
                    if int(self.otp_count) == 1:
                        self.otp_date = fields.Datetime.now()

                    return { 
                        'code': 200,
                        'results': {
                                'message': _('OTP code is successfully sent'),
                                "mobile": mobile,
                            }
                        }
                else:
                    _logger.error(msg)        
                    return { 
                        'code': 424,
                        'error': 'failed_dependency',
                        'error_descrip': _('Cannot sending SMS verification %s ') %("\n" + msg),
                    }
                            
            else:
                error_descrip = _('Sender information does not exist')
                _logger.error(error_descrip)
                return { 
                    'code': 400,
                    'error': 'does_not_exist',
                    'error_descrip': error_descrip,
                }
        
        else:
            error_descrip = _('SMS service is unavilable')
            _logger.error(error_descrip)
            return { 
                'code': 424,
                'error': 'failed_dependency',
                'error_descrip': error_descrip,
            }

    # Request OPT
    # @api.multi
    def request_otp(self, mobile):
        self.ensure_one()
        if not mobile:
            error_descrip = _('Missing mobile number')
            _logger.error(error_descrip)
            return { 
                'code': 400,
                'error': 'missing_data',
                'error_descrip': error_descrip,
            }

        if self.otp and self.otp_date:
            now = fields.Datetime.now()

            otp_date = self.otp_date
            otp_date_timte = parser.parse(str(self.otp_date))

            current_date_timte = parser.parse(str(now))
            limit_date_timte = otp_date_timte + timedelta(hours=OTP_HOUR_LIMIT)

            counter = int(self.otp_count)
            if  current_date_timte > limit_date_timte and current_date_timte > otp_date_timte and counter >= OTP_COUNT_LIMIT:
                self.otp_count = 0
                counter = 0

            if current_date_timte < limit_date_timte and counter >= OTP_COUNT_LIMIT:
                tz = pytz.timezone('Asia/Riyadh')
                remines = limit_date_timte.replace(tzinfo=tz).strftime("%I:%M")
                error_descrip = _('Exceeded the limit, please request after the clock %s') % remines
                _logger.error(error_descrip)
                return { 
                    'code': 400,
                    'error': 'exceeded_otp_limit',
                    'error_descrip': error_descrip,
                }

        return self.sudo().send_otp(mobile)
    
    # Reset Password using email account
    # @api.multi
    def reset_password_using_email(self):
        self.ensure_one()
        # Reset Password using email.. login email of user!
        try:
            self.action_reset_password()
            return { 
                    'code': 200,
                    'results': {
                        'message': _('Email verification is successfully sent'),
                        "email": self.login,
                    }
                }
        except Exception as e:
            error_descrip = _('Cannot sending email verification')
            _logger.error(error_descrip)
            return { 
                'code': 424,
                'error': 'failed_dependency',
                'error_descrip': error_descrip,
            }

    # Reset Password using Verified OTP
    # @api.multi
    def reset_password_using_otp(self, password1, password2, otp):
        self.ensure_one()
        # Reset Password using OTP processing..Should be verified otp!
        if not all([password1, password2, otp]):
            error_descrip = _('Missing Password Values or OTP')
            _logger.error(error_descrip)
            return { 
                'code': 400,
                'error': 'missing_data',
                'error_descrip': error_descrip,
            }
            
        if password1 != password2:
            error_descrip = _('The entered password does not match')
            _logger.error(error_descrip)
            return { 
                'code': 400,
                'error': 'password_not_match',
                'error_descrip': error_descrip,
            }

        if self.otp_password:
            otp_original = str(self.otp_password)
            otp_customer =  str(otp)

            if otp_customer == otp_original:
                # Reset password processing..
                self.password = password1
                self.otp_password = None
                self.env.cr.commit()
                return { 
                    'code': 200,
                    'results': {
                        'message': _('Password is successfully reset'),
                    }
                }

            else:
                error_descrip = _('Invalid OTP, Reset Password Failed')
                _logger.error(error_descrip)
                return { 
                    'code': 400,
                    'error': 'invalid_otp',
                    'error_descrip': error_descrip,
                }
        else:
            error_descrip = _('OTP does not exist or expired, please request it again')
            _logger.error(error_descrip)
            return { 
                'code': 400,
                'error': 'expired_otp',
                'error_descrip': error_descrip,
            }


    # Verify OTP
    # @api.multi
    def verify_otp(self, otp):
        self.ensure_one()
        # OTP verify processing..
        if self.otp:
            otp_original = str(self.otp)
            otp_customer =  str(otp)
            if otp_customer != otp_original:
                error_descrip = _('Invalid OTP, Verification Failed')
                _logger.error(error_descrip)
                return { 
                    'code': 400,
                    'error': 'invalid_otp',
                    'error_descrip': error_descrip,
                }
            else: 
                self.otp = None
                return { 
                    'code': 200,
                    'results': {
                            'message': _('Verification is successful'),
                        }
                }
        else:
            error_descrip = _('OTP does not exist or expired, please request it again')
            _logger.error(error_descrip)
            return { 
                'code': 400,
                'error': 'expired_otp',
                'error_descrip': error_descrip,
            } 
        
