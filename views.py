from django.contrib.auth.views import PasswordChangeView
from django.db.models import Q, F, Count
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.timezone import now
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView
from django.contrib.auth import get_user, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import (
    Carpool,
    Comment,
    Place,
    User,
    Driver,
)
from .forms import (
    CarForm,
    SignUpForm,
    StudentForm,
    DriverForm,
    CarpoolForm,
    CommentForm,
    LoginForm,
    CarpoolFilterForm,
)
from django.views import generic
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect
from datetime import date


def index(request):
    context = {"test": "Hello world"}
    return render(request, "app/index.html", context)


class SignUpAndLoginView(TemplateView):
    template_name = "app/signup_and_login.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
        if self.user_type == User.Types.STUDENT:
            self.ProfileForm = StudentForm
        else:
            self.ProfileForm = DriverForm

    def get(self, request):
        signup_form = SignUpForm()
        login_form = LoginForm()
        car_form = CarForm()
        profile_form = self.ProfileForm()

        return render(
            request,
            self.template_name,
            {
                "signup_form": signup_form,
                "profile_form": profile_form,
                "login_form": login_form,
                "car_form": car_form,
                "is_student_signup": self.user_type == User.Types.STUDENT,
            },
        )

    def post(self, request):
        signup_form = SignUpForm(request.POST)
        profile_form = self.ProfileForm(request.POST)
        login_form = LoginForm(data=request.POST)
        car_form = CarForm(request.POST)

        if login_form.is_valid():
            login(self.request, login_form.get_user())
            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()
            return redirect(reverse("app:carpools"))

        if signup_form.is_valid() and profile_form.is_valid():
            if self.user_type == User.Types.DRIVER and car_form.is_valid():
                user = signup_form.save()
                # 很糟的寫法，可能要另外做CustomUserCreationForm
                user.type = self.user_type
                user.save()
                user.refresh_from_db()
                profile_form = self.ProfileForm(request.POST, instance=user.profile)
                profile_form.full_clean()
                profile_form.save()

                # 車子資訊
                car_form = CarForm(request.POST)
                car = car_form.save(commit=False)
                car.driver = user
                car_form.save()
                return redirect(reverse("app:signup_and_login_driver"))
            elif self.user_type == User.Types.STUDENT:
                user = signup_form.save()
                # 很糟的寫法，可能要另外做CustomUserCreationForm
                user.type = self.user_type
                user.save()
                user.refresh_from_db()
                profile_form = self.ProfileForm(request.POST, instance=user.profile)
                profile_form.full_clean()
                profile_form.save()
                return redirect(reverse("app:signup_and_login_student"))

        error = None
        login_error = None
        if request.POST.get("company", None) is not None:
            # 是註冊，要把登入錯誤移除
            login_form = LoginForm()
            error = "註冊表單錯誤"
        else:
            # 是登入，要把註冊的錯誤移除
            signup_form = SignUpForm()
            profile_form = self.ProfileForm()
            car_form = CarForm()
            error = "登入表單錯誤"
            login_error = "輸入正確的使用者名稱和密碼。請注意兩者皆區分大小寫。"

        return render(
            request,
            self.template_name,
            {
                "signup_form": signup_form,
                "profile_form": profile_form,
                "login_form": login_form,
                "car_form": car_form,
                "messages": messages,
                "is_student_signup": self.user_type == User.Types.STUDENT,
                "error": error,
                "login_error": login_error,
            },
        )


class StudentSignUpAndLoginView(SignUpAndLoginView):
    def __init__(self):
        super().__init__(user_type=User.Types.STUDENT)


class DriverSignUpAndLoginView(SignUpAndLoginView):
    def __init__(self):
        super().__init__(user_type=User.Types.DRIVER)


def carpool_create(request):

    if request.method == "POST":
        form = CarpoolForm(request.POST)
        if form.is_valid():
            cp_object = form.save()
            cp_object.passengers.add(request.user.to_student())
            return HttpResponse(
                status=204, headers={"HX-Trigger": "carpoolListChanged"}
            )
    else:
        form = CarpoolForm()

    return render(request, "app/carpool_create.html", {"form": form})


class CarpoolListView(generic.ListView):
    model = Carpool
    template_name = "app/carpool_list.html"

    def get_context_data(self, **kwargs):
        context = super(CarpoolListView, self).get_context_data(**kwargs)
        context["form"] = CarpoolFilterForm()
        return context


