from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse


User = get_user_model()


class UserFormTest(TestCase):

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()

    def test_signup(self):
        """Валидная форма создает новый пост."""
        # Подсчитаем количество постов
        users_count = User.objects.count()
        form_data = {
            'first_name': 'Name',
            'last_name': 'LastName',
            'username': 'username',
            'email': 'test@test.com',
            'password1': 'c54fhWH5t!@5TG%^&',
            'password2': 'c54fhWH5t!@5TG%^&',
        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )

        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse('posts:index'))
        # Проверяем, увеличилось ли число пользователей
        self.assertEqual(User.objects.count(), users_count + 1)
        # Проверяем, что создался пользователь с данными из формы
        self.assertTrue(
            User.objects.filter(
                first_name='Name',
                last_name='LastName',
                username='username',
                email='test@test.com'
            ).exists()
        )
