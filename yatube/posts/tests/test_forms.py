from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User

HOME_URL = reverse('posts:index')
CREATE_URL = reverse('posts:post_create')
LOGIN_URL = reverse('users:login')
USERNAME = 'testuser'
GROUP_TITLE = 'Тестовая группа'
GROUP_SLUG = 'test-slug'
TEXT_POST = 'Тестовый пост'


class PostsFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=TEXT_POST,
            group=cls.group,
        )

    def setUp(self):
        self.user = PostsFormsTests.user
        self.post = PostsFormsTests.post
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = PostsFormsTests.group
        self.post_edit = reverse('posts:post_edit', args=[self.post.id])
        self.posts_count = Post.objects.count()
        self.redirected = f'{LOGIN_URL}?next={CREATE_URL}'

    def test_valid_form_create_post_in_db(self):
        form_data = {
            'text': f'{TEXT_POST}2',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            CREATE_URL, data=form_data, follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.post.refresh_from_db()
        num_posts_after = Post.objects.count()
        self.posts_count += 1
        test_post_create = Post.objects.latest('id')
        self.assertEqual(test_post_create.text, form_data['text'])
        self.assertEqual(test_post_create.group.id, form_data['group'])
        self.assertEqual(test_post_create.author.id, self.user.id)
        self.assertEqual(self.posts_count, num_posts_after)

    def test_valid_form_change_post_in_db(self):
        response = self.authorized_client.get(self.post_edit)
        form = response.context['form']
        form_data = form.initial
        form_data['text'] = f'Измененный {TEXT_POST}'
        form_data['group'] = self.group.id
        response = self.authorized_client.post(
            self.post_edit, data=form_data, follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.post.refresh_from_db()
        num_posts_after = Post.objects.count()
        test_post_edit = Post.objects.latest('id')
        self.assertEqual(test_post_edit.text, form_data['text'])
        self.assertEqual(test_post_edit.group.id, form_data['group'])
        self.assertEqual(test_post_edit.author.id, self.user.id)
        self.assertEqual(self.posts_count, num_posts_after)

    def test_unauthorized_client_cannot_create_post(self):
        form_data = {
            'text': f'{TEXT_POST}3',
            'group': self.group.id,
        }
        response = self.guest_client.post(
            CREATE_URL, data=form_data, follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, self.redirected)
        num_posts_after = Post.objects.count()
        self.assertEqual(self.posts_count, num_posts_after)
