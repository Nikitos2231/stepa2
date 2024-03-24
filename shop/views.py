import random
import string
from datetime import datetime, timedelta
from decimal import Decimal

from django import forms
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView

from shop.tasks import send_confirmation_email
from shop.models import Goods, CustomerCreationForm, Basket, BasketItem, Customer, Order


class MyHomePage(ListView):
    template_name = 'home.html'
    model = Goods
    context_object_name = "list_of_all_orders"

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('q')
        min_price = self.request.GET.get('minPrice')
        max_price = self.request.GET.get('maxPrice')
        categories = self.request.GET.getlist('categories')

        self.initial_search_query = search_query
        self.initial_min_price = min_price
        self.initial_max_price = max_price
        self.initial_categories = categories

        if min_price == '':
            min_price = 0.0

        if max_price == '':
            max_price = 10000000.0

        if search_query:
            queryset = queryset.filter(product__icontains=search_query)
        if min_price is not None and max_price is not None:
            min_price = Decimal(min_price)
            max_price = Decimal(max_price)
            queryset = queryset.filter(price__range=(min_price, max_price))
        if categories:
            queryset = queryset.filter(category__in=categories)

        queryset = queryset.order_by('-quantity')
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['initial_search_query'] = self.initial_search_query
        context['initial_min_price'] = self.initial_min_price
        context['initial_max_price'] = self.initial_max_price
        context['initial_categories'] = self.initial_categories

        user = self.request.user
        basket_items = []

        if user.is_authenticated:
            basket = (Basket.objects.filter(basket_session=self.request.session.session_key)
                      .filter(~Q(status='CLOSED')).first())
            context['basket'] = basket
            if basket:
                basket_items = [item.order_id for item in basket.items.all()]

        context['basket_items'] = basket_items
        context['user'] = user
        return context


class RemoveFromBasketView(View):
    def post(self, request):
        product_id = request.POST.get('product_id')
        customer = get_object_or_404(Customer, basket__basket_session=request.session.session_key)

        basket_items = BasketItem.objects.filter(basket__user=customer, goods_id=product_id)

        basket_items.delete()

        referer = request.META.get('HTTP_REFERER')
        return redirect(referer)


class ProductDetailView(View):
    def get(self, request, product_id):
        product = Goods.objects.get(order_id=product_id)

        user = request.user
        basket_items = []
        basket = None
        if user.is_authenticated:
            basket = (Basket.objects.filter(basket_session=self.request.session.session_key)
                      .filter(~Q(status='CLOSED')).first())
            if basket:
                basket_items = [item.order_id for item in basket.items.all()]

        context = {
            'product': product,
            'basket_items': basket_items,
            'basket': basket,
            'user': user
        }
        return render(request, 'product_detail.html', context)


class OrderDetailView(View):
    def get(self, request, order_id):
        order = (Order.objects.filter(basket__user=request.user)
                 .filter(basket__status='CLOSED')
                 .filter(order_id=order_id))

        if not order.exists():
            print('Noneeeeeeeeeeeeeeeeeeeeeeeee')

        order = order.first()
        order.nature_date = order.order_datetime + timedelta(hours=7)

        order_items = order.basket.basketitem_set.all()
        for item in order_items:
            item.total_price = item.quantity * item.goods.price
        context = {
            'order': order,
            'order_items': order_items
        }
        return render(request, 'order_detail.html', context)


class OrderAddressView(View):
    def get(self, request):
        user = request.user
        address_form = AddressForm(initial={
            'country': user.country,
            'city': user.city,
            'house': user.house,
            'street': user.street,
            'room': user.room
        })
        try:
            basket = Basket.objects.filter(basket_session=request.session.session_key) \
                .exclude(status='CLOSED').get()
        except Basket.DoesNotExist:
            return redirect('home')
        return render(request, 'order_address.html', {'user': user, 'address_form': address_form})

    def post(self, request):
        user = request.user
        address_form = AddressForm(request.POST)
        if address_form.is_valid():
            user.country = address_form.cleaned_data['country']
            user.city = address_form.cleaned_data['city']
            user.house = address_form.cleaned_data['house']
            user.street = address_form.cleaned_data['street']
            user.room = address_form.cleaned_data['room']
            user.save()
            return redirect('order_payment')
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме.")
            return render(request, 'order_address.html', {'user': user, 'address_form': address_form})


