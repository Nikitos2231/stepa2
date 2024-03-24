# Create your models here.

from django import forms
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomerManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password is not None:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class Customer(AbstractUser):
    customer_id = models.AutoField("ID", primary_key=True)
    email = models.EmailField(unique=True, null=True)
    first_name = models.CharField("First Name", max_length=128)
    last_name = models.CharField("Last Name", max_length=128)

    country = models.CharField("Country", max_length=128, default='')
    city = models.CharField("City", max_length=128, default='')
    house = models.CharField("House", max_length=128, default='')
    street = models.CharField("Street", max_length=128, default='')
    room = models.CharField("Room", max_length=128, default='')

    card_number = models.CharField("Card number", max_length=128, default='', null=True)
    card_date = models.CharField("Card date", max_length=7, null=True, default=None)
    card_cvv = models.CharField("Card cvv", max_length=128, default='', null=True)
    phone = models.CharField("Phone", max_length=128, default='', null=True)

    username = models.CharField(max_length=150, unique=True, default='')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomerManager()

    def __str__(self):
        return '%s %s' % (self.first_name, self.last_name)


class Goods(models.Model):
    order_id = models.AutoField("ID", primary_key=True)
    product = models.CharField("Product", max_length=128)
    price = models.DecimalField("Price", max_digits=10, decimal_places=2, default=0)
    product_description = models.CharField("Product description", max_length=1024, default='')
    image = models.ImageField("Image", upload_to='static/img/', default='https://via.placeholder.com/150', blank=True,
                              null=True)
    age = models.CharField("Age", max_length=128, default='')
    taste = models.CharField("Taste", max_length=128, default='')
    producer = models.CharField("Producer", max_length=128, default='')
    product_class = models.CharField("Product class", max_length=128, default='')
    features = models.CharField("Features", max_length=1024, default='')
    quantity = models.IntegerField("Quantity", default=5)
    CATEGORY_CHOICES = [
        ('cat', 'Cat'),
        ('dog', 'Dog'),
        ('parrot', 'Parrot'),
    ]
    category = models.CharField("Category", max_length=50, choices=CATEGORY_CHOICES)

    def __str__(self):
        return '%s %s' % (self.order_id, self.product)


class Basket(models.Model):
    basket_id = models.AutoField("ID", primary_key=True)
    user = models.ForeignKey(Customer, on_delete=models.CASCADE)
    items = models.ManyToManyField('Goods', through='BasketItem')
    basket_session = models.CharField("Basket session", max_length=128, default='')
    status = models.CharField("Basket session", max_length=128, default='CREATED')
    created_at = models.DateTimeField(auto_now_add=True)
    last_reserved_status_date = models.DateTimeField("Last status date", null=True, blank=True)


class Order(models.Model):
    order_id = models.AutoField("ID", primary_key=True)
    basket = models.OneToOneField(Basket, on_delete=models.CASCADE)
    order_datetime = models.DateTimeField("Order Date and Time", auto_now_add=True)
    confirmation_code = models.CharField("Confirmation Code", max_length=128)
    confirmation_status = models.BooleanField("Confirmation Status", default=False)

    country = models.CharField("Country", max_length=128, default='')
    city = models.CharField("City", max_length=128, default='')
    house = models.CharField("House", max_length=128, default='')
    street = models.CharField("Street", max_length=128, default='')
    room = models.CharField("Room", max_length=128, default='')

    card_number = models.CharField("Card number", max_length=128, default='', null=True)
    card_date = models.CharField("Card date", max_length=7, null=True, default=None)
    card_cvv = models.CharField("Card cvv", max_length=128, default='', null=True)
    phone = models.CharField("Phone", max_length=128, default='', null=True)


class BasketItem(models.Model):
    basket = models.ForeignKey(Basket, on_delete=models.CASCADE)
    goods = models.ForeignKey('Goods', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)


class CustomerCreationForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput, max_length=128,
                               error_messages={'required': _("Пароль должен содержать максимум 128 символов")})
    email = forms.EmailField(label=_("Email"), max_length=128,
                             error_messages={'unique': _("Пользователь с таким email уже зарегистрирован"),
                                             'required': _("Email должeн содержать максимум 128 символов")})
    first_name = forms.CharField(label=_("First Name"), max_length=128,
                                 error_messages={'required': _("Фамилия должна содержать максимум 128 символов")})
    last_name = forms.CharField(label=_("Last Name"), max_length=128,
                                error_messages={'required': _("Имя должно содержать максимум 128 символов")})

    class Meta:
        model = Customer
        fields = ('email', 'first_name', 'last_name', 'password')
