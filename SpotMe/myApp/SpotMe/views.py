from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from SpotMe.models import *
from django.contrib.auth.models import User
from .forms import *
from django.views.decorators.csrf import csrf_exempt
import datetime
from django.utils.crypto import get_random_string
from django.db import connection


def dictfetchall(cursor):
    #"Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


SEM_CHOICES = (
    ('FALL', 'Fall'),
    ('AUTUMN', 'Autumn'),
)
YEAR_CHOICES = [(r,r) for r in range(2012, datetime.date.today().year+1)]

# Create your views here.
##################################################### GET CONTEXT DEFS ###############################################################
def instructor_home_context(instructor):
    context = { 'instructor': None, 'instructor_courses': None}
    if instructor is not None:
        if instructor.user.is_authenticated:
            context['instructor'] = instructor
            context['instructor_courses'] = course_session.objects.filter(course_instructor=instructor)
    return context

def instructor_course_page_context(instructor, course_session_id):
    context = {'instructor': None, 'course_session': None, 'course_lectures': None}
    if instructor is not None:
        if instructor.user.is_authenticated:
            context['instructor'] = instructor
            course_session_obj = get_object_or_404(course_session, pk=course_session_id)
            context['course_session'] = course_session_obj
            if course_session_obj is not None:
                context['course_lectures'] = lecture.objects.filter(course_session=course_session_obj)
    return context

def instructor_lecture_page_context(instructor, lecture_id):
    context = {'instructor': None, 'course_session': None, 'lecture': None}
    if instructor is not None:
        if instructor.user.is_authenticated:
            context['instructor'] = instructor
            lecture_obj = get_object_or_404(lecture, pk=lecture_id)
            if lecture_obj is not None:
                context['course_session'] = lecture.course_session
                context['lecture'] = lecture_obj
    return context

############################################################ VIEWS ####################################################################
def index(request):
    if request.user.is_authenticated:
        instructor_obj = get_object_or_404(instructor, user=request.user)
        return render(request, 'SpotMe/instructor_home.html', instructor_home_context(instructor_obj))
    else:
        return render(request, 'SpotMe/index.html')

def instructor_register(request):
    form = RegisterForm(request.POST or None)
    context = {'form': form}
    if form.is_valid():
        form.save()
        user = form.save(commit=False)
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user.set_password(password)
        user.first_name = form.cleaned_data['first_name']
        user.last_name = form.cleaned_data['last_name']
        user.email = form.cleaned_data['email']
        user.save()
        instructor_obj = instructor.create(user=user)
        instructor_obj.profile_pic = form.cleaned_data['profile_pic']
        instructor_obj.save()
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return render(request, 'SpotMe/instructor_home.html', instructor_home_context(instructor_obj))
    return render(request, 'SpotMe/instructor_register.html', context)

def instructor_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                try:
                    instructor_obj = get_object_or_404(instructor, user=user)
                except:
                    return render(request, 'SpotMe/instructor_login.html')
                if instructor_obj is not None:
                    login(request, user)
                    instructor_obj = get_object_or_404(instructor, user=request.user)
                    return render(request, 'SpotMe/instructor_home.html', instructor_home_context(instructor_obj))
            else:
                return render(request, 'SpotMe/instructor_login.html', {'error_message': 'Your account has been disabled'})
        else:
            return render(request, 'SpotMe/instructor_login.html', {'error_message': 'Invalid login credentials'})
    return render(request, 'SpotMe/instructor_login.html')

def instructor_logout(request):
    logout(request)
    return render(request, 'SpotMe/index.html')

def instructor_profile(request):
    if not request.user.is_authenticated:
        return render(request, 'SpotMe/instructor_login.html')
    else:
        instructor_obj = get_object_or_404(instructor, user=request.user)
        context = {'instructor': instructor_obj}
        return render(request, 'SpotMe/instructor_profile.html', context)

def edit_instructor_profile(request):
    pass

