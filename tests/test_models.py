from django.contrib.auth import get_user
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now
from app.models import Carfare, Comment, Driver, Place, Student, User, Carpool


class UserTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            username="mango", email="mango@example.com", password="pass0000"
        )
        User.objects.create(username="d1", password="pass0000", type=User.Types.DRIVER)
        User.objects.create(username="d2", password="pass0000", type=User.Types.DRIVER)
        User.objects.create(username="d3", password="pass0000", type=User.Types.DRIVER)

        User.objects.create(username="s1", password="pass0000", type=User.Types.STUDENT)
        User.objects.create(username="s2", password="pass0000", type=User.Types.STUDENT)
        User.objects.create(username="s3", password="pass0000", type=User.Types.STUDENT)
        User.objects.create(username="s4", password="pass0000", type=User.Types.STUDENT)

    def test_user_exist(self):
        self.assertIsNotNone(User.objects.get_by_natural_key(self.user.username))

    def test_user_type_is_none(self):
        self.assertEqual(self.user.type, User.Types.NONE)

    def test_user_profile_exist(self):
        self.assertIsNotNone(self.user.profile)

    def test_student_manager(self):
        self.assertEqual(Student.objects.count(), 4)

    def test_driver_manager(self):
        self.assertEqual(Driver.objects.count(), 3)

    def test_to_role_type(self):
        self.assertEqual(
            User.objects.get_by_natural_key(username="d1").to_driver(),
            Driver.objects.get_by_natural_key(username="d1"),
        )
        self.assertEqual(
            User.objects.get_by_natural_key(username="s1").to_student(),
            Student.objects.get_by_natural_key(username="s1"),
        )


class DriverTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.d1 = Driver.objects.create(
            username="d1", password="pass0000", type=User.Types.DRIVER
        )
        cls.d2 = Driver.objects.create(
            username="d2", password="pass0000", type=User.Types.DRIVER
        )

        cls.s1 = Student.objects.create(
            username="s1", password="pass0000", type=User.Types.STUDENT
        )
        cls.s2 = Student.objects.create(
            username="s2", password="pass0000", type=User.Types.STUDENT
        )
        cls.s3 = Student.objects.create(
            username="s3", password="pass0000", type=User.Types.STUDENT
        )

        Comment.objects.create(content="bad", score=1, critic=cls.s1, criticed=cls.d1)
        Comment.objects.create(content="best", score=5, critic=cls.s2, criticed=cls.d1)

        Comment.objects.create(content="good", score=4, critic=cls.s1, criticed=cls.d2)
        Comment.objects.create(content="best", score=5, critic=cls.s2, criticed=cls.d2)
        Comment.objects.create(content="sucks", score=1, critic=cls.s3, criticed=cls.d2)

    def test_driver_exists(self):
        self.assertEqual(Driver.objects.get_by_natural_key("d1"), self.d1)

    def test_driver_score(self):
        self.assertEqual(self.d1.score, round((1 + 5) / 2))
        self.assertEqual(self.d2.score, round((1 + 4 + 5) / 3))


class CarpoolTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.d1 = Driver.objects.create(
            username="d1", password="pass0000", type=User.Types.DRIVER
        )

        cls.s1 = Student.objects.create(
            username="s1", password="pass0000", type=User.Types.STUDENT
        )
        cls.s2 = Student.objects.create(
            username="s2", password="pass0000", type=User.Types.STUDENT
        )
        cls.s3 = Student.objects.create(
            username="s3", password="pass0000", type=User.Types.STUDENT
        )

        cls.p1 = Place.objects.create(name="Place 1")
        cls.p2 = Place.objects.create(name="Place 2")

        cls.cf1 = Carfare.objects.create(departure=cls.p1, arrival=cls.p2, fare=100)

        cls.cp1 = Carpool.objects.create(
            time=now(),
            carfare=cls.cf1,
            lower_passengers=9,
            driver=cls.d1,
        )
        cls.cp1.passengers.add(cls.s1, cls.s2, cls.s3)

    def test_carfare_shortcut_property(self):
        self.assertEqual(self.cp1.departure, self.p1.name)
        self.assertEqual(self.cp1.arrival, self.p2.name)
        self.assertEqual(self.cp1.fare, 100)
