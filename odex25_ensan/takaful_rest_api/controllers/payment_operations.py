import json
import base64
import requests
from odoo import http
from odoo.http import request
from odoo.tools.translate import _
from ast import literal_eval

class PayingContoller(http.Controller):

  def paycard_sponsorship(self, name_op, amount, data):
    print("Do bussiness logic for sponsorship")

  def paycard_financial_gift(self, name_op, amount, data):
    print("Do bussiness logic for financial_gift")

  def paycard_need_contribution(self, name_op, amount, data):
    print("Do bussiness logic for need_contribution")

  @http.route('/dashboard/payment/paycard', auth='user', website=True)
  def payment_paycard(self, **kw):
      user = http.request.env['res.users'].sudo().browse(http.request.env.uid)
      required_paying = 0
      if kw.get('required_amount'):
        required_paying=float(kw.get('required_amount',300))
      name_op = kw.get('name_op', False) # 'Operation Or Payment Name'
      type_op  = kw.get('type_op')
      
      if http.request.env.uid: #and not user.has_group('base.group_public')
          moyaser_public_key = http.request.env['ir.config_parameter'].sudo().get_param('moyaser_public_key')
          tax_percent = float(request.env['ir.config_parameter'].sudo().get_param('vat_default_percent', default=0.0))
          required_amount = required_paying/(1+(tax_percent/100))
          tax_amount = required_paying-required_amount

          callback_url = '/dashboard/payment/feedback'
          metadata = {
              "name_of": user.name, 
              "email": user.email,
              "type_op": 'sponsorship',#kw.get('type_op') type_op
              "note": "This from test for creditcard",
          }
          values = {
              'callback_url':"%s%s" %( request.env['ir.config_parameter'].sudo().get_param('web.base.url'), callback_url),
              'user': user,
              'metadata_dict': metadata,
              'description': name_op or _('Paying money via creditcard'),
              'required_payment': round(required_paying, 2),
              'tax_amount': round(tax_amount,2),
              'total_needed': round(required_paying + tax_amount, 2),
              'amount': round(required_paying + tax_amount) * 100,
              'moyaser_token':moyaser_public_key,
          }
        

          return http.request.render('takaful_rest_api.paying_card', values)

      else:
          return http.redirect_with_hash('/web/login')


  @http.route('/dashboard/payment/banktransfer', auth='user', website=True)
  def payment_bank_transfer(self, **kw):
      user = http.request.env['res.users'].sudo().browse(http.request.env.uid)
      required_paying=float(kw.get('required_amount',300))
      name_op = kw.get('name_op', False) # 'Operation Or Payment Name'
      
      if http.request.env.uid: #and not user.has_group('base.group_public')
          tax_percent = float(request.env['ir.config_parameter'].sudo().get_param('vat_default_percent', default=0.0))
          required_amount = required_paying/(1+(tax_percent/100))
          tax_amount = required_paying-required_amount
          bank_accounts = request.env['res.users'].sudo().browse(request.env.uid).company_id.bank_ids

          metadata = {
              "name_of": user.name, 
              "email": user.email,
              "type_op": 'sponsorship',
              "note": "This from test for bank transfer",
          }
          values = {
              'bank': bank_accounts[0] if bank_accounts else {}, 
              'bank_accounts': bank_accounts, 
              'user': user,
              'metadata': metadata,
              'description': name_op or _('Paying money via Bankt Transfer'),
              'required_payment': round(required_amount, 2),
              'tax_amount': round(tax_amount,2),
              'total_needed': round(required_amount + tax_amount, 2),
              'amount': int(required_paying * 100),
          }

          return http.request.render('takaful_rest_api.bank_transfer', values)

      else:
          return http.redirect_with_hash('/web/login')
          
  # New Added
  @http.route(['/dashboard/payment/transfer'], methods=['POST'], type='http', auth="public", website=True)
  def payment_transfer_page(self, **kw):
      attachment = kw.get('attachment')
      name_of = kw.get('name_of')
      amount = kw.get('amount')
      date = kw.get('transfer_date')
      partner_id = http.request.env.user.partner_id
      msg = None
      suc = False
      if attachment and request.env.uid and name_of and amount:
          create_vals = {
              'name': request.env['res.users'].sudo().browse(request.env.uid).name,
              'name_of': name_of,
              'amount': amount,
              'transfer_date': date,
              'partner_id': partner_id.id,
              'transfer_attachment': base64.encodestring(attachment.read()),
              'filename': attachment.filename,
          }
          ticket_id = request.env['takaful.bank.transfer.payment'].sudo().create(create_vals)
          msg =  ticket_id.number
          suc = True

      else:
          msg = _('Problem happened while submitting your request.\n Please Try again later')
      request.session['transfer'] = msg
      request.session['transfer-status'] = suc
      return http.redirect_with_hash('/dashboard/payment/transfer')
  
  @http.route(['/dashboard/payment/transfer'], methods=['GET'], type='http', auth="public", website=True)
  def payment_transfer_pa(self, **kw):
      try:
          msg = request.session.pop('transfer')
          status = request.session.pop('transfer-status')
          if not msg :
              msg = 'Problem happened while submitting your request.\n Please Try again later'
          values = {
              "message":msg,
              "status":status,
              "user":request.env['res.users'].sudo().browse(request.env.uid)
          }
          return request.render("takaful_rest_api.success_operation", values)            
      except :
          return http.redirect_with_hash('/dashboard/payment/banktransfer')

  @http.route(['/dashboard/payment/feedback'], methods=['GET','POST'], type='http', auth="public", website=True, csrf=False)
  def card_payment_feedback(self, **kw):
    """ Payment feedback method """
    print(kw)
    """"
    https://fd81-188-48-120-225.eu.ngrok.io/dashboard/payment/feedback
    ?orderid=12&
    id=e2cd883b-799a-4299-83a3-77257ec5b461&
    status=paid&
    amount=20000&
    message=Succeeded%21+%28Test+Environment%29
    
    
    **********sponsorship
    operation_type =>(sponsorship,financial_gift,need_contribution) str => key
    operation_type = sponsorship
    month_count = number
    operation_id = orderid => number
    partner_id (takaful.sponsor) Userprofile = number
    **********financial_gift takaful.contribution
    msg = str 
    operation_id => benefit_id = number
    operation_type = financial_gift
    partner_id (takaful.sponsor) Userprofile = number
    
    ****************need_contribution
    operation_id => benefit_id = number (benefits.needs)
    operation_type = need_contribution
    partner_id (takaful.sponsor) Userprfle = number
    
    state = status
    type = 
    name =
    """
    if kw.get("id"):
      api_key = http.request.env['ir.config_parameter'].sudo().get_param('moyaser_public_key')
      url = "https://api.moyasar.com/v1/payments/"
      response = requests.get(url + kw.get("id"), auth=(api_key, ''))
      res = json.loads(response.content.decode("utf-8"))
      print(response.ok)
      print(res)
      # return json.dumps(res)
      if response and response.status_code in [200, 201, 202, 203]:
        remote_id = res.get('id')
        operation_type = kw.get('operation_type',False)
        id_obj = int(kw.get('operation_id',False))
        sponsor_id = int(kw.get('partner_id',False))
        partner_id = None
        if sponsor_id :
          sponsor_obj = request.env['takaful.sponsor'].sudo().search([('id', '=', sponsor_id)])
          partner_id  = sponsor_obj.partner_id
          print(sponsor_obj,partner_id)
        if operation_type == 'sponsorship' and id_obj:
          sponsorship_obj = request.env['takaful.sponsorship'].sudo().search([('id', '=', id_obj)])
          print(sponsorship_obj)
        print(sponsor_obj,sponsorship_obj.sponsor_id)
        if sponsor_obj==sponsorship_obj.sponsor_id and sponsorship_obj:
          print("IS VALED DATA")
        paycard = request.env['takaful.account.move'].sudo().search([('remote_id', '=', remote_id)])
        print(paycard)
        if not paycard and res.get('status') == "paid":
          name_op = res.get('description', _('Paying money via creditcard'))
          amount = res.get('amount')/100
          # Do Our Staff By Saving Pay in db
          vals = {
            'remote_id': remote_id,
            'name': name_op,
            'amount': amount,
            'type': 'card',
            'state': 'paid',
          }
          paycard = request.env['takaful.account.move'].sudo().create(vals)

          metadata = res.get('metadata')
          if metadata:
            if type(metadata.get('meta', False)) is str:
              try:
                data = literal_eval(metadata.get('meta'))
              except Exception as e:
                data = {}
            elif type(metadata.get('meta', False)) is dict:
              data = metadata.get('meta')

            if not type(data) is dict:
              data = {}
            
            type_op = data.get('type_op', '')
            name_of = data.get('name_of', '')
            note = data.get('note', '')
            email = data.get('email', False)

            partner_id = request.env['res.partner'].sudo().search([('email', '=', email)], limit=1)
            if partner_id and email:
              customer_id = partner_id.id
            else:
              customer_id = False
            
            paycard.sudo().write({
              'name_of': name_of,
              'customer_id': customer_id,
              'type_op': type_op,
              'email': email,
              'note': note,
            })

            if type_op == 'sponsorship':
              self.paycard_sponsorship(name_op, amount, data)
            elif type_op == 'financial_gift':
              self.paycard_financial_gift(name_op, amount, data)
            elif type_op == 'need_contribution':
              self.paycard_need_contribution(name_op, amount, data)
            # Keep going in your conditions

            # Final feedback..
            user_feed = {
              'code': 200,
              "status": "paid", 
              "amount": amount,
              "message": _('Payment Succeeded'),
            }
            return http.request.make_response(json.dumps(user_feed))
      
      elif response and response.status_code:
        user_feed = {
          'code': response.status_code,
          "status": response.status,
          "message": response.message,
        }
        return http.request.make_response(json.dumps(user_feed))
      else:
        return http.request.make_response(json.dumps(response.json()))
    # If Any
    else:
      user_feed = {
        'code': 404,
        "status": 'failed',
        "message": 'Not Found',
      }
      return http.request.make_response(json.dumps(user_feed))














