from django.db import models
from datetime import datetime
from django.contrib.auth.models import User
import datetime

SEM_CHOICES = (
    ('FALL', 'Fall'),
    ('AUTUMN', 'Autumn'),
)
YEAR_CHOICES = [(r,r) for r in range(2012, datetime.date.today().year+1)]
# Create your models here.

class student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, default=None)
    profile_pic = models.FileField(default=None, null=True)

    @classmethod
    def create(cls, user):
        student = cls(user=user)
        return student

    def __str__(self):
        return self.user.username

class instructor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, default=None)
    profile_pic = models.FileField(default=None, null=True)

    @classmethod
    def create(cls, user):
        instructor = cls(user=user)
        return instructor

    def __str__(self):
        return self.user.username

class course(models.Model):
    course_id = models.CharField(max_length=10)
    course_name = models.CharField(max_length=50)

    def __str__(self):
        return str(self.course_id) + '- ' + str(self.course_name)


class course_session(models.Model):
    session_token = models.CharField(max_length=10, default='sessn')
    course_instructor = models.ForeignKey(instructor, on_delete=models.CASCADE, default=None)
    course = models.ForeignKey(course, on_delete=models.CASCADE, default=None)

    course_session_info = models.CharField(max_length=1000, primary_key=False, default='')

    semester = models.CharField(max_length=10, choices=SEM_CHOICES)
    year = models.IntegerField(choices=YEAR_CHOICES)

    def __str__(self):
        return self.semester + ' ' + str(self.year) + ': ' + str(self.course)

class takes(models.Model):
    student = models.ForeignKey(student, on_delete=models.CASCADE)
    course_session = models.ForeignKey(course_session, on_delete=models.CASCADE, default=None)

    class Meta:
        unique_together = ('student', 'course_session')

    def __str__(self):
        return self.student.user.username + ' ' + str(self.course_session.course_id)

class location(models.Model):
    location_id = models.AutoField(primary_key=True)
    location_name = models.CharField(max_length=50)

    def __str__(self):
        return self.location_name

class lecture(models.Model):
    lecture_id = models.AutoField(primary_key=True, default=1)
    lecture_title = models.CharField(max_length=50, default=None, null=True)
    course_session = models.ForeignKey(course_session, on_delete=models.CASCADE)
    lecture_location = models.ForeignKey(location, on_delete=models.CASCADE)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def __str__(self):
        return self.course_session.course.course_name + ' - Lecture: ' + str(self.lecture_id)

class router(models.Model):
    BSSID = models.CharField(primary_key=True,max_length=20, default='')
    SSID = models.CharField(max_length=40)

    def __str__(self):
        return self.BSSID + self.SSID

class router_location_statistic(models.Model):
    location = models.ForeignKey(location, on_delete=models.CASCADE)
    router = models.ForeignKey(router, on_delete=models.CASCADE)
    # statistic = models.FloatField() # avg, var, min, max

class router_location_data(models.Model):
    location = models.ForeignKey(location, on_delete=models.CASCADE)
    router = models.ForeignKey(router, on_delete=models.CASCADE)
    signal_strength = models.FloatField()

    def __str__(self):
        return self.location.name + self.router.SSID

class attendance(models.Model):
    student = models.ForeignKey(student, on_delete=models.CASCADE)
    lecture = models.ForeignKey(lecture, on_delete=models.CASCADE)
    attendance_time = models.DateTimeField(default=datetime.datetime.now)

    def __str__(self):
        return self.student.user.username + ' ' + self.lecture.id

class tracking_data(models.Model):
    attendance = models.ForeignKey(attendance, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=datetime.datetime.now)
    location = models.ForeignKey(location, on_delete=models.CASCADE)

    def __str__(self):
        return self.timestamp + ' - ' + self.attendance.id + ', ' + self.location.id
