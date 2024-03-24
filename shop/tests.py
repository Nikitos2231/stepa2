from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.common.by import By

from shop.models import CustomerCreationForm, Goods, BasketItem, Customer
from shop.views import SignUp


class SignUpTestCase(TestCase):
    def test_form_valid(self):
        User = get_user_model()
        post_data = {
            'email': 'test@example.com',
            'password': 'testpassword',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = self.client.post(reverse('signup'), post_data)
        self.assertEqual(response.status_code, 302)

        # Проверяем, что пользователь был создан
        created_user = User.objects.get(email='test@example.com')
        self.assertIsNotNone(created_user)

    def test_get_form_class(self):
        view = SignUp()
        form_class = view.get_form_class()

        self.assertEqual(form_class, CustomerCreationForm)


class AddToBasketViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = Customer.objects.create_user(email='test@example.com', password='password123', first_name='John',
                                                last_name='Doe')
        cls.goods = Goods.objects.create(product='Test Product', price=10.00, quantity=10)

    def test_post_adds_to_basket(self):
        self.client.login(email='test@example.com', password='password123')
        response = self.client.post(reverse('add_to_basket'), {'product_id': self.goods.pk})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(BasketItem.objects.filter(basket__user=self.user, goods=self.goods).exists())

    def test_post_updates_quantity(self):
        self.client.login(email='test@example.com', password='password123')
        self.client.post(reverse('add_to_basket'), {'product_id': self.goods.pk})
        self.client.post(reverse('add_to_basket'), {'product_id': self.goods.pk})
        basket_item = BasketItem.objects.get(basket__user=self.user, goods=self.goods)
        self.assertEqual(basket_item.quantity, 2)


class SignUpTestCaseAuto(StaticLiveServerTestCase):
    def setUp(self):
        self.browser = webdriver.Chrome()
        self.browser.implicitly_wait(10)

    def tearDown(self):
        self.browser.quit()

    def test_user_registration(self):
        self.browser.get(self.live_server_url + reverse('signup'))

        self.browser.find_element(By.NAME, 'email').send_keys('test@example.com')
        self.browser.find_element(By.NAME, 'first_name').send_keys('John')
        self.browser.find_element(By.NAME, 'last_name').send_keys('Doe')
        self.browser.find_element(By.NAME, 'password').send_keys('testpassword')

        self.browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        self.assertIn('login', self.browser.current_url)
