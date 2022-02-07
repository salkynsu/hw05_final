import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from .. forms import PostForm, CommentForm
from .. models import Post, Group, Comment
from django.urls import reverse


User = get_user_model()


# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testAuthor')
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
        cls.form = PostForm()

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
        # Создаем авторизованый клиент, который также автор поста
        self.author_client = Client()
        self.author_client.force_login(PostFormTest.user)

    def test_post_create(self):
        """Валидная форма создает новый пост."""
        # Подсчитаем количество постов
        posts_count = Post.objects.count()
        some_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='some.gif',
            content=some_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст',
            'group': PostFormTest.group.id,
            'image': uploaded,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': 'testAuthor'})
        )
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, что создался пост с данными из формы
        self.assertTrue(
            Post.objects.filter(
                author=PostFormTest.user,
                text='Тестовый текст',
                group=PostFormTest.group,
                image='posts/some.gif'
            ).exists()
        )

    def test_post_edit(self):
        """Валидная форма обновляет выбранный пост."""
        post = PostFormTest.post
        form_data = {
            'text': 'Текст обновлённого поста',
        }
        response = self.author_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True
        )
        # Обновляем пост в базе данных
        post.refresh_from_db()
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': post.id})
        )
        # Проверяем, обновился ли пост
        self.assertEqual(post.text, 'Текст обновлённого поста')

    def test_labels(self):
        """labels в полях совпадает с ожидаемым."""
        form = PostFormTest.form
        field_labels = {
            'text': 'Текст поста',
            'group': 'Группа',
            'image': 'Изображение',
        }
        for field, expected_value in field_labels.items():
            with self.subTest(field=field):
                self.assertEqual(
                    form.fields[field].label, expected_value)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        form = PostFormTest.form
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
            'image': 'Можно добавить картинку',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    form.fields[field].help_text, expected_value)


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='PostAuthor')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст'
        )
        cls.form = CommentForm()

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованный клиент
        self.user = User.objects.create_user(username='CommentAuthor')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_add_comment(self):
        """Валидная форма добавляет комментарий к выбранному посту."""
        post = CommentFormTest.post
        form_data = {
            'text': 'Текст комментария',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': post.id})
        )
        comment = Comment.objects.first()
        # Проверяем, появился ли комментарий
        self.assertEqual(comment.text, 'Текст комментария')
        # Проверяем, появился ли комментарий в контексте шаблона post_detail
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': post.id})
        )
        self.assertIn(comment, response.context.get('comments'))

    def test_anonymous_cant_add_comment(self):
        """Анонимный пользователь не может добавить комментарий."""
        post = CommentFormTest.post
        form_data = {
            'text': 'Текст комментария анонимного пользователя',
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True
        )
        # Проверяем, что этот комментарий не появился на странице post_detail,
        # то есть, список комментариев comments пуст
        self.assertIsNone(response.context.get('comments'))

    def test_labels(self):
        """labels в полях совпадает с ожидаемым."""
        form = CommentFormTest.form
        text_label = form.fields['text'].label
        expected_value = 'Текст комментария'
        self.assertEqual(text_label, expected_value)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        form = CommentFormTest.form
        text_help_text = form.fields['text'].help_text
        expected_value = 'Введите текст комментария'
        self.assertEqual(text_help_text, expected_value)
