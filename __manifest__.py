{
    'name': 'Reportes ADICAAP',
    'summary': 'Integración de Reporteria propia de ADICAAP',
    'version': '1.0.0',
    'category': 'Technical',
    'description': 'Genera los reportes en los diferentes formatos de ADICAAP.',
    'author': 'Telemática',
    'website': 'https://telematica.hn',
    'depends': ['base', 'accountant'],
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Views
        'views/hr_report_wizard_view.xml',
        'views/hr_report_view.xml',
    ],
    'license': 'OPL-1',
    'auto_install': False,
    'application': False,
    'installable': True,
    'maintainer': 'Telemática Development Team',
}