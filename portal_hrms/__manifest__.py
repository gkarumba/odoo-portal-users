# -*- coding: utf-8 -*-
{
    'name': "Portal User leaves and attendance",
    'summary': """
        Portal user can checkin and checkout and can apply for leaves from website,  
        No need to create internal users for enterprise users so save cost and make portal users
        """,
    'description': """
          Portal user can checkin and checkout and can apply for leaves from website,  
        No need to create internal users for enterprise users so save cost and make portal users.
    """,
    'author': "Buffer Solutuions",
    'category': 'Human Resources',
    'version': '0.1',
    'license': 'OPL-1',

    'images': ['static/description/icon.jpg','static/description/banner.png'],
    # any module necessary for this one to work correctly
    'depends': ['base','portal','hr', 'hr_attendance','hr_holidays'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/ir.model.access.csv',
        'security/hr_security.xml',
        'views/knk_res_config_view.xml',
        'views/omni_menu_entries_templates.xml',
        'views/omni_attendance_views.xml',
        'views/omni_res_users_inherit.xml',
        'views/portal_templates.xml',

    ],

    'assets': {
        'web.assets_frontend': [
            "portal_hrms/static/src/js/omni_attendance.js",
            "portal_hrms/static/src/scss/omni_attendance.scss",
            'portal_hrms/static/src/js/portal_leave.js',
            'portal_hrms/static/src/js/leave_portal.js',
        ]
    },
 #'price': "10",
  #'currency': "USD",


    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
