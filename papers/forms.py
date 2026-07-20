from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import ReadingRecord


class SignupForm(UserCreationForm):
    email = forms.EmailField(label="이메일", required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("이미 사용 중인 이메일입니다.")
        return email


class PaperSearchForm(forms.Form):
    keyword = forms.CharField(
        label="관심 의학 키워드",
        max_length=500,
        widget=forms.TextInput(
            attrs={
                "placeholder": "예: cerebral amyloid angiopathy",
                "autocomplete": "off",
            }
        ),
    )
    days = forms.IntegerField(
        label="최근 검색 기간(일)", min_value=1, max_value=365, initial=30
    )
    max_results = forms.IntegerField(
        label="최대 논문 수", min_value=1, max_value=100, initial=10
    )


class ReadingRecordForm(forms.ModelForm):
    read_at = forms.DateTimeField(
        label="읽은 날짜와 시간",
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local"}
        ),
        input_formats=["%Y-%m-%dT%H:%M"],
    )

    class Meta:
        model = ReadingRecord
        fields = ("read_at", "rating", "note")
        labels = {"rating": "별점", "note": "내 메모"}
        widgets = {
            "rating": forms.Select(
                choices=[("", "선택 안 함")] + [(i, f"{i}점") for i in range(1, 6)]
            ),
            "note": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "이 논문에서 기억하고 싶은 점을 적어보세요.",
                }
            ),
        }


class UsernameRecoveryForm(forms.Form):
    email = forms.EmailField(
        label="가입할 때 사용한 이메일",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "name@example.com",
                "autocomplete": "email",
            }
        ),
    )

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()
