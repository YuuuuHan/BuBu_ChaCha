from django.test import TestCase
from django.urls import reverse
from app.models import Profile, User
from django.contrib.auth import get_user


class SignUpAndLoginViewTestCase(TestCase):
    def setUp(self):
        User.objects.create_user(username="grape", password="pass0000")

    def test_view_exist(self):
        response = self.client.get(reverse("app:signup_and_login_student"))
        self.assertEqual(response.status_code, 200)

    def test_signup_student(self):
        response = self.client.post(
            reverse("app:signup_and_login_student"),
            data={
                "username": "banana",
                "password1": "pass0000",
                "password2": "pass0000",
                "email": "banana@example.com",
                "sex": Profile.SexTypes.MALE,
                "name": "banana man",
                "phone_num": "0900000000",
                "nickname": "banananick",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context)

        user = User.objects.get_by_natural_key("banana")
        self.assertIsNotNone(user.profile)

    def test_signup_driver(self):
        response = self.client.post(
            reverse("app:signup_and_login_driver"),
            data={
                "username": "apple",
                "password1": "pass0000",
                "password2": "pass0000",
                "email": "apple@example.com",
                "sex": Profile.SexTypes.FEMALE,
                "name": "apple girl",
                "phone_num": "0900000000",
                "cert_code": "A12345",
                "cert_expirydate": "2022-12-30",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context)

        user = User.objects.get_by_natural_key("apple")
        self.assertIsNotNone(user.profile)


class LoginLogoutTestCase(TestCase):
    def setUp(self):
        User.objects.create_user(username="grape", password="pass0000")

    def test_login(self):
        self.client.post(
            reverse("app:signup_and_login_student"),
            data={"username": "grape", "password": "pass0000"},
        )
        user = get_user(self.client)
        self.assertTrue(user.is_authenticated)

    def test_logout(self):
        user = get_user(self.client)
        response = self.client.get(reverse("app:logout"))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(user.is_authenticated)


class MyPasswordChangeView(TestCase):
    def setUp(self):
        User.objects.create_user(username="grape", password="pass0000")

    def test_password_change_get(self):
        response = self.client.get(reverse("app:password_change"))
        self.assertEqual(response.status_code, 302)

    def test_password_change_post(self):
        self.client.post(
            reverse("app:signup_and_login_student"),
            data={"username": "grape", "password": "pass0000"},
        )
        user = get_user(self.client)
        self.assertTrue(user.is_authenticated)
        response = self.client.post(
            reverse("app:password_change"),
            data={
                "old_password": "pass0000",
                "new_password1": "pass1111",
                "new_password2": "pass1111",
            },
        )
        self.assertEqual(response.status_code, 302)
        # update user password changed
        user = get_user(self.client)
        self.assertTrue(user.check_password("pass1111"))