# ajax 動態更新carpool_list
def carpool_list_region(request):
    carpools = None

    if request.GET.get("filter_is_user_in", False) == "True":
        if request.user.is_authenticated:
            if request.user.is_student():
                queryset = request.user.to_student().student_carpools
            else:
                queryset = request.user.to_driver().driver_carpools
            carpools = (
                queryset.filter(date__gte=date.today(), status="w")
                .order_by("date")
                .all()
            )
    else:
        form = CarpoolFilterForm(request.GET)
        if form.is_valid():
            date_ = form.cleaned_data["date"]
            time = form.cleaned_data["time"]
            carfare = form.cleaned_data["carfare"]
            already_in = form.cleaned_data["already_in"]
            has_vacancy = form.cleaned_data["has_vacancy"]
            has_driver = form.cleaned_data["has_driver"]

            f = Carpool.objects.filter(date=date_, status="w")
            f = f.annotate(num_passengers=Count("passengers")).filter(
                num_passengers__gte=already_in
            )
            if has_driver:
                f = f.filter(~Q(driver=None))
                if has_vacancy:
                    f = f.filter(num_passengers__lt=F("driver__car__capacity"))
            if time is not None:
                f = f.filter(time__gte=time)
            if carfare is not None:
                f = f.filter(carfare=carfare)
            carpools = f.order_by("date").all()

    if carpools is None:
        carpools = (
            Carpool.objects.filter(date__gte=date.today(), status="w")
            .annotate(num_passengers=Count("passengers"))
            .filter(num_passengers__gt=0)
            .order_by("date")
            .all()
        )

    if request.user.is_authenticated:
        for c in carpools:
            c.is_user_in = c.is_user_in(request.user)

    return render(
        request,
        "app/carpool_list_region.html",
        {
            "carpools": carpools,
        },
    )


class CarpoolDetailView(generic.DetailView):
    model = Carpool
    template_name = "app/carpool_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[
            "is_student_in"
        ] = self.request.user.is_authenticated and self.object.is_user_in(
            self.request.user
        )
        return context

    def get(self, request, pk, *args, **kwargs):
        carpool_inst = get_object_or_404(Carpool, pk=pk)
        if carpool_inst.status == "a":
            return HttpResponse("你不能看")
        return super().get(request, *args, **kwargs)

    def post(self, request, pk):
        carpool_inst = get_object_or_404(Carpool, pk=pk)
        user = self.request.user

        # 加入按鈕
        if request.method == "POST" and "join" in request.POST:
            # 司機
            if user.is_driver():
                if carpool_inst.driver:
                    messages.warning(request, "已有司機!")
                elif user.current_carpool:
                    messages.warning(request, "已接其他共乘團!")
                elif user.car.capacity <= carpool_inst.passengers.count():
                    messages.warning(request, "車輛空間不足!")
                else:
                    messages.warning(request, "成功承接共乘團!")
                    carpool_inst.driver = user.to_driver()
                    carpool_inst.save()
            # 乘客
            else:
                all_passengers = carpool_inst.passengers.all()
                is_embark = False
                # 尋找所有乘客
                for temp in all_passengers:
                    if temp == user:
                        is_embark = True
                # 若還沒上車則允許上車
                embark_user = user.to_student()
                if is_embark:
                    messages.warning(request, "您已經加入共乘團!")
                elif carpool_inst.passengers.count() >= 9 or (
                    carpool_inst.driver
                    and carpool_inst.passengers.count()
                    >= carpool_inst.driver.car.capacity
                ):
                    messages.warning(request, "沒位置了!")
                else:
                    carpool_inst.passengers.add(embark_user)
                    messages.warning(request, "加入共乘團!")

        # 退出按鈕
        if request.method == "POST" and "leave" in request.POST:
            if user.is_student():
                if carpool_inst.passengers.count() == 1 and carpool_inst.is_student_in(
                    user
                ):
                    carpool_inst.delete()
                    return HttpResponseRedirect(reverse("app:carpools"))
                carpool_inst.passengers.remove(user.id)
                messages.warning(request, "退出共乘團!")

        return HttpResponseRedirect(request.path_info)


