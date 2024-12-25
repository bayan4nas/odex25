from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError
from passlib.context import CryptContext
import json
import xmlrpc.client

url = 'http://localhost:8069'
db = 'laundry'
#db = 'test13'

models = {
    'product' : {
        'model' : 'product.product', 'field' : ['lst_price', 'name',]
    },
}

class Service(http.Controller):

    @http.route('/hello', auth='public')
    def hello(self):
        return '<h1>Hello Optimum !!</h1>'

    @http.route('/user/create', auth='public')
    def user_create(self):
        user_data = dict(
            name=request.params.get('name'),
            login=request.params.get('login'),
            password=request.params.get('password'),
            #odoobot_state='not_initialized'
        )
        user_model = request.env['res.users']
        search_res = user_model.sudo().search([('login','=',user_data['login'])])
        if not search_res :
            obj = user_model.sudo().create(user_data)
            res = {
                    'code' : 1,
                    'message' : 'A new User Created Successfully',
                    'result' : {
                        'user_id' : obj.id ,
                    }
            }
        else :
            res = {
                    'code' : -1,
                    'message' : 'Login name is exist',
            }
        return json.dumps(res)


    @http.route('/user/check', auth='public')
    def check_user(self):
        username = request.params.get('login')
        password =  request.params.get('password')
        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
        uid = common.authenticate(db, username, password, {})
        if uid : 
            res = {
                    'code' : 2,
                    'message' : 'Login Sucessfuly',
                    'result' : {
                        'user_id' : uid ,
                    }
            }
        else:
            res = {
                    'code' : -2,
                    'message' : 'Wrong Login/Password',
                    'result' : {
                        #'user_id' : obj.id ,
                    }
            }       
        return json.dumps(res)


    @http.route('/product/all', auth='public')
    def all_product(self):
        product_model = request.env['product.template']
        res = product_model.sudo().search_read([],['name'])
        if res :
            result = {
                'code' : 3,
                'message' : 'Request Done',
                'result' : res
            }
        else :
            result = {
                'code' : -3,
                'message' : 'No products',
                'result' : []
            }
        return json.dumps(result)


    @http.route('/product/get', auth='public')
    def get_product(self):
        product_id = request.params.get('product_id')
        product_model = request.env['product.template']
        res = product_model.sudo().search_read([('id', '=' , product_id)],['lst_price', 'name'])
        result = {}
        if res :
            result['code'] = 4
            result['message'] = 'Request Done'
        else :
            result['code'] = 4
            result['message'] = 'No product'
        result['result'] = res 
        return json.dumps(result)

    
    @http.route('/variant/all', auth='public')
    def all_vars(self):
        product_model = request.env['product.attribute.value']
        res = product_model.sudo().search_read([],['name'])
        if res :
            result = {
                'code' : 4,
                'message' : 'Request Done',
                'result' : res
            }
        else :
            result = {
                'code' : -4,
                'message' : 'No Records',
                'result' : []
            }
        return json.dumps(result)

    
    @http.route('/product_var/all', auth='public')
    def all_product_var(self):
        product_model = request.env['product.template.attribute.value']
        res = product_model.sudo().search_read([],['price_extra', 'product_tmpl_id', 'product_attribute_value_id'])
        if res :
            result = {
                'code' : 4,
                'message' : 'Request Done',
                'result' : res
            }
        else :
            result = {
                'code' : -4,
                'message' : 'No Records',
                'result' : []
            }
        return json.dumps(result)


    @http.route('/product_var/get', auth='public')
    def get_product_var(self):
        cond = []
        product_tmpl_id = request.params.get('product_id')
        product_attribute_value_id = request.params.get('var_id')
        product_model = request.env['product.template.attribute.value']
        if product_tmpl_id : cond += [('product_tmpl_id', '=' ,int(product_tmpl_id) )]
        if product_attribute_value_id : cond += [('product_attribute_value_id', '=' ,int(product_attribute_value_id) )]
        res = product_model.sudo().search_read(cond,['price_extra', 'product_tmpl_id', 'product_attribute_value_id'])
        if res :
            result = {
                'code' : 4,
                'message' : 'Request Done',
                'result' : res
            }
        else :
            result = {
                'code' : -4,
                'message' : 'No Records',
                'result' : []
            }
        return json.dumps(result)