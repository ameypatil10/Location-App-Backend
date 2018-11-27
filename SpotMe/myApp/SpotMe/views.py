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
import json
import math

epsilon = 1e-4

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
            try:
                course_session_obj = get_object_or_404(course_session, pk=course_session_id)
                context['course_session'] = course_session_obj
                if course_session_obj is not None:
                    context['course_lectures'] = lecture.objects.filter(course_session=course_session_obj)
            except:
                pass
    return context

def instructor_lecture_page_context(instructor, lecture_id):
    context = {'instructor': None, 'course_session': None, 'students': None, 'lecture': None}
    if instructor is not None:
        if instructor.user.is_authenticated:
            context['instructor'] = instructor
            try:
                lecture_obj = get_object_or_404(lecture, pk=lecture_id)
                context['course_session'] = lecture.course_session
                context['lecture'] = lecture_obj
                takes_objs = takes.objects.filter(course_session=lecture_obj.course_session)
                students = list(map(lambda x: x.student, takes_objs))
                context['students'] = students
                for student_obj in students:
                    try:
                        att = get_object_or_404(attendance, student=student_obj, lecture=lecture_obj)
                    except:
                        att = attendance(student=student_obj, lecture=lecture_obj, attendance_time=None)
                        att.save()
                context['attendances'] = attendance.objects.filter(lecture=lecture_obj)
            except:
                pass
    return context

############################################################ Instructor VIEWS ####################################################################
def index(request):
    if request.user.is_authenticated:
        try:
            instructor_obj = get_object_or_404(instructor, user=request.user)
        except:
            instructor_obj = None
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
        try:
            instructor_obj = get_object_or_404(instructor, user=request.user)
        except:
            instructor_obj = None
        context = {'instructor': instructor_obj}
        return render(request, 'SpotMe/instructor_profile.html', context)

def edit_instructor_profile(request):
    pass

def instructor_home(request):
    if not request.user.is_authenticated:
        return render(request, 'SpotMe/instructor_login.html')
    else:
        try:
            instructor_obj = get_object_or_404(instructor, user=request.user)
        except:
            instructor_obj = None
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
            try:
                course_obj = get_object_or_404(course, course_id=course_id)
                form.course = course_obj
                form.instructor = instructor_obj
                session_token = get_random_string(10)
                try:
                    course_session_obj = course_session(course_instructor=instructor_obj, session_token=session_token,
                    course=course_obj, year=year, semester=semester, course_session_info=course_session_info)
                    course_session_obj.save()
                except:
                    print('Token value already exists.')
                return render(request, 'SpotMe/instructor_home.html', instructor_home_context(instructor_obj))
            except:
                pass
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
            lecture_date = form.cleaned_data['lecture_date']
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']
            try:
                location_obj = get_object_or_404(location, location_id=location_id)
                lecture_obj = lecture(lecture_location=location_obj, course_session=course_session_obj, 
                lecture_title=lecture_title, lecture_date=lecture_date, start_time=start_time, end_time=end_time)
                lecture_obj.save()
            except:
                print('Error while saving the lecture instanse.')
            return render(request, 'SpotMe/instructor_course_page.html', instructor_course_page_context(instructor_obj, course_session_id))
        return render(request, 'SpotMe/instructor_add_lecture.html', context)

def instructor_course_page(request, course_session_id):
    if not request.user.is_authenticated:
        return render(request, 'SpotMe/instructor_login.html')
    else:
        try:
            instructor_obj = get_object_or_404(instructor, user=request.user)
            context = instructor_course_page_context(instructor_obj, course_session_id)
        except:
            context = {}
        return render(request, 'SpotMe/instructor_course_page.html', context)

def instructor_lecture_page(request, lecture_id):
    if not request.user.is_authenticated:
        return render(request, 'SpotMe/instructor_login.html')
    else:
        try:
            instructor_obj = get_object_or_404(instructor, user=request.user)
            context = instructor_lecture_page_context(instructor_obj, lecture_id)
        except:
            context = {} 
        return render(request, 'SpotMe/instructor_lecture_page.html', context)

