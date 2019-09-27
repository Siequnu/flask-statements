from flask import send_from_directory, current_app
from flask_login import current_user

import app.models
from app import db
from app.models import StatementProject, StatementUpload, StatementDownload, User
from app.files import models

from datetime import datetime, date
from dateutil import tz
import arrow, json, time

from app import executor

def current_user_is_project_owner (project_id):
	return current_user.id == StatementProject.query.get(project_id).user_id

def new_project_from_form (form):
	new_project = StatementProject(user_id=current_user.id, title=form.title.data, timestamp = datetime.now())
	db.session.add(new_project)
	db.session.commit()

def get_projects_needing_review():
	statement_project_data = db.session.query(StatementProject, User).join(User, StatementProject.user_id==User.id).all()
	# Get latest statement for each project
	projects_needing_review = []
	for project, user in statement_project_data:
		latest_statement = db.session.query(StatementUpload, User).join(
			User, StatementUpload.user_id==User.id).filter(
			StatementUpload.project_id==project.id).order_by(
			StatementUpload.timestamp.desc()).first()
		if latest_statement is not None:
			if latest_statement[1].is_admin is not True:
				project_dict = project.__dict__
				project_dict['total_uploads'] = len(db.session.query(StatementUpload).filter_by(project_id=project.id).all())
				project_dict['humanized_timestamp'] = arrow.get(project_dict['timestamp'], tz.gettz('Asia/Hong_Kong')).humanize()
				project_dict['project_owner_username'] = user.username
				project_dict['latest_upload_humanised_timestamp'] = arrow.get(latest_statement[0].timestamp, tz.gettz('Asia/Hong_Kong')).humanize()
				projects_needing_review.append(project_dict)
				
	
	return projects_needing_review
			
def delete_all_projects_and_statements_from_user_id (user_id):
	projects = StatementProject.query.filter_by(user_id=user_id).all()
	if projects is not None:
		for project in projects:
			delete_project(project.id) # This also deleted all statements for this project

		
def new_statement_from_form (form, project_id):
	file = form.statement_upload_file.data
	random_filename = app.files.models.save_file(file)
	original_filename = app.files.models.get_secure_filename(file.filename)

	new_statement = StatementUpload (project_id = project_id,
					user_id = current_user.id,
					original_filename = original_filename,
					filename = random_filename,
					description = form.description.data,
					timestamp = datetime.now())

	db.session.add(new_statement)
	db.session.commit()
	
	# Generate thumbnail
	executor.submit(app.files.models.get_thumbnail, new_statement.filename)
	
	
def download_statement (statement_id):
	download = StatementDownload(statement_id = statement_id,
								 user_id = current_user.id,
								 timestamp = datetime.now())
	db.session.add(download)
	db.session.commit()
	
	filename = StatementUpload.query.get(statement_id).filename
	original_filename = StatementUpload.query.get(statement_id).original_filename
	
	return send_from_directory(filename=filename, directory=current_app.config['UPLOAD_FOLDER'],
								   as_attachment = True, attachment_filename = original_filename)
	
def delete_project(project_id):
	# Delete statements
	statements = db.session.query(StatementUpload).filter_by(project_id=project_id).all()
	for statement in statements:
		delete_statement(statement.id)
	# Delete project
	StatementProject.query.filter_by(id=project_id).delete()
	db.session.commit()


def delete_statement (statement_id):
	try:
		StatementUpload.query.filter_by(id=statement_id).delete()
		db.session.commit()
		return True
	except:
		return False
	