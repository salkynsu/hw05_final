import shutil
import tempfile

from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.core.cache import cache
from django import forms
from ..models import Post, Group, Follow
from .. views import POSTS_QUANTITY


User = get_user_model()


# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        some_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='some.gif',
            content=some_gif,
            content_type='image/gif'
        )
        cls.author = User.objects.create_user(username='testAuthor')
        cls.another_author = User.objects.create_user(username='anotherAuthor')
        cls.user = User.objects.create_user(username='nonAuthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.another_group = Group.objects.create(
            title='Ещё одна тестовая группа',
            slug='another-slug',
            description='Тестовое описание ещё одной группы',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Текст',
            group=cls.group
        )
        cls.another_post = Post.objects.create(
            author=cls.another_author,
            text='Текст другого поста',
            group=cls.another_group,
            image=cls.uploaded
        )
        cls.follow = Follow.objects.create(
            user=PostViewsTest.user,
            author=PostViewsTest.author
        )


    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Модуль shutil - библиотека Python с удобными инструментами
        # для управления файлами и директориями:
        # создание, удаление, копирование, перемещение,
        # изменение папок и файлов
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованный клиент
        #self.user = User.objects.create_user(username='nonAuthor')
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewsTest.user)
        # Создаем авторизованый клиент, который также автор поста
        self.author_client = Client()
        self.author_client.force_login(PostViewsTest.another_author)
        
        cache.clear()

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "reverse(name): имя_html_шаблона"
        post_id = PostViewsTest.another_post.id
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'another-slug'}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'anotherAuthor'}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': post_id}):
            'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': post_id}):
            'posts/create_post.html',
        }
        # Проверяем, что при обращении к name
        # вызывается соответствующий HTML-шаблон
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # Проверяем, что словари context страниц
    # /, group/<slug:slug>/, profile/<str:username>/
    # в первом элементе списка page_obj содержат ожидаемые значения
    def test_index_group_list_profile_pages_show_correct_context(self):
        """Шаблоны index, group_list, profile
        сформированы с правильным контекстом.
        """
        post = PostViewsTest.another_post
        reverse_names = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'another-slug'}),
            reverse('posts:profile', kwargs={'username': 'anotherAuthor'})
        )
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        # В данном случае везде первым элементом будет наш созданный пост:
        # ведь мы ему присвоили группу; проверяемый профиль -
        # профиль автора этого поста
        for reverse_name in reverse_names:
            with self.subTest():
                response = self.guest_client.get(reverse_name)
                # first_object = response.context['page_obj'][0]
                # post_author_0 = first_object.author
                # post_text_0 = first_object.text
                # post_group_0 = first_object.group
                # post_image_0 = first_object.image
                self.assertIn(post, response.context['page_obj'])
                # self.assertEqual(post_author_0, post.author)
                # self.assertEqual(post_text_0, 'Текст другого поста')
                # self.assertEqual(post_group_0, post.group)
                # self.assertEqual(post_image_0, post.image)

    def test_post_detail_page_shows_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        post = PostViewsTest.another_post
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': post.id})
        )
        self.assertEqual(response.context['post'].text, 'Текст другого поста')
        self.assertEqual(response.context['post'].id, post.id)
        self.assertEqual(response.context['post'].group, post.group)
        self.assertEqual(response.context['post'].author, post.author)
        self.assertEqual(response.context['post'].image, post.image)

    def test_follow_page_shows_correct_context(self):
        """В своей ленте авторизованный пользователь
        видит пост автора, на которого он подписан,
        и не видит пост автора, на которого не подписан.
        """
        post = PostViewsTest.post
        another_post = PostViewsTest.another_post
        response = self.authorized_client.get(reverse('posts:follow_index'))
        context = response.context.get('page_obj')
        self.assertIn(post, context)
        self.assertNotIn(another_post, context)

    def test_create_page_shows_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        # Словарь ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        form_fields = {
            # При создании формы поля модели типа TextField
            # преобразуются в CharField с виджетом forms.Textarea
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }

        # Проверяем, что типы полей формы в словаре context
        # соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_edit_page_shows_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        post = PostViewsTest.another_post
        response = self.author_client.get(
            reverse('posts:post_edit', kwargs={'post_id': post.id})
        )
        # Проверяем, что изначально поля формы заполнены так же,
        # как соответствующие поля выбранного поста.
        # Проверяем, что переменная is_edit передана в контекст
        self.assertEqual(response.context['form'].initial['text'], post.text)
        self.assertEqual(
            response.context['form'].initial['group'], post.group.id
        )
        self.assertEqual(response.context['form'].initial['image'], post.image)
        self.assertTrue(response.context['is_edit'])

    def test_another_group_list_page_not_show_post(self):
        """Пост, не принадлежащий группе,
        не показывается на странице этой группы.
        """
        post = PostViewsTest.post
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': 'another-slug'})
        )
        self.assertNotIn(post, response.context.get('page_obj'))

    def test_authorized_user_can_follow(self):
        """Авторизованный пользователь может подписаться на автора."""
        author = PostViewsTest.another_author
        user = PostViewsTest.user
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': author.username}
            )
        )
        self.assertTrue(
            Follow.objects.filter(author=author, user=user).exists()
        )

    def test_authorized_user_can_unfollow(self):
        """Авторизованный пользователь может отписаться от автора."""
        author = PostViewsTest.author
        user = PostViewsTest.user
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': author.username}
            )
        )
        self.assertFalse(
            Follow.objects.filter(author=author, user=user).exists()
        )


