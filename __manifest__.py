{
    'name': 'Gestión de Ventas por Viajes',
    'version': '1.0',
    'summary': 'Sistema de gestión de ventas para viajes comerciales',
    'description': """
        Sistema completo para gestionar ventas por viajes:
        - Registro de viajes con productos
        - Control de inventario
        - Ventas con diferentes tipos de pago
        - Gestión de deudas
        - Dashboard con estadísticas
    """,
    'category': 'Sales',
    'author': 'Roberto León Socarrás',
    'website': 'https://www.tusitio.com',
    'depends': ['base', 'mail', 'web'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        
        'views/persona_views.xml',
        'views/viaje_views.xml',
        'views/producto_views.xml',
        'views/venta_views.xml',
        'views/deuda_views.xml',
        
        'views/menu.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    
}