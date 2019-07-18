from flask import render_template, flash, redirect, url_for, request, abort, current_app, session, Response
from flask_login import current_user, login_required

from app import db
import app.models
from app.models import StatementProject, User, StatementUpload
from app.statements import bp, models, forms

import arrow
from dateutil import tz
from datetime import datetime

from flask_weasyprint import HTML, render_pdf

@bp.route("/")
@login_required
def view_statements():
	if current_user.is_authenticated and app.models.is_admin(current_user.username):
		statement_projects_object = db.session.query(StatementProject, User).join(User, StatementProject.user_id==User.id).all()
		statement_projects = []
		for project, user in statement_projects_object:
			project_dict = project.__dict__
			project_dict['total_uploads'] = len(db.session.query(StatementUpload).filter_by(project_id=project.id).all())
			project_dict['latest_project_upload'] = db.session.query(StatementUpload).filter_by(
				project_id = project.id).order_by(StatementUpload.timestamp.desc()).first()
			if project_dict['latest_project_upload'] is not None:
				project_dict['latest_upload_humanized_timestamp'] = arrow.get(project_dict['latest_project_upload'].timestamp, tz.gettz('Asia/Hong_Kong')).humanize()
				project_dict['latest_upload_by_teacher'] = app.models.is_admin(User.query.get(project_dict['latest_project_upload'].user_id).username)
			statement_projects.append([project_dict, user])
		student_count = app.user.models.get_total_user_count()
		classes = app.assignments.models.get_all_class_info()
		return render_template('statements/statements.html',
							   title='Personal Statements',
							   admin = True,
							   statement_projects = statement_projects,
							   student_count = student_count,
							   classes = classes)
	elif current_user.is_authenticated:
		statement_projects_object = db.session.query(StatementProject).filter_by(user_id = current_user.id).all()
		statement_projects_array = []
		for project in statement_projects_object:
			project_dict = project.__dict__
			project_dict['total_uploads'] = len(db.session.query(StatementUpload).filter_by(project_id=project.id).all())
			project_dict['humanized_timestamp'] = arrow.get(project_dict['timestamp'], tz.gettz('Asia/Hong_Kong')).humanize()
			statement_projects_array.append(project_dict)
			
		return render_template('statements/statements.html', title='Personal Statements', statement_projects = statement_projects_array)
	abort(403)
	

@bp.route("/project/create", methods=['GET', 'POST'])
@login_required
def create_statement_project():
	if current_user.is_authenticated:
		form = forms.StatementProjectForm()
		if form.validate_on_submit():
			app.statements.models.new_project_from_form (form)
			flash('Project successfully created!', 'success')
			return redirect(url_for('statements.view_statements'))
		return render_template('statements/create_statement_project.html', title='Create Personal Statement Project', form=form)
	abort(403)
	
	
@bp.route('/project/edit/<project_id>', methods=['GET', 'POST'])
def edit_statement_project(project_id):
	if current_user.is_authenticated and app.models.is_admin(current_user.username):
		statement_project = StatementProject.query.get(project_id)
		form = app.statements.forms.StatementProjectForm(obj=statement_project)
		if form.validate_on_submit():
			statement_project.title = form.title.data
			db.session.commit()
			flash('Statement project edited successfully.', 'success')
			return redirect(url_for('statements.view_statements'))
		return render_template('statements/create_statement_project.html', title='Edit Personal Statement Project', form=form)
	
	
@bp.route("/project/view/<project_id>")
@login_required
def view_statement_project(project_id):
	# Only admin or owner of the project can access this
	if current_user.is_authenticated and app.models.is_admin(current_user.username) or app.statements.models.current_user_is_project_owner(project_id):
		statement_project_data = db.session.query(StatementProject, User).join(User, StatementProject.user_id==User.id).filter(StatementProject.id==project_id).all()
		statement_project_uploads = db.session.query(StatementUpload, User).join(User, StatementUpload.user_id==User.id).filter(StatementUpload.project_id==project_id).all()
		statement_project_array = []
		for statement, user in statement_project_uploads:
			statement_dict = statement.__dict__ # Convert SQL Alchemy object into dictionary
			statement_dict['humanized_timestamp'] = arrow.get(statement_dict['timestamp'], tz.gettz('Asia/Hong_Kong')).humanize()
			statement_project_array.append([statement_dict, user])
		project_owner_user_id = StatementProject.query.get(project_id).user_id
		return render_template('statements/view_statement_project.html',
							   title='View project',
							   statement_project_data = statement_project_data,
							   statement_project_uploads = statement_project_array,
							   project_id = project_id,
							   project_owner_user_id = project_owner_user_id,
							   admin = app.models.is_admin(current_user.username))
	abort(403)
	
	
@bp.route('/project/delete/<project_id>')
@login_required
def delete_project(project_id):
	if current_user.is_authenticated and app.models.is_admin(current_user.username):
		app.statements.models.delete_project(project_id)
		flash ('Statement deleted successfully', 'success')
		return redirect(url_for('statements.view_statements'))
	abort (403)

@bp.route('/upload/<project_id>', methods=['GET', 'POST'])
@login_required
def upload_statement(project_id):
	if current_user.is_authenticated and app.models.is_admin(current_user.username) or app.statements.models.current_user_is_project_owner(project_id):
		form = forms.StatementUploadForm()
		if form.validate_on_submit():
			app.statements.models.new_statement_from_form(form, project_id)
			flash('New personal statement successfully uploaded!', 'success')
			return redirect(url_for('statements.view_statement_project', project_id = project_id))
		return render_template('statements/upload_statement.html', title='Upload new personal statement', form=form)
	abort (403)


@bp.route('/download/<statement_id>')
@login_required
def download_statement(statement_id):
	try:
		project_id = db.session.query(StatementUpload, StatementProject).join(
			StatementProject, StatementUpload.project_id==StatementProject.id).filter(
			StatementUpload.id==statement_id).first().StatementProject.id
	except:
		flash ('This statement could not be found.', 'error')
		return redirect(url_for('statements.view_statements'))
	if current_user.is_authenticated and app.models.is_admin(current_user.username) or app.statements.models.current_user_is_project_owner(project_id):
		return app.statements.models.download_statement(statement_id)
	abort (403)


@bp.route('/delete/<statement_id>')
@login_required
def delete_statement(statement_id):
	if current_user.is_authenticated and app.models.is_admin(current_user.username):
		try:
			project_id = db.session.query(StatementUpload, StatementProject).join(
				StatementProject, StatementUpload.project_id==StatementProject.id).filter(
				StatementUpload.id==statement_id).first().StatementProject.id
		except:
			flash ('This statement could not be found.', 'error')
			return redirect(url_for('statements.view_statements'))
		if app.statements.models.delete_statement(statement_id):
			flash ('Successfully deleted the personal statement', 'success')
			return redirect(url_for('statements.view_statement_project', project_id = project_id))
		else:
			flash ('This statement could not be found.', 'error')
			return redirect(url_for('statements.view_statements'))
	abort (403)

	
@bp.route('/builder/pdf')
def statement_pdf(data):
	return render_template('statements/pdf_statement.html', data = data)
	
@bp.route('/builder', methods=['GET', 'POST'])
@login_required
def statement_builder():
	form = forms.StatementBuilderForm()
	if form.validate_on_submit():
		del form.submit # Don't show submit button on printed form
		html = statement_pdf(data = form.data)
		return render_pdf (HTML(string=html))
		
		
	return render_template('statements/statement_builder.html', title='Personal statement builder', form=form)