from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.cache import cache
from ..models import Post, Group
from http import HTTPStatus

User = get_user_model()


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст',
            group=cls.group
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованный клиент
        self.user = User.objects.create_user(username='nonAuthor')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Создаем авторизованый клиент, который также автор поста
        self.author_client = Client()
        self.author_client.force_login(PostURLTest.user)
        cache.clear()

    def test_urls_exists_at_desired_location(self):
        """Страницы из списка urls доступны авторизованному пользователю --
        автору поста.
        """
        post = PostURLTest.post
        group = PostURLTest.group
        user = PostURLTest.user
        urls = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': group.slug}),
            reverse('posts:profile', kwargs={'username': user.username}),
            reverse('posts:post_detail', kwargs={'post_id': post.id}),
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            reverse('posts:follow_index'),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_url(self):
        """Запрос несуществующей страницы возвращает ошибку 404,
        используется кастомный шаблон для страницы 404.
        """
        response = self.guest_client.get('/unexisting/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_create_url_redirect_anonymous_on_auth_login(self):
        """Страница create перенаправляет неавторизованного пользователя
        на страницу авторизации.
        """
        response = self.guest_client.get(
            reverse('posts:post_create'), follow=True
        )
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_edit_url_redirect_anonymous_on_post_detail(self):
        """Страница edit перенаправляет неавторизованного пользователя
        на страницу подробной информации о посте.
        """
        post = PostURLTest.post
        response = self.guest_client.get(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': post.id})
        )

    def test_edit_url_redirect_non_author_on_post_detail(self):
        """Страница edit перенаправляет авторизованного пользователя,
        который не является автором выбранного поста,
        на страницу подробной информации о посте.
        """
        post = PostURLTest.post
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': post.id})
        )

    def test_add_comment_url_redirect_anonymous_on_post_detail(self):
        """Страница add_comment перенаправляет неавторизованного пользователя
        на страницу авторизации.
        """
        post = PostURLTest.post
        response = self.guest_client.get(
            reverse('posts:add_comment', kwargs={'post_id': post.id}),
            follow=True
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{post.id}/comment/'
        )

    def test_follow_url_redirect_on_profile(self):
        """По нажатию на кнопку "Подписаться"
        авторизованный пользователь перенаправляется на профайл автора.
        """
        author = PostURLTest.user
        response = self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': author.username}),
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': author.username})
        )

    def test_unfollow_url_redirect_on_profile(self):
        """По нажатию на кнопку "Отписаться"
        авторизованный пользователь перенаправляется на профайл автора.
        """
        author = PostURLTest.user
        response = self.authorized_client.get(
            reverse('posts:profile_unfollow', kwargs={'username': author.username}),
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': author.username})
        )

    # Проверка вызываемых шаблонов для каждого адреса
    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        post = PostURLTest.post
        group = PostURLTest.group
        user = PostURLTest.user
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': user.username}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': post.id}):
            'posts/post_detail.html',
            reverse('posts:post_create'):
            'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': post.id}):
            'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertTemplateUsed(response, template)