def instructor_home(request):
    if not request.user.is_authenticated:
        return render(request, 'SpotMe/instructor_login.html')
    else:
        instructor_obj = get_object_or_404(instructor, user=request.user)
        return render(request, 'SpotMe/instructor_home.html', instructor_home_context(instructor_obj))

def instructor_add_course_session(request):
    if not request.user.is_authenticated:
        return render(request, 'SpotMe/instructor_login.html')
    else:
        instructor_obj = get_object_or_404(instructor, user=request.user)
        form = AddCourseSession(request.POST or None)
        context = {'form': form, 'instructor': instructor_obj}
        context['course_list'] = course.objects.all()
        context['semester_list'] = SEM_CHOICES
        context['year_list'] = YEAR_CHOICES
        if form.is_valid():
            course_id = form.cleaned_data['course_id']
            year = form.cleaned_data['year']
            semester = form.cleaned_data['semester']
            course_session_info = form.cleaned_data['course_session_info']
            course_obj = get_object_or_404(course, course_id=course_id)
            form.course = course_obj
            form.instructor = instructor_obj
            session_token = get_random_string(10)
            course_session_obj = course_session(course_instructor=instructor_obj, session_token=session_token,
            course=course_obj, year=year, semester=semester, course_session_info=course_session_info)
            course_session_obj.save()
            return render(request, 'SpotMe/instructor_home.html', instructor_home_context(instructor_obj))
        return render(request, 'SpotMe/instructor_add_course_session.html', context)

def instructor_add_lecture(request, course_session_id):
    if not request.user.is_authenticated:
        return render(request, 'SpotMe/instructor_login.html')
    else:
        instructor_obj = get_object_or_404(instructor, user=request.user)
        course_session_obj = get_object_or_404(course_session, pk=course_session_id)
        form = AddLecture(request.POST or None)
        context = {'form': form, 'instructor': instructor_obj, 'course_session': course_session_obj}
        context['location_list'] = location.objects.all()
        if form.is_valid():
            location_id = form.cleaned_data['location_id']
            lecture_title = form.cleaned_data['lecture_title']
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']
            location_obj = get_object_or_404(location, location_id=location_id)
            lecture_obj = lecture(lecture_location=location_obj, course_session=course_session_obj, 
            lecture_title=lecture_title, start_time=start_time, end_time=end_time)
            lecture_obj.save()
            return render(request, 'SpotMe/instructor_course_page.html', instructor_course_page_context(instructor_obj, course_session_id))
        return render(request, 'SpotMe/instructor_add_lecture.html', context)

def instructor_course_page(request, course_session_id):
    if not request.user.is_authenticated:
        return render(request, 'SpotMe/instructor_login.html')
    else:
        instructor_obj = get_object_or_404(instructor, user=request.user)
        context = instructor_course_page_context(instructor_obj, course_session_id)
        return render(request, 'SpotMe/instructor_course_page.html', context)

def instructor_lecture_page(request, lecture_id):
    if not request.user.is_authenticated:
        return render(request, 'SpotMe/instructor_login.html')
    else:
        instructor_obj = get_object_or_404(instructor, user=request.user)
        context = instructor_lecture_page_context(instructor_obj, lecture_id)
        return render(request, 'SpotMe/instructor_lecture_page.html', context)

@csrf_exempt
def student_login(request):
    context = {'status': False}
    if request.method == "POST":
        username = request.POST['userid']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                try:
                    student_obj = get_object_or_404(student, user=user)
                except:
                    return JsonResponse(context)
                if student_obj is not None:
                    login(request, user)
                    context['userid'] = user.username
                    context['status'] = True
                    return JsonResponse(context)
            else:
                context['error_msg'] = 'Your account has been disabled'
                return JsonResponse(context)
        else:
            context['error_msg'] = 'Invalid login credentials'
            return JsonResponse(context)
    return JsonResponse(context)

@csrf_exempt
def student_logout(request):
    context = {'status': False}
    print('out')
    if not request.user.is_authenticated:
        print('not logged in')
        return JsonResponse(context)
    else:
        logout(request)
        print('Done')
        context['status'] = True
    return JsonResponse(context)

