{
    'name': 'supplier',
    'version': '1.0',
    'summary': "Module to add a supplier table in the equipment model",
    'description': """Module to add a supplier table in the equipment model""",
    'category': 'Purchase Management',
    'author': "End To End Tecnology",
    'website': "http://www.endtoendt.com",
    'depends': ['base', 'maintenance', 'product'],
    'data': [
        "views/maintenance_equipment_views.xml"
    ],
    'installable': True,
    'auto_install': False
}