class OrderPaymentView(View):
    def get(self, request):
        user = request.user
        payment_form = PaymentForm(initial={
            'card_number': user.card_number,
            'card_date': user.card_date,
            'card_cvv': user.card_cvv,
            'phone': user.phone
        })
        try:
            basket = Basket.objects.filter(basket_session=request.session.session_key) \
                .exclude(status='CLOSED').get()
        except Basket.DoesNotExist:
            return redirect('home')
        return render(request, 'order_payment.html',
                      {'user': user, 'payment_form': payment_form,
                       'basket': basket})

    def post(self, request):
        user = request.user
        action = request.POST.get('action')

        basket = (Basket.objects.filter(basket_session=request.session.session_key)
                  .exclude(status='CLOSED').get())
        basket_items = basket.basketitem_set.all() if basket else []

        if action == 'check-otp':
            order = Order.objects.get(basket=basket)
            entered_otp = request.POST.get('otp')

            if order.confirmation_code == entered_otp:
                order.confirmation_status = True

                order.country = user.country
                order.city = user.city
                order.house = user.house
                order.street = user.street
                order.room = user.room
                order.card_number = user.card_number
                order.card_date = user.card_date
                order.card_cvv = user.card_cvv
                order.phone = user.phone

                order.save()
                basket.status = 'CLOSED'
                basket.save()

                send_confirmation_email.delay(user.email, order.order_id)

                return redirect('order_success')
            else:
                messages.error(request, 'Неправильный код подтверждения. Пожалуйста, попробуйте снова.',
                               extra_tags='invalid-confirmation-code')
                return redirect('order_payment')

        elif action == 'change-data':
            for basket_item in basket_items:
                goods = basket_item.goods
                goods.quantity += basket_item.quantity
                goods.save()
            basket.status = 'CREATED'
            basket.save()
            return redirect('order_payment')

        else:
            payment_form = PaymentForm(request.POST)
            if payment_form.is_valid():
                user.card_number = payment_form.cleaned_data['card_number']
                user.card_date = payment_form.cleaned_data['card_date']
                user.card_cvv = payment_form.cleaned_data['card_cvv']
                user.phone = payment_form.cleaned_data['phone']
                user.save()

                for item in basket_items:
                    if item.quantity > item.goods.quantity:
                        return redirect('basket')

                with transaction.atomic():
                    for item in basket_items:
                        item.goods.quantity -= item.quantity
                        item.goods.save()

                    basket.status = 'RESERVED'
                    basket.last_reserved_status_date = datetime.now()
                    basket.save()

                    orders = Order.objects.filter(basket=basket)

                    if not orders.exists():
                        order = Order.objects.create(basket=basket,
                                                     confirmation_code=''.join(random.choices(string.digits, k=6)))
                        order.order_datetime = datetime.now()
                        order.confirmation_status = False
                        order.save()

                return redirect('order_payment')
            else:
                messages.error(request, "Пожалуйста, исправьте ошибки в форме.")
                return render(request, 'order_payment.html', {'user': user, 'payment_form': payment_form})


class PaymentForm(forms.Form):
    card_number = forms.CharField(max_length=16, required=True)
    card_date = forms.CharField(required=True)
    card_cvv = forms.CharField(max_length=3, required=True)
    phone = forms.CharField(max_length=12, required=True)


class AddressForm(forms.Form):
    country = forms.CharField(max_length=128, required=True)
    city = forms.CharField(max_length=128, required=True)
    house = forms.CharField(max_length=128, required=True)
    street = forms.CharField(max_length=128, required=True)
    room = forms.CharField(max_length=128, required=True)


class OrderSuccessView(View):
    def get(self, request):
        user = request.user
        orders = (Order.objects.filter(basket__user=user).filter(basket__status='CLOSED')
                  .order_by('-order_datetime'))
        order = orders.first()
        formatted_date = order.order_datetime.strftime('%d-%m-%Y')
        return render(request, 'order_success.html',
                      {'user': user, 'order': order, 'formatted_date': formatted_date})


