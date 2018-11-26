from django.contrib.auth.models import User
from django import forms
from datetime import datetime
from .models import *

SEM_CHOICES = (
    ('FALL', 'Fall'),
    ('AUTUMN', 'Autumn'),
)
YEAR_CHOICES = [(r,r) for r in range(2012, datetime.date.today().year+1)]

## \brief RegisterForm for new users to register into IITB-Portal.
class RegisterForm(forms.ModelForm):

    username = forms.CharField(max_length=20, required=True)
    first_name = forms.CharField(max_length=20, required=False)
    last_name = forms.CharField(max_length=20, required=False)
    email = forms.CharField(required=False)

    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    profile_pic = forms.FileField(required=False)


    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password', 'confirm_password', 'profile_pic']

    def clean(self):
        cleaned_data = super(RegisterForm, self).clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password != confirm_password:
            self.add_error('confirm_password', "Password does not match")
        return cleaned_data

## \brief RegisterForm for new users to register into IITB-Portal.
class LoginForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'password']


class AddCourseSession(forms.ModelForm):
    course_id = forms.CharField()
    class Meta:
        model = course_session
        fields = ['course_session_info', 'semester', 'year']

class AddLecture(forms.ModelForm):
    location_id = forms.IntegerField()
    lecture_title = forms.CharField()    
    lecture_date = forms.DateField()
    start_time = forms.TimeField()
    end_time = forms.TimeField()

    class Meta:
        model = lecture
        fields = ['lecture_title', 'start_time', 'end_time', 'lecture_date']

    def clean(self):
        cleaned_data = super(AddLecture, self).clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")
        if start_time > end_time:
            self.add_error('end_time', "End time must be greater than start time")
        return cleaned_data
