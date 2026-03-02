# -*- coding: utf-8 -*-
{
    'name': "TNU tích hợp xác nhận phản hồi thanh toán API",

    'summary': """
        TNU tích hợp xác nhận phản hồi thanh toán API
        """,
    'description': """
        TNU tích hợp xác nhận phản hồi thanh toán API
    """,

    'author': "IZISolution",
    'website': "https://www.izisolution.vn",
    'category': 'Tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['ev_config_connect_api', 'ev_api_sync_base', 'contacts', 'product', 'queue_job', 'izi_lib', 'base',
                'ev_tnu_hp_master_data'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/qldt_api_config_data.xml',
        'views/log_sync_receive_dot_thu_views.xml',
    ],

}