def lecture_tracking_page(request, lecture_id, student_id):
    context = {'instructor': None, 'student': None, 'attendance': None, 'tracking_data': None}
    if not request.user.is_authenticated:
        return render(request, 'SpotMe/instructor_login.html')
    else:
        try:
            instructor_obj = get_object_or_404(instructor, user=request.user)
            context['instructor'] = instructor_obj
            try:
                lecture_obj = get_object_or_404(lecture, lecture_id=lecture_id)
                student_obj = get_object_or_404(student, pk=student_id)
                context['student'] = student_obj
                try:
                    attendance_obj = get_object_or_404(attendance, student=student_obj, lecture=lecture_obj)
                    context['attendance'] = attendance_obj
                    context['tracking_data'] = tracking_data.objects.filter(attendance=attendance_obj)
                    return render(request, 'SpotMe/lecture_tracking_page.html', context)
                except:
                    pass
            except:
                pass
        except:
            pass
        return render(request, 'SpotMe/lecture_tracking_page.html', context)

###################################################### Student Views #################################################################################

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
    if not request.user.is_authenticated:
        return JsonResponse(context)
    else:
        logout(request)
        context['status'] = True
    return JsonResponse(context)

@csrf_exempt
def student_register(request):
    context = {'status': False}
    if(request.method == 'POST'):
        try:
            userid = request.POST['userid']
            password = request.POST['password']
            first_name = request.POST['first_name']
            last_name = request.POST['last_name']
            email = request.POST['email']
            try:
                user = User(username = userid, first_name=first_name, last_name=last_name, email=email)
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
            except:
                context['error_msg'] = 'User already exists'
        except:
            context['error_msg'] = 'Connection problem'
        return JsonResponse(context)

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
            cursor.execute("""SELECT SpotMe_lecture.*, SpotMe_location.location_name
                FROM SpotMe_takes, auth_user, SpotMe_course_session,
                SpotMe_instructor, SpotMe_course, SpotMe_lecture, SpotMe_location
                WHERE auth_user.id = SpotMe_instructor.user_id
                AND SpotMe_location.location_id = SpotMe_lecture.lecture_location_id
                AND SpotMe_lecture.course_session_id = SpotMe_course_session.id 
                AND SpotMe_takes.course_session_id = SpotMe_course_session.id 
                AND SpotMe_course_session.course_id = SpotMe_course.id 
                AND SpotMe_instructor.id =  SpotMe_course_session.course_instructor_id 
                AND SpotMe_takes.id = %s""", [takes_id])
            row = dictfetchall(cursor)
            # print(row)
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
            # print(course_id, session_token)
            try:
                course_obj = get_object_or_404(course, course_id=course_id)
                course_session_obj = get_object_or_404(course_session, course=course_obj, session_token=session_token)
                takes_obj = takes(student=student_obj, course_session=course_session_obj)
                takes_obj.save()
            except Exception as e:
                context['error_msg'] = str(e)
                return JsonResponse(context)            
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
        # with connection.cursor() as cursor:
        # cursor.execute("""SELECT * from SpotMe_student, auth_user 
            # WHERE auth_user.id = SpotMe_student.id AND auth_user.id = %s""", [user.id])

        # profile = dictfetchall(cursor)
        context['status'] = True
        context['username'] = user.username
        context['email'] = user.email
            # context['data'] = profile[0]
        # print(context['course_sessions'])
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
def list_location(request):
    context = {'status': False}
    if not request.user or not request.user.is_authenticated:
        context['error_msg'] = 'User not logged in'
        return JsonResponse(context)

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM SpotMe_location")
        row = dictfetchall(cursor)
        context['data'] = row
        context['status'] = True
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
    context = {'status': False, 'logged_in': True}
    if not request.user or not request.user.is_authenticated:
        context['error_msg'] = 'User not logged in'
        context['logged_in'] = False
        return JsonResponse(context) 

    user = request.user
    student_obj = get_object_or_404(student, user=user) 
    student_location = get_location_in(request)
    print('student_location - ', student_location)
    with connection.cursor() as cursor:
        cursor.execute("""SELECT SpotMe_student.*, SpotMe_takes.*, SpotMe_lecture.* 
            FROM SpotMe_takes, SpotMe_student, 
            SpotMe_lecture, SpotMe_course_session WHERE 
            SpotMe_takes.student_id = SpotMe_student.id 
            AND SpotMe_course_session.id = SpotMe_takes.course_session_id 
            AND SpotMe_lecture.course_session_id = SpotMe_course_session.id
            AND SpotMe_student.id = %s
            AND SpotMe_lecture.lecture_date = DATE('NOW', 'localtime')
            AND SpotMe_lecture.start_time < TIME('NOW', 'localtime', '+10 minutes') 
            AND SpotMe_lecture.start_time > TIME('NOW', 'localtime')""", [student_obj.id])

        next_lect = dictfetchall(cursor)
        context['data'] = {}
        if(len(next_lect) == 0):
            context['data']['next_lecture'] = "No Lecture Found"
        else:
            context['data']['next_lecture'] = next_lect[0]

        cursor.execute("SELECT DATETIME('NOW', 'localtime') as time")
        curr_time = dictfetchall(cursor)
        # print("curr_time ", curr_time)
        context['data']['curr_time'] = curr_time[0]['time']

        cursor.execute("""SELECT SpotMe_student.*, SpotMe_takes.*, 
            SpotMe_lecture.*, SpotMe_course_session.*
            FROM SpotMe_takes, SpotMe_student, 
            SpotMe_lecture, SpotMe_course_session WHERE 
            SpotMe_takes.student_id = SpotMe_student.id 
            AND SpotMe_course_session.id = SpotMe_takes.course_session_id 
            AND SpotMe_lecture.course_session_id = SpotMe_course_session.id
            AND SpotMe_student.id = %s
            AND SpotMe_lecture.lecture_date = DATE('NOW', 'localtime')
            AND SpotMe_lecture.start_time < TIME('NOW', 'localtime')
            AND SpotMe_lecture.end_time > TIME('NOW', 'localtime')""", [student_obj.id])
        # cursor.execute("select DATETIME('now')")
        row = dictfetchall(cursor)

        if(len(row) == 0):
            context['data']['curr_lecture'] = "No Lecture Found"
        else:
            context['data']['curr_lecture'] = row[0]
            student_location_dict = get_location_in(request)
            student_location = student_location_dict['location']
            if(student_location is not None and (student_location.location_id == row[0]['lecture_location_id'])):
            # MARK ATTENDANCE....
                # print("IN MARK ATTENDANCE")
                cursor.execute("""select * from SpotMe_attendance WHERE
                    lecture_id = %s AND student_id = %s""", [row[0]['lecture_id'] , student_obj.id])
                attendance_data = dictfetchall(cursor)
                # print(attendance_data)
                if(not(len(attendance_data) == 1)):
                    lecture_id = row[0]['lecture_id']
                    # Logic for flags
                    attend_flag = 1
                    # context['data']['curr_time']
                    # attendance_time = context['data']['curr_lecture']['attendance_time']
                    # lecture_start = context['data']['curr_lecture']['start_time']
                    # current_time = datetime.strptime(curr_time[0]['time'], 

                    #     '2018-11-26 19:49:02'

                    # print("hello", current_time - lecture_start)
                    new_attendance = attendance(lecture_id = lecture_id, student_id = student_obj.id, attendance_flag = attend_flag, attendance_time=datetime.datetime.now())
                    new_attendance.save()
                    cursor.execute("""select * from SpotMe_attendance WHERE
                        lecture_id = %s AND student_id = %s""", [row[0]['lecture_id'] , student_obj.id])
                    attendance_data = dictfetchall(cursor)
                    new_tracking_data = tracking_data(attendance_id = attendance_data[0]['id'], location_id = student_location)
                    new_tracking_data.save()
                elif attendance_data[0]['attendance_time'] is None or attendance_data[0]['attendance_flag'] == 0:    
                    attendance_obj = get_object_or_404(attendance, lecture_id = row[0]['lecture_id'], student_id = student_obj.id)
                    attendance_obj.attendance_time = datetime.datetime.now()
                    attendance_obj.attendance_flag = 1
                    attendance_obj.save()
                    # attendance_obj.update(attendance_time = datetime.datetime.now, attendance_flag = 1)
                else:  
                    cursor.execute("""select * from SpotMe_attendance WHERE
                        lecture_id = %s AND student_id = %s""", [row[0]['lecture_id'] , student_obj.id])
                    attendance_data = dictfetchall(cursor)
                    cursor.execute("""SELECT * FROM SpotMe_tracking_data WHERE
                        attendance_id = %s AND location_id = %s
                        AND timestamp > DATETIME('NOW', '-1 minutes')""", [attendance_data[0]['id'], student_location.location_id])
                    tracking_data1 = dictfetchall(cursor)
                    if(len(tracking_data1) == 0):
                        new_tracking_data = tracking_data(attendance_id = attendance_data[0]['id'], location_id = student_location.location_id)
                        new_tracking_data.save()
                        context['data']['msg'] = "new tracking_data added"
                    else:
                        context['data']['msg'] = "no tracking_data added"
                # print(attendance_data[0]['id'])
                # print(json.dumps(student_location))

                # context['data']['msg'] = "new tracking_data added"

        context['status'] = True
        context['userid'] = user.username
        return JsonResponse(context)

    return JsonResponse(context)