@csrf_exempt
def student_register(request):
    context = {'status': False}
    if(request.method == 'POST'):
        userid = request.POST['userid']
        password = request.POST['password']
        user = User(username = userid)
        user.set_password(password)
        user.save()
        student_obj = student.create(user=user)
        student_obj.save()
        user = authenticate(username=userid, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                context['userid'] = user.username
                context['status'] = True
                return JsonResponse(context)
        context['status'] = False

    # form = RegisterForm(request.POST or None)
    # context = {'form': form}
    # if form.is_valid():
    #     form.save()
    #     user = form.save(commit=False)
    #     username = form.cleaned_data['username']
    #     password = form.cleaned_data['password']
    #     user.set_password(password)
    #     user.first_name = form.cleaned_data['first_name']
    #     user.last_name = form.cleaned_data['last_name']
    #     user.email = form.cleaned_data['email']
    #     user.save()
    #     instructor_obj = instructor.create(user=user)
    #     instructor_obj.profile_pic = form.cleaned_data['profile_pic']
    #     instructor_obj.save()
    #     user = authenticate(username=username, password=password)
    #     if user is not None:
    #         if user.is_active:
    #             login(request, user)
    #             return render(request, 'SpotMe/instructor_home.html', instructor_home_context(instructor_obj))



        
        return JsonResponse(context)

# def course_detail(request):
#     if request.method == "GET":
#         username = request.GET['username']
#         password = request.GET['password']
#         user = authenticate(username=username, password=password)
#         context = {'status': 'false'}
#         if user is not None:
#             if user.is_active:
#                 login(request, user)
#                 student_obj = get_object_or_404(student, user=request.user)
#                 context['username'] = student_obj.user.username
#                 return JsonResponse(context)
#             else:
#                 context['error_message'] = 'Your account has been disabled'
#                 return JsonResponse(context)
#         else:
#             context['error_message'] = 'Invalid login credentials'
#             return JsonResponse(context)
#     return JsonResponse({'FUN': 'Bitches have fun!'})


def lecture_detail(request):
    pass

def get_location(request, scan_data):
    pass

@csrf_exempt
def student_home(request):
    context = {'status': False}
    if not request.user or not request.user.is_authenticated:
        context['error_msg'] = 'User not logged in'
        return JsonResponse(context)
    else:
        user = request.user
        student_obj = student.objects.get(user=user) 
        # print(student_obj.id)

        with connection.cursor() as cursor:
            cursor.execute("""SELECT SpotMe_course.course_id, SpotMe_course.course_name,
                SpotMe_takes.id as takes_id, auth_user.first_name as instructor
                FROM SpotMe_takes, auth_user, SpotMe_course_session, SpotMe_instructor, SpotMe_course 
                WHERE auth_user.id = SpotMe_instructor.user_id 
                AND SpotMe_takes.course_session_id = SpotMe_course_session.id 
                AND SpotMe_course_session.course_id = SpotMe_course.id 
                AND SpotMe_instructor.id =  SpotMe_course_session.course_instructor_id 
                AND SpotMe_takes.student_id = %s""", [student_obj.id])
            row = dictfetchall(cursor)
            context['data'] = row
            context['status'] = True
            context['userid'] = user.username
            return JsonResponse(context)
    return JsonResponse(context)

@csrf_exempt
def student_course_details(request):
    context = {'status': False}
    takes_id = request.GET['takes_id']
    if not request.user or not request.user.is_authenticated:
        context['error_msg'] = 'User not logged in'
        return JsonResponse(context)
    elif takes_id is None:
        context['error_msg'] = 'No takes_id provided'
        return JsonResponse(context)
    elif request.method == 'POST':
        context['error_msg'] = 'Needed GET request, done POST request'
        return JsonResponse(context)
    elif request.method == 'GET':
        user = request.user
        takes_id = request.GET['takes_id']
        # student_obj = student.objects.get(user=user)

        with connection.cursor() as cursor:
            cursor.execute("""SELECT *
                FROM SpotMe_takes, auth_user, SpotMe_course_session,
                SpotMe_instructor, SpotMe_course, SpotMe_lecture
                WHERE auth_user.id = SpotMe_instructor.user_id
                AND SpotMe_lecture.course_session_id = SpotMe_course_session.id 
                AND SpotMe_takes.course_session_id = SpotMe_course_session.id 
                AND SpotMe_course_session.course_id = SpotMe_course.id 
                AND SpotMe_instructor.id =  SpotMe_course_session.course_instructor_id 
                AND SpotMe_takes.id = %s""", [takes_id])
            row = dictfetchall(cursor)
            context['data'] = row
            context['status'] = True
            context['userid'] = user.username
            return JsonResponse(context)
    return JsonResponse(context)


@csrf_exempt
def student_register_course(request):
    context = {'status': False}
    if not request.user or not request.user.is_authenticated:
        context['error_msg'] = 'User not logged in'
        return JsonResponse(context)
    else:
        user = request.user
        student_obj = get_object_or_404(student, user=user)
        if request.POST:
            course_id = request.POST['course_id']
            session_token = request.POST['session_token']
            print(course_id, session_token)
            try:
                course_obj = get_object_or_404(course, course_id=course_id)
                course_session_obj = get_object_or_404(course_session, course=course_obj, session_token=session_token)
                takes_obj = takes(student=student_obj, course_session=course_session_obj)
                takes_obj.save()
            except Exception as e:
                context['error_msg'] = str(e)
                return JsonResponse(context)
            print(takes_obj)
            # context['course_session'] = takes_obj.course_session
            # print(context['course_sessions'])
            context['status'] = True
            context['userid'] = user.username
        return JsonResponse(context)

@csrf_exempt
def student_profile(request):
    context = {'status': False}
    if not request.user or not request.user.is_authenticated:
        context['error_msg'] = 'User not logged in'
        return JsonResponse(context)
    else:
        user = request.user
        student_obj = get_object_or_404(student, user=user)
        context['status'] = True
        context['userid'] = user.username
        context['student'] = list(student_obj.values())
        print(context['course_sessions'])
        return JsonResponse(context)


@csrf_exempt
def add_location(request):
    context = {'status': False}
    if not request.user or not request.user.is_authenticated:
        context['error_msg'] = 'User not logged in'
        return JsonResponse(context)

    if request.method == "POST":
        if location.objects.filter(location_name = request.POST['location_name']).exists():
            # at least one object satisfying query exists
            context['error_msg'] = 'Location already exists'
            return JsonResponse(context)
        else:
            # no object satisfying query exists
            location_obj = location(location_name=request.POST['location_name'])
            location_obj.save()
            context['status'] = True
            return JsonResponse(context)
    else:
        context['error_msg'] = "Needed POST request, done GET"
        return JsonResponse(context)

@csrf_exempt
def get_location(request):
    context = {'status': False}
    if not request.user or not request.user.is_authenticated:
        context['error_msg'] = 'User not logged in'
        return JsonResponse(context)

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM SPotMe_location")
        row = dictfetchall(cursor)
        context['data'] = row
        context['status'] = True;
        return JsonResponse(context)

@csrf_exempt
def Wifi_data(request):
    context = {'status': False}
    if not request.user or not request.user.is_authenticated:
        context['error_msg'] = 'User not logged in'
        return JsonResponse(context)   

    if request.method == "POST":
        if location.objects.filter(location_name = request.POST['location_name']).exists():
            # at least one object satisfying query exists
            context['error_msg'] = 'Location already exists'
            return JsonResponse(context)
        else:
            # no object satisfying query exists
            location_obj = location(location_name=request.POST['location_name'])
            location_obj.save()
            context['status'] = True
            return JsonResponse(context)
    else:
        context['error_msg'] = "Needed POST request, done GET"
        return JsonResponse(context)

@csrf_exempt
def ping(request):
    context = {'status': False}
    if not request.user or not request.user.is_authenticated:
        context['error_msg'] = 'User not logged in'
        return JsonResponse(context) 

    context['data'] = request.POST;
    context['status'] = True;
    return JsonResponse(context)
