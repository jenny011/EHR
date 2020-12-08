from sys import exec_prefix
import os

from flask import Flask, render_template, redirect, url_for, request, json, jsonify, session, flash, make_response, abort, send_from_directory
from flask.globals import current_app
from flask.signals import appcontext_tearing_down, request_finished
from flask_login.utils import logout_user
from flask_login import login_user, logout_user, current_user, login_required
import collections
from itertools import count


from datetime import timedelta
from time import strftime
from numpy.core.arrayprint import TimedeltaFormat
from numpy.lib.function_base import select
from sqlalchemy.util.langhelpers import methods_equivalent

from werkzeug.utils import secure_filename
from EHR import app, db, login
#from flask import current_app as app
from EHR.model.models import *
from EHR.Controller import control_helper as helper
from EHR.Controller.control_helper import DATE_FORMAT, TIME_FORMAT, id2name

import datetime


#------------------------------common functionalities-------------------------------
#------------------------------common functionalities-------------------------------
#------------------------------common functionalities-------------------------------
#--- edit personal information ---
@app.route('/nurseSettings', methods=['GET'])
@app.route('/doctorSettings', methods=['GET'])
@app.route('/patientSettings', methods=['GET'])
def Settings():
	id = current_user.get_id()
	user, role_user = None, None

	if current_user.role == RoleEnum.patient:
		user, role_user = db.session.query(User, Patient).join(User).filter(User.id==id).first()
		return render_template("patientSettings.html",
					firstName=user.first_name,
					lastName=user.last_name,
					nationalID=role_user.id,
					email=user.email,
					phone=user.phone)

	elif current_user.role == RoleEnum.nurse:
		user, role_user = db.session.query(User, Nurse).join(User).filter(User.id==id).first()
	elif current_user.role == RoleEnum.doctor:
		user, role_user = db.session.query(User, Doctor).join(User).filter(User.id==id).first()
	hospital_id = helper.user2hosp(id, user.role.value)

	return render_template("doctorNurseSettings.html",
					hospitalID=hospital_id,
					deptID=role_user.department_id,
					firstName=user.first_name,
					lastName=user.last_name,
					licenseID=user.id,
					email=user.email,
					phone=user.phone)


@app.route('/doctorNurseUpdateInfo', methods=['POST'])
@app.route('/patientUpdateInfo', methods=['POST'])
def UpdateInfo():
	try:
		f_name = request.form['firstName']
		l_name = request.form['lastName']
		old_id = current_user.get_id()
		new_id = request.form['id']
		email = request.form['email']
		phone = request.form['phone']
		role_user = None
		user = None
		if current_user.role == RoleEnum.doctor:
			user, role_user = db.session.query(User, Doctor).join(User).filter(User.id==old_id).first()
		elif current_user.role == RoleEnum.nurse:
			user, role_user = db.session.query(User, Nurse).join(User).filter(User.id==old_id).first()
		elif current_user.role == RoleEnum.patient:
			user, role_user = db.session.query(User, Patient).join().filter(User.id==old_id).first()
		if not role_user or not user:
			return make_response(jsonify({'ret':"user not found"}))

		if old_id != new_id:
			user.id = new_id
		user.first_name = f_name
		user.last_name= l_name
		user.email= email
		user.phone = phone
		db.session.commit()

		# return make_response(jsonify({'ret':0, 'firstName': f_name, "lastName": l_name, "id": new_id, "email": email, "phone": phone}), 200)
		return make_response(jsonify({'ret':0}), 200)
	except:
		db.session.rollback()
		return make_response(jsonify({'ret':1, 'msg':'Please double check your License ID'}))



#------------------------------Admin-------------------------------
#------------------------------Admin-------------------------------
#------------------------------Admin-------------------------------
@app.route('/addHospital',methods=['POST'])
def addHospital():
	if not helper.check_admin_privilege():
		return redirect("/login")

	name = helper.get_from_form(request, 'name')
	phone = helper.get_from_form(request, 'phone')
	address = helper.get_from_form(request, 'address')
	description = helper.get_from_form(request, 'description')

	# check for duplicated hospital name
	res = Hospital.query.filter(Hospital.name == name).all()
	if res != []:
		return make_response(jsonify({'ret':'Duplicated Hospital Name'}))

	hos = Hospital(
		name=name,
		phone=phone,
		address=address,
		description=description
	)
	try:
		db.session.add(hos)
		db.session.commit()
	except:
		db.session.rollback()
		return make_response(jsonify({'ret': "Database error"}))

	return make_response(jsonify({'ret':0}))

@app.route('/addDepartment',methods=['POST'])
def addDepartment():
	if not helper.check_admin_privilege():
		return redirect("/login")

	hospital_id = helper.get_from_form(request, 'hospitalID')
	title = helper.get_from_form(request, 'title')
	phone = helper.get_from_form(request, 'phone')
	description = helper.get_from_form(request, 'description')

	# check for duplicated hospital name
	res = Department.query.filter(Department.title == title).all()
	if res != []:
		return make_response(jsonify({'ret':'Duplicated Department Name'}))

	dept = Department(
		hospital_id=hospital_id,
		title = title,
		phone=phone,
		description=description
	)
	try:
		db.session.add(dept)
		db.session.commit()
	except:
		db.session.rollback()
		return make_response(jsonify({'ret': "Database error"}))

	return make_response(jsonify({'ret':0}))


@app.route('/addLabReportType', methods=['POST'])
def addLabReportType():
	if not helper.check_admin_privilege():
		return redirect("/login")

	lr_type_value = helper.get_from_form(request, 'type')
	lr_description = helper.get_from_form(request, 'description')
	lr_type = Lab_report_type(
		type = lr_type_value,
		description = lr_description
	)
	db.session.add(lr_type)
	try:
		db.session.commit()
		return make_response(jsonify({'ret':0}))
	except:
		db.session.rollback()
		return make_response(jsonify({'ret':"Duplicate"}))


@app.route('/updateAffiliation', methods=['POST'])
def updateAffiliation():
	if not helper.check_admin_privilege():
		return redirect("/login")

	license_id = request.form['licenseID']
	hospital_id = request.form['hospitalID']
	dept_id = request.form['deptID']

	#check if dept belongs to hospital
	dept_hospital = Department.query.filter(Department.id==dept_id).one().hospital_id
	if hospital_id != str(dept_hospital):
		return make_response(jsonify({'ret': "Department and hospital don't match."}))

	user = User.query.get(license_id)
	if not user:
		return make_response(jsonify({'ret': "User doesn't exist."}))
	if user.role != RoleEnum.doctor and user.role != RoleEnum.nurse:
		return make_response(jsonify({'ret': "Invalid role."}))
	user.hospital_id = hospital_id
	user.dept_id = dept_id

	try:
		db.session.commit()
		return make_response(jsonify({'ret':0}))
	except:
		db.session.rollback()
		return make_response(jsonify({'ret':"Database error"}))