#  @http.route(['/dashboard/payment/feedback'], methods=['GET','POST'], type='http', auth="public", website=True, csrf=False)
#   def card_payment_feedback(self, **kw):
#     """ Payment feedback method """
#     print(kw)
#     """"
#     https://fd81-188-48-120-225.eu.ngrok.io/dashboard/payment/feedback
#     ?orderid=12&
#     id=e2cd883b-799a-4299-83a3-77257ec5b461&
#     status=paid&
#     amount=20000&
#     message=Succeeded%21+%28Test+Environment%29
    
    
#     **********sponsorship
#     operation_type =>(sponsorship,financial_gift,need_contribution) str => key
#     operation_type = sponsorship
#     month_count = number
#     operation_id = orderid => number
#     partner_id (takaful.sponsor) Userprofile = number
#     **********financial_gift takaful.contribution
#     msg = str 
#     operation_id => benefit_id = number
#     operation_type = financial_gift
#     partner_id (takaful.sponsor) Userprofile = number
    
#     ****************need_contribution
#     operation_id => benefit_id = number (benefits.needs)
#     operation_type = need_contribution
#     partner_id (takaful.sponsor) Userprfle = number
    
#     state = status
#     type = 
#     name =
#     """
#     if kw.get("id"):
#       api_key = http.request.env['ir.config_parameter'].sudo().get_param('moyaser_public_key')
      