class CarpoolHistoryListView(generic.ListView, LoginRequiredMixin):
    template_name = "app/carpool_history.html"

    def get_queryset(self):
        user = get_user(self.request)
        if user.is_anonymous:
            return None

        if user.is_student():
            user = user.to_student()
            queryset = user.student_carpools.filter(status="a")
        else:
            queryset = user.driver_carpools
        return queryset


class DriverListView(generic.ListView):
    model = Driver
    template_name = "app/driver_list.html"


class DriverReviewView(generic.DetailView):
    model = Driver
    template_name = "app/driver_review.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comment_form"] = CommentForm(instance=context["object"])
        return context


def delete_comment_view(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    comment.delete()

    url = request.META.get("HTTP_REFERER", reverse("app:index"))

    return redirect(url)


def edit_comment_view(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    url = request.META.get("HTTP_REFERER", reverse("app:index"))

    form = CommentForm(request.POST, instance=comment)
    if form.is_valid():
        form.instance.time = now()
        form.save()
        return redirect(url)

    return HttpResponse("編輯失敗")


def carpool_change_status_view(request, pk):
    carpool = get_object_or_404(Carpool, pk=pk)
    if carpool.driver != request.user.to_driver():
        return HttpResponse("you are not the driver")

    if carpool.status == "w":
        status = "d"  # Driving
    elif carpool.status == "d":
        status = "a"  # Arrived
    else:
        return HttpResponse("Already arrived")
    carpool.status = status
    carpool.save()

    return render(
        request,
        template_name="app/htmx/carpool_change_status.html",
        context={"carpool": carpool},
    )


def carpool_update_status_view(request, pk):
    carpool = get_object_or_404(Carpool, pk=pk)
    if request.user.is_authenticated and not carpool.is_student_in(
        request.user.to_student()
    ):
        return HttpResponse("You are not in this carpool")

    if carpool.status == "a":
        request.driver = carpool.driver
        return CommentCreateView.as_view()(request, driver=carpool.driver)
    else:
        return HttpResponse("waiting or driving")


class CommentCreateView(CreateView, LoginRequiredMixin):
    template_name = "app/htmx/create_comment.html"
    model = Comment
    fields = ["content", "score"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["driver"] = self.request.driver
        self.request.session["driver_username"] = self.request.driver.username
        return context

    def form_valid(self, form):
        comment = form.save(commit=False)

        driver = Driver.objects.get_by_natural_key(
            username=self.request.session.get("driver_username")
        )
        print(driver)
        user = get_user(self.request)
        student = user.to_student()

        comment.criticed = driver
        comment.critic = student
        comment.time = now()
        comment.save()
        del self.request.session["driver_username"]

        return super().form_valid(form)

    def form_invalid(self, form):
        print(form.errors)
        return HttpResponse(form.errors)

    def get_success_url(self):
        return reverse("app:carpools")


@login_required
def logout_view(request):
    logout(request)
    return redirect(reverse("app:index"))


def aboutus_view(request):
    return render(request, template_name="app/aboutus.html")


class PriceView(generic.ListView):
    model = Place
    template_name = "app/price.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        return context


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "app/profile.html"

    def get(self, request):
        user = self.request.user
        if request.method == "POST":
            return super().get(request)

        if user.is_student():
            self.ProfileForm = StudentForm
        else:
            self.ProfileForm = DriverForm

        self.profile_form = self.ProfileForm(instance=user.profile)
        if user.type == User.Types.DRIVER:
            self.car_form = CarForm(instance=user.car)

        return super().get(request)

    def post(self, request):
        user = self.request.user
        if user.is_student():
            self.ProfileForm = StudentForm
        else:
            self.ProfileForm = DriverForm

        self.profile_form = self.ProfileForm(
            instance=user.profile, data=self.request.POST
        )
        if user.is_driver():
            self.car_form = CarForm(instance=user.car, data=self.request.POST)
            if self.profile_form.is_valid() and self.car_form.is_valid():
                self.profile_form.save()
                self.car_form.save()
        else:
            if self.profile_form.is_valid():
                self.profile_form.save()

        return self.get(request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["profile_form"] = self.profile_form
        if hasattr(self, "car_form"):
            context["car_form"] = self.car_form
        return context


class MyPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = "app/password_change.html"

    def get_success_url(self):
        return reverse("app:index")
