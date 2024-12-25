# -*- coding: utf-8 -*-
import json
from odoo import http
from odoo.http import request
from odoo import models, fields,_
from pyIslam.zakat import Zakat
from urllib.parse import urljoin

product_fields = ['id','type','default_code','lst_price','name','description']
gift_fields = ['reciever_name','reciever_phone','reciever_mail','sender_name','sale_order_id']
order_fields = ['name','amount_total','confirmation_date','payment_methods']


class TakafulWebsiteCustom(http.Controller):
    #التبرع السريع
    @http.route('/get_quick_donation', type='http', auth='public', methods=['GET'])
    def get_quick_donation(self):
        quick_donation_products = request.env['product.product'].sudo().search([('quick_donation','=',True)])
        if quick_donation_products:
            li = []
            for product in quick_donation_products:
                records = product.read(product_fields)[0]
                base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                if product.image:
                    records['image_url'] = urljoin(base_url,'/web/image?model=product.product&id=%s&field=image' % product.id)
                else:
                    records['image_url'] = ''
                li.append(records)
            data = {'status': True, 'msg': (_('Quick Donation Products Found')), 'data': li}
        else:
            data = {'status': False, 'msg': (_('Quick Donation Products Not Found')), 'data': {}}
        return json.dumps(data)
    #ننتظر تبرعكم
    @http.route('/get_wait_donation_products', type='http', auth='public', methods=['GET'])
    def wait_donation_products(self):
        wait_donation_products = request.env['product.product'].sudo().search([('tags_ids.code', '=', 'WAIT')])
        if wait_donation_products:
            li = []
            for product in wait_donation_products:
                records = product.read(product_fields)[0]
                base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                if product.image:
                    records['image_url'] = urljoin(base_url,'/web/image?model=product.product&id=%s&field=image' % product.id)
                else:
                    records['image_url'] = ''
                li.append(records)
            data = {'status': True, 'msg': (_('Wait Donation Products Found')), 'data': li}
        else:
            data = {'status': False, 'msg': (_('Wait Donation Products Not Found')), 'data': {}}
        return json.dumps(data)
    #اهدي تبرعك الى من تحب
    @http.route('/get_dedications_products', type='http', auth='public', methods=['GET'])
    def dedications_products(self):
        dedications_products = request.env['product.product'].sudo().search([('tags_ids.code', '=', 'DED')])
        if dedications_products:
            li = []
            for product in dedications_products:
                records = product.read(product_fields)[0]
                base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                if product.image:
                    records['image_url'] = urljoin(base_url,'/web/image?model=product.product&id=%s&field=image' % product.id)
                else:
                    records['image_url'] = ''
                li.append(records)
            data = {'status': True, 'msg': (_('Quick Dedications Products Found')), 'data': li}
        else:
            data = {'status': False, 'msg': (_('Quick Dedications Products Not Found')), 'data': {}}
        return json.dumps(data)
    #زكاة الأموال
    @http.route('/get_money_zakat', type='http', auth='public', methods=['GET'])
    def get_money_zakat(self,money):
        z = Zakat()
        nisab = 239.96 * 85
        result = z.calculate_zakat(int(money),nisab)
        if int(money) > nisab :
            data = {'status': True, 'msg': (_('You must pay zakat')), 'data': result}
        else :
            data = {'status': False , 'msg': (_('You do not have to pay zakat because you did not reach the nisab')), 'data': result}
        return json.dumps(data)
    #زكاة الذهب
    @http.route('/get_gold_zakat', type='http', auth='public', methods=['GET'])
    def get_gold_zakat(self,gold,weight):
        z = Zakat()
        nisab = 239.96 * 85
        money = int(gold)*int(weight)
        result = z.calculate_zakat(money,nisab)
        if money > nisab :
            data = {'status': True, 'msg': (_('You must pay zakat')), 'data': result}
        else :
            data = {'status': False , 'msg': (_('You do not have to pay zakat because you did not reach the nisab')), 'data': result}
        return json.dumps(data)
    #زكاة الأصول والممتلكات
    @http.route('/get_properties_zakat', type='http', auth='public', methods=['GET'])
    def get_properties_zakat(self,property,gain):
        z = Zakat()
        nisab = 239.96 * 85
        money = int(property) +int(gain)
        result = z.calculate_zakat(money, nisab)
        if money > nisab:
            data = {'status': True, 'msg': (_('You must pay zakat')), 'data': result}
        else:
            data = {'status': False, 'msg': (_('You do not have to pay zakat because you did not reach the nisab')),
                    'data': result}
        return json.dumps(data)
    #زكاة العقارات المملوكة
    @http.route('/get_soporific', type='http', auth='public', methods=['GET'])
    def get_soporific_zakat(self, rent, cost):
        z = Zakat()
        nisab = 239.96 * 85
        money = (int(rent) + int(cost))*12
        result = z.calculate_zakat(money, nisab)
        if money > nisab:
            data = {'status': True, 'msg': (_('You must pay zakat')), 'data': result}
        else:
            data = {'status': False, 'msg': (_('You do not have to pay zakat because you did not reach the nisab')),
                    'data': result}
        return json.dumps(data)
    @http.route('/get_zakat_total_res', type='http', auth='public', methods=['GET'])
    def get_zakat_total_res(self,money,gold,weight,property,gain,rent,cost):
        res1 = json.loads(self.get_money_zakat(money).data.decode())["data"]
        res2 = json.loads(self.get_gold_zakat(gold,weight).data.decode())["data"]
        res3 = json.loads(self.get_properties_zakat(property,gain).data.decode())["data"]
        res4 = json.loads(self.get_soporific_zakat(rent,cost).data.decode())["data"]
        res = res1 + res2 + res3 + res4
        data = {'status': True, 'msg': (_('You must pay zakat')), 'data': res}
        return json.dumps(data)
    @http.route('/create_gifts', type='http', auth='public', website=True,csrf=False,methods=['POST'])
    def create_gifts(self,**kw):
        values = {}
        for field_name, field_value in kw.items():
            values[field_name] = field_value
        sale_order_id = request.website.sale_get_order(force_create=True)
        is_gift_exist = request.env['sale.order.gifts'].sudo().search([('sale_order_id', '=', int(sale_order_id))])
        if is_gift_exist:
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            url = urljoin(base_url, '/open_gifts?id=%s'%sale_order_id.id)
            data = {'status': True, 'msg': (_('Gift is already Exist to view git details from this link')), 'data': url}
        else:
            gift = request.env['sale.order.gifts'].sudo().create(values)
            sale_order_id.sale_gifts_id = gift.id
            gift.sudo().write({'sale_order_id':sale_order_id.id})
            if gift:
                records = gift.id
                data = {'status': True, 'msg': (_('Gift is Created')), 'data': records}
            else:
                data = {'status': False, 'msg': (_('Gift Not Created')), 'data': {}}
        return json.dumps(data)
    @http.route('/open_gifts', type='http', auth='public', website=True, methods=['GET'])
    def open_gifts(self,id):
        gifts = request.env['sale.order.gifts'].sudo().search([('sale_order_id', '=', int(id))])
        if gifts:
            li = []
            for gift in gifts:
                records = gift.read(gift_fields)[0]
                li.append(records)
            data = {'status': True, 'msg': (_('Gift for this Sale order is Found')), 'data': li}
        else:
            data = {'status': False, 'msg': (_('Gift for this Sale order is not Found')), 'data': {}}
        return json.dumps(data)
    #API for create quick donation (التبرع السريع)
    @http.route(['/create_quick_donation'], type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update_quick(self,donation_type , cost, **kw):
        sale_order = request.website.sale_get_order(force_create=True)
        sale_order.quick_donation = True
        # if sale_order.quick_donation == False:
        #     x = request.env["sale.order"].browse(sale_order.id)
        #     print(x)
        #     request.env["sale.order"].browse(sale_order.id).order_line.unlink()
        if sale_order.state != 'draft':
            request.session['sale_order_id'] = None
            sale_order = request.website.sale_get_order(force_create=True)
        sale_order._cart_update(
            product_id=int(donation_type),
            add_qty=int(cost),
            set_qty=int(cost),
            attributes=self._filter_attributes(**kw),
        )
        return request.redirect("/shop/payment")
    def _filter_attributes(self, **kw):
        return {k: v for k, v in kw.items() if "attribute" in k}

    @http.route('/create_fast_gifts', type='http', auth='public', website=True, csrf=False, methods=['POST'])
    def create_fast_gifts(self, **kw):
        values = {}
        for field_name, field_value in kw.items():
            values[field_name] = field_value
        sale_order_id = request.website.sale_get_order(force_create=True)
        if sale_order_id:
            gift = request.env['sale.order.gifts'].sudo().create(values)
            sale_order_id.sale_gifts_id = gift.id
            gift.sudo().write({'sale_order_id': sale_order_id.id})
        sale_order_id._cart_update(
            product_id=int(kw.get('product_id')),
            add_qty=int(kw.get('cost')),
            set_qty=int(kw.get('cost')),
            attributes=self._filter_attributes(**kw),
        )
        return request.redirect("/shop/payment")

    @http.route('/get_product_details', type='http', auth='public', website=True, methods=['GET'])
    def get_product_details(self, id):
        product = request.env['product.template'].sudo().search([('id', '=', int(id))])
        if product:
            li = []
            banks = []
            iban = []
            for bank in product.bank_id:
                banks.append(bank.name)
                iban.append(bank.iban)
            records = product.read(product_fields)[0]
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            if product.image:
                records['image_url'] = urljoin(base_url,
                                               '/web/image?model=product.template&id=%s&field=image' % product.id)
            else:
                records['image_url'] = ''
            records["banks"] = banks
            records["iban"] = iban
            li.append(records)
            data = {'status': True, 'msg': (_('Product is Found')), 'data': li}
        else:
            data = {'status': False, 'msg': (_('Product is not Found')), 'data': {}}
        return json.dumps(data)

    @http.route('/get_profile_details', type='http', auth='public', website=True, methods=['GET'])
    def get_profile_details(self):
        orders = request.env['sale.order'].sudo().search([('partner_id', '=',request.env.user.partner_id.id)])
        orders_count = request.env['sale.order'].sudo().search_count([('partner_id', '=',request.env.user.partner_id.id)])
        total_amount= 0
        projects_count = 0
        if orders:
            li = []
            records={}
            for order in orders:
                total_amount += order.amount_total
                projects_count += len(order.order_line)
            records['total_amount'] = round(total_amount,2)
            records['projects_count'] = projects_count
            records['total_orders'] = orders_count
            li.append(records)
            data = {'status': True, 'msg': (_('Sale Order is Found')), 'data': li}
        else:
            data = {'status': False, 'msg': (_('Sale Order is not Found')), 'data': {}}
        return json.dumps(data)

    @http.route('/get_orders_details', type='http', auth='public', website=True, methods=['GET'])
    def get_orders_details(self):
        orders = request.env['sale.order'].sudo().search([('partner_id', '=', request.env.user.partner_id.id)])
        if orders:
            li = []
            records = {}
            seq = 0
            order_lines=[]
            for order in orders:
                seq += 1
                records = order.read(order_fields)[0]
                if order.order_line:
                    for line in order.order_line:
                        order_lines.append(line.product_id.name)
                records["seq"] = seq
                records["project"] = order_lines
                base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                url = urljoin(base_url, '/print/invoice?sale_order_id=%s' % order.id)
                records["download"] = url
                order_lines = []
                li.append(records)
            data = {'status': True, 'msg': (_('Sale Order is Found')), 'data': li}
        else:
            data = {'status': False, 'msg': (_('Sale Order is not Found')), 'data': {}}
        return json.dumps(data)

    @http.route('/print/invoice', type='http', auth="public")
    def print_docum(self,sale_order_id):
        sale_order= request.env['sale.order'].sudo().search(
            [("id",'=',int(sale_order_id))])
        pdf = request.env.ref('sale.action_report_pro_forma_invoice').sudo().render_qweb_pdf(
                [sale_order.id])[
                0]
        pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
        return request.make_response(pdf, headers=pdfhttpheaders)

    @http.route('/zakat/shop', type='http', auth="public",website=True)
    def zakat_shop(self,amount):
        values = {}
        zakat_products = request.env['product.product'].sudo().search([('zakat_product', '=', True)],limit=1)
        if zakat_products:
            self.cart_update(zakat_products,add_qty=amount, set_qty=amount)
        return request.redirect("/shop/cart")

    @http.route(['/shop/cart/update'], type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        sale_order = request.website.sale_get_order(force_create=True)
        if sale_order.state != 'draft':
            request.session['sale_order_id'] = None
            sale_order = request.website.sale_get_order(force_create=True)
        sale_order._cart_update(
            product_id=int(product_id),
            add_qty=add_qty,
            set_qty=set_qty,
            attributes=self._filter_attributes(**kw),
        )
        return request.redirect("/shop/cart")