class PaginatorViewsTest(TestCase):
    # Здесь создаются фикстуры: клиент и 13 тестовых записей.
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testAuthor2')
        cls.group = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описание 2',
        )
        cls.BATCH_SIZE = 13
        cls.obj_list = [
            Post(
                author=cls.user,
                text=f'Текст {i}',
                group=cls.group
            )
            for i in range(cls.BATCH_SIZE)
        ]
        Post.objects.bulk_create(cls.obj_list)
        cls.post_list = Post.objects.all()

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        cache.clear()

    def test_1st_page_contains_10_records_2nd_page_contains_3_records(self):
        """Проверка паджинатора для страниц index, group_list и profile."""
        # В фикстурах созданы посты одного автора, принадлежащие к одной группе
        reverse_names = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug-2'}),
            reverse('posts:profile', kwargs={'username': 'testAuthor2'})
        )
        POSTS_REST = PaginatorViewsTest.BATCH_SIZE - POSTS_QUANTITY
        obj_list_1st_page = [
            PaginatorViewsTest.post_list[i] for i in range(POSTS_QUANTITY)
        ]
        obj_list_2nd_page = [
            PaginatorViewsTest.post_list[i] for i in range(
                POSTS_QUANTITY, PaginatorViewsTest.BATCH_SIZE
            )
        ]
        for reverse_name in reverse_names:
            with self.subTest():
                response = self.client.get(reverse_name)
                # Проверка: количество постов на первой странице равно 10
                # (количество отображаемых на одной странице постов задано
                # в константе POSTS_QUANTITY, импортированной из views).
                self.assertEqual(
                    len(response.context['page_obj']), POSTS_QUANTITY
                )
                # Проверка: посты на первой странице соответствуют
                # первым 10-ти созданным в фикстурах постам
                self.assertEqual(
                    response.context.get('page_obj').object_list,
                    obj_list_1st_page
                )
                response = self.client.get(reverse_name + '?page=2')
                # Проверка: на второй странице должно быть три поста
                # (количество отображаемых постов посчитано как
                # разность между количеством созданных в фикстурах постов
                # и количеством отображаемых на одной странице постов)
                self.assertEqual(len(response.context['page_obj']), POSTS_REST)
                # Проверка: посты на второй странице соответствуют
                # последним трём созданным в фикстурах постам
                self.assertEqual(
                    response.context.get('page_obj').object_list,
                    obj_list_2nd_page
                )


class CacheindexTest(TestCase):
    def setUp(self):
        # Создаем авторизованный клиент
        self.user = User.objects.create_user(username='cache_test')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Создаём пост
        self.post = Post.objects.create(
            author=self.user,
            text='Текст кэшируемого поста'
        )
        cache.clear()

    def test_cache(self):
        """Проверка кэширования главной страницы."""
        response = self.authorized_client.get(reverse('posts:index'))
        content = response.content
        context = response.context['page_obj']
        self.assertIn(self.post, context)
        post = Post.objects.get(id=self.post.id)
        post.delete()
        second_response = self.authorized_client.get(reverse('posts:index'))
        second_content = second_response.content
        self.assertEqual(content, second_content)
        cache.clear()
        third_response = self.authorized_client.get(reverse('posts:index'))
        third_content = third_response.content
        self.assertNotEqual(content, third_content)
