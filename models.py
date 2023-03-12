from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
import datetime
from django.utils.timezone import now
from django.core.exceptions import ObjectDoesNotExist


class User(AbstractUser):
    class Types(models.TextChoices):
        STUDENT = "STUDENT", "Student"
        DRIVER = "DRIVER", "Driver"
        NONE = "NONE", "None"

    # 使用者類型：學生 or 司機
    type = models.CharField(
        max_length=50,
        choices=Types.choices,
        default=Types.NONE,
        verbose_name="user type",
    )

    def is_student(self):
        return self.type == self.Types.STUDENT

    def is_driver(self):
        return self.type == self.Types.DRIVER

    def to_student(self):
        try:
            return Student.objects.get(pk=self.pk)
        except ObjectDoesNotExist:
            return None

    def to_driver(self):
        try:
            return Driver.objects.get(pk=self.pk)
        except ObjectDoesNotExist:
            return None

    @property
    def current_carpool(self):
        if self.is_student():
            return (
                self.to_student()
                .student_carpools.filter(status="w")
                .order_by("date")
                .first()
            )
        elif self.is_driver():
            return self.to_driver().driver_carpools.filter(status="w").last()

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"username": self.username})


class StudentManager(UserManager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(type=User.Types.STUDENT)


class DriverManager(UserManager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(type=User.Types.DRIVER)


class Student(User):
    objects = StudentManager()

    class Meta:
        proxy = True

    def __str__(self):
        """String for representing the Student object."""
        return self.username


class Driver(User):
    objects = DriverManager()

    class Meta:
        proxy = True

    @property
    def score(self):
        # from Comment model "related_name"
        score = self.driver_comments.aggregate(models.Avg("score")).get("score__avg")
        if score:
            return round(score)
        else:
            return None


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # 性別，預設為男性
    class SexTypes(models.TextChoices):
        MALE = "MALE", "生理男"
        FEMALE = "FEMALE", "生理女"

    base_type = SexTypes.MALE
    sex = models.CharField(
        max_length=10, choices=SexTypes.choices, default=base_type, verbose_name="sex"
    )
    # 姓名
    name = models.CharField(max_length=8, verbose_name="name")
    # 手機號碼
    phone_num = models.CharField(
        max_length=10,
        validators=[RegexValidator(regex=r"^09\d{8}$", message="手機號碼格式輸入錯誤！")],
        verbose_name="phone number",
    )

    """ Driver Only """
    # 隸屬公司
    company = models.CharField(max_length=25, blank=True, verbose_name="company")
    # 執業登記證號
    cert_code = models.CharField(
        max_length=7,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^(?=.{7}$)[a-zA-Z]{1,}\d{1,}$", message="登記證證號格式輸入錯誤！"
            )
        ],
        verbose_name="certificate code",
    )
    # 執業登記證號到期日
    cert_expirydate = models.DateField(
        null=True, blank=True, verbose_name="certificate expiration date"
    )


@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, **kwargs):
    if created and not hasattr(instance, "profile"):
        Profile.objects.create(user=instance)
    instance.profile.save()


class Car(models.Model):
    capacity = models.IntegerField(
        default=3,
        validators=[MaxValueValidator(9), MinValueValidator(3)],
        verbose_name="car capacity",
    )
    plate = models.CharField(
        max_length=8,
        verbose_name="car plate number",
        validators=[RegexValidator(regex=r"^[A-Z]{3}\-\d{4}$", message="車牌號碼格式輸入錯誤！")],
    )

    UTILITY_CHOICES = (
        ("n", "一般轎車"),  # 1
        ("e", "環保電動車"),  # 0.9
        ("l", "豪華轎車"),  # 1.5
        ("a", "無障礙汽車"),  # 1
    )

    type = models.CharField(
        max_length=1,
        choices=UTILITY_CHOICES,
        default="n",
        verbose_name="car utility type",
    )

    # relations one to one
    driver = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=False)

    class Meta:
        ordering = ["type", "capacity"]


class Place(models.Model):
    """Model representing a place"""

    # 地點名稱
    name = models.CharField(
        max_length=50,
        verbose_name="place name",
    )

    def __str__(self):
        """String for representing the Place object."""
        return self.name


class Comment(models.Model):
    """Model representing a comment"""

    time = models.DateTimeField(
        default=now, help_text="Enter a time you want to take a car"
    )
    content = models.TextField()
    score = models.IntegerField(validators=[MaxValueValidator(5), MinValueValidator(1)])

    # relations many to one
    critic = models.ForeignKey(
        Student, on_delete=models.SET_NULL, null=True, related_name="student_comments"
    )
    criticed = models.ForeignKey(
        Driver, on_delete=models.SET_NULL, null=True, related_name="driver_comments"
    )

    def __str__(self):
        """String for representing the Comment object."""
        return self.content


class Carfare(models.Model):
    """Model representing a carfare"""

    # relations many to one
    # 出發地
    departure = models.ForeignKey(
        Place,
        on_delete=models.SET_NULL,
        null=True,
        related_name="departure_fares",
        verbose_name="departure",
    )
    # 目的地
    arrival = models.ForeignKey(
        Place,
        on_delete=models.SET_NULL,
        null=True,
        related_name="arrival_fares",
        verbose_name="arrival",
    )

    # 車資
    fare = models.PositiveIntegerField(verbose_name="fare")

    class Meta:
        ordering = ["departure", "arrival"]

    def __str__(self):
        """String for representing the Place object."""
        return f"{self.departure} -> {self.arrival}: {self.fare}"


class Carpool(models.Model):
    """Model representing a carpool."""

    date = models.DateField(default="2022-12-21")
    time = models.TimeField(default="21:24")

    carfare = models.ForeignKey(Carfare, on_delete=models.SET_NULL, null=True)
    lower_passengers = models.IntegerField()

    # relations many to one
    driver = models.ForeignKey(
        Driver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="driver_carpools",
    )

    # relations many to many
    passengers = models.ManyToManyField(
        Student, related_name="student_carpools", blank=True
    )

    STATUS_CHOICES = (
        ("w", "Waiting"),
        ("d", "Driving"),
        ("a", "Arrived"),
    )

    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default="w")

    class Meta:
        ordering = ["date", "time"]

    @property
    def departure(self):
        return self.carfare.departure.name

    @property
    def arrival(self):
        return self.carfare.arrival.name

    @property
    def fare(self):
        return self.carfare.fare

    @property
    def has_vacancy(self):
        if not self.driver:
            return True
        return self.driver.car.capacity > self.passengers.count()

    @property
    def has_driver(self):
        if self.driver:
            return True
        else:
            return False

    # def is_overdue(self):
    #     if self.time >= datetime.datetime.today():
    #         return False
    #     return True

    @property
    def avg_fare(self):
        total_passengers = self.passengers.count()
        if total_passengers == 0:
            return None
        return round(self.carfare.fare / self.passengers.count())

    def is_student_in(self, student):
        if student is None:
            return False
        try:
            self.passengers.get(username=student.username)
            return True
        except ObjectDoesNotExist:
            return False

    def is_driver_in(self, driver):
        return self.driver == driver

    def is_user_in(self, user):
        if user and user.is_student():
            return self.is_student_in(user)
        else:
            return self.is_driver_in(user)

    def __str__(self):
        """String for representing the Carpool object."""
        return f"s: {self.status} {self.time}, {self.departure} to {self.arrival}"

    def get_absolute_url(self):
        """Returns the url to access a detail record for this carpool."""
        return reverse("app:carpool-detail", args=[str(self.id)])
