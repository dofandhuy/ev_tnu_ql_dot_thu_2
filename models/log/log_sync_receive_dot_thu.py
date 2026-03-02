import json
import logging
from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo import Command
_logger = logging.getLogger(__name__)

class LogSyncReceivePayment(models.Model):
    _name = 'log.sync.receive.payment'
    _inherit = 'log.sync.receive'
    _description = 'Log nhận thông tin thanh toán sinh viên'
    _rec_name = 'code'

    @api.model_create_multi
    def create(self, vals_list):
        res = super(LogSyncReceivePayment, self).create(vals_list)
        for log in res:
            log.code = 'LSRP' + str(log.id)
        return res

    def execute_data(self):
        self.ensure_one()
        self.state = 'queue'
        return self.sudo().with_delay(
            channel=self.job_queue.complete_name if self.job_queue else 'root',
            max_retries=3,
            priority=2
        ).action_handle()

    def action_handle(self):
        self.ensure_one()
        try:
            raw_data = json.loads(self.params or "{}")
            params = raw_data.get('params', raw_data)
            data = params.get('data') or {}

            student_code = data.get('student_code')
            date_payment = data.get('date_payment')
            ma_dv_raw = str(data.get('unit_code') or '').strip()

            if student_code == 'xyz':
                _logger.info(">>> Đang trả về dữ liệu GIẢ LẬP cho sinh viên xyz để test Postman")
                result_data = {
                    "ma_sinh_vien": "xyz",
                    "ma_don_vi": ma_dv_raw or "MB",
                    "ngay_thanh_toan": date_payment or "2026-02-28",
                    "ct_tt_ids": {
                        "HK1_2025": {
                            "TC_126": 5000000,
                            "BHYT": 1050000
                        },
                        "HK2_2025": {
                            "HP_CHUYEN_NGANH": 12000000
                        }
                    }
                }
                self.write({'state': 'done', 'date_done': datetime.now()})
                return '000', "Thành công (Dữ liệu Demo)", result_data
            # --- KẾT THÚC ĐOẠN CODE CỨNG ---

            if 'hp.thanh.toan.sinh.vien' not in self.env.registry:
                return '096', "Hệ thống chưa nạp Model Thanh toán. Hãy kiểm tra cài đặt module .", {}
            # Tìm mã đơn vị
            business_unit = self.env['res.business.unit'].sudo().search([
            ('code', '=', ma_dv_raw)
                ], limit=1)

            if not business_unit:
                msg = f"Mã đơn vị {ma_dv_raw} không tồn tại trong hệ thống"
                _logger.error(msg)
                return '147', msg, {}
            # Tìm sinh viên
            StudentObj = self.env['res.partner'].sudo()
            student=StudentObj.search([('ma_sinh_vien','=',student_code)], limit=1 )

            if not student:
                msg = f"Sinh viên {student_code} không tồn tại trong hệ thống "
                _logger.error(msg)
                return '147', msg, {}

            # tìm bản ghi thanh toán
            master_record = self.env['hp.thanh.toan.sinh.vien'].sudo().search([
            ('partner_id', '=', student.id),
            ('unit_id', '=', business_unit.id),
            ('ngay_thanh_toan', '=', date_payment)
            ], limit=1)

            if not master_record:
                return '147', "Không tìm thấy dữ liệu thanh toán cho các thông tin đã cung cấp", {}

            result_data = {
            "ma_sinh_vien": student.ma_sinh_vien,
            "ma_don_vi": ma_dv_raw,
            "ngay_thanh_toan": date_payment,
            "ct_tt_ids": {}  # Khởi tạo rỗng để nạp dữ liệu từ DB vào
            }

            for line in master_record.ct_tt_ids:
                m_dot = line.dot_thu_id.code
                m_khoan = line.product_id.default_code

            # Gom nhóm theo mã đợt thu
                if m_dot not in result_data["ct_tt_ids"]:
                    result_data["ct_tt_ids"][m_dot] = {}

            # Gán số tiền từ database vào JSON
                result_data["ct_tt_ids"][m_dot][m_khoan] = line.so_tien

            self.write({'state': 'done', 'date_done': datetime.now()})

        # Trả về kết quả cho Controller để hiển thị ra Postman
            return '000', "Thành công", result_data

        except Exception as e:
            _logger.error("Lỗi Action Handle: %s", str(e))
            self.write({'state': 'fail', 'date_done': datetime.now()})
            return '096', str(e), {}


