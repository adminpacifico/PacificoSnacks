
{
    'name': "Nomina",

    'summary': """
        Nomina management""",

    'description': """
        Nomina management
    """,

    'author': "Táctica",
    'website': "http://www.puntosdeventa.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','product','purchase'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        #'data/products.xml',
        'views/views.xml',
        
    ],
    # only loaded in demonstration mode
    
}