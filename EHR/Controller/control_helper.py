from flask import request
from sqlalchemy.sql.sqltypes import String

from EHR.model.models import *
import math
import datetime
from operator import and_
from enum import Enum
from flask_login import current_user

TIME_FORMAT = "%H:%M"
DATE_FORMAT = "%Y-%m-%d"
id_name_map = {}

def check_doctor_privilege():
	if current_user.role.value == "doctor":
		return True
	return False

def check_nurse_privilege():
	if current_user.role.value == "nurse":
		return True
	return False

def check_admin_privilege():
	if current_user.role.value == "admin":
		return True
	return False

def check_patient_privilege():
	if current_user.role.value == "patient":
		return True
	return False

def StrOrNone(string):
	if string == "":
		return None
	return string

def get_from_form(request, field):
	if field in request.form:
		return request.form[field]
	else:
		return None

def paginate(db_obj):
	try:
		curr_page = int(request.form['currPage'])
		page_size = int(request.form['pageSize'])
	except:
		curr_page = int(request.args.get('currPage'))
		page_size = int(request.args.get('pageSize'))

	# n_offset = (curr_page-1) * page_size + 1
	n_offset = (curr_page-1) * page_size
	n_tot_records = db_obj.query.count()
	n_tot_page = n_tot_records // page_size + 1
	page_count = math.ceil(n_tot_records / page_size)

	return n_offset, n_tot_records, n_tot_page, page_count

def day2slotid(period: int, start_day=datetime.date.today()):
	next_d_slotid = [ res.id for res in (
										  Time_slot.query.filter(
											  Time_slot.slot_date<=start_day+timedelta(days=period),
											  Time_slot.slot_date>=start_day)).all()]
	return next_d_slotid


def segid2time(t_seg_id):
	return Time_segment.query.filter(Time_segment.t_seg_id==t_seg_id).one().t_seg_starttime

def load_id2name_map(mustLoad=False):
	if not mustLoad:
		if id_name_map:
			return
	print("load")
	users = User.query.with_entities(User.id, User.first_name, User.last_name)
	for u in users:
		id_name_map[u.id] = u.first_name + " " + u.last_name

def id2name(this_id:int)->String:
	# person = User.query.filter(User.id==this_id).first()
	person_name = id_name_map[this_id]
	return person_name


def dept_appts(user, direction=None, period=None, start_date=datetime.date.today()):
	"""
	check this nurse dept. all appointments, with specified time period
	"""

	deptID = None

	if user.role == RoleEnum.nurse:
		deptID = Nurse.query.filter(Nurse.id == user.id).first().department_id
	elif user.role == RoleEnum.doctor:
		deptID = Nurse.query.filter(Doctor.id == user.id).first().department_id

	if period is not None:
		same_dept_appts = Application.query.\
							join(Doctor, Doctor.id == Application.doctor_id).\
							join(Time_slot, Time_slot.id == Application.time_slot_id).\
								filter(
									Doctor.department_id == deptID,
									Time_slot.slot_date >= start_date,
									Time_slot.slot_date <= start_date + timedelta(days = period))
	else: #JZ
		if direction == "future":
			same_dept_appts = Application.query.\
							join(Doctor, Doctor.id == Application.doctor_id).\
							join(Time_slot, Time_slot.id == Application.time_slot_id).\
								filter(
									Doctor.department_id == deptID,
									Time_slot.slot_date >= start_date,
									Application.status == StatusEnum.approved)
		elif direction == "past":
			same_dept_appts = Application.query.\
							join(Doctor, Doctor.id == Application.doctor_id).\
							join(Time_slot, Time_slot.id == Application.time_slot_id).\
								filter(
									Doctor.department_id == deptID,
									Time_slot.slot_date <= start_date,
									Application.status == StatusEnum.finished)
		else:
			same_dept_appts = Application.query.\
							join(Doctor, Doctor.id == Application.doctor_id).\
								filter(
									Doctor.department_id == deptID)
	return same_dept_appts

