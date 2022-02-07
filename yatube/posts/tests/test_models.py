from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post, Comment, CHAR_Q

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        post_obj_name = str(post)
        post_expected = post.text[:CHAR_Q]
        self.assertEqual(post_obj_name, post_expected)

        group = PostModelTest.group
        group_obj_name = str(group)
        group_expected = group.title
        self.assertEqual(group_obj_name, group_expected)

        comment = PostModelTest.comment
        comment_obj_name = str(comment)
        comment_expected = comment.text
        self.assertEqual(comment_obj_name, comment_expected)

    def test_post_verbose_name(self):
        """verbose_name в полях Post совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'created': 'Дата создания',
            'author': 'Автор',
            'group': 'Группа',
            'image': 'Изображение',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_post_help_text(self):
        """help_text в полях Post совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
            'image': 'Можно добавить картинку',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text,
                    expected_value
                )

    def test_comment_verbose_name(self):
        """verbose_name в полях Comment совпадает с ожидаемым."""
        comment = PostModelTest.comment
        field_verboses = {
            'author': 'Автор',
            'text': 'Текст комментария',
            'created': 'Дата создания',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    comment._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_comment_help_text(self):
        """help_text в полях Comment совпадает с ожидаемым."""
        comment = PostModelTest.comment
        text_help_text = comment._meta.get_field('text').help_text
        expected = 'Введите текст комментария'
        self.assertEqual(text_help_text, expected)
