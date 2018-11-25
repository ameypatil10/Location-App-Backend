"""myApp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.urls import path
from . import views

app_name = 'SpotMe'

urlpatterns = [
    # Instructor URLS 
    url(r'^$', views.index, name='index'),
    url(r'^index/$', views.index, name='index'),
    url(r'^reg/$', views.instructor_register, name='instructor_register'),
    url(r'^login/$', views.instructor_login, name='instructor_login'),
    url(r'^logout/$', views.instructor_logout, name='instructor_logout'),
    url(r'^home/$', views.instructor_home, name='instructor_home'),
    url(r'^profile/$', views.instructor_profile, name='instructor_profile'),
    url(r'^course_session/(?P<course_session_id>[0-9]+)/$', views.instructor_course_page, name='instructor_course_page'),
    url(r'^add_course_session/$', views.instructor_add_course_session, name='instructor_add_course_session'),
    url(r'^lecture/(?P<lecture_id>[0-9]+)/$', views.instructor_lecture_page, name='instructor_lecture_page'),
    url(r'^add_lecture/(?P<course_session_id>[0-9]+)/$', views.instructor_add_lecture, name='instructor_add_lecture'),

    # Student URLS 
    url(r'^sreg/$', views.student_register, name='student_register'),
    url(r'^slogin/$', views.student_login, name='student_login'),
    url(r'^slogout/$', views.student_logout, name='student_logout'),
    url(r'^shome/$', views.student_home, name='student_home'),
    url(r'^scourse_register/$', views.student_register_course, name='student_register_course'),
    url(r'^scourse_details/$', views.student_course_details, name='student_course_details'),
    url(r'^sprofile/$', views.student_profile, name='student_profile'),
    url(r'^get_location/$', views.get_location, name='get_location'),

    # General URLS 
    url(r'^add_location/$', views.add_location, name='add_location'),
    url(r'^list_location/$', views.list_location, name='list_location'),
    url(r'^ping/$', views.ping, name='ping'),
    url(r'^location_data/$', views.location_data, name='location_data'),
    
]