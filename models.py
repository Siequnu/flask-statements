from flask import send_from_directory, current_app
from flask_login import current_user

import app.models
from app import db
from app.models import StatementProject, StatementUpload, StatementDownload
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
	db.session.flush()
	
	# Generate thumbnail
	executor.submit(app.files.models.get_thumbnail, new_statement.filename)
	
	
def download_statement (statement_id):
	download = StatementDownload(statement_id = statement_id, user_id = current_user.id)
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


def delete_statement (statement_id):
	try:
		StatementUpload.query.filter_by(id=statement_id).delete()
		return True
	except:
		return False
	