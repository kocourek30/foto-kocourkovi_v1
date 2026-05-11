from django.urls import path

from apps.orders.views import (
    cart_add_item_view,
    cart_detail_view,
    cart_remove_item_view,
    cart_update_item_quantity_view,
    orders_cart_new_view,
    orders_cart_submit_view,
    orders_confirmation_view,
)

urlpatterns = [
    path("g/<str:token>/cart/", cart_detail_view, name="orders-cart-detail"),
    path("g/<str:token>/cart/add/", cart_add_item_view, name="orders-cart-add"),
    path("g/<str:token>/cart/new/", orders_cart_new_view, name="orders-cart-new"),
    path("g/<str:token>/cart/submit/", orders_cart_submit_view, name="orders-cart-submit"),
    path(
        "g/<str:token>/cart/item/<int:item_id>/remove/",
        cart_remove_item_view,
        name="orders-cart-item-remove",
    ),
    path(
        "g/<str:token>/cart/item/<int:item_id>/quantity/",
        cart_update_item_quantity_view,
        name="orders-cart-item-quantity",
    ),
    path(
        "g/<str:token>/order/<uuid:public_id>/",
        orders_confirmation_view,
        name="orders-confirmation",
    ),
]
