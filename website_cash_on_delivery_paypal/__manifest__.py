# -*- coding: utf-8 -*-

{
    'name': 'Website Cash on Delivery Paypal',
    'summary':'Adding New Payment Provider with new Payment Method',
    'description': """Adding New Payment Provider with new Payment Method""" , 
    'category': 'eCommerce',
    'version': '17.0.0.1',
    'author': 'Deja-Tech',
    "website" : "",
    'depends': ['sale', 'account', 'website','website_sale','payment','sale_management','payment_custom'],
    'data': [
        'security/ir.model.access.csv',
        'views/cod_view.xml',
        'views/template.xml',
        'data/payment_acquirer_data.xml',
        
    ],
    'application': True,
    "auto_install": False,
    'installable': True,
    'license': 'OPL-1',
    "images":['static/description/banner.gif'],
    'assets':{
        'web.assets_frontend': [
            'website_cash_on_delivery_paypal/static/src/js/cod_payment.js',
            ],
    },
    'currency': 'USD',
    'price': 30.10,
}
