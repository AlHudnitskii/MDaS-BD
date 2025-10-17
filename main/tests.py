from django.test import TestCase, Client
from django.urls import reverse
from main.models import Product, Category
from users.models import User 
from django.core.files.uploadedfile import SimpleUploadedFile


class ViewsTest(TestCase):
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
        
    def test_popular_list_view(self):
        response = self.client.get(reverse('main:popular_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/index/index.html')
        self.assertContains(response, 'Test Product')
        
    def test_product_list_view(self):
        response = self.client.get(reverse('main:product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/product/list.html')
        self.assertContains(response, 'Test Product')
        
    def test_product_list_by_category_view(self):
        response = self.client.get(reverse('main:product_list_by_category',
                                         args=[self.category.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/product/list.html')
        self.assertContains(response, 'Test Product')
        
    def test_info_views(self):
        info_pages = [
            ('main:about', 'main/info/about.html'),
            ('main:news', 'main/info/news.html'),
            ('main:dict', 'main/info/dict.html'),
            ('main:contacts', 'main/info/contacts.html'),
            ('main:vacancies', 'main/info/vacancies.html'),
            ('main:promocodes', 'main/info/promocodes.html'),
            ('main:reviews', 'main/info/reviews.html'),
        ]
        
        for url_name, template in info_pages:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, template)
                
    def test_statistics_view(self):
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('main:statistics'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/info/statistics.html')


class ModelsTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            category=self.category,
            name='Test Product',
            slug='test-product',
            price=100.00,
            discount=10.00,
            available=True
        )
        
    def test_category_str(self):
        self.assertEqual(str(self.category), 'Test Category')
        
    def test_category_get_absolute_url(self):
        expected_url = reverse('main:product_list_by_category',
                             args=[self.category.slug])
        self.assertEqual(self.category.get_absolute_url(), expected_url)
        
    def test_product_str(self):
        self.assertEqual(str(self.product), 'Test Product')
        
    def test_product_get_absolute_url(self):
        expected_url = reverse('main:product_detail',
                             args=[self.product.slug])
        self.assertEqual(self.product.get_absolute_url(), expected_url)
        
    def test_product_sell_price(self):
        self.assertEqual(self.product.sell_price(), 90.00)
        
        product_no_discount = Product.objects.create(
            category=self.category,
            name='No Discount Product',
            slug='no-discount-product',
            price=100.00,
            discount=0.00,
            available=True
        )
        self.assertEqual(product_no_discount.sell_price(), 100.00)