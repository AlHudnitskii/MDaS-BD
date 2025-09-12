from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpRequest

from main.models import Product, Category
from users.models import User
from orders.models import Order, OrderItem
from cart.cart import Cart


class OrderModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            category=self.category,
            name='Test Product',
            slug='test-product',
            price=100.00,
            available=True
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
        
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            price=self.product.price,
            quantity=2
        )
    
    def test_order_str(self):
        self.assertEqual(str(self.order), f'Order {self.order.id}')
    
    def test_order_get_total_cost(self):
        self.assertEqual(self.order.get_total_cost(), 200.00)
    
    def test_order_item_str(self):
        self.assertEqual(str(self.order_item), str(self.order_item.id))
    
    def test_order_item_get_cost(self):
        self.assertEqual(self.order_item.get_cost(), 200.00)


class OrderViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            category=self.category,
            name='Test Product',
            slug='test-product',
            price=100.00,
            available=True
        )
        
        self.client = Client()
        
        session = self.client.session
        session['cart'] = {str(self.product.id): {'quantity': 1, 'price': str(self.product.price)}}
        session.save()
    
    def test_order_create_view_get(self):
        response = self.client.get(reverse('orders:order_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'orders/order/create.html')
        self.assertIn('cart', response.context)
        self.assertIn('from', response.context)
 
    
    def test_order_create_view_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'city': 'Test City',
            'address': 'Test Address',
            'postal_code': '123456',
        }
        
        response = self.client.post(reverse('orders:order_create'), data=form_data)
        
        order = Order.objects.first()
        self.assertEqual(order.user, self.user)


class CartOrderIntegrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product1 = Product.objects.create(
            category=self.category,
            name='Product 1',
            slug='product-1',
            price=100.00,
            available=True
        )
        
        self.product2 = Product.objects.create(
            category=self.category,
            name='Product 2',
            slug='product-2',
            price=200.00,
            available=True
        )
        
        self.client = Client()
        
        session = self.client.session
        session['cart'] = {
            str(self.product1.id): {'quantity': 2, 'price': str(self.product1.price)},
            str(self.product2.id): {'quantity': 1, 'price': str(self.product2.price)},
        }
        session.save()
    
  