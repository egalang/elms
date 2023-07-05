# -*- coding: utf-8 -*-
# from odoo import http


# class Loans(http.Controller):
#     @http.route('/loans/loans', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/loans/loans/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('loans.listing', {
#             'root': '/loans/loans',
#             'objects': http.request.env['loans.loans'].search([]),
#         })

#     @http.route('/loans/loans/objects/<model("loans.loans"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('loans.object', {
#             'object': obj
#         })
