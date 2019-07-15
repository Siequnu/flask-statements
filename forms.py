from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, SelectMultipleField, DateField, BooleanField, FormField, TextAreaField
from wtforms.validators import ValidationError, DataRequired
from flask_wtf.file import FileField, FileRequired
from app import db


class StatementProjectForm(FlaskForm):
	title = StringField('Project title:', validators=[DataRequired()])
	submit = SubmitField('Create new project...')
	
class StatementUploadForm(FlaskForm):
	statement_upload_file = FileField(label='File:')
	description = StringField('Comments or questions:', validators=[DataRequired()])
	submit = SubmitField('Upload new personal statement...')