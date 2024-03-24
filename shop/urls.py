from django.urls import path

from shop.views import MyHomePage, ProductDetailView, ProfileView, AddToBasketView, RemoveFromBasketView, BasketView, \
    OrderAddressView, OrderPaymentView, OrderSuccessView, OrderDetailView

urlpatterns = [
    path('', MyHomePage.as_view(), name='home'),
    path('product/<int:product_id>/', ProductDetailView.as_view(), name='product_detail'),
    path('profile', ProfileView.as_view(), name='profile'),
    path('add-to-basket/', AddToBasketView.as_view(), name='add_to_basket'),
    path('remove-item/', RemoveFromBasketView.as_view(), name='remove_from_basket'),
    path('basket/', BasketView.as_view(), name='basket'),
    path('order-address/', OrderAddressView.as_view(), name='order_address'),
    path('order-payment/', OrderPaymentView.as_view(), name='order_payment'),
    path('order-success/', OrderSuccessView.as_view(), name='order_success'),
    path('order/<int:order_id>/', OrderDetailView.as_view(), name='order_detail')
]


