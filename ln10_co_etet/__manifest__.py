# -*- coding: utf-8 -*-
{
    'name': "Colombian Location - End to End Technology SAS",

    'description': 'Adjust Colombian Location, to have complete definitions that we need to send e-invoice with DIAN.',
    # Long description of module's purpose

    'summary': 'Adjust Colombian Location',
    # Short (1 phrase/line) summary of the module's purpose, used as
    # subtitle on modules listing or apps.openerp.com""",

    'author': "End to End Technology SAS",
    'website': "http://www.endtoendt.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Localization',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'base_address_city', 'l10n_co','sale'],
    'application': True,

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ln10_co_etet.diancodes.csv',
        'data/ln10_co_etet.ciiucodes.csv',
        'data/ln10_co_etet.nomenclaturedian.csv',
        'data/ln10_co_etet.taxestype.csv',
        'data/ln10co_document_type.xml',
        'data/res.country.state.csv',
        'data/res.city.csv',

        'views/account_move_reversal_view.xml',
        'views/account_view.xml',
        'views/ln10co_etet.xml',
        'views/res_city_view.xml',
        'views/res_company.xml',
        'views/res_country_views.xml',
        'views/res_currency_views.xml',
        'views/res_lang_views.xml',
        'views/res_partner.xml',
        'views/uom_uom_views.xml'

    ],

    # only loaded in demonstration mode
    # 'demo': [
    # ],
}