#       url = "https://api.moyasar.com/v1/payments/"
#       response = requests.get(url + kw.get("id"), auth=(api_key, ''))
#       res = json.loads(response.content.decode("utf-8"))
#       print(response.ok)
#       print(res)
#       # return json.dumps(res)
#       if response and response.status_code in [200, 201, 202, 203]:
#         remote_id = res.get('id')
#         paycard = request.env['takaful.account.move'].sudo().search([('remote_id', '=', remote_id)])
#         print(paycard)
#         if not paycard and res.get('status') == "paid":
#           name_op = res.get('description', _('Paying money via creditcard'))
#           amount = res.get('amount')/100
#           # Do Our Staff By Saving Pay in db
#           vals = {
#             'remote_id': remote_id,
#             'name': name_op,
#             'amount': amount,
#             'type': 'card',
#             'state': 'paid',
#           }
#           paycard = request.env['takaful.account.move'].sudo().create(vals)

#           metadata = res.get('metadata')
#           if metadata:
#             if type(metadata.get('meta', False)) is str:
#               try:
#                 data = literal_eval(metadata.get('meta'))
#               except Exception as e:
#                 data = {}
#             elif type(metadata.get('meta', False)) is dict:
#               data = metadata.get('meta')

#             if not type(data) is dict:
#               data = {}
            
#             type_op = data.get('type_op', '')
#             name_of = data.get('name_of', '')
#             note = data.get('note', '')
#             email = data.get('email', False)

#             partner_id = request.env['res.partner'].sudo().search([('email', '=', email)], limit=1)
#             if partner_id and email:
#               customer_id = partner_id.id
#             else:
#               customer_id = False
            
#             paycard.sudo().write({
#               'name_of': name_of,
#               'customer_id': customer_id,
#               'type_op': type_op,
#               'email': email,
#               'note': note,
#             })

#             if type_op == 'sponsorship':
#               self.paycard_sponsorship(name_op, amount, data)
#             elif type_op == 'financial_gift':
#               self.paycard_financial_gift(name_op, amount, data)
#             elif type_op == 'need_contribution':
#               self.paycard_need_contribution(name_op, amount, data)
#             # Keep going in your conditions

#             # Final feedback..
#             user_feed = {
#               'code': 200,
#               "status": "paid", 
#               "amount": amount,
#               "message": _('Payment Succeeded'),
#             }
#             return http.request.make_response(json.dumps(user_feed))
      
#       elif response and response.status_code:
#         user_feed = {
#           'code': response.status_code,
#           "status": response.status,
#           "message": response.message,
#         }
#         return http.request.make_response(json.dumps(user_feed))
#       else:
#         return http.request.make_response(json.dumps(response.json()))
#     # If Any
#     else:
#       user_feed = {
#         'code': 404,
#         "status": 'failed',
#         "message": 'Not Found',
#       }
#       return http.request.make_response(json.dumps(user_feed))