def get_prob(loc, data):
    prob = 0
    wts = epsilon
    for (router_obj, signal) in data:
        try:
            stat = get_object_or_404(router_location_statistic, location=loc, router=router_obj)
            avg = stat.avg
            Max = stat.Max
            var = stat.var
            p = math.exp(-(avg - signal)**2/(var+epsilon))
            wt = math.exp(-(Max - stat.avg)**2/(var+epsilon))
            prob += p*wt
            wts += wt
        except:
            pass
    return (loc, prob/wts)

@csrf_exempt
def get_location(request):
    context = {'status': False, 'location': None, 'loc_prob': 0}
    data = request.POST['wifi-data']
    data = json.loads(data)
    id_signal_data = []
    for d in data:
        try:
            r = get_object_or_404(router, BSSID=d['bssid'])
            id_signal_data.append((r, d['signal']))
        except:
            pass
    locations = location.objects.all()
    probs = []
    max_prob = 0
    out_loc = None
    for l in locations:
        p = get_prob(l, id_signal_data)
        # print(p)
        probs.append(p)
        if p[1] > max_prob:
            max_prob = p[1]
            out_loc = p[0]
    if out_loc and max_prob > 0.00000001:
        context['status'] = True
        context['location_name'] = out_loc.location_name
        context['loc_prob'] = max_prob
    return JsonResponse(context)

