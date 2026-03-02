import logging
import json
from odoo.http import route, Controller, request
from odoo.addons.izi_lib.helpers.Route import Route
from odoo.addons.izi_lib.helpers.ApiException import ApiException
from odoo.addons.izi_lib.helpers.Response import Response
from odoo.addons.ev_tnu_api_utils.controllers import utils
from odoo.addons.ev_tnu_api_utils.controllers.code_response import RESPONSE_CODE_MSG
from odoo.addons.ev_config_connect_api.helpers import Configs
from datetime import datetime

_logger = logging.getLogger(__name__)

api_url= Route('payment',version='1', app='qldt')

class QLDTPayment(Controller):
    @route(route=api_url, methods=['POST'], auth='public', type='json')
    def payment(self, **post):
       try:
            verify = ["student_code","unit_code","date_payment"]
            params = request.httprequest.json
            result, code, message, remote_ip, api_name, api_id = utils.check_error(
            request, api_url, require_params=verify
            )
            if result:
                return Response.error(message=message, code=code).to_json()
            data = params.get('data', {})
            res_code = "000"
            res_msg = "Thành công"

            ngay_tt= data.get('date_payment')
            if not ngay_tt:
                res_code = "145"
                res_msg = "Thiếu dữ liệu ngày thanh toán"
            try:
                datetime.strptime(str(ngay_tt).strip(), '%Y-%m-%d')
            except (ValueError, TypeError):
                return Response.error(
                    message=f"Định dạng ngày thanh toán '{ngay_tt}' không hợp lệ (Kỳ vọng: YYYY-MM-DD)",
                    code='146'
                    ).to_json()


            student_code = data.get('student_code')
            if not student_code:
                res_code = "145"
                res_msg = "Thiếu dữ liệu student_code"

            ma_dv_raw = str(data.get('unit_code') or '').strip()
            if not ma_dv_raw:
                res_msg = "Dữ liệu thiếu Unit Code để xác định Company"
                res_code = '145'

            Configs._set_log_api(remote_ip, api_url, api_name, params, res_code, res_msg)

            if res_code == '000':
                log_sync = request.env['log.sync.receive.payment'].sudo().create({
                    'params': json.dumps(params, ensure_ascii=False),
                    'state': 'draft',
                    'job_queue': api_id.job_queue.id if api_id and api_id.job_queue else False,
                    'ip_address': remote_ip
                        })

            res_code, res_msg, res_data = log_sync.action_handle()

            # Ghi nhận kết quả vào Log Sync
            log_sync.sudo().write({
            'response': json.dumps({'code': res_code, 'message': res_msg}, ensure_ascii=False)
            })
        # --- PHẢN HỒI KẾT QUẢ ---

            if res_code == '000':
                return Response.success(res_msg, data=res_data).to_json()
            else:
                # BẮN RA MESSAGE CHI TIẾT KÈM CODE LỖI
                return Response.error(message=res_msg, code=res_code).to_json()

       except Exception as e:
            _logger.error("API Payment Critical Error: %s", str(e), exc_info=True)
            return Response.error(message=f"Lỗi hệ thống: {str(e)}", code="096").to_json()
