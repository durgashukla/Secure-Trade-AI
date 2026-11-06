from django.urls import path
from . import views

urlpatterns =[
    path('register/',views.register, name="register"),
    path('login/',views.login_view ,name="login"),
    path('dashboard/',views.dashboard ,name="dashboard"),
    path('upload/',views.upload_invoice ,name="upload_invoice"),
    path('testing/',views.testing_view ,name="testing_view"),
    path('update-status/<int:invoice_id>/',views.update_invoice_status,name='update_invoice_status'),
    path('invoices/<str:status>/',views.invoice_list,name='invoice_list'),
    path('invoice/<int:invoice_id>/',views.invoice_detail,name='invoice_detail'),
    path('invoice/',views.view_invoice,name='view_invoice'),
    path('search-invoice/', views.search_invoice, name='search_invoice'),
    path(
    'download-clearance/<int:invoice_id>/',
    views.download_clearance_certificate,
    name='download_clearance_certificate'
),
    path('logout/', views.logout_view, name='logout'),
    path('account/', views.account_view, name='account'),

path('edit-profile/', views.edit_profile, name='edit_profile'),

path('change-password/', views.change_password, name='change_password'),
]