class ProfileView(View):
    def get(self, request):
        user = request.user
        form = UserUpdateForm(instance=user)

        orders = (Order.objects.filter(basket__user=user).filter(basket__status='CLOSED')
                  .order_by('-order_datetime'))
        for order in orders:
            order.nature_date = order.order_datetime + timedelta(hours=7)
            num_items = order.basket.items.count()
            if num_items == 1:
                order.num_items_text = "позиция"
            elif 2 <= num_items <= 4:
                order.num_items_text = "позиции"
            else:
                order.num_items_text = "позиций"
            total_price = sum(item.price for item in order.basket.items.all())
            order.total_price = total_price

        return render(request, 'profile.html',
                      {'user': user, 'form': form, 'orders': orders})

    def post(self, request):
        user = request.user
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('profile')
        else:
            if 'email' in form.errors:
                messages.error(request, form.errors['email'])
        return render(request, 'profile.html', {'user': user, 'form': form})


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'email', 'country', 'city', 'house', 'street', 'room', 'card_number',
                  'card_date', 'card_cvv', 'phone']
        widgets = {
            'card_date': forms.TextInput(attrs={'placeholder': 'MM/YYYY'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ['country', 'city', 'house', 'street', 'room', 'card_number', 'card_date', 'card_cvv',
                           'phone']:
            self.fields[field_name].required = False


class AddToBasketView(View):
    @staticmethod
    def post(request, *args, **kwargs):
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))

        basket_session = request.session.session_key
        try:
            basket = Basket.objects.filter(basket_session=basket_session).exclude(status='CLOSED').get()
        except Basket.DoesNotExist:
            basket = None

        if not basket:
            basket = Basket.objects.create(user=request.user, basket_session=basket_session)

        goods = Goods.objects.get(pk=product_id)
        basket_item, created = BasketItem.objects.get_or_create(basket=basket, goods=goods)
        if not created:
            basket_item.quantity += quantity
            basket_item.save()

        return redirect(request.META.get('HTTP_REFERER', '/'))


class SignUp(CreateView):
    form_class = CustomerCreationForm
    success_url = reverse_lazy('login')
    template_name = 'signup.html'

    def form_valid(self, form):
        user = form.save(commit=False)
        user.username = form.cleaned_data['email']
        user.set_password(form.cleaned_data['password'])
        user.save()
        return super().form_valid(form)

    def get_form_class(self):
        return self.form_class


class BasketView(View):
    def get(self, request):
        basket = (Basket.objects.filter(basket_session=self.request.session.session_key)
                  .filter(~Q(status='CLOSED')).first())
        basket_items = basket.basketitem_set.all() if basket else []

        for basket_item in basket_items:
            basket_item.goods.refresh_from_db()

        for item in basket_items:
            item.total_price = item.quantity * item.goods.price
            if item.quantity > item.goods.quantity:
                messages.error(request,
                               f"Недостаточное количество товара "
                               f"'{item.goods.product}' на складе. Всего: '{item.goods.quantity}'")

        total_basket_price = sum(item.total_price for item in basket_items)

        return render(request, 'basket.html',
                      {'basket_items': basket_items,
                       'total_basket_price': total_basket_price,
                       'basket': basket})

    @staticmethod
    def post(request):
        action = request.POST.get('action')
        item_id = request.POST.get('item_id')

        if action == 'add':
            basket_item = BasketItem.objects.get(id=item_id)
            goods = basket_item.goods
            if goods.quantity >= basket_item.quantity + 1:
                basket_item.quantity += 1
                basket_item.save()
            else:
                messages.error(request,
                               f"Недостаточное количество товара '{goods.product}' на складе. Всего: '{goods.quantity}'")

        elif action == 'remove':
            basket_item = BasketItem.objects.get(id=item_id)
            if basket_item.quantity > 1:
                basket_item.quantity -= 1
                basket_item.save()
            else:
                basket_item.delete()
        elif action == 'delete':
            basket_item = BasketItem.objects.get(id=item_id)
            basket_item.delete()
        elif action == 'clear':
            basket_items = BasketItem.objects.all()
            basket_items.delete()
        elif action == 'reset-reserve':
            basket = (Basket.objects.filter(basket_session=request.session.session_key)
                      .filter(status='RESERVED').get())
            if basket:
                basket_items = basket.basketitem_set.all()
                for basket_item in basket_items:
                    goods = basket_item.goods
                    goods.quantity += basket_item.quantity
                    goods.save()
                basket.status = 'CREATED'
                basket.save()

        return redirect('basket')
