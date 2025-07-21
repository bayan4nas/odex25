# -*- coding: utf-8 -*-
from odoo import _
from odoo.http import request, Response, Controller, route
from odoo.addons.odex_mobile.validator import validator
from odoo.addons.odex_mobile.http_helper import http_helper
from odoo.exceptions import UserError, AccessError, ValidationError, Warning

import simplejson as json

WORKFLOW = "workflow.mobile"
BTN = "workflow.mobile.node.button"
NODE = "workflow.mobile.node"


# filtered
# filtered_domain
# mapped
class RestApi(Controller):

    @route(["/rest_api/workflows/", "/rest_api/workflow/<mobile_id>", "/workflows/", "/workflow/<mobile_id>"], type="http", auth="none", method=["GET"], csrf=False,)
    def get_all_workflow(self, mobile_id=None, **kw):
        try:
            http_method, body, headers, token = http_helper.parse_request()
            result = validator.verify_token(token)
            if not result["status"]:
                return http_helper.errcode(
                    code=result["code"], message=result["message"]
                )
            user = validator.verify(token)
            if not user:
                return http_helper.response(
                    code=400,
                    message="You are not allowed to perform this operation. please check with one of your team admins",
                    success=False,
                )

            domain = []
            if mobile_id:
                domain = [("mobile_id", "=", mobile_id)]
            _workflows = request.env[WORKFLOW].sudo().search(domain)
            user = request.env.user
            data = []
            for wk in _workflows:
                wkd = {}
                list_nodes = (
                    wk.node_ids.filtered(
                        lambda n: n.sequence_in_hdr < 10000 or n.button_ids
                    ).read(["id", "sequence", "name", "node_name", "sequence_in_hdr"])
                    if wk.node_ids
                    else []
                )
                workflow_list = []
                for node in list_nodes:
                    #     button_ids =wk.btn_ids.search_read([('id','in', node['button_ids'])],['id','name','string' ,'groups'])
                    #     button_ids_groups = []
                    #     for btn in button_ids :
                    #         groups = user.user_has_groups(str(btn.get('groups').replace(' ', ''))) if btn.get('groups') else True
                    #         if groups :
                    #             del btn['groups']
                    #             button_ids_groups.append(btn)
                    #     node['button_ids'] = button_ids_groups
                    if wk.statusbar_visible:
                        node["sequence"] = node["sequence_in_hdr"]
                    del node["sequence_in_hdr"]
                    workflow_list.append({"id": node["id"], "name": node["name"]})

                # wkd['id'] = wk.id
                wkd["name"] = wk.name
                wkd["mobile_id"] = wk.mobile_id
                # wkd['view_xml_id'] = wk.view_id.xml_id
                # wkd['len_node'] = len(list_nodes)
                wkd["workflow"] = workflow_list
                data.append(wkd)
            return http_helper.response(message="Successful", data=data)
        except (UserError, AccessError, ValidationError, Warning) as e:
            error = str(e.name) + "\n" + str(e)
            return http_helper.response(code=400, message=str(error), success=False)
        except Exception as e:
            return http_helper.response_500(str(e))

    @route([
        "/rest_api/workflow/record_btns/<mobile_id>/<active_id>",
        "/workflow/record_btns/<mobile_id>/<active_id>", ],
        type="http",
        auth="none",
        method=["GET"],
        csrf=False,
    )
    def get_validation_workflow(self, mobile_id, active_id, **kw):
        try:
            http_method, body, headers, token = http_helper.parse_request()
            result = validator.verify_token(token)
            if not result["status"]:
                return http_helper.errcode(
                    code=result["code"], message=result["message"]
                )
            user = validator.verify(token)
            if not user:
                return http_helper.response(
                    code=400,
                    message="You are not allowed to perform this operation. please check with one of your team admins",
                    success=False,
                )

            domain = []
            if mobile_id:
                domain = [("mobile_id", "=", mobile_id)]
            _workflows = request.env[WORKFLOW].sudo().search(domain)
            if not _workflows:
                return http_helper.response(
                    code=400,
                    message="You are not allowed to perform this operation. please check ID of this object (Mobile ID)",
                    success=False,
                )
            obj = (
                request.env[_workflows.model_id.model]
                .sudo()
                .search([("id", "=", int(active_id))])
            )
            if not obj:
                return http_helper.response(
                    code=400,
                    message="You are not allowed to perform this operation. please check ID of this object (rec  -> Active ID)",
                    success=False,
                )
            # user = request.env.user
            data = []
            for wk in _workflows:
                wkd = {}
                workflow_list = []
                list_nodes = (
                    wk.node_ids.filtered(
                        lambda n: n.sequence_in_hdr < 10000 or n.button_ids
                    ).read(
                        [
                            "id",
                            "sequence",
                            "name",
                            "node_name",
                            "button_ids",
                            "sequence_in_hdr",
                        ]
                    )
                    if wk.node_ids
                    else []
                )
                for node in list_nodes:
                    button_ids = wk.btn_ids.search_read(
                        [("id", "in", node["button_ids"])],
                        ["id", "name", "string", "groups"],
                    )
                    button_ids_groups = []
                    for btn in button_ids:
                        btn_id = request.env[BTN].sudo().search([("id", "=", int(btn.get("id")))], [])
                        context = request.env.context.copy()
                        context.update({"active_model": btn_id.model})
                        context.update({"active_id": int(active_id)})
                        request.env.context = context
                        invisible_attrs = btn_id.with_context(context)._run_invisible_attrs()
                        readonly_attrs = btn_id.with_context(context)._run_readonly_attrs()
                        groups = (
                            user.user_has_groups(
                                str(btn.get("groups")).replace(" ", "")
                            )
                            if btn.get("groups")
                            else True
                        )
                        if groups and invisible_attrs:
                            del btn["groups"]
                            # btn['is_readonly_attrs'] = readonly_attrs
                            button_ids_groups.append(btn)

                    node["button_ids"] = button_ids_groups
                    if wk.statusbar_visible:
                        node["sequence"] = node["sequence_in_hdr"]
                    del node["sequence_in_hdr"]
                    workflow_list.append(
                        {
                            "id": node["id"],
                            "name": node["name"],
                            "state": node["node_name"],
                            "buttons": button_ids_groups,
                        }
                    )

                # wkd['id'] = wk.id
                wkd["mobile_id"] = wk.mobile_id
                wkd["name"] = wk.name
                # wkd['view_id'] = wk.view_id.id
                # wkd['view_xml_id'] = wk.view_id.xml_id
                # wkd['len_node'] = len(list_nodes)
                wkd["workflow"] = workflow_list
                data.append(wkd)
            return http_helper.response(message="Successful", data=wkd)
        except (UserError, AccessError, ValidationError, Warning) as e:
            error = str(e.name) + "\n" + str(e)
            return http_helper.response(code=400, message=str(error), success=False)
        except Exception as e:
            return http_helper.response_500(str(e))

    @route(
        [
        "/rest_api/workflow/execute_btn/<active_id>/<btn_id>",
        "/workflow/execute_btn/<active_id>/<btn_id>", ],
        type="http",
        auth="none",
        method=["GET"],
        csrf=False,
    )
    def get_execute_btn_workflow(self, btn_id, active_id, **kw):
        try:
            http_method, body, headers, token = http_helper.parse_request()
            result = validator.verify_token(token)
            if not result["status"]:
                return http_helper.errcode(
                    code=result["code"], message=result["message"]
                )
            user = validator.verify(token)
            if not user:
                return http_helper.response(
                    code=400,
                    message="You are not allowed to perform this operation. please check with one of your team admins",
                    success=False,
                )

            btn = request.env[BTN].sudo().search([("id", "=", int(btn_id))], [])
            if not btn:
                return http_helper.response(
                    code=400,
                    message=_("not found action check parm btn_id"),
                    success=False,
                )
            obj = request.env[btn.model].sudo().search([("id", "=", int(active_id))])
            if not obj:
                return http_helper.response(
                    code=400,
                    message="You are not allowed to perform this operation. please check ID of this object (rec)",
                    success=False,
                )

            context = request.env.context.copy()
            context.update({"active_model": btn.model})
            reject_reason = kw.get('reason_msg')
            
            context.update({"active_id": int(active_id)})
            request.env.context = context
            btn.with_context(context)._run_code(active_id, btn.model, request.env)
            res = obj.read(["id", "state"])[0]
            state = res["state"]
            refuse=False
            btn_new = request.env[BTN].sudo().search([("workflow_id", "=", int(btn.workflow_id.id)), (("node_id.node_name", "=", state)), ], [],)
            if any(btn.is_refuse for btn in btn_new):
                refuse = True
            if any(btn.send_manager for btn in btn_new):
                emp_manager = self.get_emp_manager(obj)
                obj.with_context(refuse=refuse).firebase_notification(emp_manager.user_id)
                return http_helper.response(message="Successful", data=res)
            group_ids = btn_new.mapped("group_ids")
            rule_groups = btn_new.mapped("group_ids").mapped("rule_groups").filtered(lambda rec:rec.model_id.model == obj._name)
            users_list = self.access_users(group_ids, obj)
            users = request.env['res.users'].sudo().search([('id', 'in', users_list)])          
            if reject_reason:
                obj.write({"reason": reject_reason})
            obj.with_context(refuse=refuse).firebase_notification(users)
            return http_helper.response(message="Successful", data=res)

        except (UserError, AccessError, ValidationError, Warning) as e:
            error = str(e)
            return http_helper.response(code=400, message=str(error), success=False)
        except Exception as e:
            return http_helper.response_500(str(e))

    def has_access(self, user_id, record, mode='read'):
        try:
            record.with_user(user_id).check_access_rule(mode)
            return True
        except:
            return False

    def get_emp_manager(self, record):
        try:
            return record.employee_id.parent_id
        except:
            return False

    def access_users(self, groups, record):
        users = []
        for group in groups:
            for user in group.users:
                if self.has_access(user_id=user.id, record=record, mode='read'):
                    users.append(int(user.id))
        return users

