from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, SelectMultipleField, DateField, BooleanField, FormField, TextAreaField
from wtforms.validators import ValidationError, DataRequired
from flask_wtf.file import FileField, FileRequired
from app import db


class StatementProjectForm(FlaskForm):
	title = StringField('Project title:', default = 'My personal statement project', validators=[DataRequired()])
	submit = SubmitField('Create new project...')
	
class StatementUploadForm(FlaskForm):
	statement_upload_file = FileField(label='File:')
	description = StringField('Comments or questions:', validators=[DataRequired()])
	submit = SubmitField('Upload new personal statement...')
	
class StatementBuilderForm (FlaskForm):
	question_one = TextAreaField ('Why are you applying for your chosen course?', validators=[DataRequired()])
	question_two = TextAreaField ('Why does this subject interest you?', validators=[DataRequired()])
	question_three = TextAreaField ("Why do you think you're suitable for the course?", validators=[DataRequired()])
	question_four = TextAreaField ('Do your current or previous studies relate to the course that you have chosen?', validators=[DataRequired()])
	question_five = TextAreaField ('Have you taken part in any other activities that demonstrate your interest in the course?', validators=[DataRequired()])
	
	submit = SubmitField('Next step >')