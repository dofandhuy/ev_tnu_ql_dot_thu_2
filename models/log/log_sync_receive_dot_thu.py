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
            # 1. Giải mã Request
            raw_data = json.loads(self.params or "{}")
            params = raw_data.get('params', raw_data)
            data = params.get('data') or {}
            student_code = data.get('student_code')
            date_payment = data.get('date_payment')
            ma_dv_raw = str(data.get('unit_code') or '').strip()

            # 2. Tìm gốc dữ liệu (Phải có Sinh viên & Đơn vị thật mới tạo được phiếu)
            unit = self.env['res.business.unit'].sudo().search([('code', '=', ma_dv_raw)], limit=1)
            student = self.env['res.partner'].sudo().search([('ma_sinh_vien', '=', student_code)], limit=1)
            # _logger.info("========== XỬ LÝ API: %s ==========", student_code)
            # # 3. CHIẾN THUẬT: TỰ TẠO DỮ LIỆU NẾU DB TRỐNG (Dành cho mã xyz)
            # if student_code == 'XYZ' and student and unit:
            #     existing = self.env['hp.thanh.toan.sinh.vien'].sudo().search([
            #         ('partner_id', '=', student.id),
            #         ('ngay_thanh_toan', '=', date_payment)
            #     ], limit=1)
            #
            #     if not existing:
            #         _logger.info(">>> DATABASE TRỐNG: Đang tự động tạo dữ liệu mẫu cho xyz...")
            #         # Tìm hoặc tạo nhanh 1 đợt thu để gắn vào chi tiết
            #         dot_thu = self.env['hp.ql.dot.thu'].sudo().search([], limit=1)
            #         if not dot_thu:
            #             dot_thu = self.env['hp.ql.dot.thu'].sudo().create({'name': 'Kỳ hè 2025', 'code': 'SUMMER_2025'})
            #
            #         self.env['hp.thanh.toan.sinh.vien'].sudo().create({
            #             'partner_id': student.id,
            #             'unit_id': unit.id,
            #             'ngay_thanh_toan': date_payment,
            #             'ct_tt_ids': [(0, 0, {
            #                 'dot_thu_id': dot_thu.id,
            #                 'product_id': self.env['product.product'].sudo().search([], limit=1).id,
            #                 'so_tien': 9999999
            #             })]
            #         })

            # 4. LOGIC SEARCH THẬT (Bốc dữ liệu từ DB trả về)
            if 'hp.thanh.toan.sinh.vien' in self.env.registry and student and unit:
                master_record = self.env['hp.thanh.toan.sinh.vien'].sudo().search([
                    ('partner_id', '=', student.id),
                    ('unit_id', '=', unit.id),
                    ('ngay_thanh_toan', '=', date_payment)
                ], limit=1)

                if master_record:
                    result_data = {
                        "ma_sinh_vien": student.ma_sinh_vien,
                        "ma_don_vi": ma_dv_raw,
                        "ngay_thanh_toan": date_payment,
                        "ct_tt_ids": {}
                    }
                    for line in master_record.ct_tt_ids:
                        m_dot = line.dot_thu_id.code or 'DOT_UNKNOWN'
                        m_khoan = line.product_id.default_code or 'KHOAN_UNKNOWN'
                        if m_dot not in result_data["ct_tt_ids"]:
                            result_data["ct_tt_ids"][m_dot] = {}
                        result_data["ct_tt_ids"][m_dot][m_khoan] = line.so_tien

                    _logger.info(">>> THÀNH CÔNG: Đã bốc được dữ liệu từ Database.")
                    self.write({'state': 'done', 'date_done': datetime.now()})
                    return '000', "Thành công ", result_data

            # 5. Nếu vẫn không thấy (do mã khác xyz hoặc thiếu partner/unit)
            return '147', "Không tìm thấy dữ liệu cho thông tin này", {}

        except Exception as e:
            _logger.error("!!! LỖI API: %s", str(e))
            self.write({'state': 'fail', 'date_done': datetime.now()})
            return '096', str(e), {}
