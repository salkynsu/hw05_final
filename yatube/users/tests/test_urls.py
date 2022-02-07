from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from http import HTTPStatus

User = get_user_model()


class UserURLTest(TestCase):
    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованный клиент
        self.user = User.objects.create_user(username='TestUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_exists_at_desired_location_for_authorized_user(self):
        """Страницы из списка urls доступны авторизованному пользователю."""
        urls = [
            '/auth/logout/',
            '/auth/signup/',
            '/auth/login/',
            '/auth/password_reset_form/'
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_exists_at_desired_location_for_anonymous(self):
        """Страницы из списка urls доступны неавторизованному пользователю."""
        urls = [
            '/auth/logout/',
            '/auth/signup/',
            '/auth/login/',
            '/auth/password_reset_form/'
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