def t_slotid2date(slot_id):
	slot_date = Time_slot.query.filter(Time_slot.id == slot_id).first().slot_date
	return slot_date

def t_slot2time(slot_id):
	slot_time = Time_segment.query.\
							join(Time_slot, Time_segment.t_seg_id == Time_slot.slot_seg_id).\
								filter(Time_slot.id == slot_id).first().t_seg_starttime
	return slot_time

def user2hosp(id, role):
	deptID = None
	if role == "nurse":
		deptID = Nurse.query.filter(Nurse.id == id).first().department_id
	elif role == "doctor":
		deptID = Nurse.query.filter(Doctor.id == id).first().department_id
	hospitalID = Department.query.filter(Department.id == deptID).first().hospital_id
	return hospitalID

def nurse_hosp2dept(nurseID):
	deptID = Nurse.query.filter(Nurse.id == nurseID).first().department_id
	hospitalID = Department.query.filter(Department.id == deptID).first().hospital_id
	dept_list,dept_name = hosp2dept(hospitalID)
	return dept_list,dept_name

def hosp2dept(hospitalID):
	dept_list = Department.query.filter(Department.hospital_id == hospitalID).all()
	return [dept_list[i].id for i in range(len(dept_list))],[dept_list[j].title for j in range(len(dept_list))]

def dept2doc(deptID):
	doctor_list = Doctor.query.filter(Doctor.department_id == deptID).all()
	return [doctor_list[i].id for i in range(len(doctor_list))]

def dept2doc_all(deptID):
	doctor_list = Doctor.query.join(Department, Doctor.department_id == Department.id).\
					join(Hospital,Department.hospital_id == Hospital.id).filter(Doctor.department_id == deptID).all()
	load_id2name_map()
	return [{"doctorID": doctor_list[i].id,
		 "doctorName": id2name(doctor_list[i].id),"hospital": doctor_list[i].department.hospital.name,"department": doctor_list[i].department.title} for i in range(len(doctor_list))]

def doc2slots(doctorID, period, start_date = datetime.date.today()):
	return Time_slot.query.filter(Time_slot.doctor_id == doctorID,Time_slot.slot_date >= start_date,
					   Time_slot.slot_date <= start_date + timedelta(days = period)).all()

def doc2slots_available(doctorID, period, start_date = datetime.date.today()):
	return Time_slot.query.filter(Time_slot.doctor_id == doctorID,Time_slot.slot_date >= start_date,
					   Time_slot.slot_date <= start_date + timedelta(days = period),Time_slot.n_total>Time_slot.n_booked).all()

def doc2appts(doctorID,period=0, start_date = datetime.date.today(), direction = "future",limit = 'yes'):
	if direction == 'future':
		if limit == 'yes':
			return Application.query.filter(Application.doctor_id == doctorID,
				Application.status == StatusEnum.approved,Application.date >= start_date, Application.date <= start_date + timedelta(days = period)).all()
		else:
			return Application.query.filter(Application.doctor_id == doctorID,
				Application.status == StatusEnum.approved,Application.date >= start_date).all()
	elif direction == 'past':
		if limit == 'yes':
			return Application.query.filter(Application.doctor_id == doctorID,
				Application.status == StatusEnum.finished,Application.date <= start_date, Application.date >= start_date - timedelta(days = period)).all()
		else:
			return Application.query.filter(Application.doctor_id == doctorID,
				Application.status == StatusEnum.finished,Application.date <= start_date).all()

def dept_to_doc(deptID):
	doctor_list = dept2doc(deptID)
	load_id2name_map()
	return [{"doctorID": doctor_list[i],
			"doctorName": id2name(doctor_list[i])} for i in range(len(doctor_list))]

def user2dept_name(id, role):
	deptID = None
	if role == "nurse":
		deptID = Nurse.query.filter(Nurse.id == id).first().department_id
	elif role == "doctor":
		deptID = Nurse.query.filter(Doctor.id == id).first().department_id
	dept_name = Department.query.filter(Department.id == deptID).first().title
	return dept_name
