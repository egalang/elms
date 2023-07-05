# -*- coding: utf-8 -*-
{
    'name': "loans",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mail',],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'report/loan_report.xml',
        'report/loan_summary_report.xml',
        'views/loans_main_views.xml',
        
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

    'installable': True,
    'application': True
}