@csrf_exempt
def get_location_in(request):
    context = {'status': False, 'location_name': None}
    data = request.POST['wifi-data']
    data = json.loads(data)
    id_signal_data = []
    for d in data:
        try:
            r = get_object_or_404(router, BSSID=d['bssid'])
            id_signal_data.append((r, d['signal']))
        except:
            pass
    locations = location.objects.all()
    probs = []
    max_prob = 0
    out_loc = None
    for l in locations:
        p = get_prob(l, id_signal_data)
        # print(p)
        probs.append(p)
        if p[1] > max_prob:
            max_prob = p[1]
            out_loc = p[0]
    if out_loc and max_prob > 0.00000001:
        context['status'] = True
        context['location'] = out_loc
        context['loc_prob'] = max_prob
    return context

@csrf_exempt
def location_data(request):
    # get location data(json) from user and save to the database.
    context = {'status': False}
    location_id = request.POST['location']
    data = request.POST['wifi-data']
    data = json.loads(data)
    location_obj = get_object_or_404(location, location_id=location_id)
    for d in data:
        try:
            router_obj = get_object_or_404(router, BSSID=d['bssid'])
        except:
            router_obj = router(BSSID=d['bssid'], SSID=d['ssid'])
            router_obj.save()
            print('router added.')
        try:
            router_location_data_obj = get_object_or_404(router_location_data, router=router_obj, location=location_obj, signal_strength=d['signal'])
        except:
            router_location_data_obj = router_location_data(router=router_obj, location=location_obj, signal_strength=d['signal'])
            router_location_data_obj.save()
            print('data added.')
        try:
            router_location_statistic_obj = get_object_or_404(router_location_statistic, location=location_obj, router=router_obj)
        except:
            router_location_statistic_obj = router_location_statistic(location=location_obj, router=router_obj)
            router_location_statistic_obj.save()
        avg_old = router_location_statistic_obj.avg
        var_old = router_location_statistic_obj.var
        num_old = 1.0*router_location_statistic_obj.num
        x = d['signal']
        num = num_old + 1
        avg = (avg_old*num_old + x)/num
        var = num_old*(var_old + (((x-avg_old)**2)/num) )/num
        router_location_statistic_obj.Max = max(router_location_statistic_obj.Max, x)
        router_location_statistic_obj.num = num
        router_location_statistic_obj.avg = avg
        router_location_statistic_obj.var = var
        router_location_statistic_obj.save()
        context = {'status': True}
    return JsonResponse(context)


