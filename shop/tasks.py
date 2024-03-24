from celery import shared_task
from django.template.loader import render_to_string
from django.utils import timezone
from django.core.mail import send_mail

from djangoProject7 import settings
from .models import Basket, Order


@shared_task
def process_expired_baskets():
    print('Start shared task for expired baskets')
    expired_baskets = Basket.objects.filter(
        status='RESERVED',
        last_reserved_status_date__lte=timezone.now() - timezone.timedelta(minutes=30)
    )
    print('Founded baskets: {}'.format(expired_baskets.count()))

    for basket in expired_baskets:
        basket_items = basket.basketitem_set.all()
        for basket_item in basket_items:
            goods = basket_item.goods
            goods.quantity += basket_item.quantity
            goods.save()

        basket.status = 'CREATED'
        basket.save()


@shared_task
def send_confirmation_email(email, order_id):
    order = Order.objects.get(pk=order_id)
    subject = 'Подтверждение заказа'
    html_message = render_to_string('confirmation_email.html',
                                    {'order': order})
    send_mail(subject, '', settings.EMAIL_HOST_USER, [email], html_message=html_message)
