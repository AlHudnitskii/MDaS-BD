from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from users.models import User
from users.forms import UserLoginForm, UserRegistrationForm, ProfileForm
from orders.models import Order, OrderItem
from main.models import Product, Category


User = get_user_model()

class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_creation(self):
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('testpass123'))
        self.assertFalse(self.user.is_superuser)
        self.assertFalse(self.user.is_staff)
    
    def test_user_str(self):
        self.assertEqual(str(self.user), 'testuser')
    
    def test_user_image_field(self):
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'simple image content',
            content_type='image/jpeg'
        )
        user_with_image = User.objects.create_user(
            username='userwithimage',
            email='image@example.com',
            password='testpass123',
            image=image
        )
        self.assertTrue(user_with_image.image)
        self.assertIn('test_image', user_with_image.image.name)


class UserViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        category = Category.objects.create(name='Test Category', slug='test-category')
        self.product = Product.objects.create(
            category=category,
            name='Test Product',
            slug='test-product',
            price=100.00
        )
        self.order = Order.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            city='Test City',
            address='Test Address',
            postal_code='123456',
            paid=True
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            price=self.product.price,
            quantity=2
        )
    
    def test_login_view_get(self):
        response = self.client.get(reverse('user:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/login.html')
        self.assertIsInstance(response.context['form'], UserLoginForm)
    
    def test_login_view_post_success(self):
        response = self.client.post(reverse('user:login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertRedirects(response, reverse('main:product_list'))
        self.assertTrue('_auth_user_id' in self.client.session)
 
    def test_logout_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('user:logout'))
        self.assertRedirects(response, reverse('main:product_list'))
        self.assertFalse('_auth_user_id' in self.client.session)


class UserFormsTest(TestCase):
    def test_user_login_form_valid(self):
        User.objects.create_user(username='testuser', password='testpass123')
        form = UserLoginForm(data={
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertTrue(form.is_valid())
    
    def test_user_login_form_invalid(self):
        form = UserLoginForm(data={
            'username': '',
            'password': ''
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 2)