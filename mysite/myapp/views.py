import re
import random
import string
import json
import os
from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from datetime import datetime,date
from django.contrib import messages
from django.db.models import Value,CharField


from django.template.loader import render_to_string
from mysite.settings import EMAIL_HOST_USER
from django.core.mail import send_mail, EmailMessage

from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib import auth
from .models import *
import uuid
from django.utils import timezone
from django.http import JsonResponse,HttpResponse,FileResponse
from pathlib import Path
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
import csv
from django.contrib.auth.forms import AuthenticationForm



# Landing Page
def landing(request):
    return render(request,'landing.html')

# -----------------------------------
# Faculty Section
# -----------------------------------


# Login View
def facultyLogin(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        try:
            detail = User.objects.get(email=email)
            username = detail.username
            # Add debugging messages
            print(f"Found user with email {email}, username: {username}")
        except User.DoesNotExist:
            # Add debugging for user not found
            print(f"User with email {email} not found")
            username = 'Temp'
        
        user = authenticate(username=username, password=password)
        # Add debugging for authentication results
        print(f"Authentication result: {user}")
        
        # Roles
        if user is not None:
            login(request, user)
            return redirect('facultyDashboard')
        else:
            messages.error(request, "Invalid Credentials")
            return redirect('facultyLogin')
    return render(request,'faculty/facultyLogin.html')

# Register View
def facultyRegister(request):
    if request.method=='POST':
        first_name = request.POST['fname']
        last_name = request.POST['lname']
        email = request.POST['email']
        password = request.POST['password']
        gender = request.POST['gender']
        dob = request.POST['dob']
        contact = request.POST['contact']
        institute = request.POST['institute']
        state = request.POST['state']
        yearOfStudy = request.POST['yos']
        about = request.POST['about']
        profilePic = request.FILES.get('profilePic')

        print(profilePic)
        # Generating unique username
        num = random.randint(10000000, 99999999)
        str1 = 'EF'
        unique_id = str1 + str(num)
        username=unique_id
        # End Generating unique username

        full_name = first_name + last_name

        if User.objects.filter(email=email).exists():
            messages.error(request,'You Already have an account. Please Log In')
            return redirect('facultyLogin')
        else:
            user = User.objects.create_user(username=username,password=password,email=email,first_name=first_name,last_name=last_name)
            user.is_staff=True;
            user.is_superuser=False;
            user.save()

            u_id = User.objects.get(username=username)

            faculty = FacultyDetails(facultyId=u_id,facultyName=full_name,facultyPhone=contact,facultyGender=gender,facultyDOB = dob,
                            facultyDesc=about,facultyCollege=institute,collegeState=state,experience=yearOfStudy,facultyPic=profilePic)

            faculty.save()

            # Registration Confirmation Email
            role_user_email = user.email
            # role_user_email = 'rahul.agarwal31101999@gmail.com'
            mail_subject = "[Welcome Faculty] - You have successfully registered to VirtualClassroom!!"
            message = render_to_string('register_successful.html', {
                'firstname': user.first_name,
                'lastname': user.last_name,
                'unique_id' : unique_id
            })

            email = EmailMessage(mail_subject, message, from_email=EMAIL_HOST_USER, to=[role_user_email])
            email.send()
            # End Registration Confirmation Email


            messages.success(request,'You are now registered')
            return redirect('facultyLogin')

    return render(request,'faculty/facultyRegister.html')


# Logout View
@login_required
def facultyLogout(request):
    if request.user.is_active and request.user.is_staff and not request.user.is_superuser:
        auth.logout(request)
        return render(request, 'faculty/facultyLogout.html')
    else:
        return redirect('facultyLogin')

# Dashboard View
@login_required
def facultyDashboard(request):
    if request.user.is_active and request.user.is_staff and not request.user.is_superuser:
        user=request.user
        faculty = FacultyDetails.objects.get(facultyId = user.id)
        classRooms = ClassRoom.objects.filter(classFacultyID=faculty.id)
        unique_id=faculty.facultyId

        # Calculate active assignments
        active_assignments = 0
        total_students = 0
        total_attendance = 0
        total_classes = 0

        for classroom in classRooms:
            # Count active assignments
            assignments = Assignment.objects.filter(classId=classroom.pk)
            active_assignments += assignments.count()
            
            # Count total students
            try:
                student_list = ClassroomStudentsList.objects.get(classId=classroom.pk)
                students_dict = json.loads(student_list.studentList)
                total_students += len(students_dict)
            except:
                pass
                
            # Calculate attendance rate
            try:
                attendence_obj = Attendence.objects.get(classId=classroom.pk)
                total_classes += attendence_obj.totalClassConducted
                
                if attendence_obj.totalClassConducted > 0:
                    student_attendance = json.loads(attendence_obj.studentAttendence)
                    for student, attended in student_attendance.items():
                        total_attendance += int(attended)
            except:
                pass

        # Calculate overall attendance rate
        attendance_rate = "N/A"
        if total_classes > 0 and total_students > 0:
            possible_attendances = total_classes * total_students
            if possible_attendances > 0:
                rate = (total_attendance / possible_attendances) * 100
                attendance_rate = f"{rate:.1f}%"

        # Email Testing
        if request.method=='POST':
            # send_mail(
            #             'Daily Rozgaar',
            #             'Thank you for showing interest in our website. You have been successfully registered. Feel free to call for any house help and avail our facilities at a rational price !',
            #             'rahul.agarwal31101999@gmail.com',
            #             ['adityaverma0198@gmail.com'],
            #             fail_silently = False
            #             )

            role_user_email = 'adityaverma0198@gmail.com'
            mail_subject = "Welcome To VC - Virtual Classroom"
            message = render_to_string('register_successful.html', {
                'user': role_user_email,
                'firstname': user.first_name,
                'lastname': user.last_name,
                'unique_id' : unique_id,
            })

            email = EmailMessage(mail_subject, message, from_email=EMAIL_HOST_USER, to=[role_user_email])
            email.send()

            # End Email Testing


            return redirect(request.path_info)


        # Email Testing Ends

        # Prepare recent activities from announcements and assignments
        recent_activities = []
        for classroom in classRooms:
            # Get recent announcements
            announcements = Announcement.objects.filter(classId=classroom.pk).order_by('-publishedTime')[:2]
            for announcement in announcements:
                recent_activities.append({
                    'type': 'announcement',
                    'title': f"Announcement in {classroom.classname}",
                    'description': announcement.announcementHeading,
                    'timestamp': announcement.publishedTime
                })
                
            # Get recent assignments
            assignments = Assignment.objects.filter(classId=classroom.pk).order_by('-publishedTime')[:2]
            for assignment in assignments:
                recent_activities.append({
                    'type': 'assignment',
                    'title': f"Assignment in {classroom.classname}",
                    'description': assignment.assignmentHeading,
                    'timestamp': assignment.publishedTime
                })
        
        # Sort by timestamp
        recent_activities = sorted(recent_activities, key=lambda x: x['timestamp'], reverse=True)[:5]

        context={
            'classRooms': classRooms,
            'userDetails': faculty,
            'active_assignments': active_assignments,
            'total_students': total_students,
            'attendance_rate': attendance_rate,
            'recent_activities': recent_activities
        }
        return render(request,'faculty/facultyDashboard.html',context)
    else:
        return redirect('facultyLogin')


# Profile View
@login_required
def facultyProfile(request):
    if request.user.is_active and request.user.is_staff and not request.user.is_superuser:
        user=request.user
        userDetails = FacultyDetails.objects.get(facultyId = user.pk)

        if request.method=='POST':
            contact = request.POST['contact']
            institute = request.POST['institute']
            experience = request.POST['year']
            about = request.POST['about']
            profilePic = request.FILES.get('profilePic')

            userDetails.facultyPhone = contact
            userDetails.facultyCollege = institute

            if 'state' in request.POST:
                state = request.POST['state']
                userDetails.collegeState = state
            else:
                None

            userDetails.experience = experience
            userDetails.facultyDesc = about
            if profilePic:
                userDetails.facultyPic = profilePic

            userDetails.save()
            return redirect(request.path_info)

        context={
            'userDetails' : userDetails,
        }
        return render(request,'faculty/facultyProfile.html',context)
    else:
        return redirect('facultyLogin')


# Classroom Creation View
@login_required
def facultyClassCreate(request):
    if request.user.is_active and request.user.is_staff and not request.user.is_superuser:
        # Getting faculty details
        user=request.user
        faculty = FacultyDetails.objects.get(facultyId = user.pk)

        if request.method=='POST':
            className = request.POST['className']
            facultyName = request.POST['faculty']
            department = request.POST['department']
            academicYear = request.POST['year']
            gmeetLink = request.POST['gmeet']

            # unique class id
            classId = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

            # Testing
            # print('---------Testing-------')
            # print('Timetable : ' + timetable)
            # print(faculty.facultyId)
            # print(user.id)

            # Creating classroom Object
            classCreate = ClassRoom(classId=classId, classname=className, classDepartment= department, academicYear=academicYear,
                                    classFacultyID_id = faculty.pk, classFacultyName=faculty.facultyName)

            if gmeetLink is not None:
                classCreate.classLink = gmeetLink

            classCreate.save()
            # End Classroom Created


            # Creating object for ClassroomStudentsList
            # Creating empty dict for the student list
            my_dict = {}
            input = json.dumps(my_dict)
            classroomStudentsList  = ClassroomStudentsList(classId_id = classCreate.pk, studentList = input )
            classroomStudentsList.save()
            # End Creating object for ClassroomStudentsList


            # Creating object for attendence
            attendenceId = str(classCreate.pk)
            attendence = Attendence(attendenceId = attendenceId, classId_id = classCreate.pk)
            attendence.save()
            # End Creating object for attendence

            # Creating object for Offline Classes
            my_dict1 = {}
            input1 = json.dumps(my_dict1)
            offline = OfflineClass(classId_id = classCreate.pk, studentList = input1)
            offline.save()
            # End Creating object for Offline Classes

            messages.success(request,"Classroom Created Successfully")
            return redirect('facultyDashboard')


        context ={
            'faculty' : faculty,
        }
        return render(request,'faculty/facultyClassCreate.html',context)
    else:
        return redirect('facultyLogin')


@login_required
def facultySubject(request,pk):
    if request.user.is_active and request.user.is_staff and not request.user.is_superuser:
        id=pk
        user=request.user
        classDetails = ClassRoom.objects.get(classId=id)
        userDetails = FacultyDetails.objects.get(facultyId_id = user.pk)
        if request.method=='POST':

            if 'timeSubmit' in request.POST:
                # Getting list of days when class will happen
                timetable = ""
                temp = request.POST.getlist('time')

                # monday = request.POST['monday']
                if 'Monday' in temp:
                    # Storing Day,start_time and end_time as a list
                    timing=[]
                    timing.append('Monday')
                    monday_start = request.POST.get('monday_start',0)
                    monday_end = request.POST.get('monday_end',0)
                    timing.append(monday_start)
                    timing.append(monday_end)
                    timetable += str(timing)
                    timetable += '+'

                # print(monday)

                # tuesday = request.POST.get('tuesday')
                if 'Tuesday' in temp:
                    # Storing Day,start_time and end_time as a timing
                    timing=[]
                    timing.append('Tuesday')
                    tuesday_start = request.POST.get('tuesday_start',0)
                    tuesday_end = request.POST.get('tuesday_end',0)
                    timing.append(tuesday_start)
                    timing.append(tuesday_end)
                    timetable += str(timing)
                    timetable += '+'

                # print(tuesday)

                # wednesday = request.POST['wednesday']
                if 'Wednesday' in temp:
                    # Storing Day,start_time and end_time as a timing
                    timing=[]
                    timing.append('Wednesday')
                    wednesday_start = request.POST.get('wednesday_start',0)
                    wednesday_end = request.POST.get('wednesday_end',0)
                    timing.append(wednesday_start)
                    timing.append(wednesday_end)
                    timetable += str(timing)
                    timetable += '+'


                # thursday = request.POST['thursday']
                if 'Thursday' in temp:
                    # Storing Day,start_time and end_time as a timing
                    timing=[]
                    timing.append('Thursday')
                    thursday_start = request.POST.get('thursday_start',0)
                    thursday_end = request.POST.get('thursday_end',0)
                    timing.append(thursday_start)
                    timing.append(thursday_end)
                    timetable += str(timing)
                    timetable += '+'


                # friday = request.POST['friday']
                if 'Friday' in temp:
                    # Storing Day,start_time and end_time as a timing
                    timing=[]
                    timing.append('Friday')
                    friday_start = request.POST.get('friday_start',0)
                    friday_end = request.POST.get('friday_end',0)
                    timing.append(friday_start)
                    timing.append(friday_end)
                    timetable += str(timing)
                    timetable += '+'

                # saturday = request.POST['saturday']
                if 'Saturday' in temp:
                    # Storing Day,start_time and end_time as a timing
                    timing=[]
                    timing.append('Saturday')
                    saturday_start = request.POST.get('saturday_start',0)
                    saturday_end = request.POST.get('saturday_end',0)
                    timing.append(saturday_start)
                    timing.append(saturday_end)
                    timetable += str(timing)
                    timetable += '+'

                # sunday = request.POST['sunday']
                if 'Sunday' in temp:
                    # Storing Day,start_time and end_time as a timing
                    timing=[]
                    timing.append('Sunday')
                    sunday_start = request.POST.get('sunday_start',0)
                    sunday_end = request.POST.get('sunday_end',0)
                    timing.append(sunday_start)
                    timing.append(sunday_end)
                    timetable += str(timing)
                    timetable += '+'

                if len(timetable) > 0:
                    timetable = timetable[:-1]
                # print(timetable)
                classDetails.classTimeTable = timetable
                classDetails.save()
                return redirect(request.path_info)


            if 'postAnnouncement' in request.POST:
                announcementHeading = request.POST['announcementHeading']
                announcementDescription = request.POST['announcementDescription']

                # print('-------Testing---------')
                # print(announcementDescription)

                temp = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                announcementId = 'AN' + temp
                newAnnouncement = Announcement(announcementId = announcementId, classId_id = classDetails.pk ,announcementHeading = announcementHeading,
                                                announcementDescription = announcementDescription)

                newAnnouncement.save()
                messages.success(request,"Announcement Posted Successfully")
                return redirect(request.path_info)

            if 'postAssignment' in request.POST:
                assignmentHeading = request.POST['assignmentHeading']
                assignmentDescription = request.POST['assignmentDescription']
                assignmentLink = request.POST['assignmentLink']
                dueDate = request.POST['dueDate']

                temp = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                assignmentId = 'AS' + temp

                newAssignment = Assignment(assignmentId = assignmentId, classId_id = classDetails.pk ,assignmentHeading = assignmentHeading,
                                                assignmentDescription = assignmentDescription, assignmentLink = assignmentLink, assignmentDueTime = dueDate)

                newAssignment.save()
                messages.success(request,"Assignment Posted Successfully")
                return redirect(request.path_info)
                
            if 'postMaterial' in request.POST:
                materialHeading = request.POST['materialHeading']
                materialDescription = request.POST['materialDescription']
                materialType = request.POST['materialType']
                materialLink = request.POST.get('materialLink', '')  # Optional field
                
                # Generate a unique ID for the material
                material_id = str(uuid.uuid4())
                
                # Handle file upload
                material_file = None
                if request.FILES and 'materialFile' in request.FILES:
                    material_file = request.FILES['materialFile']
                
                # Create and save the Material object
                material = Material(
                    materialId=material_id,
                    classId=classDetails,
                    materialHeading=materialHeading,
                    materialDescription=materialDescription,
                    materialType=materialType,
                    materialLink=materialLink,
                    materialFile=material_file,
                    publishedTime=timezone.now()
                )
                material.save()
                
                messages.success(request, "Material posted successfully!")
                return redirect(request.path_info)

            if 'deleteClass' in request.POST:
                classroom_id = request.POST.get('classroom_id')
                try:
                    # Find the classroom
                    classroom = ClassRoom.objects.get(classId=classroom_id)
                    
                    # Check if the faculty is the owner of the class
                    if classroom.classFacultyID.facultyId == request.user:
                        # Delete associated data
                        Announcement.objects.filter(classId=classroom).delete()
                        Assignment.objects.filter(classId=classroom).delete()
                        Attendence.objects.filter(classId=classroom).delete()
                        ClassroomStudentsList.objects.filter(classId=classroom).delete()
                        OfflineClass.objects.filter(classId=classroom).delete()
                        Material.objects.filter(classId=classroom).delete()
                        
                        # Finally delete the classroom
                        classroom.delete()
                        
                        messages.success(request, "Classroom deleted successfully")
                        return redirect('facultyDashboard')
                    else:
                        messages.error(request, "You don't have permission to delete this classroom")
                        
                except ClassRoom.DoesNotExist:
                    messages.error(request, "Classroom not found")
                
                return redirect(request.path_info)
                
            if 'removeStudent' in request.POST:
                student_id = request.POST.get('student_id')
                try:
                    # Get the student from User model
                    student = User.objects.get(username=student_id)
                    
                    # Get the classroom students list
                    classroom_list = ClassroomStudentsList.objects.get(classId=classDetails)
                    student_list = json.loads(classroom_list.studentList)
                    
                    # Remove the student from the list
                    if student_id in student_list:
                        student_list.remove(student_id)
                        classroom_list.studentList = json.dumps(student_list)
                        classroom_list.save()
                        
                        # Also update the student's class list
                        student_class_list = StudentClassroomList.objects.get(studentId=student)
                        class_list = json.loads(student_class_list.classList)
                        if id in class_list:
                            class_list.remove(id)
                            student_class_list.classList = json.dumps(class_list)
                            student_class_list.save()
                        
                        messages.success(request, f"Student {student.first_name} {student.last_name} removed from class")
                    else:
                        messages.error(request, "Student not found in this classroom")
                    
                except (User.DoesNotExist, ClassroomStudentsList.DoesNotExist, StudentClassroomList.DoesNotExist):
                    messages.error(request, "Error removing student from classroom")
                
                return redirect(request.path_info)

            if 'deleteMaterial' in request.POST:
                material_id = request.POST.get('material_id')
                try:
                    # Find the material
                    material = Material.objects.get(materialId=material_id)
                    
                    # Check if the material belongs to this class
                    if material.classId.pk == id:
                        # Delete the file if it exists
                        if material.materialFile:
                            try:
                                material.materialFile.delete()
                            except:
                                pass  # Continue with deletion even if file removal fails
                        
                        # Delete the material record
                        material.delete()
                        messages.success(request, "Material deleted successfully")
                    else:
                        messages.error(request, "You don't have permission to delete this material")
                except Material.DoesNotExist:
                    messages.error(request, "Material not found")
                
                return redirect(request.path_info)

            if 'sendInvite' in request.POST:
                studentId = request.POST['studentId']

                try:
                    student = User.objects.get(username = studentId)
                    email = student.email

                    role_user_email = email

                    mail_subject = "[CLASSROOM INVITE] - You have been invited to join the Classroom"
                    message = render_to_string('classInviteSend.html', {
                        'facultyName': classDetails.classFacultyName,
                        'className' : classDetails.classname,
                        'firstname': student.first_name,
                        'lastname': student.last_name,
                        'classId' : id,
                    })

                    email = EmailMessage(mail_subject, message, from_email=EMAIL_HOST_USER, to=[role_user_email])
                    email.send()
                    messages.success(request,"Invite Sent Successfully")

                    return redirect(request.path_info)
                except:
                    messages.error(request,"Invalid Student ID")
                    return redirect(request.path_info)

                return redirect(request.path_info)


            if 'linkSubmit' in request.POST:
                meetLink = request.POST['meetLink']

                # Saving the changes
                classDetails = ClassRoom.objects.get(classId=id)
                classDetails.classLink = meetLink
                classDetails.save()
                messages.success(request,'Meeting Link Updated')
                return redirect(request.path_info)

            if 'enableOffline' in request.POST:
                vaccine = request.POST['vaccine']
                strength = request.POST['strength']

                classOfflineStatus = OfflineClass.objects.get(classId = id)
                classOfflineStatus.offlineStatus = 'YES'
                classOfflineStatus.vaccineRequired = vaccine
                classOfflineStatus.classStrength = strength
                classOfflineStatus.studentList = '{}'
                classOfflineStatus.save()
                messages.success(request,'Offline Mode Activated')
                return redirect(request.path_info)

            if 'disableOffline' in request.POST:
                classOfflineStatus = OfflineClass.objects.get(classId = id)
                classOfflineStatus.offlineStatus = 'NO'
                classOfflineStatus.vaccineRequired = 0
                classOfflineStatus.classStrength = 0
                classOfflineStatus.studentList = '{}'
                classOfflineStatus.save()
                messages.success(request,'Offline Mode Deactivated')
                return redirect(request.path_info)


            return redirect(request.path_info)

        # Feed List
        announcements = Announcement.objects.filter(classId = classDetails.pk).annotate(type=Value('announcement', CharField()))
        assignments = Assignment.objects.filter(classId = classDetails.pk).annotate(type=Value('assignment', CharField()))
        materials = Material.objects.filter(classId = classDetails.pk).order_by('-publishedTime')
        all_items = list(assignments) + list(announcements)
        all_items_feed = sorted(all_items, key=lambda obj: obj.publishedTime,reverse=True)
        # print(all_items_feed)
        # End Feed List


        # Time Table
        timeTable = {}
        strTime = classDetails.classTimeTable
        try:
            days = strTime.split('+')
            for x in days:
                curr = x.split(',')
                a = curr[0][1:]
                a=a.strip()
                a=a.strip("\'")
                b = curr[1]
                b=b.strip()
                b=b.strip("\'")
                c = curr[2][:len(curr[2])-1]
                c=c.strip()
                c=c.strip("\'")
                timeTable[a] = [b,c]
        except:
            timeTable={}
        # print(timeTable)
        # End Time Table

        classOfflineStatus = OfflineClass.objects.get(classId = id)

        # Calculate total students
        studentListObject = ClassroomStudentsList.objects.get(classId = id)
        studentListDict = json.loads(studentListObject.studentList)
        totalStudents = len(studentListDict)
        
        # Get student details for the class members list
        students = []
        for student_id in studentListDict:
            try:
                student = User.objects.get(username=student_id)
                students.append(student)
            except User.DoesNotExist:
                continue

        context={
            'class':classDetails,
            'announcements' : announcements,
            'assignments': assignments,
            'materials': materials,
            'all_items_feed' : all_items_feed,
            'userDetails': userDetails,
            'timeTable':timeTable,
            'classOfflineStatus' : classOfflineStatus,
            'id': id,  # Ensure 'id' is passed to the template
            'classDetails': classDetails,
            'totalStudents': totalStudents,
            'students': students
        }
        
        # Check URL path to determine which template to render
        if 'faculty_assignment' in request.path:
            return render(request, 'faculty/facultyAssignment.html', context)
        elif 'faculty_material' in request.path:
            return render(request, 'faculty/facultyMaterial.html', context)
        else:
            return render(request, 'faculty/facultySubject.html', context)
    else:
        return redirect('facultyLogin')

@login_required
def offlineOptedList(request,pk):
    if request.user.is_active and request.user.is_staff and not request.user.is_superuser:
        id = pk

        user=request.user
        userDetails = FacultyDetails.objects.get(facultyId_id = user.pk)

        studentListObject = ClassroomStudentsList.objects.get(classId = id)
        studentListDict = json.loads(studentListObject.studentList)

        studentList = [*studentListDict]
        students = []

        for x in studentList:
            temp = User.objects.get(username = x)
            students.append(temp)

        offlineClass = OfflineClass.objects.get(classId = id)
        offlineList = json.loads(offlineClass.studentList)

        context = {
            'students' : students,
            'offlineList' : offlineList,
            'userDetails':userDetails,
            'id' : id
        }
        return render(request,'faculty/offlineOptedList.html',context)
    else:
        return redirect('facultyLogin')

@login_required
def classMembersList(request,pk):
    if request.user.is_active and request.user.is_staff and not request.user.is_superuser:
        id = pk

        user=request.user
        userDetails = FacultyDetails.objects.get(facultyId_id = user.pk)

        studentListObject = ClassroomStudentsList.objects.get(classId = id)
        studentListDict = json.loads(studentListObject.studentList)

        studentList = [*studentListDict]
        students = []

        for x in studentList:
            temp = User.objects.get(username = x)
            students.append(temp)

        context = {
            'students' : students,
            'id' : id,
            'userDetails' : userDetails
        }
        return render(request,'faculty/classMembersList.html',context)
    else:
        return redirect('facultyLogin')

@login_required
def facultyProfileView(request,pk):
    if request.user.is_active and request.user.is_staff and not request.user.is_superuser:
        id = pk

        user=request.user
        userDetails = FacultyDetails.objects.get(facultyId_id = user.pk)

        studentUser = User.objects.get(username = id)
        studentDetails = StudentDetails.objects.get(studentId_id =  studentUser.pk)
        context={
            'studentUser' : studentUser,
            'studentDetails' : studentDetails,
            'userDetails':userDetails
        }
        return render(request,'faculty/profileView.html',context)
    else:
        return redirect('facultyLogin')

@login_required
def classAttendence(request,pk):
    if request.user.is_active and request.user.is_staff and not request.user.is_superuser:
        id = pk
        studentListObject = ClassroomStudentsList.objects.get(classId = id)
        studentListDict = json.loads(studentListObject.studentList)
        studentList = [*studentListDict]
        students = []

        user=request.user
        userDetails = FacultyDetails.objects.get(facultyId_id = user.pk)

        for x in studentList:
            temp = User.objects.get(username = x)
            students.append(temp)

        # Getting attendence list of the classroom
        attendenceObject = Attendence.objects.get(classId = id)
        attendence = json.loads(attendenceObject.attendenceList)
        studentAttendence =  json.loads(attendenceObject.studentAttendence)

        now = date.today()
        dt_string = now.strftime("%d/%m/%Y")

        status = False
        if dt_string in attendence:
            status = True

        if request.method == 'POST':
            # Handle download attendance request
            if 'downloadAttendance' in request.POST:
                attendance_date = request.POST.get('attendance_date', dt_string)
                
                # Create response with CSV content
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="attendance_{attendance_date}.csv"'
                
                # Create CSV writer
                writer = csv.writer(response)
                writer.writerow(['Serial No', 'Student ID', 'Name', 'Email', 'Status'])
                
                # Get attendance for the selected date
                date_attendance = {}
                if attendance_date in attendence:
                    date_attendance = attendence[attendance_date]
                
                # Write data rows
                for index, student in enumerate(students, 1):
                    status = "Present" if student.username in date_attendance else "Absent"
                    writer.writerow([
                        index, 
                        student.username, 
                        f"{student.first_name} {student.last_name}", 
                        student.email, 
                        status
                    ])
                
                return response
                
            # Handle regular attendance submission
            attended = request.POST.getlist('attendence')
            print(attended)

            now = date.today()
            dt_string = now.strftime("%d/%m/%Y")

            # Date already present
            if dt_string in list(attendence):
                attendee = attendence.get(dt_string)   #Getting todays dict of presentee

                for student in attendee:
                    studentAttendence[student] = studentAttendence.get(student,0) - 1

                attendence[dt_string] = {}
                attendee = {}

                for student in attended:          #Traversing todays list of presentee list
                    studentAttendence[student] = studentAttendence.get(student,0) + 1
                    attendee[student]=True
                attendence[dt_string] = attendee

            #Date not present
            else:
                # Update total class conducted
                attendenceObject.totalClassConducted += 1
                temp = {}
                attendence[dt_string] = temp
                attendee = attendence.get(dt_string)   #Getting todays set of presentee
                for student in attended:          #Traversing todays list of presentee list
                    if student not in attendee:
                        studentAttendence[student] = studentAttendence.get(student,0) + 1
                    attendee[student]=True
                attendence[dt_string] = attendee

            attendenceStr = json.dumps(attendence)
            studentAttendenceStr = json.dumps(studentAttendence)
            attendenceObject.attendenceList = attendenceStr
            attendenceObject.studentAttendence = studentAttendenceStr
            attendenceObject.save()

            messages.success(request,'Attendence Updated Successfully')

            return redirect(request.path_info)

        now = date.today()
        dt_string = now.strftime("%d/%m/%Y")
        todayPresent = {}
        # Date already present
        if dt_string in list(attendence):
            todayPresent = attendence[dt_string]
        else:
            todayPresent ={}

        # Get all dates with attendance for the dropdown
        attendance_dates = list(attendence.keys())
        attendance_dates.sort(reverse=True)  # Most recent first

        print(attendence)
        context = {
            'students' : students,
            'status' : status,
            'id':id,
            'todayPresent' : todayPresent,
            'userDetails' : userDetails,
            'attendance_dates': attendance_dates,
            'current_date': dt_string
        }
        return render(request,'faculty/facultyAttendencePage.html',context)
    else:
        return redirect('facultyLogin')




# Function to get assignment Submission link and time
@login_required
def assignmentSubmissions(request,pk):
    if request.user.is_active and request.user.is_staff and not request.user.is_superuser:
        id = pk

        user=request.user
        userDetails = FacultyDetails.objects.get(facultyId_id = user.pk)

        assignment = Assignment.objects.get(assignmentId = id)
        assignmentDict = json.loads(assignment.assignmentSubmission)

        classId = assignment.classId
        studentListObject = ClassroomStudentsList.objects.get(classId = classId)
        studentListDict = json.loads(studentListObject.studentList)
        studentList = [*studentListDict]
        students = []
        for x in studentList:
            temp = User.objects.get(username = x)
            students.append(temp)
        context = {
            'assignments' : assignmentDict,
            'students' : students,
            'userDetails' : userDetails,
            'classId': classId
        }


        return render(request,'faculty/assignmentSubmissionList.html',context)
    else:
        return redirect('facultyLogin')

# Faculty Meeting
@login_required
def facultyMeeting(request, pk):
    if request.user.is_active and request.user.is_staff and not request.user.is_superuser:
        id = pk
        user = request.user
        classDetails = ClassRoom.objects.get(classId=id)
        userDetails = FacultyDetails.objects.get(facultyId_id=user.pk)
        
        if request.method == 'POST':
            if 'createMeeting' in request.POST:
                title = request.POST['title']
                description = request.POST['description']
                meetingLink = request.POST['meetingLink']
                meetingDate = request.POST['meetingDate']
                meetingTime = request.POST['meetingTime']
                
                # Process the meeting creation
                # Here we would normally save this to a Meeting model
                # Since there's no Meeting model yet, we'll update the class link
                classDetails.classLink = meetingLink
                classDetails.save()
                
                messages.success(request, 'Meeting scheduled successfully')
                return redirect(request.path_info)
                
            if 'updateMeetingLink' in request.POST:
                meetLink = request.POST['meetLink']
                classDetails.classLink = meetLink
                classDetails.save()
                messages.success(request, 'Meeting Link Updated')
                return redirect(request.path_info)
                
        # Calculate total students
        studentListObject = ClassroomStudentsList.objects.get(classId=id)
        studentListDict = json.loads(studentListObject.studentList)
        totalStudents = len(studentListDict)
        
        context = {
            'id': id,
            'classDetails': classDetails,
            'userDetails': userDetails,
            'totalStudents': totalStudents,
        }
        
        return render(request, 'faculty/facultyMeeting.html', context)
    else:
        return redirect('facultyLogin')

# -----------------------------------
# Student Section
# -----------------------------------


# Login View
def studentLogin(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        try:
            detail = User.objects.get(email=email)
            username = detail.username
            # Add debugging messages
            print(f"Found student with email {email}, username: {username}")
        except User.DoesNotExist:
            # Add debugging for user not found
            print(f"Student with email {email} not found")
            username = 'Temp'
        
        user = authenticate(username=username, password=password)
        # Add debugging for authentication results
        print(f"Authentication result: {user}")
        
        if user is not None:
            login(request, user)
            return redirect('studentDashboard')
        else:
            messages.error(request, "Invalid Credentials")
            return redirect('studentLogin')
    return render(request,'student/studentLogin.html')

# Register View
def studentRegister(request):
    if request.method=='POST':
        first_name = request.POST['fname']
        last_name = request.POST['lname']
        email = request.POST['email']
        password = request.POST['password']
        gender = request.POST['gender']
        dob = request.POST['dob']
        contact = request.POST['contact']
        institute = request.POST['institute']
        department = request.POST['department']
        state = request.POST['state']
        yearOfStudy = request.POST['yos']
        about = request.POST['about']
        profilePic = request.FILES.get('profilePic')

        # print(profilePic)
        # Generating unique username
        num = random.randint(10000000, 99999999)
        str1 = 'ES'
        unique_id = str1 + str(num)
        username=unique_id
        # End Generating unique username

        full_name = first_name + last_name

        if User.objects.filter(email=email).exists():
            messages.error(request,'You Already have an account. Please Log In')
            return redirect('studentLogin')
        else:
            user = User.objects.create_user(username=username,password=password,email=email,first_name=first_name,last_name=last_name)
            user.is_staff=False;
            user.is_superuser=False;
            user.save()

            u_id = User.objects.get(username=username)

            student = StudentDetails(studentId=u_id,studentName=full_name,studentPhone=contact,studentGender=gender,studentDOB = dob,
                            studentDesc=about,studentCollege=institute,collegeState=state,yearOfStudy=yearOfStudy,studentPic=profilePic,studentDepartment = department)

            student.save()

            # Creating StudentClassroomList object
            my_dict={}
            input = json.dumps(my_dict)
            studentClassroomList = StudentClassroomList(studentId_id = user.pk, classList = input)
            studentClassroomList.save()
            # End Creating StudentClassroomList object


            # Registration Confirmation Email
            role_user_email = user.email
            # role_user_email = 'rahul.agarwal31101999@gmail.com'
            mail_subject = "[Welcome Student] - You have successfully registered to VirtualClassroom!!"
            message = render_to_string('register_successful.html', {
                'firstname': user.first_name,
                'lastname': user.last_name,
                'unique_id' : unique_id
            })

            email = EmailMessage(mail_subject, message, from_email=EMAIL_HOST_USER, to=[role_user_email])
            email.send()
            # End Registration Confirmation Email

            messages.success(request,'You are now registered')
            return redirect('studentLogin')
    return render(request,'student/studentRegister.html')

# Logout View
@login_required
def studentLogout(request):
    if request.user.is_active and not request.user.is_staff and not request.user.is_superuser:
        auth.logout(request)
        return render(request, 'student/studentLogout.html')
    else:
        return redirect('studentLogin')


# Dashboard View
@login_required
def studentDashboard(request):
    if request.user.is_active and not request.user.is_staff and not request.user.is_superuser:

        # Getting user details
        user = request.user
        student = StudentDetails.objects.get(studentId = user.pk)
        userDetails = StudentDetails.objects.get(studentId = user.pk)

        # Getting classroom list joined by student
        classRoomList = StudentClassroomList.objects.get(studentId_id = user.pk)
        dict = json.loads(classRoomList.classList)
        temp = [*dict]
        classList =[]
        for x in temp:
            temp = ClassRoom.objects.get(classId = x)
            classList.append(temp)
        # ends
        
        # Get attendance rate for all classes
        attendance_rate = "0%"
        total_classes_attended = 0
        total_classes_conducted = 0
        
        for classroom in classList:
            try:
                attendence_obj = Attendence.objects.get(classId=classroom.pk)
                attendence_list = json.loads(attendence_obj.studentAttendence)
                classes_conducted = attendence_obj.totalClassConducted
                classes_attended = 0
                
                if user.username in attendence_list:
                    classes_attended = int(attendence_list.get(user.username, 0))
                
                total_classes_attended += classes_attended
                total_classes_conducted += classes_conducted
            except Attendence.DoesNotExist:
                pass
        
        if total_classes_conducted > 0:
            attendance_percentage = round((total_classes_attended / total_classes_conducted) * 100, 1)
            attendance_rate = f"{attendance_percentage}%"
        
        # Get pending assignments
        pending_assignments = []
        for classroom in classList:
            try:
                assignments = Assignment.objects.filter(classId=classroom.pk)
                for assignment in assignments:
                    submission_dict = json.loads(assignment.assignmentSubmission)
                    if str(userDetails) not in submission_dict:
                        pending_assignments.append({
                            'title': assignment.assignmentHeading,
                            'class_name': classroom.classname,
                            'faculty_name': classroom.classFacultyName,
                            'description': assignment.assignmentDescription,
                            'due_date': assignment.assignmentDueTime,
                            'class_id': classroom.classId,
                            'id': assignment.assignmentId
                        })
            except:
                pass
        
        # Get upcoming classes (today's classes)
        upcoming_classes = []
        today = datetime.now().strftime('%A')  # Current day name
        
        for classroom in classList:
            try:
                timetable = {}
                str_time = classroom.classTimeTable
                if str_time:
                    days = str_time.split('+')
                    for x in days:
                        curr = x.split(',')
                        a = curr[0][1:]
                        a = a.strip().strip("\'")
                        b = curr[1]
                        b = b.strip().strip("\'")
                        c = curr[2][:len(curr[2])-1]
                        c = c.strip().strip("\'")
                        timetable[a] = [b, c]
                    
                    if today in timetable:
                        upcoming_classes.append({
                            'class_name': classroom.classname,
                            'start_time': timetable[today][0],
                            'end_time': timetable[today][1],
                            'faculty_name': classroom.classFacultyName
                        })
            except:
                pass

        if request.method == 'POST':
            if 'classJoin' in request.POST:
                classId = request.POST['classJoinCode']

                # datetime object containing current date and time
                now = datetime.now()
                # dd/mm/YY H:M:S format
                dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

                try:
                    getClass = ClassRoom.objects.get(classId = classId)
                except:
                    messages.error(request,"Invalid Class Code")
                    return redirect(request.path_info)


                try:
                    list = StudentClassroomList.objects.get(studentId = user.pk)
                    my_dict = json.loads(list.classList)
                    if classId in my_dict.keys():
                        return redirect('studentSubject',pk=classId)
                    else:
                        # print('----student not in classroom-------')
                        # classroom  added in student list of StudentClassroomList
                        my_dict[classId] = dt_string
                        input = json.dumps(my_dict)
                        list.classList = input
                        list.save()
                        # ends

                        # student addid in classroom list of ClassroomStudentsList
                        studentId_str = str(student.studentId)
                        classroomStudentsList = ClassroomStudentsList.objects.get(classId = classId)
                        studentList = classroomStudentsList.studentList
                        print(studentList)
                        my_dict = json.loads(studentList)
                        my_dict[studentId_str] = dt_string
                        input = json.dumps(my_dict)
                        classroomStudentsList.studentList = input
                        classroomStudentsList.save()
                        # ends
                        messages.success(request,"Classroom joined successfully")
                        return redirect('studentSubject',pk=classId)
                    return redirect(request.path_info)

                except(StudentClassroomList.DoesNotExist):
                    my_dict={}
                    my_dict[classId] = dt_string
                    input = json.dumps(my_dict)
                    list = StudentClassroomList(studentId_id = user.pk,classList = input)
                    list.save()
                    return redirect('studentSubject',pk=classId)

                return redirect(request.path_info)    # classJoin post ends
            return redirect(request.path_info)   #  post ends

        context={
            'classList': classList,
            'userDetails': userDetails,
            'all_courses': classList,
            'attendance_rate': attendance_rate,
            'pending_assignments': pending_assignments,
            'upcoming_classes': upcoming_classes
        }
        return render(request,'student/studentDashboard.html',context)

    else:
        return redirect('studentLogin')

# Profile View
@login_required
def studentProfile(request):
    if request.user.is_active and not request.user.is_staff and not request.user.is_superuser:
        user=request.user
        userDetails = StudentDetails.objects.get(studentId = user.pk)

        if request.method=='POST':
            contact = request.POST['contact']
            institute = request.POST['institute']
            state = request.POST['state']
            yos = request.POST['year']
            about = request.POST['about']
            department = request.POST['department']
            profilePic = request.FILES.get('profilePic')


            userDetails.studentPhone = contact
            userDetails.studentCollege = institute
            userDetails.collegeState = state
            userDetails.yearOfStudy = yos
            userDetails.studentDesc = about
            userDetails.studentDepartment = department

            if profilePic:
                userDetails.studentPic = profilePic

            userDetails.save()

            try:
                vaccine = VaccineStatus.objects.get(userId_id = user.pk)
                if 'vaccineDose' in request.POST:
                    totalDose = request.POST['vaccineDose']
                    vaccine.vaccineDose = totalDose
                else:
                    None
                vaccine.save()
            except:
                vaccine = VaccineStatus(userId_id = user.pk)
                if 'vaccineDose' in request.POST:
                    totalDose = request.POST['vaccineDose']
                    vaccine.vaccineDose = totalDose
                else:
                    None
                vaccine.save()


            return redirect(request.path_info)

        dose = 0
        try:
            vaccine = VaccineStatus.objects.get(userId = user.pk)
            print('------in-------')
            dose = vaccine.vaccineDose
        except:
            dose = 0

        context={
            'userDetails' : userDetails,
            'dose' : dose
        }
        return render(request,'student/studentProfile.html',context)
    else:
        return redirect('studentLogin')

# Student Subject View
@login_required
def studentSubject(request,pk):
    if request.user.is_active and not request.user.is_staff and not request.user.is_superuser:
        id = pk
        user = request.user
        
        try:
            # Get classroom and user details
            classroom = ClassRoom.objects.get(classId = id)
            details = StudentDetails.objects.get(studentId_id = user.pk)
            faculty = FacultyDetails.objects.get(facultyId_id = classroom.classFacultyID.pk)

            # Get attendance data - with error handling for JSON decode errors
            try:
                attendenceObject = Attendence.objects.get(classId = id)
                # Handle possible JSON decode errors
                try:
                    attendence = json.loads(attendenceObject.attendenceList)
                except json.JSONDecodeError:
                    attendence = {}
                    
                try:
                    studentAttendence = json.loads(attendenceObject.studentAttendence)
                except json.JSONDecodeError:
                    studentAttendence = {}
                    
                totalClass = attendenceObject.totalClassConducted
                totalPresent = studentAttendence.get(user.username, 0)
                
                if totalClass > 0:
                    attendencePercentage = int((totalPresent/totalClass) * 100)
                else:
                    attendencePercentage = 0
                    
                totalAbsent = totalClass - totalPresent
            except Attendence.DoesNotExist:
                # Create default values if no attendance record exists
                attendence = {}
                totalClass = 0
                totalPresent = 0
                totalAbsent = 0
                attendencePercentage = 0
            
            # Handle attendance download request
            if request.method == 'POST' and 'downloadAttendance' in request.POST:
                # Create response with CSV content
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="{user.username}_attendance_{classroom.classname}.csv"'
                
                # Create CSV writer
                writer = csv.writer(response)
                writer.writerow(['Date', 'Status'])
                
                # Add all attendance data
                for date, attendees in attendence.items():
                    status = "Present" if user.username in attendees else "Absent"
                    writer.writerow([date, status])
                
                # Add summary row
                writer.writerow(['', ''])
                writer.writerow(['Total Classes', totalClass])
                writer.writerow(['Classes Attended', totalPresent])
                writer.writerow(['Attendance Percentage', f"{attendencePercentage}%"])
                
                return response
            
            # Handle assignment submissions
            if request.method == 'POST' and 'postSubmission' in request.POST:
                assignmentId = request.POST['assignmentId']
                assignmentSubmission = request.POST['assignmentLink']

                assignment = Assignment.objects.get(assignmentId = assignmentId)
                try:
                    submissionDict = json.loads(assignment.assignmentSubmission)
                except json.JSONDecodeError:
                    submissionDict = {}
                
                now = datetime.now()
                # dd/mm/YY H:M:S format
                dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
                submissionDict[str(details)] = [assignmentSubmission, dt_string]
                assignmentJson = json.dumps(submissionDict)
                assignment.assignmentSubmission = assignmentJson
                assignment.save()

                messages.success(request, "Assignment Submitted Successfully")
                return redirect(request.path_info)
            
            # Handle offline/online mode options
            if request.method == 'POST':
                if 'optOffline' in request.POST:
                    offline = OfflineClass.objects.get(classId_id = id)
                    try:
                        studentList = json.loads(offline.studentList)
                    except json.JSONDecodeError:
                        studentList = {}
                        
                    studentList[user.username] = True
                    offline.studentList = json.dumps(studentList)
                    offline.save()
                    messages.success(request, "Opted for Offline Mode")
                    return redirect(request.path_info)

                if 'optOnline' in request.POST:
                    offline = OfflineClass.objects.get(classId_id = id)
                    try:
                        studentList = json.loads(offline.studentList)
                    except json.JSONDecodeError:
                        studentList = {}

                    if user.username in studentList:
                        del studentList[user.username]
                        
                    offline.studentList = json.dumps(studentList)
                    offline.save()

                    messages.success(request, "Opted for Online Mode")
                    return redirect(request.path_info)

            # Get timetable data
            try:
                if classroom.classTimeTable and classroom.classTimeTable.strip():
                    timeTable = {}
                    strTime = classroom.classTimeTable
                    
                    try:
                        days = strTime.split('+')
                        for x in days:
                            curr = x.split(',')
                            a = curr[0][1:]
                            a = a.strip().strip("\'")
                            b = curr[1]
                            b = b.strip().strip("\'")
                            c = curr[2][:len(curr[2])-1]
                            c = c.strip().strip("\'")
                            timeTable[a] = [b, c]
                    except (IndexError, ValueError):
                        timeTable = {}
                else:
                    timeTable = {}
            except:
                timeTable = {}
            
            # Feeds
            announcements = Announcement.objects.filter(classId = id).annotate(type=Value('announcement', CharField()))
            assignments = Assignment.objects.filter(classId = id).annotate(type=Value('assignment', CharField()))
            all_items = list(assignments) + list(announcements)
            all_items_feed = sorted(all_items, key=lambda obj: obj.publishedTime, reverse=True)
            
            # Get study materials
            materials = Material.objects.filter(classId = id).order_by('-publishedTime')
            
            # Offline Class Status
            try:
                classOfflineStatus = OfflineClass.objects.get(classId = id)
            except OfflineClass.DoesNotExist:
                # Create a default object if it doesn't exist
                classOfflineStatus = OfflineClass.objects.create(
                    classId=classroom,
                    offlineStatus="NO",
                    vaccineRequired=0,
                    classStrength=0,
                    studentList="{}"
                )

            eligible = False
            available = False
            opted = False
            
            try:
                vaccineStatus = VaccineStatus.objects.get(userId_id = user.pk)
                if vaccineStatus.vaccineDose >= classOfflineStatus.vaccineRequired:
                    eligible = True
            except VaccineStatus.DoesNotExist:
                eligible = False

            if classOfflineStatus.offlineStatus == 'NO':
                pass
            else:
                try:
                    classroomStudent = ClassroomStudentsList.objects.get(classId = id)
                    try:
                        studentListDict = json.loads(classroomStudent.studentList)
                    except json.JSONDecodeError:
                        studentListDict = {}
                        
                    totalClassStrength = len(studentListDict)
                    
                    try:
                        offlineStudentList = json.loads(classOfflineStatus.studentList)
                    except json.JSONDecodeError:
                        offlineStudentList = {}
                        
                    totalSeat = int((totalClassStrength * classOfflineStatus.classStrength)/100)
                    totalBooked = len(offlineStudentList)
                    
                    if user.username in offlineStudentList:
                        opted = True

                    if totalBooked < totalSeat:
                        available = True
                except ClassroomStudentsList.DoesNotExist:
                    pass

            context = {
                'class': classroom,
                'all_items_feed': all_items_feed,
                'totalConducted': totalClass,
                'totalAttended': totalPresent,
                'totalAbsent': totalAbsent,
                'attendencePercent': attendencePercentage,
                'userDetails': details,
                'timeTable': timeTable,
                'classOfflineStatus': classOfflineStatus,
                'eligible': eligible,
                'available': available,
                'opted': opted,
                'materials': materials
            }
            
            return render(request, 'student/studentSubject.html', context)
            
        except Exception as e:
            # Log the error and show a friendly error message
            print(f"Error in studentSubject view: {str(e)}")
            messages.error(request, "An error occurred while loading the classroom. Please try again later.")
            return redirect('studentDashboard')
            
    else:
        return redirect('studentLogin')

# Assignment View
@login_required
def studentAssignment(request):
    if request.user.is_active and not request.user.is_staff and not request.user.is_superuser:
        user = request.user
        userDetails = StudentDetails.objects.get(studentId=user.pk)
        
        # Get any assignments relevant to the student's courses
        studentClass = StudentClassroomList.objects.get(studentId=user.pk)
        student_classes = json.loads(studentClass.classList)
        
        pending_assignments = []
        completed_assignments = []
        
        for class_id in student_classes:
            assignments = Assignment.objects.filter(classId=class_id)
            for assignment in assignments:
                submission_data = json.loads(assignment.assignmentSubmission)
                if str(userDetails) in submission_data:
                    # This assignment has been submitted by the student
                    completed_assignments.append({
                        'id': assignment.assignmentId,
                        'title': assignment.assignmentHeading,
                        'description': assignment.assignmentDescription,
                        'due_date': assignment.assignmentDueTime,
                        'submission_date': submission_data[str(userDetails)][1],
                        'class_id': class_id,
                        # Get class details
                        'class_name': ClassRoom.objects.get(pk=class_id).classname,
                        'faculty_name': ClassRoom.objects.get(pk=class_id).classFacultyName
                    })
                else:
                    # This assignment is pending
                    pending_assignments.append({
                        'id': assignment.assignmentId,
                        'title': assignment.assignmentHeading,
                        'description': assignment.assignmentDescription,
                        'due_date': assignment.assignmentDueTime,
                        'class_id': class_id,
                        # Get class details
                        'class_name': ClassRoom.objects.get(pk=class_id).classname,
                        'faculty_name': ClassRoom.objects.get(pk=class_id).classFacultyName
                    })
        
        # Calculate statistics
        total_assignments = len(pending_assignments) + len(completed_assignments)
        completion_rate = 0
        if total_assignments > 0:
            completion_rate = int((len(completed_assignments) / total_assignments) * 100)
        
        context = {
            'userDetails': userDetails,
            'pending_assignments': pending_assignments,
            'completed_assignments': completed_assignments,
            'total_assignments': total_assignments,
            'completion_rate': completion_rate
        }
        
        return render(request, 'student/studentAssignment.html', context)
    else:
        return redirect('studentLogin')

# Student Classes View
@login_required
def studentClasses(request):
    if request.user.is_active and not request.user.is_staff and not request.user.is_superuser:
        # Getting user details
        user = request.user
        student = StudentDetails.objects.get(studentId = user.pk)
        userDetails = StudentDetails.objects.get(studentId = user.pk)

        # Getting classroom list joined by student
        classRoomList = StudentClassroomList.objects.get(studentId_id = user.pk)
        class_dict = json.loads(classRoomList.classList)
        class_ids = [*class_dict]
        all_courses = []
        
        for class_id in class_ids:
            try:
                classroom = ClassRoom.objects.get(classId = class_id)
                all_courses.append({
                    'classRoom': classroom,
                    'joined_date': class_dict[class_id]
                })
            except ClassRoom.DoesNotExist:
                continue
        
        context = {
            'all_courses': all_courses,
            'userDetails': userDetails
        }
        
        return render(request, 'student/studentClasses.html', context)
    else:
        return redirect('studentLogin')

# Forgot Password Views
def forgot_password(request):
    if request.method == 'POST':
        email = request.POST['email']
        user_type = request.POST.get('user_type', 'student')  # Default to student if not specified
        
        try:
            user = User.objects.get(email=email)
            
            # Generate password reset token
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            
            # Create reset link
            reset_link = f"{request.scheme}://{request.get_host()}/reset-password/{uid}/{token}/"
            
            # Send email with reset link
            mail_subject = "ATLAS - Password Reset"
            message = render_to_string('password_reset_email.html', {
                'user': user,
                'reset_link': reset_link,
                'user_type': user_type
            })
            
            email_message = EmailMessage(mail_subject, message, from_email=EMAIL_HOST_USER, to=[email])
            email_message.content_subtype = "html"  # Set the content type to HTML
            email_message.send()
            
            messages.success(request, "Password reset link has been sent to your email")
            if user_type == 'faculty':
                return redirect('facultyLogin')
            else:
                return redirect('studentLogin')
        
        except User.DoesNotExist:
            # Don't reveal that the user doesn't exist for security reasons
            messages.success(request, "If your email exists in our system, you'll receive a password reset link")
            if user_type == 'faculty':
                return redirect('facultyLogin')
            else:
                return redirect('studentLogin')
    
    return render(request, 'forgot_password.html')

def reset_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        
        # Verify the token is valid
        if default_token_generator.check_token(user, token):
            if request.method == 'POST':
                password = request.POST['password']
                confirm_password = request.POST['confirm_password']
                
                if password == confirm_password:
                    # Set the new password
                    user.set_password(password)
                    user.save()
                    
                    messages.success(request, "Your password has been reset successfully. You can now login with your new password.")
                    
                    # Determine if the user is faculty or student based on user properties
                    if user.is_staff:
                        return redirect('facultyLogin')
                    else:
                        return redirect('studentLogin')
                else:
                    messages.error(request, "Passwords do not match")
            
            return render(request, 'reset_password.html', {'uidb64': uidb64, 'token': token})
        else:
            messages.error(request, "The password reset link is invalid or has expired")
            return redirect('forgot_password')
    
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        messages.error(request, "The password reset link is invalid or has expired")
        return redirect('forgot_password')
