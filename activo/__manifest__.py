{
    'name': 'Activo',
    'version': '1.0',
    'summary': "Module Activo, se extende 3 campo para el modelo de maintenance_equipment",
    'description': """Module Activo, se extende 3 campo para el modelo de maintenance_equipment para obtener 
                      una relacion para el modelo activo """,
    'category': 'maintenance equipment',
    'author': "End To End Tecnology",
    'website': "http://www.endtoendt.com",
    'depends': ['base', 'maintenance', 'account_asset', 'fiscal_depreciation_report_etet_v1'],
    'data': [
        "views/maintenance_equipment_views.xml"
    ],
    'installable': True,
    'auto_install': False
}
