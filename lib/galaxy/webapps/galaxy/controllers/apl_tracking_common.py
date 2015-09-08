

# apl_tracking_common.py

# So that the user does not need to manually download all necessary modules,
# Galaxy comes equipped with all eggs (Python modules are stored in .egg files)
# necessary for Python to run. This just makes it more difficult to import
# certain modules.
from galaxy import eggs
eggs.require("SQLAlchemy")

import csv
import logging
import re
import datetime
import sys, traceback
from ast import literal_eval
import time
import shlex, subprocess, urllib
from galaxy import model, util, web
#from galaxy.model.orm import and_, func, select
from galaxy.security.validate_user_input import validate_email
from galaxy.web.base.controller import BaseUIController, UsesFormDefinitionsMixin
from galaxy.web.form_builder import build_select_field, CheckboxField, SelectField, TextField, TextArea, HiddenField
from galaxy.web.framework.helpers import grids, iff, time_ago

import sqlalchemy
from sqlalchemy.sql.expression import func
import psycopg2 as pg


log = logging.getLogger( __name__ )

# If a user gives an invalid ID, redirect them to some other page, forcing them to re-enter information
def invalid_id_redirect( trans, cntrller, obj_id, item='sample', action='browse_samples' ):
	status = 'error'
	message = "Invalid %s id (%s)" % (item, str(obj_id))
	return trans.response.send_redirect(web.url_for(controller=cntrller,
													action=action,
													status=status,
													message=message))


def isNoneOrEmptyOrBlankString (myString):
	# from http://stackoverflow.com/a/24534152
	# comment under: http://stackoverflow.com/questions/9573244/most-elegant-way-to-check-if-the-string-is-empty-in-python
	""" Returns True if string is None, '', ' ', or 'None'
	"""
	# sometimes my mako templates return None as u'None' - and I don't know how to fix this a better way
	# testing if the string is 'None' does the trick for now
	if myString:
		# catch any unicode characters that don't play nice when typecasted as str()
		# typecasting to str() necessary when integers are passed into this function
		try:
			if not str(myString).strip() or myString == 'None':
				return True
		except:
			return False
	else:
		return True
	return False

def formatNullString (myString):
	# from http://stackoverflow.com/a/24534152
	# comment under: http://stackoverflow.com/questions/9573244/most-elegant-way-to-check-if-the-string-is-empty-in-python
	""" Returns None if string is None, '', ' ', or 'None'
		else, returns the original string
	"""
	# sometimes my mako templates return None as u'None' - and I don't know how to fix this a better way
	# testing if the string is 'None' does the trick for now
	if myString:
		# catch any unicode characters that don't play nice when typecasted as str()
		# typecasting to str() necessary when integers are passed into this function
		try:
			if not str(myString).strip() or myString == 'None':
				return ''
		except:
			pass
	else:
		return ''
	return myString

def format_date (myDate):
	# from Evan's original code
	""" Formats an input date as YYYY-MM-DD
		Input format can be YYYYMMDD, MMDDYYYY, or MDYYYY
		and can have dashes or forward slashes separating the fields

		Dates can also begin with the letter 's'
		indicating a 'scheduled' date for Prophecy ID sample tracking
	"""

	# these regex assume no false dates (ex: 20140231) have been given
	bad_date = re.compile('^s?(?P<month>1[0-2]|0?[1-9])[/-]?(?P<day>0?[1-9]|[1-2][0-9]|3[0-1])[/-]?(?P<year>[1-2][0-9]{3})$')
	good_date = re.compile('^s?(?P<year>[1-2][0-9]{3})[/-]?(?P<month>0[1-9]|1[0-2])[/-]?(?P<day>[0-2][0-9]|3[0-1])$')

	if isNoneOrEmptyOrBlankString(myDate):
		newDate = None
	elif re.match(good_date, myDate):
		gdf = re.match(good_date, myDate)
		newDate = "%s" % (str(datetime.date( int(gdf.group('year')), int(gdf.group('month')), int(gdf.group('day')) )))
	elif re.match(bad_date, myDate):
		bdf = re.match(bad_date, myDate)
		newDate = "%s" % (str(datetime.date( int(bdf.group('year')), int(bdf.group('month')), int(bdf.group('day')) )))
	else:
		raise ValueError('Incorrect format for date: %s' % myDate)

	# add 's' back to beginning if necessary
	if myDate[0] == 's':
		newDate = 's%s' % newDate

	return newDate

def hyphen_range(s):
	# adapted from the comment by zongzhi liu at this site:
	# http://code.activestate.com/recipes/577279-generate-list-of-numbers-from-hyphenated-and-comma/
	""" yield each integer from a complex range string like "1-9,12, 15-20,23"

	>>> list(hyphen_range('1-9,12, 15-20,23'))
	[1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 15, 16, 17, 18, 19, 20, 23]

	>>> list(hyphen_range('1-9,12, 15-20,2-3-4'))
	Traceback (most recent call last):
		...
	ValueError: format error in 2-3-4
	"""

	# remove any characters from the string in case people do pass in full IDs
	s = re.sub('[_A-Za-z]', '', s)

	out = []
	for x in s.split(','):
		elem = x.split('-')
		if len(elem) == 1: # a number
			out.append(int(elem[0]))
		elif len(elem) == 2: # a range inclusive
			start, end = map(int, elem)
			for i in xrange(start, end+1):
				out.append(i)
		else: # more than one hyphen
			raise ValueError('Incorrect format for range of IDs: %s' % x)
	return out

def getIlluminaIndices ():
	""" Returns a dictionary of MiSeq index sequences
	"""

	out = {}

	out['n701'] = 'TAAGGCGA'
	out['n702'] = 'CGTACTAG'
	out['n703'] = 'AGGCAGAA'
	out['n704'] = 'TCCTGAGC'
	out['n705'] = 'GGACTCCT'
	out['n706'] = 'TAGGCATG'
	out['n707'] = 'CTCTCTAC'
	out['n708'] = 'CAGAGAGG'
	out['n709'] = 'GCTACGCT'
	out['n710'] = 'CGAGGCTG'
	out['n711'] = 'AAGAGGCA'
	out['n712'] = 'GTAGAGGA'
	out['n501'] = 'TAGATCGC'
	out['n502'] = 'CTCTCTAT'
	out['n503'] = 'TATCCTCT'
	out['n504'] = 'AGAGTAGA'
	out['n505'] = 'GTAAGGAG'
	out['n506'] = 'ACTGCATA'
	out['n507'] = 'AAGGAGTA'
	out['n508'] = 'CTAAGCCT'

	return out

# Though this is not strictly necessary, each grid typically has a unique Column class for each of the columns of its model class' table.
class SamplesGrid(grids.Grid):
	class IDColumn(grids.IntegerColumn):
		def get_value(self, trans, grid, sample):
			# Ensures that ID is displayed in a familiar, user-readable format.
			# APL samples are numbered up from SMP000000000 to SMP999999999
			return "SMP%09d" % sample.id
	class ParentIDColumn(grids.IntegerColumn):
		def get_value(self, trans, grid, sample):
			if isNoneOrEmptyOrBlankString(sample.parent_id):
				return ''
			else:
				return "SMP%09d" % sample.parent_id
	class NameColumn(grids.TextColumn):
		def get_value(self, trans, grid, sample):
			return formatNullString(sample.name)
	class SpeciesColumn(grids.TextColumn):
		def get_value(self, trans, grid, sample):
			return formatNullString(sample.species)
	class HostColumn(grids.TextColumn):
		def get_value(self, trans, grid, sample):
			return formatNullString(sample.host)
	class SampleTypeColumn(grids.TextColumn):
		def get_value(self, trans, grid, sample):
			return formatNullString(sample.sample_type)
	class CreatedDateColumn(grids.TextColumn):
		def get_value(self, trans, grid, sample):
			return formatNullString(sample.created)
	class UserColumn(grids.TextColumn):
		def get_value(self, trans, grid, sample):
			return formatNullString(trans.sa_session.query(trans.model.User).get(sample.user_id).username)
	class LabColumn(grids.TextColumn):
		def get_value(self, trans, grid, sample):
			return formatNullString(sample.lab)
	class ProjectColumn(grids.TextColumn):
		def get_value(self, trans, grid, sample):
			return formatNullString(sample.project)
	class ExperimentTypeColumn(grids.TextColumn):
		def get_value(self, trans, grid, sample):
			return formatNullString(sample.experiment_type)
	class NotesColumn(grids.TextColumn):
		def get_value(self, trans, grid, sample):
			return formatNullString(sample.notes)

	# Grid definition
	title = "Samples"
	template = "apl_tracking/grid.mako"
	# Very important - Galaxy assumes that the table will closely or exactly match the columns of the model class.
	model_class = model.APLSample
	default_sort_key = "id"
	# All samples are in one large page if use_paging = False
	num_rows_per_page = 250
	use_paging = True
	default_filter = dict(deleted="False")
	# To see how the "link" argument works, see the apl_tracking.py browse_samples() method.
	# The "operation" argument causes the view_sample template to be displayed.
	# Invisible "deleted" column added to allow filtering by deletion state - only view deleted samples, only view active samples, etc.
	columns = [
		IDColumn("Sample ID",
				key="id",
				attach_popup=True,
				filterable="advanced"),
		ParentIDColumn("Parent ID",
						key="parent_id",
						link=(lambda item: iff(item.parent_id, dict(operation="view_sample", id=item.parent_id), None)),
						filterable="advanced"),
		NameColumn("Name",
					key="name",
					filterable="advanced"),
		SpeciesColumn("Species",
					key="species",
					filterable="advanced"),
		HostColumn("Host",
					key="host",
					filterable="advanced"),
		SampleTypeColumn("Sample Type",
						key="sample_type",
						filterable="advanced"),
		CreatedDateColumn("Date Created",
						key="created",
						filterable="advanced"),
		UserColumn("User",
					key="user",
					filterable=None),
		LabColumn("Lab",
				key="lab",
				filterable="advanced"),
		ProjectColumn("Project",
					key="project",
					filterable="advanced"),
		ExperimentTypeColumn("Experiment Type",
					key="experiment_type",
					filterable="advanced"),
		NotesColumn("Notes",
					key="notes",
					filterable="advanced"),
		grids.DeletedColumn("Deleted",
							key="deleted",
							visible=False,
							filterable="advanced")
	]

	operations = []


class ProphecySamplesGrid(grids.Grid):
	# Prophecy ID scheme is slightly default - 5 digits instead of 9
	class IDColumn(grids.IntegerColumn):
		def get_value(self, trans, grid, prophecy):
			return "PRO_%05d" % prophecy.id
	class SampleIDColumn(grids.IntegerColumn):
		def get_value(self, trans, grid, prophecy):
			if isNoneOrEmptyOrBlankString(prophecy.sample_id):
				return ''
			else:
				return "SMP%09d" % prophecy.sample_id
	class AssociatedSampleColumn(grids.TextColumn):
		def get_value(self, trans, grid, prophecy):
			return formatNullString(prophecy.associated_sample)
	class UsernameColumn(grids.TextColumn):
		def get_value(self, trans, grid, prophecy):
			return formatNullString(trans.sa_session.query(trans.model.User).get(trans.sa_session.query(trans.model.APLSample).get(prophecy.sample_id).user_id).username)
	class NameColumn(grids.TextColumn):
		def get_value(self, trans, grid, prophecy):
			return formatNullString(trans.sa_session.query(trans.model.APLSample).get(prophecy.sample_id).name)
	class RGTranscribedColumn(grids.TextColumn):
		def get_value(self, trans, grid, prophecy):
			return formatNullString(prophecy.rg_transcribed)
	class RGTransfectedColumn(grids.TextColumn):
		def get_value(self, trans, grid, prophecy):
			return formatNullString(prophecy.rg_transfected)
	class RGAmplificationColumn(grids.TextColumn):
		def get_value(self, trans, grid, prophecy):
			return formatNullString(prophecy.rg_amplification)
	class BulkExperimentColumn(grids.TextColumn):
		def get_value(self, trans, grid, prophecy):
			return formatNullString(prophecy.expt_bulk)
	class DropletExperimentColumn(grids.TextColumn):
		def get_value(self, trans, grid, prophecy):
			return formatNullString(prophecy.expt_droplet)
	class TCIDAnalysisColumn(grids.TextColumn):
		def get_value(self, trans, grid, prophecy):
			return formatNullString(prophecy.analysis_tcid50)
	class qPCRAnalysisColumn(grids.TextColumn):
		def get_value(self, trans, grid, prophecy):
			return formatNullString(prophecy.analysis_qpcr)
	class RNAIsolationColumn(grids.TextColumn):
		def get_value(self, trans, grid, prophecy):
			return formatNullString(prophecy.rna_isolation)
	class SequencingAnalysisColumn(grids.TextColumn):
		def get_value(self, trans, grid, prophecy):
			return formatNullString(prophecy.analysis_sequencing)
	class NotesColumn(grids.TextColumn):
		def get_value(self, trans, grids, prophecy):
			return formatNullString(prophecy.notes)

	# Grid definition
	title = "Prophecy Samples"
	template = "apl_tracking/grid.mako"
	model_class = model.APLProphecySample
	default_sort_key = "id"
	num_rows_per_page = 250
	use_paging = True
	default_filter = dict(deleted="False")
	columns = [
		IDColumn("Prophecy ID",
				key="id",
				attach_popup=True,
				filterable="advanced"),
		SampleIDColumn("Sample ID",
						key="sample_id",
						link=(lambda item: dict(operation="view_sample", id=item.sample_id))),
		AssociatedSampleColumn("Associated Sample",
								key="associated_sample",
								filterable="advanced"),
		UsernameColumn("User",
							key="username",
							filterable=None),
		NameColumn("Name",
							key="name",
							filterable=None),
#		RGTranscribedColumn("RG Transcription",
#							key="rg_transcribed",
#							filterable="advanced"),
		RGTransfectedColumn("RG Transfection",
							key="rg_transfected",
							filterable="advanced"),
		RGAmplificationColumn("RG Amplification",
								key="rg_amplification",
								filterable="advanced"),
		BulkExperimentColumn("Bulk Experiment",
								key="expt_bulk",
								filterable="advanced"),
		DropletExperimentColumn("Droplet Experiment",
								key="expt_droplet",
								filterable="advanced"),
		TCIDAnalysisColumn("TCID50 Analysis",
							key="analysis_tcid50",
							filterable="advanced"),
		qPCRAnalysisColumn("qPCR Analysis",
							key="analysis_qpcr",
							filterable="advanced"),
		RNAIsolationColumn("RNA Isolation",
							key="rna_isolation",
							filterable="advanced"),
		SequencingAnalysisColumn("Sequencing",
								key="analysis_sequencing",
								filterable="advanced"),
		NotesColumn("Notes",
					key="notes",
					filterable="advanced"),
		grids.DeletedColumn("Deleted",
							key="deleted",
							visible=False,
							filterable="advanced")
	]

	operations = []


class PrepsGrid(grids.Grid):
	class IDColumn(grids.IntegerColumn):
		def get_value(self, trans, grid, prep):
			return "APL%09d" % prep.id
	class SampleIDColumn(grids.IntegerColumn):
		def get_value(self, trans, grid, prep):
			if isNoneOrEmptyOrBlankString(prep.sample_id):
				return ''
			else:
				return "SMP%09d" % prep.sample_id
	class PrepDateColumn(grids.TextColumn):
		def get_value(self, trans, grid, prep):
			return formatNullString(prep.prep_date)
	class UserColumn(grids.TextColumn):
		def get_value(self, trans, grid, prep):
			return formatNullString(trans.sa_session.query(trans.model.User).get(prep.user_id).username)
	class NotesColumn(grids.TextColumn):
		def get_value(self, trans, grid, prep):
			return formatNullString(prep.notes)

	# Grid definition
	title = "Illumina Preps"
	template = "apl_tracking/grid.mako"
	model_class = model.APLPrep
	default_sort_key = "id"
	num_rows_per_page = 250
	use_paging = True
	default_filter = dict(deleted="False")
	columns = [
		IDColumn("Prep ID",
				key="id",
				link=(lambda item: dict(operation="edit_prep_info", id=item.id)),
				attach_popup=True,
				filterable="advanced"),
		SampleIDColumn("Sample ID",
						key="sample_id",
						link=(lambda item: dict(operation="view_sample", id=item.sample_id))),
		PrepDateColumn("Date Prepared",
						key="prep_date",
						filterable="advanced"),
		UserColumn("User",
					key="user",
					filterable="advanced"),
		NotesColumn("Notes",
					key="notes",
					filterable="advanced"),
		grids.DeletedColumn("Deleted",
							key="deleted",
							visible=False,
							filterable="advanced")
	]

	operations = []


class RunsGrid(grids.Grid):
	class IDColumn(grids.TextColumn):
		def get_value(self, trans, grid, run):
			return formatNullString(run.id)
	class RunDateColumn(grids.TextColumn):
		def get_value(self, trans, grid, run):
			return formatNullString(run.run_date)
	class UserColumn(grids.TextColumn):
		def get_value(self, trans, grid, run):
			return formatNullString(trans.sa_session.query(trans.model.User).get(run.user_id).username)
	class SequencerIDColumn(grids.TextColumn):
		def get_value(self, trans, grid, run):
			return formatNullString(run.sequencer_id)
	class NotesColumn(grids.TextColumn):
		def get_value(self, trans, grid, run):
			return formatNullString(run.notes)

	# Grid definition
	title = "Sequencing Runs"
	template = "apl_tracking/grid.mako"
	model_class = model.APLSequencingRun
	default_sort_key = "run_date"
	num_rows_per_page = 250
	use_paging = True
	default_filter = dict(deleted="False")
	columns = [
		IDColumn("ID",
				key="id",
#				link=(lambda item: dict(operation="edit_run_info", id=item.id)),
#				attach_popup=True,
				filterable="advanced"),
		RunDateColumn("Date Sequenced",
						key="run_date",
						filterable="advanced"),
		UserColumn("User",
					key="user",
					filterable="advanced"),
		SequencerIDColumn("Sequencer ID",
							key="sequencer_id",
								filterable="advanced"),
		NotesColumn("Notes",
					key="notes",
					filterable="advanced"),
		grids.DeletedColumn("Deleted",
							key="deleted",
							visible=False,
							filterable="advanced")
	]

	operations = []


class PrimerGrid(grids.Grid):
	class IDColumn(grids.IntegerColumn):
		def get_value(self, trans, grid, primer):
			return "PT_%05d" % primer.id
	class DesignDateColumn(grids.TextColumn):
		def get_value(self, trans, grid, primer):
			return formatNullString(primer.design_date)
	class UserColumn(grids.TextColumn):
		def get_value(self, trans, grid, primer):
			return formatNullString(trans.sa_session.query(trans.model.User).get(primer.user_id).username)
	class DescriptionColumn(grids.TextColumn):
		def get_value(self, trans, grid, primer):
			return formatNullString(primer.description)
	class SequenceColumn(grids.TextColumn):
		def get_value(self, trans, grid, primer):
			return formatNullString(primer.sequence)
	class SpeciesColumn(grids.IntegerColumn):
		def get_value(self, trans, grid, primer):
			if isNoneOrEmptyOrBlankString(primer.species):
				return ''
			else:
				return trans.sa_session.query(trans.model.APLOrganism).get(primer.species).name
	class ScaleColumn(grids.TextColumn):
		def get_value(self, trans, grid, primer):
			return formatNullString(primer.scale)
	class PurificationColumn(grids.TextColumn):
		def get_value(self, trans, grid, primer):
			return formatNullString(primer.purification)
	class NotesColumn(grids.TextColumn):
		def get_value(self, trans, grid, primer):
			return formatNullString(primer.notes)

	# Grid definition
	title = "Primers"
	template = "apl_tracking/grid.mako"
	model_class = model.APLPrimer
	default_sort_key = "id"
	num_rows_per_page = 250
	use_paging = True
	default_filter = dict(deleted="False")
	columns = [
		IDColumn("Primer ID",
				key="id",
				link=(lambda item: dict(operation="edit_prep_info", id=item.id)),
				attach_popup=True,
				filterable="advanced"),
		DesignDateColumn("Design date",
						key="design_date",
						filterable="advanced"),
		UserColumn("User",
					key="user",
					filterable="advanced"),
		DescriptionColumn("Description",
					key="description",
					filterable="advanced"),
		SequenceColumn("Sequence",
					key="sequence",
					filterable="advanced"),
		SpeciesColumn("Species",
					key="species",
					filterable="advanced"),
		ScaleColumn("Scale",
					key="scale",
					filterable="advanced"),
		PurificationColumn("Purification",
					key="purification",
					filterable="advanced"),
		NotesColumn("Notes",
					key="notes",
					filterable="advanced"),
		grids.DeletedColumn("Deleted",
							key="deleted",
							visible=False,
							filterable="advanced")
	]

	operations = []


#=====================================================================================================================================================

class APLTrackingCommon(BaseUIController, UsesFormDefinitionsMixin):
	""" Controller code for apl_tracking tab.
	"""

	# -------------------------------
	# Standard sample-related methods
	# -------------------------------

	# expose decorator creates a url for the create_sample method
	@web.expose
	@web.require_login("Add sample to samples table")
	def create_sample(self, trans, cntrller, **kwd):
		# is this an admin using the admin channel to create a sample?
		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		user_id_encoded = True
		user_id = kwd.get('user_id', 'none')
		if user_id != 'none':
			try:
				user = trans.sa_session.query( trans.model.User ).get( trans.security.decode_id( user_id ) )
			except TypeError as e:
				# We must have an email address rather than an encoded user id
				# This is because the galaxy.base.js creates a search+select box
				# when there are more than 20 items in a SelectField.

				# returns the first user with the correct email
				user = trans.sa_session.query( trans.model.User ) \
										.filter( trans.model.User.table.c.username==user_id ) \
										.first()
				user_id_encoded = False

		elif not is_admin:
			# assume no impersonation
			# Technically, the admin could impersonate another user, but we'll assume that that won't happen.
			user = trans.user
		else:
			user = None

		# The 'create_sample_button' is an attribute of the Web page that gets passed to parameters when the user saves their sample.
		if kwd.get('create_sample_button', False):
			name = kwd.get( 'name', '')
			if user is None:
				message = 'Invalid user ID (%s)' % str(user_id)
				status = 'error'
			elif not name:
				message = 'Error: No name'
				status = 'error'
			else:
				request = self.__save_sample(trans, cntrller, **kwd)
				message = 'The sample has been created.'
				return trans.response.send_redirect(web.url_for(controller=cntrller,
																action='browse_samples',
																message=message,
																status="done"))

		# Widgets to be rendered on the request form
		# This way, the template can be less terse and can merely take input from this method.
		widgets = []
		widgets.append(dict(label='Parent ID',
							widget=TextField('parent_id', 10, kwd.get('parent_id', '')),
							helptext='Leave input blank if sample has no parent (Required)'))
		widgets.append(dict(label='Name',
							widget=TextField('name', 200, kwd.get('name', '')),
							helptext='(Required)'))
		widgets.append(dict(label='Species',
							widget=TextField('species', 50, kwd.get('species', '')),
							helptext='(Required)'))
		widgets.append(dict(label='Sample Type',
							widget=TextField('sample_type', 50, kwd.get('sample_type', '')),
							helptext='(Required)'))
		widgets.append(dict(label='Date Created',
							widget=TextField('created', 8, kwd.get('created', str(datetime.date.today()))),
							helptext='Format: YYYY-MM-DD (Required)'))
		widgets.append(dict(label='User',
							widget=TextField('user_id', 8, kwd.get('user_id', trans.sa_session.query(trans.model.User).get(trans.user.id).username)),
							helptext='(Required)'))
		widgets.append(dict(label='Lab',
							widget=TextField('lab', 100, kwd.get('lab', '')),
							helptext='(Required)'))
		widgets.append(dict(label='Project',
							widget=TextField('project', 200, kwd.get('project', '')),
							helptext='(Required)'))
		widgets.append(dict(label='Experiment Type',
							widget=TextField('experiment_type', 200, kwd.get('experiment_type', '')),
							helptext='(Required)'))
		widgets.append(dict(label='Notes',
							widget=	TextArea('notes', size="10x30", value=kwd.get('notes', '')),
							helptext='(Optional)'))

		return trans.fill_template('/apl_tracking/sample/create_sample.mako',
									cntrller=cntrller,
									widgets=widgets,
									message=message,
									status=status)


	@web.expose
	@web.require_login("Edit samples")
	def edit_sample_info(self, trans, cntrller, **kwd):
		message = ''
		status = 'done'
		sample_id = kwd.get('id', None)

		# pull out variables that need format-checking
		parent_id = kwd.get('parent_id', '')
		species = kwd.get('species', '')
		host = kwd.get('host', '')
		created = kwd.get('created', '')
		sample_user = kwd.get('user_id', '')

		try:
			sample = trans.sa_session.query(trans.model.APLSample).get(trans.security.decode_id(sample_id))
		except:
			return invalid_id_redirect(trans, cntrller, sample_id)

		if kwd.get('edit_sample_info_button', False):

			# check formatting for attributes that need format-checking

			# check that user exists
			try:
				sample_user_id = trans.sa_session.query(trans.model.User)\
											.filter(trans.model.User.table.c.username == sample_user)\
											.first()\
											.id
			except:
				message = 'Error: User does not exist: %s' % sample_user
				status = 'error'

			# check formatting of created date
			try:
				test = format_date(created)
			except Exception as e:
				if not isNoneOrEmptyOrBlankString(created):
					message = 'Error: %s' % e
					status = 'error'

			# check that host exists in the organism table
			if not isNoneOrEmptyOrBlankString(host):
				try:
					test_host = trans.sa_session.query(trans.model.APLOrganism)\
								.filter(trans.model.APLOrganism.table.c.dbkey == host).first()
					if test_host == None:
						message = 'Error: Host species is not present in the Organism table: %s' % host
						status = 'error'
				except Exception as e:
						message = 'Error: %s' % e
						status = 'error'

			# check that species exists in the organism table
			if not isNoneOrEmptyOrBlankString(species):
				try:
					test_species = trans.sa_session.query(trans.model.APLOrganism)\
								.filter(trans.model.APLOrganism.table.c.dbkey == species).first()
					if test_species == None:
						message = 'Error: This species is not present in the Organism table: %s' % species
						status = 'error'
				except Exception as e:
						message = 'Error: %s' % e
						status = 'error'

			# check that parent ID is formatted properly and exists in the database
			try:
				test = int(re.sub('^SMP0*', '', parent_id))
				test_sample = trans.sa_session.query(trans.model.APLSample).get(test)
				if test_sample == None:
					message = 'Error: parent ID does not exist: %s' % test
					status = 'error'
			except Exception as e:
				if not isNoneOrEmptyOrBlankString(parent_id):
					message = 'Error: %s' % e
					status = 'error'

			if status != 'error':
				sample = self.__save_sample(trans, cntrller, sample=sample, **kwd)
				message = 'The changes made to sample (SMP%09d) have been saved.' % sample.id
				return trans.response.send_redirect(web.url_for(controller=cntrller,
																action='browse_samples',
																message=message,
																status="done"))
		# Widgets to be rendered on the request form
		widgets = []
		widgets.append(dict(label='Parent ID',
							widget=TextField('parent_id', 10, kwd.get('parent_id', sample.parent_id)),
							helptext='(Optional - leave blank if sample has no parent)'))
		widgets.append(dict(label='Name',
							widget=TextField('name', 200, kwd.get('name', sample.name)),
							helptext='(Required)'))
		widgets.append(dict(label='Species',
							widget=TextField('species', 50, kwd.get('species', sample.species)),
							helptext='(Required)'))
		widgets.append(dict(label='Host',
							widget=TextField('host', 50, kwd.get('host', sample.host)),
							helptext='(Optional)'))
		widgets.append(dict(label='Sample Type',
							widget=TextField('sample_type', 50, kwd.get('sample_type', sample.sample_type)),
							helptext='(Required)'))
		widgets.append(dict(label='Date Created',
							widget=TextField('created', 8, kwd.get('created', sample.created)),
							helptext='Format: YYYY-MM-DD'))
		widgets.append(dict(label='User',
							widget=TextField('user_id', 8, kwd.get('user_id', trans.sa_session.query(trans.model.User).get(sample.user_id).username)),
							helptext='(Required)'))
		widgets.append(dict(label='Lab',
							widget=TextField('lab', 100, kwd.get('lab', sample.lab)),
							helptext='(Required)'))
		widgets.append(dict(label='Project',
							widget=TextField('project', 200, kwd.get('project', sample.project)),
							helptext='(Required)'))
		widgets.append(dict(label='Experiment Type',
							widget=TextField('experiment_type', 200, kwd.get('experiment_type', sample.experiment_type)),
							helptext='(Optional)'))
		widgets.append(dict(label='Notes',
#							widget=TextArea('notes', size="10x30", value=kwd.get('notes', sample.notes)),
							value=kwd.get('notes', formatNullString(sample.notes)),
							helptext='(Optional)'))

		return trans.fill_template('/apl_tracking/sample/edit_sample_info.mako',
									cntrller=cntrller,
									sample=sample,
									widgets=widgets,
									message=message,
									status=status)


	def __save_sample( self, trans, cntrller, sample=None, **kwd ):
		""" Saves changes to an existing sample, or creates a new one if one does not already exist
		"""

#		is_admin = trans.user_is_admin()

#		if is_admin:
			# The admin user is creating a sample on behalf of another user
#			user_id = kwd.get('user_id', '')
#			if user_id == '':
#				user = trans.user
#			else:
#				user = trans.sa_session.query(trans.model.User).get(trans.security.decode_id(user_id))
#		else:
#			user = trans.user

		parent_id = kwd.get('parent_id', None)
		name = kwd.get('name', None)
		species = kwd.get('species', None)
		host = kwd.get('host', None)
		sample_type = kwd.get('sample_type', None)
		created = kwd.get('created', None)
		sample_user = kwd.get('user_id', None)
		lab = kwd.get('lab', None)
		project = kwd.get('project', None)
		experiment_type = kwd.get('experiment_type', None)
		notes = kwd.get('notes', None)

		data = [parent_id, name, species, host, sample_type, created, sample_user, lab, project, experiment_type, notes]

		# Deal with any empty strings or UTF-8 encoding
		for i in range(0, len(data)):
			if isNoneOrEmptyOrBlankString(data[i]):
				data[i] = None
			try:
				data[i] = data[i].decode('utf-8')
			except:
				pass

		# format parent_id to integer if it exists
		try:
			data[0] = int(re.sub('^SMP0*', '', data[0]))
		except:
			data[0] = None

		# format created as a date
		try:
			data[5] = format_date(data[5])
		except:
			data[5] = None

		# pull out user ID
		sample_user_id = trans.sa_session.query(trans.model.User)\
										.filter(trans.model.User.table.c.username == sample_user)\
										.first()\
										.id


		if sample is None:
			sample = trans.model.APLSample(data[0], data[1], data[2], data[3], data[4], data[5], sample_user_id, data[7], data[8], data[9],
											notes=data[10])
			# These are SQLAlchemy methods, not galaxy methods!
			trans.sa_session.add(sample)
			trans.sa_session.flush()
			trans.sa_session.refresh(sample)

		else:
			# We're saving changes to an existing request
			sample.parent_id = data[0]
			sample.name = data[1]
			sample.species = data[2]
			sample.host = data[3]
			sample.sample_type = data[4]
			sample.created = data[5]
			sample.user_id = sample_user_id
			sample.lab = data[7]
			sample.project = data[8]
			sample.experiment_type = data[9]
			sample.notes = data[10]
			trans.sa_session.add(sample)
			trans.sa_session.flush()

		return sample


	@web.expose
	@web.require_login("View sample")
	def view_sample(self, trans, cntrller, **kwd):
#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get('status', 'done')
		sample_id = kwd.get('id', None)
		try:
			sample = trans.sa_session.query(trans.model.APLSample).get(trans.security.decode_id(sample_id))
		except:
			return invalid_id_redirect(trans, cntrller, sample_id)

		return trans.fill_template('/apl_tracking/sample/view_sample.mako',
									cntrller=cntrller,
									sample=sample,
									status=status,
									message=message)


	@web.expose
	@web.require_login( "Delete samples" )
	def delete_samples( self, trans, cntrller, **kwd ):
		sample_ids = kwd.get( 'id', '' )
		message = kwd.get( 'message', '' )
		status = kwd.get( 'status', 'done' )
		is_admin = trans.user_is_admin()
		num_deleted = 0
		not_deleted = []
		num_prophecy = 0

		for id in sample_ids:
			ok_for_now = True
			is_prophecy = True

			try:
				# This block will handle bots that do not send valid sample ids.
				sample = trans.sa_session.query(trans.model.APLSample).get(trans.security.decode_id(id))
			except:
				ok_for_now = False

			try:
				prophecy = trans.sa_session.query(trans.model.APLProphecySample).\
					filter(trans.model.APLProphecySample.table.c.sample_id == trans.security.decode_id(id)).\
					first()
			except:
				is_prophecy = False

			if ok_for_now:
				if is_admin:
					# Nothing is ever actually deleted. We keep all data in the database, we just block samples from view by "deleting" them.
					sample.deleted = True
					trans.sa_session.add(sample)
					trans.sa_session.flush()
					num_deleted += 1
				else:
					not_deleted.append(sample)
				if is_prophecy and prophecy is not None:
					prophecy.deleted = True
					trans.sa_session.add(prophecy)
					trans.sa_session.flush()
					num_prophecy += 1

		message += '%i samples have been deleted.' % num_deleted

		if num_prophecy > 1:
			message += '%i Prophecy samples have been deleted' % num_prophecy

		if not_deleted:
			message += '  Contact the administrator to delete the following samples: '
			for request in not_deleted:
				message += '%s, ' % request.name
			message = message.rstrip( ', ' )
		return trans.response.send_redirect(web.url_for(controller=cntrller,
														action='browse_samples',
														status=status,
														message=message))

	@web.expose
	@web.require_login( "Undelete samples" )
	def undelete_samples( self, trans, cntrller, **kwd ):
		sample_ids = kwd.get('id', '')
		message = kwd.get( 'message', '' )
		status = kwd.get( 'status', 'done' )
		num_undeleted = 0
		num_prophecy = 0
		for id in sample_ids:
			ok_for_now = True
			is_prophecy = True
			try:
				# This block will handle bots that do not send valid sample ids.
				sample = trans.sa_session.query(trans.model.APLSample).get(trans.security.decode_id(id))
			except:
				ok_for_now = False

			try:
				prophecy = trans.sa_session.query(trans.model.APLProphecySample)\
											.filter(trans.model.APLProphecySample.table.c.sample_id == trans.security.decode_id(id))\
											.first()
			except:
				is_prophecy = False

			if ok_for_now:
				sample.deleted = False
				trans.sa_session.add(sample)
				trans.sa_session.flush()
				num_undeleted += 1

				if is_prophecy and prophecy is not None:
					prophecy.deleted = False
					trans.sa_session.add(prophecy)
					trans.sa_session.flush()
					num_prophecy += 1

		message += '%i samples have been undeleted.' % num_undeleted
		if num_prophecy > 1:
			message += '%i Prophecy samples have been undeleted' % num_prophecy
		return trans.response.send_redirect(web.url_for(controller=cntrller,
															action='browse_samples',
															status=status,
															message=message))

	@web.expose
	@web.require_login("Import samples from text file")
	def import_samples(self, trans, cntrller, **kwd):
#		is_admin = trans.user_is_admin()
		message = ''
		status = 'done'
		file = kwd.get('file_data', '')

		# create template file
		filepath = '/var/www/html/publicshare/samplesheets'
		filename = '%s/import_sample_template.txt' % filepath
		f = open(filename, 'w')
		f.write('parent_id\tsample_name\tspecies\thost\tsample_type\tdate_created\tlab\tproject\texperiment_type\tnotes\n')
		f.close()

		if kwd.get('import_samples_button', False):
			try:
				if isNoneOrEmptyOrBlankString(str(file)):
					raise Exception("Please select a file")
				else:
					parameters = self.__import_sample(trans, cntrller, **kwd)
					return trans.fill_template('/apl_tracking/sample/review_sample_import.mako',
												cntrller=cntrller,
												parameters=parameters,
												message=None,
												status="done")

					return trans.response.send_redirect(web.url_for(controller='apl_tracking',
																	action='browse_samples',
																	message=message,
																	status='done'))
			except Exception as e:
				if str(e)[0:3] == '302':
					message = urllib.unquote_plus(str(e).split('message=')[1])
				else:
					message = str(e);
				status = 'error'

		return trans.fill_template('/apl_tracking/sample/import_samples.mako',
									cntrller=cntrller,
									message=message,
									status=status)


	def __import_sample(self, trans, cntrller, **kwd):
		""" Reads a tab-separated file, checks the values, and sends the data to be reviewed
		"""

#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get( 'status', 'done' )

#		try:
# this is most definitely incorrect - 'user' does not exist as a variable
#			user_id = trans.sa_session.query(trans.model.User)\
#										.filter(trans.model.User.table.c.username==user)\
#										.first()\
#										.id
#		except:
#			user_id = trans.user.id

		# get file object from file that was imported
		# file_obj.file is equivalent to what would be returned by open("filename", "rb")
		file_obj = kwd.get('file_data', '')

		try:
			if isNoneOrEmptyOrBlankString(str(file_obj.file)):
				raise Exception("File does not exist")
			else:
				# pull value of current pointer
				# open connection to the galaxy database - I'd rather not do this, but I can't figure out how using SQLAlchemy
				conn = pg.connect("host=odin port=5477 dbname=galaxy_database user=galaxy password=galaxy")
				cur = conn.cursor()
				cur.execute("SELECT last_value FROM apl_sample_id_seq;")
				conn.commit()
				last_value = int(cur.fetchone()[0])
				cur.close()
				conn.close()

				# read in input file as single string
				opened = file_obj.file.read()
				# split by any possible line endings, remove empty lines
				lines = filter(None, re.split(r'[\n\r]+', opened))

				# pull off header, make sure it is correct
				header = lines[0].rstrip().split('\t')
				lines = lines[1:]
				if sorted(header) != sorted(['parent_id', 'sample_name', 'species', 'host', 'sample_type', 'date_created', 'lab', 'project', 'experiment_type', 'notes']):
					raise Exception('Header is not correct, make sure you use the provided template (your header: %s)' % header)

				new_samples = []

				# go through each line of input file
				for l,line in enumerate(lines):

					# make sure line is not entirely composed of whitespace
					if line.strip():

						# remove trailing whitespace, split input line, and nullify empty strings
						sample = line.rstrip().split('\t')

						for i in range(0, len(sample)):
							if isNoneOrEmptyOrBlankString(sample[i]):
								sample[i] = None
							else:
								# Deal with any UTF-8 encoding
								try:
									sample[i] = sample[i].rstrip().decode('utf-8')
								except:
									sample[i] = sample[i].rstrip()

						# make sure list is the correct length
						if len(sample) > 10:
							raise Exception('Sample in row %i contains %i columns (should contain 10)' % (l+1, len(sample)))
						while len(sample) < 10:
							sample.append(None)

						# check formatting for parent ID
						if not sample[0]:
							parent_id = None
						else:
							try:
								parent_id = int(re.sub('^SMP0*', '', sample[0]))
							except:
								raise Exception('Invalid parent ID (\'%s\') in row %i' % (sample[0], l+1))
							# make sure parent ID exists in sample table
							try:
								test_sample = trans.sa_session.query(trans.model.APLSample).get(sample[0])
								if test_sample == None:
									message = 'Sample ID does not exist: %s' % sample[0]
									status = 'error'
							except:
								message = 'Sample ID does not exist: %s' % sample[0]
								status = 'error'

						# make sure species exists in Organism table
						if not sample[2]:
							species = None
						else:
							try:
								test_species = trans.sa_session.query(trans.model.APLOrganism)\
											.filter(trans.model.APLOrganism.table.c.dbkey == sample[2]).first()
								if test_sample == None:
									message = 'Species does not exist in Organism table: %s' % sample[2]
									status = 'error'
							except:
								message = 'Species does not exist in Organism table: %s' % sample[2]
								status = 'error'

						# make sure host exists in Organism table
						if not sample[3]:
							host = None
						else:
							try:
								test_host = trans.sa_session.query(trans.model.APLOrganism)\
											.filter(trans.model.APLOrganism.table.c.dbkey == sample[3]).first()
								if test_sample == None:
									message = 'Host species does not exist in Organism table: %s' % sample[3]
									status = 'error'
							except:
								message = 'Host species does not exist in Organism table: %s' % sample[3]
								status = 'error'

						# check formatting for created date, make it today if it does not exist
						if sample[5] is not None:
							try:
								created = format_date(sample[5])
							except:
								raise Exception('Invalid created date (\'%s\') in row %i' % (sample[5], l+1))
						else:
							created = str(datetime.date.today())

						# I don't believe these need any format checking
						name = sample[1]
						sample_type = sample[4]
						user_id = trans.user.id
						lab = sample[6]
						project = sample[7]
						experiment_type = sample[8]
						if len(sample) == 10:
							notes = sample[9]
						else:
							notes = None

						new_samples.append([parent_id, name, species, host, sample_type, created, user_id, lab, project, experiment_type, notes])

				parameters = []
				parameters.append(dict(widget=HiddenField('last_value', last_value), value=last_value))
				parameters.append(dict(widget=HiddenField('samples', new_samples), value=new_samples))

				return parameters

		except Exception as e:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
			trans.sa_session.rollback()
			message = 'Error: %s.' % str( e )
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_samples',
															status='error',
															message=message))

	@web.expose
	@web.require_login("Review samples for import")
	def review_sample_import(self, trans, cntrller, **kwd):
#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get('status', 'done')
		last_value = int(kwd.get('last_value',''))
		samples = literal_eval(kwd.get('samples',''))

		if kwd.get('review_sample_import_button', False):
			# open connection to the galaxy database - I'd rather not do this, but I can't figure out how using SQLAlchemy
			conn = pg.connect("host=odin port=5477 dbname=galaxy_database user=galaxy password=galaxy")
			cur = conn.cursor()
			cur.execute("SELECT last_value FROM apl_sample_id_seq;")
			conn.commit()
			current_value = int(cur.fetchone()[0])
			cur.close()
			conn.close()

			# check to make sure last_value is still equal to the current_value
			if current_value != last_value:
				message = "The database has been modified since you began this edit.  Sample IDs have been updated.  Please try again."
				status = 'error'
				last_value = current_value
			else:
				message = self.__save_sample_import(trans, cntrller, **kwd)
				return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_samples',
															message=message,
															status='done'))

		if kwd.get('cancel_sample_import_button', False):
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_samples',
															message='Import canceled',
															status='done'))

		parameters = []
		parameters.append(dict(widget=HiddenField('last_value', last_value),
					value=last_value))
		parameters.append(dict(widget=HiddenField('samples', samples),
					value=samples))

		return trans.fill_template('/apl_tracking/sample/review_sample_import.mako',
									cntrller=cntrller,
									parameters=parameters,
									message=message,
									status=status)


	def __save_sample_import(self, trans, cntrller, **kwd):
		""" Saves a list of imported samples to the database
		"""

		# sanitize is set to False so that unicode characters in any fields are not destroyed
#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get( 'status', 'done' )

		last_value = int(kwd.get('last_value',''))
		samples = literal_eval(kwd.get('samples',''))

		try:
			# open connection to the galaxy database - I'd rather not do this, but I can't figure out how using SQLAlchemy
			conn = pg.connect("host=odin port=5477 dbname=galaxy_database user=galaxy password=galaxy")
			cur = conn.cursor()
			cur.execute("SELECT last_value FROM apl_sample_id_seq;")
			conn.commit()
			current_value = int(cur.fetchone()[0])
			cur.close()
			conn.close()

			# check to make sure last_value is still equal to the current_value
			if current_value != last_value:
				raise Exception("The database has been modified since you began this edit.  Please try again.")

			num_added = 0

			for sample in samples:
				for i,attr in enumerate(sample):
					try:
						sample[i] = sample[i].decode('utf-8')
					except:
						pass

				parent_id = sample[0]
				name = sample[1]
				species = sample[2]
				host = sample[3]
				sample_type = sample[4]
				created = sample[5]
				user_id = trans.user.id
				lab = sample[7]
				project = sample[8]
				experiment_type = sample[9]
				notes = sample[10]

				this_sample = trans.model.APLSample(parent_id, name, species, host, sample_type, created, user_id, lab, project,
													experiment_type, notes=notes)

				# These are SQLAlchemy methods, not galaxy methods!
				trans.sa_session.add(this_sample)
				trans.sa_session.flush()
				trans.sa_session.refresh(this_sample)

				num_added += 1

			message = '%i samples have been imported.' % num_added

			return message

		except Exception as e:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
			trans.sa_session.rollback()
			message = 'Error: %s.' % str( e )
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_samples',
															status='error',
															message=message))


	@web.expose
	@web.require_login("Edit a group of samples")
	def edit_sample_group(self, trans, cntrller, **kwd):
#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = 'done'

		sample_ids = kwd.get('sample_ids', '')
		attribute = kwd.get('attribute', '')
		new_value = kwd.get('new_value', None)
		try:
			sample_ids = sample_ids.decode('utf-8')
		except:
			pass
		try:
			new_value = new_value.decode('utf-8')
		except:
			pass

		if kwd.get('edit_sample_group_button', False):

			# check formatting for attributes that need format-checking

			# check to make sure user exists
			if attribute == 'user_id':
				try:
					user_id = trans.sa_session.query(trans.model.User)\
											.filter(trans.model.User.table.c.username==new_value)\
											.first()\
											.id
				except:
					message = 'Error: user does not exist: %s' % new_value
					status = 'error'

			# fix formatting of new_value in case it is a date
			if attribute == 'created':
				try:
					test = format_date(new_value)
				except:
					if not isNoneOrEmptyOrBlankString(new_value):
						message = 'Error: Invalid date format: %s' % new_value
						status = 'error'

			# check that host exists in the organism table
			if attribute == 'host':
				if not isNoneOrEmptyOrBlankString(new_value):
					try:
						test_host = trans.sa_session.query(trans.model.APLOrganism)\
									.filter(trans.model.APLOrganism.table.c.dbkey == new_value).first()
						if test_host == None:
							message = 'Error: Host species is not present in the Organism table: %s' % new_value
							status = 'error'
					except Exception as e:
							message = 'Error: %s' % e
							status = 'error'

			# check that species exists in the organism table
			if attribute == 'species':
				if not isNoneOrEmptyOrBlankString(new_value):
					try:
						test_species = trans.sa_session.query(trans.model.APLOrganism)\
									.filter(trans.model.APLOrganism.table.c.dbkey == new_value).first()
						if test_species == None:
							message = 'Error: This species is not present in the Organism table: %s' % new_value
							status = 'error'
					except Exception as e:
							message = 'Error: %s' % e
							status = 'error'

			# check formatting for parent ID
			if attribute == 'parent_id':
				try:
					test = int(re.sub('^SMP0*', '', new_value))
				except:
					if not isNoneOrEmptyOrBlankString(new_value):
						message = 'Error: Invalid parent ID format: %s' % new_value
						status = 'error'

			# check that sample IDs are formatted properly and exist in the database
			try:
				s = hyphen_range(sample_ids)
				good_ids = []
				problem_ids = []
				for i, id in enumerate(s):
					test_sample = trans.sa_session.query(trans.model.APLSample).get(id)
					if test_sample == None:
						problem_ids.append(id)
				if len(problem_ids) > 0:
					message = 'Error: These sample IDs do not exist (%s).' % problem_ids
					status = 'error'
			except:
				message = 'Error: Invalid format for sample IDs'
				status = 'error'

			if status != 'error':
				parameters = self.__edit_sample_group(trans, cntrller, **kwd)
				return trans.fill_template('/apl_tracking/sample/review_sample_group.mako',
											cntrller=cntrller,
											parameters=parameters,
											message=None,
											status="done")

				return trans.response.send_redirect(web.url_for(controller='apl_tracking',
																action='browse_samples',
																message=message,
																status='done'))

		attributes = SelectField('attribute', multiple=False)
		attributes.add_option('Parent ID', 'parent_id')
		attributes.add_option('Species', 'species')
		attributes.add_option('Host', 'host')
		attributes.add_option('Sample Type', 'sample_type')
		attributes.add_option('Date Created', 'created')
		attributes.add_option('User', 'user_id')
		attributes.add_option('Lab', 'lab')
		attributes.add_option('Project', 'project')
		attributes.add_option('Experiment Type', 'experiment_type')
		attributes.add_option('Notes', 'notes')

		widgets = []
		widgets.append(dict(label='Sample IDs',
							widget=TextField('sample_ids', 200, kwd.get('sample_ids','')),
							helptext='Use commas and dashes for multiple samples / sample ranges'))
		widgets.append(dict(label='Attribute',
							widget=attributes,
							helptext='Select the attribute you want to edit'))
		widgets.append(dict(label='New Value',
							widget=TextField('new_value', 200, kwd.get('new_value','')),
							helptext='Change the selected attribute to this value for all of the listed sample IDs'))

		return trans.fill_template('/apl_tracking/sample/edit_sample_group.mako',
									cntrller=cntrller,
									widgets=widgets,
									message=message,
									status=status)


	def __edit_sample_group(self, trans, cntrller, **kwd):
		""" Edit a large group of samples at once
		"""

		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get( 'status', 'done' )

		sample_ids = kwd.get('sample_ids', '')
		attribute = kwd.get('attribute', '')
		new_value = kwd.get('new_value', None)

		try:
			user_id = trans.sa_session.query(trans.model.User)\
										.filter(trans.model.User.table.c.username==user)\
										.first()\
										.id
		except:
			user_id = trans.user.id

		if not isNoneOrEmptyOrBlankString(sample_ids):
			try:
				# split sample_ids
				s = hyphen_range(sample_ids)

				# fix formatting of new_value if not empty
				if not isNoneOrEmptyOrBlankString(new_value):

					# remove any trailing spaces
					try:
						new_value = new_value.strip()
					except:
						pass
					# fix formatting of new_value in case it is unicode
					try:
						new_value = new_value.decode('utf-8')
					except:
						pass
					# check formatting for parent ID
					if attribute == 'parent_id':
						new_value = int(re.sub('^SMP0*', '', new_value))
					# fix formatting of new_value in case it is a date
					if attribute == 'created':
						new_value = format_date(new_value)

				parameters = []
				parameters.append(dict(widget=HiddenField('sample_ids', s),
							value=s))
				parameters.append(dict(widget=HiddenField('attribute', attribute),
							value=attribute))
				parameters.append(dict(widget=HiddenField('new_value', new_value),
							value=new_value))

				return parameters

			except Exception as e:
				exc_type, exc_value, exc_traceback = sys.exc_info()
				traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
				trans.sa_session.rollback()
				message = 'Error: %s.' % str( e )
				return trans.response.send_redirect(web.url_for(controller='apl_tracking',
																action='browse_samples',
																status='error',
																message=message))


	@web.expose
	@web.require_login("Edit a group of samples")
	def review_sample_group(self, trans, cntrller, **kwd):
		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get('status', 'done')

		if kwd.get('review_sample_group_button', False):
			message = self.__save_sample_group(trans, cntrller, **kwd)
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_samples',
															message=message,
															status='done'))

		if kwd.get('cancel_sample_group_button', False):
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_samples',
															message='Edit canceled',
															status='done'))

		return trans.fill_template('/apl_tracking/sample/review_sample_group.mako',
									cntrller=cntrller,
									parameters=parameters,
									message=None,
									status="done")


	def __save_sample_group(self, trans, cntrller, **kwd):
		""" Save changes to a large group of samples at once
		"""

#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get( 'status', 'done' )

		sample_ids = literal_eval(kwd.get('sample_ids', ''))
		attribute = kwd.get('attribute', '')
		new_value = kwd.get('new_value', None)

		# set new value to None if necessary
		if isNoneOrEmptyOrBlankString(new_value):
			new_value = None

		# deal with UTF-8 encoding
		try:
			new_value = new_value.decode('utf-8')
		except:
			pass

		# convert username to user ID if necessary
		if attribute == 'user_id':
			new_value = trans.sa_session.query(trans.model.User)\
										.filter(trans.model.User.table.c.username==new_value)\
										.first()\
										.id

		num_changed = 0

		# backup existing table
		backup_file = "/data/backups/apl-tables/apl_sample-%d" % (int(time.time()*1e9))
		args = shlex.split("pg_dump --port 5477 --username galaxy --format plain --ignore-version --verbose --file %s --table apl_sample galaxy_database" % (backup_file))
		p = subprocess.Popen(args)
		p.wait()

		try:
			# change attribute on all sample_ids to new_value
			for sample_id in sample_ids:

				sample = trans.sa_session.query(trans.model.APLSample).get(sample_id)
				setattr(sample, str(attribute), new_value)
				trans.sa_session.add(sample)
				trans.sa_session.flush()
				num_changed += 1

			message = '%i samples have been updated.' % num_changed

			return message

		except Exception as e:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
			trans.sa_session.rollback()
			message = 'Error: %s.' % str( e )
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_samples',
															status='error',
															message=message))


#=====================================================================================================================================================

	# ------------------------
	# Prophecy-specfic methods
	# ------------------------

	@web.expose
	@web.require_login("Add sample to Prophecy-specific samples table")
	def create_prophecy_sample(self, trans, cntrller, **kwd):
		# is this an admin using the admin channel to create a sample?
		is_admin = trans.user_is_admin()
		message = ''
		status = 'done'
		user_id = kwd.get('user_id', 'none')
		if user_id != 'none':
			try:
				user = trans.sa_session.query(trans.model.User).get(trans.security.decode_id(user_id))
			except TypeError as e:
				# We must have an email address rather than an encoded user id
				# This is because the galaxy.base.js creates a search+select box
				# when there are more than 20 items in a SelectField.

				# returns the first user with the correct email
				user = trans.sa_session.query( trans.model.User ) \
										.filter( trans.model.User.table.c.username==user_id ) \
										.first()
				user_id_encoded = False

		elif not is_admin:
			# assume no impersonation
			user = trans.user
		else:
			user = None

		# I'm not sure about 'create_sample_button' - I assume it's something we'll create or return from the template?
		if kwd.get('create_prophecy_sample_button', False):
			name = kwd.get( 'name', '')
			if user is None:
				message = 'Invalid user ID (%s)' % str(user_id)
				status = 'error'
			elif not name:
				message = 'Error: No name'
				status = 'error'
			else:
				request = self.__save_prophecy_sample(trans, cntrller, **kwd)
				message = 'The sample has been created.'
				if kwd.get('create_prophecy_sample_button', False):
					return trans.response.send_redirect(web.url_for(controller=cntrller,
																	action='browse_prophecies',
																	message=message,
																	status="done"))

		# Widgets to be rendered on the request form
		# not sure why they call these widgets - I think these will basically end up being interactive features
		widgets = []

		widgets.append(dict(label='Sample ID',
							widget=TextField('sample_id', 9, value=kwd.get('sample_id', '')),
							helptext='(Required)'))
		widgets.append(dict(label='Associated Sample',
							widget=TextField('associated_sample', 200, value=kwd.get('associated_sample', '')),
							helptext='(Required)'))
		widgets.append(dict(label='RG Transcribed',
							widget=TextField('rg_transcribed', 100, value=kwd.get('rg_transcribed', '')),
							helptext='(Required)'))
		widgets.append(dict(label='RG Transfected',
							widget=TextField('rg_transfected', 100, value=kwd.get('rg_transfected', '')),
							helptext='(Required)'))
		widgets.append(dict(label='RG Amplification',
							widget=TextField('rg_amplification', 100, value=kwd.get('rg_amplification', '')),
							helptext='(Required)'))
		widgets.append(dict(label='Bulk Experiment',
							widget=TextField('expt_bulk', 100, value=kwd.get('expt_bulk', '')),
							helptext='(Required)'))
		widgets.append(dict(label='Droplet Experiment',
							widget=TextField('expt_droplet',100, value=kwd.get('expt_droplet', '')),
							helptext='(Required)'))
		widgets.append(dict(label='TCID50 Analysis',
							widget=TextField('analysis_tcid50', 100, value=kwd.get('analysis_tcid50', '')),
							helptext='(Required)'))
		widgets.append(dict(label='qPCR Analysis',
							widget=TextField('analysis_qpcr', 100, value=kwd.get('analysis_qpcr', '')),
							helptext='(Required)'))
		widgets.append(dict(label='RNA Isolation',
							widget=TextField('rna_isolation', 100, value=kwd.get('rna_isolation', '')),
							helptext='(Required)'))
		widgets.append(dict(label='Sequencing',
							widget=TextField('analysis_sequencing', 100, value=kwd.get('analysis_sequencing', '')),
							helptext='(Required)'))
		widgets.append(dict(label='Notes',
							widget=	TextArea('notes', size="10x30", value=kwd.get('notes', '')),
							helptext='(Optional)'))

		return trans.fill_template('/apl_tracking/prophecy/create_samples.mako',
									cntrller=cntrller,
									widgets=widgets,
									message=message,
									status=status)


	@web.expose
	@web.require_login("Edit Prophecy samples")
	def edit_prophecy_sample_info(self, trans, cntrller, **kwd):
		message = ''
		status = 'done'
		prophecy_id = kwd.get('id', None)

		# pull out variables that need format-checking
		sample_id = kwd.get('sample_id', None)

		try:
			prophecy = trans.sa_session.query(trans.model.APLProphecySample).get(trans.security.decode_id(prophecy_id))
		except:
			return invalid_id_redirect(trans, cntrller, prophecy_id)

		if kwd.get( 'edit_prophecy_sample_info_button', False ):

			# check formatting for attributes that need format-checking

			# check that sample ID is formatted properly and exists in the database
			try:
				test = int(re.sub('^SMP0*', '', sample_id))
				test_sample = trans.sa_session.query(trans.model.APLSample).get(test)
				if test_sample == None:
					message = 'Sample ID does not exist: %s' % test
					status = 'error'
			except:
				message = 'Check formatting of Sample ID: %s' % sample_id
				status = 'error'

			if status != 'error':
				prophecy = self.__save_prophecy_sample( trans, cntrller, prophecy=prophecy, **kwd )
				message = 'The changes made to Prophecy sample (PRO_%05d) have been saved.' % prophecy.id
				return trans.response.send_redirect(web.url_for(controller=cntrller,
																action='browse_prophecies',
																message=message,
																status="done"))

		# Widgets to be rendered on the request form
		widgets = []

		widgets.append(dict(label='Sample ID',
							widget=TextField('sample_id', 10, kwd.get('sample_id', prophecy.sample_id)),
							helptext='(Required)'))
		widgets.append(dict(label='Associated Sample',
							widget=TextField('associated_sample', 200, value=kwd.get('associated_sample', prophecy.associated_sample)),
							helptext='(Optional)'))
		widgets.append(dict(label='RG Transcribed',
							widget=TextField('rg_transcribed', 100, value=kwd.get('rg_transcribed', prophecy.rg_transcribed)),
							helptext='(Required)'))
		widgets.append(dict(label='RG Transfected',
							widget=TextField('rg_transfected', 100, value=kwd.get('rg_transfected', prophecy.rg_transfected)),
							helptext='(Required)'))
		widgets.append(dict(label='RG Amplification',
							widget=TextField('rg_amplification', 100, value=kwd.get('rg_amplification', prophecy.rg_amplification)),
							helptext='(Required)'))
		widgets.append(dict(label='Bulk Experiment',
							widget=TextField('expt_bulk', 100, value=kwd.get('expt_bulk', prophecy.expt_bulk)),
							helptext='(Required)'))
		widgets.append(dict(label='Droplet Experiment',
							widget=TextField('expt_droplet',100, value=kwd.get('expt_droplet', prophecy.expt_droplet)),
							helptext='(Required)'))
		widgets.append(dict(label='TCID50 Analysis',
							widget=TextField('analysis_tcid50', 100, value=kwd.get('analysis_tcid50', prophecy.analysis_tcid50)),
							helptext='(Required)'))
		widgets.append(dict(label='qPCR Analysis',
							widget=TextField('analysis_qpcr', 100, value=kwd.get('analysis_qpcr', prophecy.analysis_qpcr)),
							helptext='(Required)'))
		widgets.append(dict(label='RNA Isolation',
							widget=TextField('rna_isolation', 100, value=kwd.get('rna_isolation', prophecy.rna_isolation)),
							helptext='(Required)'))
		widgets.append(dict(label='Sequencing',
							widget=TextField('analysis_sequencing', 100, value=kwd.get('analysis_sequencing', prophecy.analysis_sequencing)),
							helptext='(Required)'))
		widgets.append(dict(label='Notes',
#							widget=	TextArea('notes', size="10x30", value=kwd.get('notes', prophecy.notes)),
							value=kwd.get('notes', formatNullString(prophecy.notes)),
							helptext='(Optional)'))

		return trans.fill_template('/apl_tracking/prophecy/edit_sample_info.mako',
									cntrller=cntrller,
									prophecy=prophecy,
									widgets=widgets,
									message=message,
									status=status)


	def __save_prophecy_sample( self, trans, cntrller, prophecy=None, **kwd ):
		""" Saves changes to an existing sample, or creates a new
			sample if prophecy is None.
		"""

#		is_admin = trans.user_is_admin()

#		if is_admin:
#			# The admin user is creating a sample on behalf of another user
#			user_id = kwd.get('user_id', '')
#			if user_id == '':
#				user = trans.user
#			else:
#				user = trans.sa_session.query(trans.model.User).get(trans.security.decode_id(user_id))
#		else:
#			user = trans.user

		sample_id = kwd.get('sample_id', None)
		associated_sample = kwd.get('associated_sample', None)
		rg_transcribed = kwd.get('rg_transcribed', None)
		rg_transfected = kwd.get('rg_transfected', None)
		rg_amplification = kwd.get('rg_amplification', None)
		expt_bulk = kwd.get('expt_bulk', None)
		expt_droplet = kwd.get('expt_droplet', None)
		analysis_tcid50 = kwd.get('analysis_tcid50', None)
		analysis_qpcr = kwd.get('analysis_qpcr', None)
		rna_isolation = kwd.get('rna_isolation', None)
		analysis_sequencing = kwd.get('analysis_sequencing', None)
		notes = kwd.get('notes', None)

		data = [sample_id, associated_sample, rg_transcribed, rg_transfected, rg_amplification, expt_bulk, expt_droplet,
				analysis_tcid50, analysis_qpcr, rna_isolation, analysis_sequencing, notes]

		# Deal with any empty strings or UTF-8 encoding
		for i in range(0, len(data)):
			if isNoneOrEmptyOrBlankString(data[i]):
				data[i] = None
			try:
				data[i] = data[i].decode('utf-8')
			except:
				pass

		# Format any dates appropriately
		for i in range(2, len(data)-1):
			try:
				data[i] = format_date(data[i])
			except:
				pass

		if prophecy is None:
			prophecy = trans.model.APLProphecySample(data[0], data[1], data[2], data[3], data[4],
													data[5], data[6], data[7], data[8], data[9],
													data[10], notes=data[11])
			# These are SQLAlchemy methods, not galaxy methods!
			trans.sa_session.add(prophecy)
			trans.sa_session.flush()
			trans.sa_session.refresh(prophecy)

		else:
			# We're saving changes to an existing request
			prophecy.sample_id = data[0]
			prophecy.associated_sample = data[1]
			prophecy.rg_transcribed = data[2]
			prophecy.rg_transfected = data[3]
			prophecy.rg_amplification = data[4]
			prophecy.expt_bulk = data[5]
			prophecy.expt_droplet = data[6]
			prophecy.analysis_tcid50 = data[7]
			prophecy.analysis_qpcr = data[8]
			prophecy.rna_isolation = data[9]
			prophecy.analysis_sequencing = data[10]
			prophecy.notes = data[11]

			trans.sa_session.add(prophecy)
			trans.sa_session.flush()

		return prophecy


	@web.expose
	@web.require_login("View sample")
	def view_prophecy_sample(self, trans, cntrller, **kwd):
#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get('status', 'done')
		prophecy_id = kwd.get('id', None)
		try:
			prophecy = trans.sa_session.query(trans.model.APLProphecySample).get(trans.security.decode_id(prophecy_id))
		except:
			return invalid_id_redirect(trans, cntrller, prophecy_id)

		return trans.fill_template('/apl_tracking/prophecy/view_sample.mako',
									cntrller=cntrller,
									prophecy=prophecy,
									status=status,
									message=message)


	@web.expose
	@web.require_login("Create Prophecy samples")
	def create_prophecy_samples(self, trans, cntrller, **kwd):
#		is_admin = trans.user_is_admin()
		message = ''
		status = 'done'
		file = kwd.get('file_data', '')

		# create template file
		filepath = '/var/www/html/publicshare/samplesheets'
		filename = '%s/create_prophecy_template.txt' % filepath
		f = open(filename, 'w')
		f.write('sample_name\tspecies\n')
		f.close()

		if kwd.get('create_prophecy_samples_button', False):
			try:
				if isNoneOrEmptyOrBlankString(str(file)):
					raise Exception("Please select a file")
				else:
					parameters = self.__create_prophecy(trans, cntrller, **kwd)
					return trans.fill_template('/apl_tracking/prophecy/review_prophecy_create.mako',
												cntrller=cntrller,
												parameters=parameters,
												message=None,
												status="done")

					return trans.response.send_redirect(web.url_for(controller=cntrller,
																	action='browse_prophecies',
																	message=message,
																	status='done'))
			except Exception as e:
				if str(e)[0:3] == '302':
					message = urllib.unquote_plus(str(e).split('message=')[1])
				else:
					message = str(e);
				status = 'error'

		return trans.fill_template('/apl_tracking/prophecy/create_samples.mako',
									cntrller=cntrller,
									message=message,
									status=status)


	def __create_prophecy(self, trans, cntrller, **kwd):
		""" Reads a tab-separated file, checks the values, and sends the data to be reviewed
		"""

		message = kwd.get('message', '')
		status = kwd.get( 'status', 'done' )

		file_obj = kwd.get('file_data', '')

		try:
			if isNoneOrEmptyOrBlankString(str(file_obj.file)):
				raise Exception("File does not exist")
			else:
				# pull value of current pointer
				# open connection to the galaxy database - I'd rather not do this, but I can't figure out how using SQLAlchemy
				conn = pg.connect("host=odin port=5477 dbname=galaxy_database user=galaxy password=galaxy")
				cur = conn.cursor()
				cur.execute("SELECT last_value FROM apl_sample_id_seq;")
				conn.commit()
				last_sample = int(cur.fetchone()[0])
				cur.execute("SELECT last_value FROM apl_prophecy_sample_id_seq;")
				conn.commit()
				last_prophecy = int(cur.fetchone()[0])
				cur.close()
				conn.close()

				# read in input file as single string
				opened = file_obj.file.read()
				# split by any possible line endings, remove empty lines
				lines = filter(None, re.split(r'[\n\r]+', opened))

				# pull off header, make sure it is correct
				header = lines[0].rstrip().split('\t')
				if sorted(header) == sorted(['sample_name', 'species']):
					lines = lines[1:]

				new_samples = []

				# go through each line of input file
				for l,line in enumerate(lines):

					# make sure line is not entirely composed of whitespace
					if line.strip():

						# remove trailing whitespace, split input line, and nullify empty strings
						prophecy = line.rstrip().split('\t')
						for i in range(0, len(prophecy)):
							if isNoneOrEmptyOrBlankString(prophecy[i]):
								prophecy[i] = None
							else:
								# Deal with any UTF-8 encoding
								try:
									prophecy[i] = prophecy[i].rstrip().decode('utf-8')
								except:
									prophecy[i] = prophecy[i].rstrip()

						# make sure list is the correct length
						if len(prophecy) > 2:
							raise Exception('Sample in row %i contains %i columns (should contain 1 or 2)' % (l+1, len(prophecy)))
						while len(prophecy) < 2:
							prophecy.append(None)

						# store these values (formatted above)
						name = prophecy[0]
						if len(prophecy) == 2:
							species = prophecy[1]
						else:
							species = ''

						new_samples.append([name, species])

				parameters = []
				parameters.append(dict(widget=HiddenField('last_sample', last_sample), value=last_sample))
				parameters.append(dict(widget=HiddenField('last_prophecy', last_prophecy), value=last_prophecy))
				parameters.append(dict(widget=HiddenField('prophecies', new_samples), value=new_samples))

				return parameters

		except Exception as e:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
			trans.sa_session.rollback()
			message = 'Error: %s.' % str( e )
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_prophecies',
															status='error',
															message=message))

	@web.expose
	@web.require_login("Review Prophecy samples to create")
	def review_prophecy_create(self, trans, cntrller, **kwd):
#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get('status', 'done')
		last_sample = int(kwd.get('last_sample',''))
		last_prophecy = int(kwd.get('last_prophecy',''))
		prophecies = literal_eval(kwd.get('prophecies',''))

		if kwd.get('review_prophecy_create_button', False):
			# open connection to the galaxy database - I'd rather not do this, but I can't figure out how using SQLAlchemy
			conn = pg.connect("host=odin port=5477 dbname=galaxy_database user=galaxy password=galaxy")
			cur = conn.cursor()
			cur.execute("SELECT last_value FROM apl_sample_id_seq;")
			conn.commit()
			current_sample = int(cur.fetchone()[0])
			cur.execute("SELECT last_value FROM apl_prophecy_sample_id_seq;")
			conn.commit()
			current_prophecy = int(cur.fetchone()[0])
			cur.close()
			conn.close()

			# check to make sure last_value is still equal to the current_value
			if current_sample != last_sample or current_prophecy != last_prophecy:
				message = "The database has been modified since you began this edit.  Sample IDs have been updated.  Please try again."
				status = 'error'
				last_sample = current_sample
				last_prophecy = current_prophecy
			else:
				message = self.__save_prophecy_create(trans, cntrller, **kwd)
				return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_prophecies',
															message=message,
															status='done'))

		if kwd.get('cancel_prophecy_create_button', False):
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_prophecies',
															message='',
															status='done'))

		parameters = []
		parameters.append(dict(widget=HiddenField('last_sample', last_sample),
					value=last_sample))
		parameters.append(dict(widget=HiddenField('last_prophecy', last_prophecy),
					value=last_prophecy))
		parameters.append(dict(widget=HiddenField('prophecies', prophecies),
					value=prophecies))

		return trans.fill_template('/apl_tracking/sample/review_prophecy_create.mako',
									cntrller=cntrller,
									parameters=parameters,
									message=message,
									status=status)


	def __save_prophecy_create(self, trans, cntrller, **kwd):
		""" Saves a list of created samples to the database
		"""

		# sanitize is set to False so that unicode characters in any fields are not destroyed
#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get( 'status', 'done' )

		last_sample = int(kwd.get('last_sample',''))
		last_prophecy = int(kwd.get('last_prophecy',''))
		prophecies = literal_eval(kwd.get('prophecies',''))

		try:
			# open connection to the galaxy database - I'd rather not do this, but I can't figure out how using SQLAlchemy
			conn = pg.connect("host=odin port=5477 dbname=galaxy_database user=galaxy password=galaxy")
			cur = conn.cursor()
			cur.execute("SELECT last_value FROM apl_sample_id_seq;")
			conn.commit()
			current_sample = int(cur.fetchone()[0])
			cur.execute("SELECT last_value FROM apl_prophecy_sample_id_seq;")
			conn.commit()
			current_prophecy = int(cur.fetchone()[0])

			# check to make sure last_value is still equal to the current_value
			if current_sample != last_sample or current_prophecy != last_prophecy:
				raise Exception("The database has been modified since you began this edit.  Please try again.")

			num_added = 0

			# loop through every sample
			for i,prophecy in enumerate(prophecies):

				# deal with any unicode characters
				for j,attr in enumerate(prophecy):
					try:
						prophecy[i] = prophecy[i].decode('utf-8')
					except:
						pass

				name = prophecy[0]
				if prophecy[1]:
					species = prophecy[1]
				else:
					species = ''
				host = ''
				created = str(datetime.date.today())
				user_id = trans.user.id
				lab = 'APL'
				project = 'prophecy'

				parent_id = None
				sample_type = None
				experiment_type = None
				notes = None

				this_sample = trans.model.APLSample(parent_id, name, species, host, sample_type, created, user_id, lab, project,
													experiment_type, notes=notes)

				# These are SQLAlchemy methods, not galaxy methods!
				trans.sa_session.add(this_sample)
				trans.sa_session.flush()
				trans.sa_session.refresh(this_sample)

				sample_id = this_sample.id
				associated_sample = None
				rg_transcribed = None
				rg_transfected = None
				rg_amplification = None
				expt_bulk = None
				expt_droplet = None
				analysis_tcid50 = None
				analysis_qpcr = None
				rna_isolation = None
				analysis_sequencing = None

				this_prophecy = trans.model.APLProphecySample(sample_id, associated_sample,
															rg_transcribed, rg_transfected,
															rg_amplification, expt_bulk,
															expt_droplet, analysis_tcid50,
															analysis_qpcr, rna_isolation,
															analysis_sequencing, notes)

				# These are SQLAlchemy methods, not galaxy methods!
				trans.sa_session.add(this_prophecy)
				trans.sa_session.flush()
				trans.sa_session.refresh(this_prophecy)

				num_added += 1

			cur.close()
			conn.close()
			message = '%i samples have been created.' % num_added

			return message

		except Exception as e:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
			trans.sa_session.rollback()
			message = 'Error: %s.' % str( e )
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_prophecies',
															status='error',
															message=message))


	@web.expose
	@web.require_login("Import Prophecy samples from text file")
	def import_prophecy_samples(self, trans, cntrller, **kwd):
#		is_admin = trans.user_is_admin()
		message = ''
		status = 'done'
		file = kwd.get('file_data', '')

		# create template file
		filepath = '/var/www/html/publicshare/samplesheets'
		filename = '%s/import_prophecy_template.txt' % filepath
		f = open(filename, 'w')
		f.write('id\tassociated_sample\tname\tlab\trg_transfected\trg_amplification\texpt_bulk\texpt_droplet\tanalysis_tcid50\tanalysis_qpcr\trna_isolation\tanalysis_sequencing\tnotes\n')
		f.close()

		if kwd.get('import_prophecy_samples_button', False):
			try:
				if isNoneOrEmptyOrBlankString(str(file)):
					raise Exception("Please select a file")
				else:
					parameters = self.__import_prophecy(trans, cntrller, **kwd)
					return trans.fill_template('/apl_tracking/prophecy/review_prophecy_import.mako',
												cntrller=cntrller,
												parameters=parameters,
												message=None,
												status="done")

					return trans.response.send_redirect(web.url_for(controller=cntrller,
																	action='browse_prophecies',
																	message=message,
																	status='done'))
			except Exception as e:
				if str(e)[0:3] == '302':
					message = urllib.unquote_plus(str(e).split('message=')[1])
				else:
					message = str(e);
				status = 'error'

		return trans.fill_template('/apl_tracking/prophecy/import_samples.mako',
									cntrller=cntrller,
									message=message,
									status=status)


	def __import_prophecy(self, trans, cntrller, **kwd):
		""" Reads a tab-separated file, checks the values, and sends the data to be reviewed
		"""

#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get( 'status', 'done' )

#		try:
#			user_id = trans.sa_session.query(trans.model.User)\
#										.filter(trans.model.User.table.c.username==user)\
#										.first()\
#										.id
#		except:
#			user_id = trans.user.id

		# get file object from file that was imported
		# file_obj.file is equivalent to what would be returned by open("filename", "rb")
		file_obj = kwd.get('file_data', '')

		try:
			if isNoneOrEmptyOrBlankString(str(file_obj.file)):
				raise Exception("File does not exist")
			else:
				# pull value of current pointer
				# open connection to the galaxy database - I'd rather not do this, but I can't figure out how using SQLAlchemy
				conn = pg.connect("host=odin port=5477 dbname=galaxy_database user=galaxy password=galaxy")
				cur = conn.cursor()
				cur.execute("SELECT last_value FROM apl_sample_id_seq;")
				conn.commit()
				last_sample = int(cur.fetchone()[0])
				cur.execute("SELECT last_value FROM apl_prophecy_sample_id_seq;")
				conn.commit()
				last_prophecy = int(cur.fetchone()[0])
				cur.close()
				conn.close()

				# read in input file as single string
				opened = file_obj.file.read()
				# split by any possible line endings, remove empty lines
				lines = filter(None, re.split(r'[\n\r]+', opened))

				# pull off header, make sure it is correct
				header = lines[0].rstrip().split('\t')
				lines = lines[1:]
				if sorted(header) != sorted(['id', 'associated_sample', 'name', 'lab', 'rg_transfected', 'rg_amplification', 'expt_bulk', 'expt_droplet', 'analysis_tcid50', 'analysis_qpcr', 'rna_isolation', 'analysis_sequencing', 'notes']):
					raise Exception('Header is not correct, make sure you use the provided template (your header: %s)' % header)

				new_samples = []

				# go through each line of input file
				for l,line in enumerate(lines):

					# make sure line is not entirely composed of whitespace
					if line.strip():

						# remove trailing whitespace, split input line, and nullify empty strings
						prophecy = line.rstrip().split('\t')
						for i in range(0, len(prophecy)):
							if isNoneOrEmptyOrBlankString(prophecy[i]):
								prophecy[i] = None
							else:
								# Deal with any UTF-8 encoding
								try:
									prophecy[i] = prophecy[i].rstrip().decode('utf-8')
								except:
									prophecy[i] = prophecy[i].rstrip()
							if i >= 4 and i <= 11:
								try:
									prophecy[i] = format_date(prophecy[i])
								except:
									pass

						# make sure list is the correct length
						if len(prophecy) > 13:
							raise Exception('Prophecy sample in row %i contains %i columns (should contain 13)' % (l+1, len(prophecy)))
						while len(prophecy) < 13:
							prophecy.append(None)

						# store these values (formatted above)
						rg_transfected = prophecy[4]
						rg_amplification = prophecy[5]
						expt_bulk = prophecy[6]
						expt_droplet = prophecy[7]
						analysis_tcid50 = prophecy[8]
						analysis_qpcr = prophecy[9]
						rna_isolation = prophecy[10]
						analysis_sequencing = prophecy[11]

						# I don't believe these need any format checking
						associated_sample = prophecy[1]
						name = prophecy[2]
						lab = prophecy[3]
						if len(prophecy) == 13:
							notes = prophecy[12]
						else:
							notes = None

						new_samples.append([associated_sample, name, lab, rg_transfected, rg_amplification, expt_bulk, expt_droplet,
											analysis_tcid50, analysis_qpcr, rna_isolation, analysis_sequencing, notes])

				parameters = []
				parameters.append(dict(widget=HiddenField('last_sample', last_sample), value=last_sample))
				parameters.append(dict(widget=HiddenField('last_prophecy', last_prophecy), value=last_prophecy))
				parameters.append(dict(widget=HiddenField('prophecies', new_samples), value=new_samples))

				return parameters

		except Exception as e:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
			trans.sa_session.rollback()
			message = 'Error: %s.' % str( e )
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_prophecies',
															status='error',
															message=message))


	@web.expose
	@web.require_login("Review Prophecy samples for import")
	def review_prophecy_import(self, trans, cntrller, **kwd):
#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get('status', 'done')
		last_sample = int(kwd.get('last_sample',''))
		last_prophecy = int(kwd.get('last_prophecy',''))
		prophecies = literal_eval(kwd.get('prophecies',''))

		if kwd.get('review_prophecy_import_button', False):
			# open connection to the galaxy database - I'd rather not do this, but I can't figure out how using SQLAlchemy
			conn = pg.connect("host=odin port=5477 dbname=galaxy_database user=galaxy password=galaxy")
			cur = conn.cursor()
			cur.execute("SELECT last_value FROM apl_sample_id_seq;")
			conn.commit()
			current_sample = int(cur.fetchone()[0])
			cur.execute("SELECT last_value FROM apl_prophecy_sample_id_seq;")
			conn.commit()
			current_prophecy = int(cur.fetchone()[0])
			cur.close()
			conn.close()

			# check to make sure last_value is still equal to the current_value
			if current_sample != last_sample or current_prophecy != last_prophecy:
				message = "The database has been modified since you began this edit.  Sample IDs have been updated.  Please try again."
				status = 'error'
				last_sample = current_sample
				last_prophecy = current_prophecy
			else:
				message = self.__save_prophecy_import(trans, cntrller, **kwd)
				return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_prophecies',
															message=message,
															status='done'))

		if kwd.get('cancel_prophecy_import_button', False):
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_prophecies',
															message='Import canceled',
															status='done'))

		parameters = []
		parameters.append(dict(widget=HiddenField('last_sample', last_sample),
					value=last_sample))
		parameters.append(dict(widget=HiddenField('last_prophecy', last_prophecy),
					value=last_prophecy))
		parameters.append(dict(widget=HiddenField('prophecies', prophecies),
					value=prophecies))

		return trans.fill_template('/apl_tracking/sample/review_prophecy_import.mako',
									cntrller=cntrller,
									parameters=parameters,
									message=message,
									status=status)


	def __save_prophecy_import(self, trans, cntrller, **kwd):
		""" Saves a list of imported samples to the database
		"""

		# sanitize is set to False so that unicode characters in any fields are not destroyed
#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get( 'status', 'done' )

		last_sample = int(kwd.get('last_sample',''))
		last_prophecy = int(kwd.get('last_prophecy',''))
		prophecies = literal_eval(kwd.get('prophecies',''))

		try:
			# open connection to the galaxy database - I'd rather not do this, but I can't figure out how using SQLAlchemy
			conn = pg.connect("host=odin port=5477 dbname=galaxy_database user=galaxy password=galaxy")
			cur = conn.cursor()
			cur.execute("SELECT last_value FROM apl_sample_id_seq;")
			conn.commit()
			current_sample = int(cur.fetchone()[0])
			cur.execute("SELECT last_value FROM apl_prophecy_sample_id_seq;")
			conn.commit()
			current_prophecy = int(cur.fetchone()[0])

			# check to make sure last_value is still equal to the current_value
			if current_sample != last_sample or current_prophecy != last_prophecy:
				raise Exception("The database has been modified since you began this edit.  Please try again.")

			num_added = 0

			# loop through every sample
			for i,prophecy in enumerate(prophecies):

				# deal with any unicode characters
				for j,attr in enumerate(prophecy):
					try:
						prophecy[i] = prophecy[i].decode('utf-8')
					except:
						pass

				parent_id = None
				name = prophecy[1]
				species = None
				host = None
				sample_type = None
				created = str(datetime.date.today())
				user_id = trans.user.id
				lab = prophecy[2]
				project = 'prophecy'
				experiment_type = None
				notes = prophecy[11]

				this_sample = trans.model.APLSample(parent_id, name, species, host, sample_type, created, user_id, lab, project,
													experiment_type, notes=notes)

				# These are SQLAlchemy methods, not galaxy methods!
				trans.sa_session.add(this_sample)
				trans.sa_session.flush()
				trans.sa_session.refresh(this_sample)

				sample_id = this_sample.id
				associated_sample = prophecy[0]
				rg_transcribed = None
				rg_transfected = prophecy[3]
				rg_amplification = prophecy[4]
				expt_bulk = prophecy[5]
				expt_droplet = prophecy[6]
				analysis_tcid50 = prophecy[7]
				analysis_qpcr = prophecy[8]
				rna_isolation = prophecy[9]
				analysis_sequencing = prophecy[10]

				this_prophecy = trans.model.APLProphecySample(sample_id, associated_sample,
															rg_transcribed, rg_transfected,
															rg_amplification, expt_bulk,
															expt_droplet, analysis_tcid50,
															analysis_qpcr, rna_isolation,
															analysis_sequencing, notes)

				# These are SQLAlchemy methods, not galaxy methods!
				trans.sa_session.add(this_prophecy)
				trans.sa_session.flush()
				trans.sa_session.refresh(this_prophecy)

				num_added += 1

			cur.close()
			conn.close()
			message = '%i samples have been imported.' % num_added

			return message

		except Exception as e:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
			trans.sa_session.rollback()
			message = 'Error: %s.' % str( e )
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_prophecies',
															status='error',
															message=message))


	@web.expose
	@web.require_login("Edit a group of Prophecy samples")
	def edit_prophecy_group(self, trans, cntrller, **kwd):
#		is_admin = trans.user_is_admin()
		message = ''
		status = 'done'

		sample_ids = kwd.get('sample_ids', '')
		attribute = kwd.get('attribute', '')
		new_value = kwd.get('new_value', None)
		try:
			sample_ids = sample_ids.decode('utf-8')
		except:
			pass
		try:
			new_value = new_value.decode('utf-8')
		except:
			pass

		if kwd.get('edit_prophecy_group_button', False):

			# check formatting for attributes that need format-checking

			# check that sample IDs are formatted properly and exist in the database
			try:
				s = hyphen_range(sample_ids)
				good_ids = []
				problem_ids = []
				for i, id in enumerate(s):
					test_sample = trans.sa_session.query(trans.model.APLProphecySample).get(id)
					if test_sample == None:
						problem_ids.append(id)
				if len(problem_ids) > 0:
					message = 'Error: These Prophecy IDs do not exist (%s).' % problem_ids
					status = 'error'
			except:
				message = 'Error: Invalid format for Prophecy IDs'
				status = 'error'

			if status != 'error':
				parameters = self.__edit_prophecy_group(trans, cntrller, **kwd)
				return trans.fill_template('/apl_tracking/prophecy/review_prophecy_group.mako',
											cntrller=cntrller,
											parameters=parameters,
											message=None,
											status="done")

				return trans.response.send_redirect(web.url_for(controller='apl_tracking',
																action='browse_prophecies',
																message=message,
																status='done'))

		attributes = SelectField('attribute', multiple=False)
		attributes.add_option('Associated Sample', 'associated_sample')
		attributes.add_option('RG Transfection', 'rg_transfected')
		attributes.add_option('RG Amplification', 'rg_amplification')
		attributes.add_option('Bulk Experiment', 'expt_bulk')
		attributes.add_option('Droplet Experiment', 'expt_droplet')
		attributes.add_option('TCID50 Analysis', 'analysis_tcid50')
		attributes.add_option('qPCR Analysis', 'analysis_qpcr')
		attributes.add_option('RNA Isolation', 'rna_isolation')
		attributes.add_option('Sequencing', 'analysis_sequencing')
		attributes.add_option('Notes', 'notes')

		widgets = []
		widgets.append(dict(label='Prophecy sample IDs',
							widget=TextField('sample_ids', 200, kwd.get('sample_ids', '')),
							helptext='Use commas and dashes for multiple samples / sample ranges'))
		widgets.append(dict(label='Attribute',
							widget=attributes,
							helptext='Select the attribute you want to edit'))
		widgets.append(dict(label='New Value',
							widget=TextField('new_value', 200, kwd.get('new_value', '')),
							helptext='Change the selected attribute to this value for all of the listed sample IDs'))

		return trans.fill_template('/apl_tracking/prophecy/edit_prophecy_group.mako',
									cntrller=cntrller,
									widgets=widgets,
									message=message,
									status=status)


	def __edit_prophecy_group(self, trans, cntrller, **kwd):
		""" Edit a large group of samples at once
		"""

#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get( 'status', 'done' )

		sample_ids = kwd.get('sample_ids', '')
		attribute = kwd.get('attribute', '')
		new_value = kwd.get('new_value', None)

#		try:
#			user_id = trans.sa_session.query(trans.model.User)\
#										.filter(trans.model.User.table.c.username==user)\
#										.first()\
#										.id
#		except:
#			user_id = trans.user.id

		if not isNoneOrEmptyOrBlankString(sample_ids):
			try:
				# split sample_ids
				s = hyphen_range(sample_ids)

				# fix formatting of new_value if not empty
				if not isNoneOrEmptyOrBlankString(new_value):

					# remove any trailing spaces
					try:
						new_value = new_value.strip()
					except:
						pass
					# fix formatting of new_value in case it is unicode
					try:
						new_value = new_value.decode('utf-8')
					except:
						pass
					# fix formatting of new_value in case it is a date
					if attribute != 'associated_sample' and attribute != 'notes':
						try:
							new_value = format_date(new_value)
						except:
							pass
					# fix formatting of new_value in case it is an integer
					if re.match('^[0-9]+$', new_value):
						new_value = int(new_value)

				parameters = []
				parameters.append(dict(widget=HiddenField('sample_ids', s),
							value=s))
				parameters.append(dict(widget=HiddenField('attribute', attribute),
							value=attribute))
				parameters.append(dict(widget=HiddenField('new_value', new_value),
							value=new_value))

				return parameters

			except Exception as e:
				exc_type, exc_value, exc_traceback = sys.exc_info()
				traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
				trans.sa_session.rollback()
				message = 'Error: %s.' % str( e )
				return trans.response.send_redirect(web.url_for(controller='apl_tracking',
																action='browse_prophecies',
																status='error',
																message=message))


	@web.expose
	@web.require_login("Edit a group of Prophecy samples")
	def review_prophecy_group(self, trans, cntrller, **kwd):
#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get('status', 'done')

		if kwd.get('review_prophecy_group_button', False):
			message = self.__save_prophecy_group(trans, cntrller, **kwd)
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_prophecies',
															message=message,
															status='done'))

		if kwd.get('cancel_prophecy_group_button', False):
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_prophecies',
															message='Edit canceled',
															status='done'))

		return trans.fill_template('/apl_tracking/prophecy/review_prophecy_group.mako',
									cntrller=cntrller,
									parameters=parameters,
									message=None,
									status="done")


	def __save_prophecy_group(self, trans, cntrller, **kwd):
		""" Save changes to a large group of samples at once
		"""

#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get( 'status', 'done' )

		sample_ids = kwd.get('sample_ids', '')
		attribute = kwd.get('attribute', '')
		new_value = kwd.get('new_value', None)

		# set new value to None if necessary
		if isNoneOrEmptyOrBlankString(new_value):
			new_value = None

		# deal with UTF-8 encoding
		try:
			new_value = new_value.decode('utf-8')
		except:
			pass

		num_changed = 0

		# backup existing table
		backup_file = "/data/backups/apl-tables/apl_prophecy_sample-%d" % (int(time.time()*1e9))
		args = shlex.split("pg_dump --port 5477 --username galaxy --format plain --ignore-version --verbose --file %s --table apl_prophecy_sample galaxy_database" % (backup_file))
		p = subprocess.Popen(args)
		p.wait()

		try:
			for prophecy_id in literal_eval(sample_ids):

				# change attribute on all sample_ids to new_value
				prophecy = trans.sa_session.query(trans.model.APLProphecySample).get(prophecy_id)
				setattr(prophecy, str(attribute), new_value)
				trans.sa_session.add(prophecy)
				trans.sa_session.flush()
				num_changed += 1

			message = '%i Prophecy samples have been updated.' % num_changed

			return message

		except Exception as e:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
			trans.sa_session.rollback()
			message = 'Error: %s.' % str( e )
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_prophecies',
															status='error',
															message=message))


#=====================================================================================================================================================

	# ------------------------
	# Illumina Prep methods
	# ------------------------

	@web.expose
	@web.require_login("Add sample to Preps table")
	def create_prep(self, trans, cntrller, **kwd):
		# is this an admin using the admin channel to create a sample?
		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		user_id_encoded = True
		user_id = kwd.get('user_id', 'none')
		if user_id != 'none':
			try:
				user = trans.sa_session.query(trans.model.User).get(trans.security.decode_id(user_id))
			except TypeError as e:
				# We must have an email address rather than an encoded user id
				# This is because the galaxy.base.js creates a search+select box
				# when there are more than 20 items in a SelectField.

				# returns the first user with the correct email
				user = trans.sa_session.query( trans.model.User ) \
										.filter( trans.model.User.table.c.username==user_id ) \
										.first()
				user_id_encoded = False

		elif not is_admin:
			# assume no impersonation
			user = trans.user
		else:
			user = None

		if kwd.get('create_prep_button', False):
			name = kwd.get( 'name', '')
			if user is None:
				message = 'Invalid user ID (%s)' % str(user_id)
				status = 'error'
			elif not name:
				message = 'Error: No name'
				status = 'error'
			else:
				request = self.__save_prep(trans, cntrller, **kwd)
				message = 'The sample has been created.'
				if kwd.get('create_prep', False):
					return trans.response.send_redirect(web.url_for(controller=cntrller,
																	action='browse_preps',
																	message=message,
																	status="done"))

		# Widgets to be rendered on the request form
		# not sure why they call these widgets - I think these will basically end up being interactive features
		widgets = []

		widgets.append(dict(label='Sample ID',
							widget=TextField('sample_id', 9, kwd.get('sample_id', '')),
							helptext='(Required)'))
		widgets.append(dict(label='Date Prepared',
							widget=TextField('prep_date', 8, kwd.get('prep_date', str(datetime.date.today()))),
							helptext='Format: YYYY-MM-DD (Required)'))
		widgets.append(dict(label='User',
							widget=TextField('user_id', 8, kwd.get('user_id', trans.sa_session.query(trans.model.User).get(trans.user.id).username)),
							helptext='(Required)'))
		widgets.append(dict(label='Notes',
							widget=	TextArea('notes', size="10x30", value=kwd.get('notes', '')),
							helptext='(Optional)'))

		return trans.fill_template('/apl_tracking/preps/create_prep.mako',
									cntrller=cntrller,
									widgets=widgets,
									message=message,
									status='done')


	@web.expose
	@web.require_login("Edit Preps")
	def edit_prep_info(self, trans, cntrller, **kwd):
		message = ''
		status = 'done'
		prep_id = kwd.get('id', None)

		# pull out variables that need format-checking
		sample_id = kwd.get('sample_id', '')
		prep_date = kwd.get('prep_date', '')
		prep_user = kwd.get('user_id', '')

		try:
			prep = trans.sa_session.query(trans.model.APLPrep).get(trans.security.decode_id(prep_id))
		except:
			return invalid_id_redirect(trans, cntrller, prep_id)

		if kwd.get( 'edit_prep_info_button', False ):

			# check formatting for attributes that need format-checking

			# check that user exists
			try:
				test = trans.sa_session.query(trans.model.User)\
											.filter(trans.model.User.table.c.username == prep_user)\
											.first()\
											.id
			except:
				message = 'Error: User does not exist: %s' % prep_user
				status = 'error'

			# check formatting of prep date
			try:
				test = format_date(prep_date)
			except:
				if not isNoneOrEmptyOrBlankString(prep_date):
					message = 'Error: Invalid date format: %s' % prep_date
					status = 'error'

			# check that sample IDs are formatted properly and exist in the database
			try:
				test = int(re.sub('^SMP0*', '', sample_id))
				test_sample = trans.sa_session.query(trans.model.APLSample).get(test)
				if test_sample == None:
					message = 'Error: Sample ID does not exist: %s' % test
					status = 'error'
			except:
				message = 'Error: Check formatting of Sample ID: %s' % sample_id
				status = 'error'

			if status != 'error':
				prep = self.__save_prep( trans, cntrller, prep=prep, **kwd )
				message = 'The changes made to prep (APL_%09d) have been saved.' % prep.id
				return trans.response.send_redirect(web.url_for(controller=cntrller,
																action='browse_preps',
																message=message,
																status="done"))

		# Widgets to be rendered on the request form
		widgets = []

		widgets.append(dict(label='Sample ID',
							widget=TextField('sample_id', 10, kwd.get('sample_id', prep.sample_id)),
							helptext='(Required)'))
		widgets.append(dict(label='Date Created',
							widget=TextField('prep_date', 8, kwd.get('prep_date', prep.prep_date)),
							helptext='Format: YYYY-MM-DD'))
		widgets.append(dict(label='User',
							widget=TextField('user_id', 8, kwd.get('user_id', trans.sa_session.query(trans.model.User).get(prep.user_id).username)),
							helptext='(Required)'))
		widgets.append(dict(label='Notes',
#							widget=	TextArea('notes', size="10x30", value=kwd.get('notes', prep.notes)),
							value=kwd.get('notes', formatNullString(prep.notes)),
							helptext='(Optional)'))

		return trans.fill_template('/apl_tracking/preps/edit_prep_info.mako',
									cntrller=cntrller,
									prep=prep,
									widgets=widgets,
									message=message,
									status=status)


	def __save_prep( self, trans, cntrller, prep=None, **kwd ):
		""" Saves changes to an existing prep, or creates a new
			prep if prep is None.
		"""

#		is_admin = trans.user_is_admin()

		sample_id = kwd.get('sample_id', None)
		prep_date = kwd.get('prep_date', None)
		prep_user = kwd.get('user_id', None)
		notes = kwd.get('notes', None)

		# convert username to numerical ID
		prep_user_id = trans.sa_session.query(trans.model.User)\
									.filter(trans.model.User.table.c.username == prep_user)\
									.first()\
									.id

		data = [sample_id, prep_date, prep_user_id, notes]

		# Deal with any empty strings or UTF-8 encoding
		for i in range(0, len(data)):
			if isNoneOrEmptyOrBlankString(data[i]):
				data[i] = None
			try:
				data[i] = data[i].decode('utf-8')
			except:
				pass

		# format prep_date as a date
		try:
			data[1] = format_date(data[1])
		except:
			data[1] = None

		if prep is None:
			prep = trans.model.APLPrep(data[0], data[1], data[2], data[3])
			# These are SQLAlchemy methods, not galaxy methods!
			trans.sa_session.add(prep)
			trans.sa_session.flush()
			trans.sa_session.refresh(prep)

		else:
			# We're saving changes to an existing request
			prep.sample_id = data[0]
			prep.prep_date = data[1]
			prep.user_id = data[2]
			prep.notes = data[3]
			trans.sa_session.add(prep)
			trans.sa_session.flush()

		return prep


	@web.expose
	@web.require_login("View prep")
	def view_prep(self, trans, cntrller, **kwd):
#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get('status', 'done')
		prep_id = kwd.get('id', None)
		try:
			prep = trans.sa_session.query(trans.model.APLPrep).get(trans.security.decode_id(prep_id))
		except:
			return invalid_id_redirect(trans, cntrller, prep_id)

		return trans.fill_template('/apl_tracking/preps/view_prep.mako',
									cntrller=cntrller,
									prep=prep,
									status=status,
									message=message)


	@web.expose
	@web.require_login("Create pool of preps")
	def create_prep_pool(self, trans, cntrller, **kwd):
#		is_admin = trans.user_is_admin()
		message = ''
		status = 'done'

		if kwd.get('create_prep_pool_button', False):
				parameters = self.__create_prep_pool(trans, cntrller, **kwd)
				return trans.fill_template('/apl_tracking/preps/review_prep_pool_create.mako',
											cntrller=cntrller,
											parameters=parameters,
											message=None,
											status="done")

				return trans.response.send_redirect(web.url_for(controller=cntrller,
																action='browse_preps',
																message=message,
																status='done'))
			except Exception as e:
				if str(e)[0:3] == '302':
					message = urllib.unquote_plus(str(e).split('message=')[1])
				else:
					message = str(e);
				status = 'error'

		return trans.fill_template('/apl_tracking/preps/create_prep_pool.mako',
									cntrller=cntrller,
									message=message,
									status=status)


	def __create_prep_pool(self, trans, cntrller, **kwd):
		""" Creates a prep pool, checks the values, and sends the data to be reviewed
		"""

		message = kwd.get('message', '')
		status = kwd.get( 'status', 'done' )

		try:
			# pull value of current pointer
			# open connection to the galaxy database - I'd rather not do this, but I can't figure out how using SQLAlchemy
			conn = pg.connect("host=odin port=5477 dbname=galaxy_database user=galaxy password=galaxy")
			cur = conn.cursor()
			cur.execute("SELECT last_value FROM apl_prep_pool_id_seq;")
			conn.commit()
			last_pool = int(cur.fetchone()[0])
			cur.close()
			conn.close()

					# remove trailing whitespace, split input line, and nullify empty strings
					prophecy = line.rstrip().split('\t')
					for i in range(0, len(prophecy)):
						if isNoneOrEmptyOrBlankString(prophecy[i]):
							prophecy[i] = None
						else:
							# Deal with any UTF-8 encoding
							try:
								prophecy[i] = prophecy[i].rstrip().decode('utf-8')
							except:
								prophecy[i] = prophecy[i].rstrip()

					# make sure list is the correct length
					if len(prophecy) > 2:
						raise Exception('Sample in row %i contains %i columns (should contain 1 or 2)' % (l+1, len(prophecy)))
					while len(prophecy) < 2:
						prophecy.append(None)

					# store these values (formatted above)
					name = prophecy[0]
					if len(prophecy) == 2:
						species = prophecy[1]
					else:
						species = ''

					new_samples.append([name, species])

				parameters = []
				parameters.append(dict(widget=HiddenField('last_sample', last_sample), value=last_sample))
				parameters.append(dict(widget=HiddenField('last_prophecy', last_prophecy), value=last_prophecy))
				parameters.append(dict(widget=HiddenField('prophecies', new_samples), value=new_samples))

				return parameters

		except Exception as e:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
			trans.sa_session.rollback()
			message = 'Error: %s.' % str( e )
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_prophecies',
															status='error',
															message=message))

	@web.expose
	@web.require_login("Review Prophecy samples to create")
	def review_prep_pool_create(self, trans, cntrller, **kwd):
#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get('status', 'done')
		last_sample = int(kwd.get('last_sample',''))
		last_prophecy = int(kwd.get('last_prophecy',''))
		prophecies = literal_eval(kwd.get('prophecies',''))

		if kwd.get('review_prophecy_create_button', False):
			# open connection to the galaxy database - I'd rather not do this, but I can't figure out how using SQLAlchemy
			conn = pg.connect("host=odin port=5477 dbname=galaxy_database user=galaxy password=galaxy")
			cur = conn.cursor()
			cur.execute("SELECT last_value FROM apl_sample_id_seq;")
			conn.commit()
			current_sample = int(cur.fetchone()[0])
			cur.execute("SELECT last_value FROM apl_prophecy_sample_id_seq;")
			conn.commit()
			current_prophecy = int(cur.fetchone()[0])
			cur.close()
			conn.close()

			# check to make sure last_value is still equal to the current_value
			if current_sample != last_sample or current_prophecy != last_prophecy:
				message = "The database has been modified since you began this edit.  Sample IDs have been updated.  Please try again."
				status = 'error'
				last_sample = current_sample
				last_prophecy = current_prophecy
			else:
				message = self.__save_prophecy_create(trans, cntrller, **kwd)
				return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_prophecies',
															message=message,
															status='done'))

		if kwd.get('cancel_prophecy_create_button', False):
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_prophecies',
															message='',
															status='done'))

		parameters = []
		parameters.append(dict(widget=HiddenField('last_sample', last_sample),
					value=last_sample))
		parameters.append(dict(widget=HiddenField('last_prophecy', last_prophecy),
					value=last_prophecy))
		parameters.append(dict(widget=HiddenField('prophecies', prophecies),
					value=prophecies))

		return trans.fill_template('/apl_tracking/sample/review_prophecy_create.mako',
									cntrller=cntrller,
									parameters=parameters,
									message=message,
									status=status)


	def __save_prep_pool_create(self, trans, cntrller, **kwd):
		""" Saves a list of created samples to the database
		"""

#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get( 'status', 'done' )

		last_sample = int(kwd.get('last_sample',''))
		last_prophecy = int(kwd.get('last_prophecy',''))
		prophecies = literal_eval(kwd.get('prophecies',''))

		try:
			# open connection to the galaxy database - I'd rather not do this, but I can't figure out how using SQLAlchemy
			conn = pg.connect("host=odin port=5477 dbname=galaxy_database user=galaxy password=galaxy")
			cur = conn.cursor()
			cur.execute("SELECT last_value FROM apl_sample_id_seq;")
			conn.commit()
			current_sample = int(cur.fetchone()[0])
			cur.execute("SELECT last_value FROM apl_prophecy_sample_id_seq;")
			conn.commit()
			current_prophecy = int(cur.fetchone()[0])

			# check to make sure last_value is still equal to the current_value
			if current_sample != last_sample or current_prophecy != last_prophecy:
				raise Exception("The database has been modified since you began this edit.  Please try again.")

			num_added = 0

			# loop through every sample
			for i,prophecy in enumerate(prophecies):

				# deal with any unicode characters
				for j,attr in enumerate(prophecy):
					try:
						prophecy[i] = prophecy[i].decode('utf-8')
					except:
						pass

				name = prophecy[0]
				if prophecy[1]:
					species = prophecy[1]
				else:
					species = ''
				host = ''
				created = str(datetime.date.today())
				user_id = trans.user.id
				lab = 'APL'
				project = 'prophecy'

				parent_id = None
				sample_type = None
				experiment_type = None
				notes = None

				this_sample = trans.model.APLSample(parent_id, name, species, host, sample_type, created, user_id, lab, project,
													experiment_type, notes=notes)

				# These are SQLAlchemy methods, not galaxy methods!
				trans.sa_session.add(this_sample)
				trans.sa_session.flush()
				trans.sa_session.refresh(this_sample)

				sample_id = this_sample.id
				associated_sample = None
				rg_transcribed = None
				rg_transfected = None
				rg_amplification = None
				expt_bulk = None
				expt_droplet = None
				analysis_tcid50 = None
				analysis_qpcr = None
				rna_isolation = None
				analysis_sequencing = None

				this_prophecy = trans.model.APLProphecySample(sample_id, associated_sample,
															rg_transcribed, rg_transfected,
															rg_amplification, expt_bulk,
															expt_droplet, analysis_tcid50,
															analysis_qpcr, rna_isolation,
															analysis_sequencing, notes)

				# These are SQLAlchemy methods, not galaxy methods!
				trans.sa_session.add(this_prophecy)
				trans.sa_session.flush()
				trans.sa_session.refresh(this_prophecy)

				num_added += 1

			cur.close()
			conn.close()
			message = '%i samples have been created.' % num_added

			return message

		except Exception as e:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
			trans.sa_session.rollback()
			message = 'Error: %s.' % str( e )
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_prophecies',
															status='error',
															message=message))


	@web.expose
	@web.require_login("Import preps from text file")
	def import_preps(self, trans, cntrller, **kwd):
#		is_admin = trans.user_is_admin()
		message = ''
		status = 'done'
		file = kwd.get('file_data', '')
		sample_ids = kwd.get('sample_ids', '')

		# create template file
		filepath = '/var/www/html/publicshare/samplesheets'
		filename = '%s/import_prep_template.txt' % filepath
		f = open(filename, 'w')
		f.write('sample_id\tprep_date\tnotes\n')
		f.close()

		if kwd.get('import_preps_button', False):
			try:
				if isNoneOrEmptyOrBlankString(str(file)):
					message="Please select a file"
					status="error"
				else:
					parameters = self.__import_prep(trans, cntrller, **kwd)
					return trans.fill_template('/apl_tracking/preps/review_prep_import.mako',
												cntrller=cntrller,
												parameters=parameters,
												message=None,
												status="done")

					return trans.response.send_redirect(web.url_for(controller=cntrller,
																	action='browse_preps',
																	message=message,
																	status='done'))
			except Exception as e:
				if str(e)[0:3] == '302':
					message = urllib.unquote_plus(str(e).split('message=')[1])
				else:
					message = str(e);
				status = 'error'

		if kwd.get('create_prep_group_button', False):
			if isNoneOrEmptyOrBlankString(str(sample_ids)):
				message="Please enter at least one Sample ID"
				status="error"
			elif isNoneOrEmptyOrBlankString(str(hyphen_range(sample_ids))):
				message="Check formatting of Sample IDs"
				status="error"
			else:
				parameters = self.__create_prep_group(trans, cntrller, **kwd)
				return trans.fill_template('/apl_tracking/preps/review_prep_import.mako',
											cntrller=cntrller,
											parameters=parameters,
											message=None,
											status="done")

				return trans.response.send_redirect(web.url_for(controller=cntrller,
																action='browse_preps',
																message=message,
																status='done'))

		widgets = []
		widgets.append(dict(label='Sample IDs',
							widget=TextField('sample_ids', 200, ''),
							helptext='Use commas and dashes for multiple samples / sample ranges'))
		widgets.append(dict(label='Date prepared',
							widget=TextField('prep_date', 200, str(datetime.date.today())),
							helptext='This prep date will be used for every prep'))
		widgets.append(dict(label='Notes',
							widget=TextArea('notes', size='4x30', value=''),
							helptext='These notes will be used for every prep'))

		return trans.fill_template('/apl_tracking/preps/import_preps.mako',
									cntrller=cntrller,
									widgets=widgets,
									message=message,
									status=status)


	def __import_prep(self, trans, cntrller, **kwd):
		""" Reads a tab-separated file, checks the values, and sends the data to be reviewed
		"""

#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get( 'status', 'done' )

#		try:
#			user_id = trans.sa_session.query(trans.model.User)\
#										.filter(trans.model.User.table.c.username==user)\
#										.first()\
#										.id
#		except:
#			user_id = trans.user.id

		# get file object from file that was imported
		# file_obj.file is equivalent to what would be returned by open("filename", "rb")
		file_obj = kwd.get('file_data', '')

		try:
			if isNoneOrEmptyOrBlankString(str(file_obj.file)):
				raise Exception("File does not exist")
			else:
				# pull value of current pointer
				# open connection to the galaxy database - I'd rather not do this, but I can't figure out how using SQLAlchemy
				conn = pg.connect("host=odin port=5477 dbname=galaxy_database user=galaxy password=galaxy")
				cur = conn.cursor()
				cur.execute("SELECT last_value FROM apl_prep_id_seq;")
				conn.commit()
				last_value = int(cur.fetchone()[0])
				cur.close()
				conn.close()

				# read in input file as single string
				opened = file_obj.file.read()
				# split by any possible line endings, remove empty lines
				lines = filter(None, re.split(r'[\n\r]+', opened))

				# pull off header, make sure it is correct
				header = lines[0].rstrip().split('\t')
				lines = lines[1:]
				if sorted(header) != sorted(['sample_id', 'prep_date', 'notes']):
					raise Exception('Header is not correct, make sure you use the provided template (your header: %s)' % header)

				new_preps = []

				# go through each line of input file
				for l,line in enumerate(lines):

					# make sure line is not entirely composed of whitespace
					if line.strip():

						# remove trailing whitespace, split input line, and nullify empty strings
						prep = line.rstrip().split('\t')
						for i in range(0, len(prep)):
							if isNoneOrEmptyOrBlankString(prep[i]):
								prep[i] = None
							else:
								# Deal with any UTF-8 encoding
								try:
									prep[i] = prep[i].rstrip().decode('utf-8')
								except:
									prep[i] = prep[i].rstrip()

						# make sure list is the correct length
						if len(prep) > 3:
							raise Exception('Prep in row %i contains %i columns (should contain 3)' % (l+1, len(prep)))
						while len(prep) < 3:
							prep.append(None)

						# check formatting for sample ID
						if not prep[0]:
							raise Exception('Sample ID cannot be left blank for prep in row %i' % (l+1))
						else:
							try:
								sample_id = int(re.sub('^SMP0*', '', prep[0]))
							except:
								raise Exception('Invalid sample ID (\'%s\') in row %i' % (prep[0], l+1))

							if trans.sa_session.query(trans.model.APLSample).get( int(re.sub('^SMP0*', '', prep[0])) ) == None:
								raise Exception("No sample in database with ID = %s" % prep[0])

						# check formatting for created date, make it today if it does not exist
						if prep[1] is not None:
							try:
								prep_date = format_date(prep[1])
							except:
								raise Exception('Invalid prep date (\'%s\') in row %i' % (prep[1], l+1))
						else:
							prep_date = str(datetime.date.today())

						# I don't believe these need any format checking
						if len(prep) == 3:
							notes = prep[2]
						else:
							notes = None

						new_preps.append([sample_id, prep_date, notes])

				parameters = []
				parameters.append(dict(widget=HiddenField('last_value', last_value), value=last_value))
				parameters.append(dict(widget=HiddenField('preps', new_preps), value=new_preps))

				return parameters

		except Exception as e:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
			trans.sa_session.rollback()
			message = 'Error: %s.' % str( e )
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_preps',
															status='error',
															message=message))

	def __create_prep_group(self, trans, cntrller, **kwd):
		""" Creates a group of preps from the input values, checks the values, and sends the data to be reviewed
		"""

#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get( 'status', 'done' )

#		try:
#			user_id = trans.sa_session.query(trans.model.User)\
#										.filter(trans.model.User.table.c.username==user)\
#										.first()\
#										.id
#		except:
#			user_id = trans.user.id

		sample_ids = kwd.get('sample_ids', None)
		prep_date = kwd.get('prep_date', None)
		notes = kwd.get('notes', None)

		# split prep_ids
		s = hyphen_range(sample_ids)

		# check formatting for created date, make it today if it does not exist
		if prep_date is not None:
			prep_date = format_date(prep_date)
		else:
			prep_date = str(datetime.date.today())

		# I don't believe these need any format checking
		if isNoneOrEmptyOrBlankString(notes):
			notes = None

		try:
			# pull value of current pointer
			# open connection to the galaxy database - I'd rather not do this, but I can't figure out how using SQLAlchemy
			conn = pg.connect("host=odin port=5477 dbname=galaxy_database user=galaxy password=galaxy")
			cur = conn.cursor()
			cur.execute("SELECT last_value FROM apl_prep_id_seq;")
			conn.commit()
			last_value = int(cur.fetchone()[0])
			cur.close()
			conn.close()

			new_preps = []

			# go through each line of input file
			for sample_id in s:

				# check formatting for sample ID
				if trans.sa_session.query(trans.model.APLSample).get(sample_id) == None:
					raise Exception("No sample in database with ID = %i" % int(sample_id))

				new_preps.append([sample_id, prep_date, notes])

			parameters = []
			parameters.append(dict(widget=HiddenField('last_value', last_value),
									value=last_value))
			parameters.append(dict(widget=HiddenField('preps', new_preps),
									value=new_preps))

			return parameters

		except Exception as e:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
			trans.sa_session.rollback()
			message = 'Error: %s.' % str( e )
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_preps',
															status='error',
															message=message))

	@web.expose
	@web.require_login("Review preps for import")
	def review_prep_import(self, trans, cntrller, **kwd):
#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get('status', 'done')
		last_value = int(kwd.get('last_value',''))
		preps = literal_eval(kwd.get('preps',''))

		if kwd.get('review_prep_import_button', False):
			# open connection to the galaxy database - I'd rather not do this, but I can't figure out how using SQLAlchemy
			conn = pg.connect("host=odin port=5477 dbname=galaxy_database user=galaxy password=galaxy")
			cur = conn.cursor()
			cur.execute("SELECT last_value FROM apl_prep_id_seq;")
			conn.commit()
			current_value = int(cur.fetchone()[0])
			cur.close()
			conn.close()

			# check to make sure last_value is still equal to the current_value
			if current_value != last_value:
				message = "The database has been modified since you began this edit.  Prep IDs have been updated.  Please try again."
				status = 'error'
				last_value = current_value
			else:
				message = self.__save_prep_import(trans, cntrller, **kwd)
				return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_preps',
															message=message,
															status='done'))

		if kwd.get('create_samplesheet_button', False):
			# open connection to the galaxy database - I'd rather not do this, but I can't figure out how using SQLAlchemy
			conn = pg.connect("host=odin port=5477 dbname=galaxy_database user=galaxy password=galaxy")
			cur = conn.cursor()
			cur.execute('SELECT last_value FROM apl_prep_id_seq;')
			conn.commit()
			current_value = int(cur.fetchone()[0])
			cur.close()
			conn.close()

			# check to make sure last_value is still equal to the current_value
			if current_value != last_value:
				message = 'The database has been modified since you began this edit.  Prep IDs have been updated.  Please try again.'
				status = 'error'
				last_value = current_value
			else:
				message = self.__save_prep_import(trans, cntrller, **kwd)
				widgets = self.__create_default_samplesheet(trans, cntrller, **kwd)
				return trans.fill_template('/apl_tracking/preps/review_samplesheet.mako',
											cntrller=cntrller,
											message=message,
											widgets=widgets,
											status='done')
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_preps',
															message=message,
															status='done'))

		if kwd.get('cancel_prep_import_button', False):
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_preps',
															message='Import canceled',
															status='done'))

		parameters = []
		parameters.append(dict(widget=HiddenField('last_value', last_value),
					value=last_value))
		parameters.append(dict(widget=HiddenField('preps', preps),
					value=preps))

		return trans.fill_template('/apl_tracking/preps/review_prep_import.mako',
									cntrller=cntrller,
									parameters=parameters,
									message=message,
									status=status)


	def __save_prep_import(self, trans, cntrller, **kwd):
		""" Saves a list of imported preps to the database
		"""

#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get( 'status', 'done' )

		last_value = int(kwd.get('last_value',''))
		preps = literal_eval(kwd.get('preps',''))

		try:
			# open connection to the galaxy database - I'd rather not do this, but I can't figure out how using SQLAlchemy
			conn = pg.connect("host=odin port=5477 dbname=galaxy_database user=galaxy password=galaxy")
			cur = conn.cursor()
			cur.execute("SELECT last_value FROM apl_prep_id_seq;")
			conn.commit()
			current_value = int(cur.fetchone()[0])
			cur.close()
			conn.close()

			# check to make sure last_value is still equal to the current_value
			if current_value != last_value:
				raise Exception("The database has been modified since you began this edit.  Please try again.")

			num_added = 0

			for prep in preps:
				for i,attr in enumerate(prep):
					try:
						prep[i] = prep[i].decode('utf-8')
					except:
						pass

				sample_id = prep[0]
				prep_date = prep[1]
				user_id = trans.user.id
				notes = prep[2]

				this_prep = trans.model.APLPrep(sample_id=sample_id, prep_date=prep_date, user_id=user_id, notes=notes)

				# These are SQLAlchemy methods, not galaxy methods!
				trans.sa_session.add(this_prep)
				trans.sa_session.flush()
				trans.sa_session.refresh(this_prep)

				num_added += 1

			message = '%i preps have been imported.' % num_added

			return message

		except Exception as e:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
			trans.sa_session.rollback()
			message = 'Error: %s.' % str( e )
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_preps',
															status='error',
															message=message))


	@web.expose
	@web.require_login("Edit a group of preps")
	def edit_prep_group(self, trans, cntrller, **kwd):
#		is_admin = trans.user_is_admin()
		message = ''
		status = 'done'

		prep_ids = kwd.get('prep_ids', '')
		attribute = kwd.get('attribute', '')
		new_value = kwd.get('new_value', None)
		try:
			prep_ids = prep_ids.decode('utf-8')
		except:
			pass
		try:
			new_value = new_value.decode('utf-8')
		except:
			pass

		if kwd.get('edit_prep_group_button', False):

			# check formatting for attributes that need format-checking

			# check to make sure user exists
			if attribute == 'user_id':
				try:
					user_id = trans.sa_session.query(trans.model.User)\
											.filter(trans.model.User.table.c.username==new_value)\
											.first()\
											.id
				except:
					message = 'Error: user does not exist: %s' % new_value
					status = 'error'

			# fix formatting of new_value in case it is a date
			if attribute == 'prep_date':
				try:
					test = format_date(new_value)
				except:
					if not isNoneOrEmptyOrBlankString(new_value):
						message = 'Error: Invalid date format: %s' % new_value
						status = 'error'

			# check that prep IDs are formatted properly and exist in the database
			try:
				s = hyphen_range(prep_ids)
				good_ids = []
				problem_ids = []
				for i, id in enumerate(s):
					test_prep = trans.sa_session.query(trans.model.APLPrep).get(id)
					if test_prep == None:
						problem_ids.append(id)
				if len(problem_ids) > 0:
					message = 'Error: These prep IDs do not exist (%s).' % problem_ids
					status = 'error'
			except:
				message = 'Error: Invalid format for prep IDs'
				status = 'error'

			if status != 'error':
				parameters = self.__edit_prep_group(trans, cntrller, **kwd)
				return trans.fill_template('/apl_tracking/preps/review_prep_group.mako',
											cntrller=cntrller,
											parameters=parameters,
											message=None,
											status="done")

				return trans.response.send_redirect(web.url_for(controller='apl_tracking',
																action='browse_preps',
																message=message,
																status='done'))

		attributes = SelectField('attribute', multiple=False)
		attributes.add_option('Date Prepared', 'prep_date')
		attributes.add_option('User', 'user_id')
		attributes.add_option('Notes', 'notes')

		widgets = []
		widgets.append(dict(label='Prep IDs',
							widget=TextField('prep_ids', 200, kwd.get('prep_ids', '')),
							helptext='Use commas and dashes for multiple preps / prep ranges'))
		widgets.append(dict(label='Attribute',
							widget=attributes,
							helptext='Select the attribute you want to edit'))
		widgets.append(dict(label='New Value',
							widget=TextField('new_value', 200, kwd.get('new_value', '')),
							helptext='Change the selected attribute to this value for all of the listed prep IDs'))

		return trans.fill_template('/apl_tracking/preps/edit_prep_group.mako',
									cntrller=cntrller,
									widgets=widgets,
									message=message,
									status=status)


	def __edit_prep_group(self, trans, cntrller, **kwd):
		""" Edit a large group of preps at once
		"""

#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get( 'status', 'done' )

		prep_ids = kwd.get('prep_ids', '')
		attribute = kwd.get('attribute', '')
		new_value = kwd.get('new_value', None)

#		try:
#			user_id = trans.sa_session.query(trans.model.User)\
#										.filter(trans.model.User.table.c.username==user)\
#										.first()\
#										.id
#		except:
#			user_id = trans.user.id

		if not isNoneOrEmptyOrBlankString(prep_ids):
			try:
				# split prep_ids
				s = hyphen_range(prep_ids)

				# fix formatting of new_value if not empty
				if not isNoneOrEmptyOrBlankString(new_value):

					# remove any trailing spaces
					try:
						new_value = new_value.strip()
					except:
						pass
					# fix formatting of new_value in case it is unicode
					try:
						new_value = new_value.decode('utf-8')
					except:
						pass
					# fix formatting of new_value in case it is a date
					if attribute == 'prep_date':
						new_value = format_date(new_value)
					# fix formatting of new_value in case it is an integer
					if re.match('^[0-9]+$', new_value):
						new_value = int(new_value)

				parameters = []
				parameters.append(dict(widget=HiddenField('prep_ids', s),
							value=s))
				parameters.append(dict(widget=HiddenField('attribute', attribute),
							value=attribute))
				parameters.append(dict(widget=HiddenField('new_value', new_value),
							value=new_value))

				return parameters

			except Exception as e:
				exc_type, exc_value, exc_traceback = sys.exc_info()
				traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
				trans.sa_session.rollback()
				message = 'Error: %s.' % str( e )
				return trans.response.send_redirect(web.url_for(controller='apl_tracking',
																action='browse_preps',
																status='error',
																message=message))


	@web.expose
	@web.require_login("Edit a group of preps")
	def review_prep_group(self, trans, cntrller, **kwd):
#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get('status', 'done')

		if kwd.get('review_prep_group_button', False):
			message = self.__save_prep_group(trans, cntrller, **kwd)
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_preps',
															message=message,
															status='done'))

		if kwd.get('cancel_prep_group_button', False):
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_preps',
															message='Edit canceled',
															status='done'))

		return trans.fill_template('/apl_tracking/preps/review_prep_group.mako',
									cntrller=cntrller,
									parameters=parameters,
									message=None,
									status="done")


	def __save_prep_group(self, trans, cntrller, **kwd):
		""" Save changes to a large group of preps at once
		"""

#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get( 'status', 'done' )

		prep_ids = kwd.get('prep_ids', '')
		attribute = kwd.get('attribute', '')
		new_value = kwd.get('new_value', None)

		# set new value to None if necessary
		if isNoneOrEmptyOrBlankString(new_value):
			new_value = None

		# deal with UTF-8 encoding
		try:
			new_value = new_value.decode('utf-8')
		except:
			pass

		# convert username to user ID if necessary
		if attribute == 'user_id':
			new_value = trans.sa_session.query(trans.model.User)\
										.filter(trans.model.User.table.c.username==new_value)\
										.first()\
										.id

		num_changed = 0

		# backup existing table
		backup_file = "/data/backups/apl-tables/apl_prep-%d" % (int(time.time()*1e9))
		args = shlex.split("pg_dump --port 5477 --username galaxy --format plain --ignore-version --verbose --file %s --table apl_prep galaxy_database" % (backup_file))
		p = subprocess.Popen(args)
		p.wait()

		try:
			for prep_id in literal_eval(prep_ids):

				# change attribute on all prep_ids to new_value
				prep = trans.sa_session.query(trans.model.APLPrep).get(prep_id)
				setattr(prep, str(attribute), new_value)
				trans.sa_session.add(prep)
				trans.sa_session.flush()
				num_changed += 1

			message = '%i preps have been updated.' % num_changed

			return message

		except Exception as e:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
			trans.sa_session.rollback()
			message = 'Error: %s.' % str( e )
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_preps',
															status='error',
															message=message))


	def __create_default_samplesheet(self, trans, cntrller, **kwd):
		""" Creates all of the widgets to create a SampleSheet
		"""

		preps = literal_eval(kwd.get('preps', ''))
		last_value = int(kwd.get('last_value', ''))

		workflows = SelectField('workflow')
		workflows.add_option('Assembly', 'Assembly')
		workflows.add_option('Custom Amplicon', 'Custom Amplicon')
		workflows.add_option('Enrichment', 'Enrichment')
		workflows.add_option('GenerateFASTQ', 'GenerateFASTQ', selected=True)
		workflows.add_option('LibraryQC', 'LibraryQC')
		workflows.add_option('Metagenomics', 'Metagenomics')
		workflows.add_option('PCR Amplicon', 'PCR Amplicon')
		workflows.add_option('Resequencing', 'Resequencing')
		workflows.add_option('SmallRNA', 'SmallRNA')

		applications = SelectField('application')
		applications.add_option('TruSeq Amplicon', 'TruSeq Amplicon')
		applications.add_option('PCR Amplicon', 'PCR Amplicon')
		applications.add_option('Metagenomics', 'Metagenomics')
		applications.add_option('Enrichment', 'Enrichment')
		applications.add_option('Clone Checking', 'Clone Checking')
		applications.add_option('Amplicon - DS', 'Amplicon - DS')
		applications.add_option('Resequencing', 'Resequencing')
		applications.add_option('Plasmids', 'Plasmids')
		applications.add_option('Assembly', 'Assembly')
		applications.add_option('Targeted RNA', 'Targeted RNA')
		applications.add_option('Small RNA', 'Small RNA')
		applications.add_option('RNA-Seq', 'RNA-Seq')
		applications.add_option('Library QC', 'Library QC')
		applications.add_option('FASTQ Only', 'FASTQ Only', selected=True)
		applications.add_option('ChIP-Seq', 'ChIP-Seq')

		assays = SelectField('assay')
		assays.add_option('Nextera', 'Nextera')
		assays.add_option('Nextera XT', 'Nextera XT', selected=True)
		assays.add_option('TruSeq LT', 'TruSeq LT')
		assays.add_option('Small RNA', 'Small RNA')

		chemistries = SelectField('chemistry')
		chemistries.add_option('Amplicon', 'Amplicon')
		chemistries.add_option('Default', 'Default', selected=True)

		widgets = []
		widgets.append(dict(label='Investigator name',
#							widget=TextField('investigator', 50, trans.user.username[0:2].upper() + trans.user.username[2:]),
							widget=TextField('investigator', 50, trans.user.username),
							helptext=''))
		widgets.append(dict(label='Project name',
							widget=TextField('project_name', 50, ''),
							helptext=''))
		widgets.append(dict(label='Experiment name',
							widget=TextField('experiment_name', 50, ''),
							helptext=''))
		widgets.append(dict(label='Date',
							widget=TextField('date', 50, str(datetime.date.today())),
							helptext=''))

		widgets.append(dict(label='Workflow', widget=workflows, helptext=''))
		widgets.append(dict(label='Application', widget=applications, helptext=''))
		widgets.append(dict(label='Assay', widget=assays, helptext=''))
		widgets.append(dict(label='Chemistry', widget=chemistries, helptext=''))

		widgets.append(dict(label='Forward read length',
							widget=TextField('forward_length', 50, '251'),
							helptext=''))
		widgets.append(dict(label='Reverse read length',
							widget=TextField('reverse_length', 50, '251'),
							helptext=''))
		widgets.append(dict(label='Adapter',
							widget=TextField('adapter', 50, 'CTGTCTCTTATACACATCT'),
							helptext=''))

		widgets.append(dict(label='Preps',widget=HiddenField('preps', preps)))
		widgets.append(dict(label='Last Value', widget=HiddenField('last_value', last_value)))

		return widgets


	@web.expose
	@web.require_login('Enter values for SampleSheet')
	def review_samplesheet(self, trans, cntrller, **kwd):

#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get('status', 'done')

		# pull out values that need to be checked
		header = []
		header.append(dict(desc='Investigator name', value=kwd.get('investigator', '')))
		header.append(dict(desc='Project name', value=kwd.get('project_name', '')))
		header.append(dict(desc='Experiment name', value=kwd.get('experiment_name', '')))
		date = kwd.get('date', '')
		forward_length = kwd.get('forward_length', '')
		reverse_length = kwd.get('reverse_length', '')
		adapter = kwd.get('adapter', '')

		if kwd.get('submit_samplesheet_button', False):
			try:
				# check formatting
				for entry in header:
					try:
						entry['value'].decode('ascii')
					except:
						raise Exception('Remove special (non-ASCII) characters from %s' % entry['desc'])
				test = format_date(str(date))
				if divmod(float(forward_length), int(round(float(forward_length), 0)))[1] != 0:
					raise Exception('Forward read length (%s) must be an integer' % str(forward_length))
				if divmod(float(reverse_length), int(round(float(reverse_length), 0)))[1] != 0:
					raise Exception('Forward read length (%s) must be an integer' % str(reverse_length))
				if not re.match('[acgtACGT]*$', adapter):
					raise Exception('Adapter (%s) can only contain the letters A, C, G, and T' % str(adapter))

				download_file = self.__write_samplesheet(trans, cntrller, **kwd)

				# test to see if a file was properly created
				if download_file[-4:] == '.csv':
					return trans.fill_template('/apl_tracking/preps/download_samplesheet.mako',
												cntrller=cntrller,
												download_file=download_file,
												message=message,
												status=status)

					return trans.response.send_redirect(web.url_for(controller='apl_tracking',
																	action='browse_preps',
																	message=message,
																	status='done'))
				else:
					status = 'error'
					message = download_file

			except Exception as e:
				status = 'error'
				message = 'Error: %s' % str(e)

		if kwd.get('cancel_samplesheet_button', False):
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_preps',
															message='',
															status='done'))

		widgets = []

		preps = literal_eval(kwd.get('preps', ''))
		last_value = int(kwd.get('last_value', ''))

		workflows = SelectField('workflow')
		workflows.add_option('Assembly', 'Assembly')
		workflows.add_option('Custom Amplicon', 'Custom Amplicon')
		workflows.add_option('Enrichment', 'Enrichment')
		workflows.add_option('GenerateFASTQ', 'GenerateFASTQ', selected=True)
		workflows.add_option('LibraryQC', 'LibraryQC')
		workflows.add_option('Metagenomics', 'Metagenomics')
		workflows.add_option('PCR Amplicon', 'PCR Amplicon')
		workflows.add_option('Resequencing', 'Resequencing')
		workflows.add_option('SmallRNA', 'SmallRNA')

		applications = SelectField('application')
		applications.add_option('TruSeq Amplicon', 'TruSeq Amplicon')
		applications.add_option('PCR Amplicon', 'PCR Amplicon')
		applications.add_option('Metagenomics', 'Metagenomics')
		applications.add_option('Enrichment', 'Enrichment')
		applications.add_option('Clone Checking', 'Clone Checking')
		applications.add_option('Amplicon - DS', 'Amplicon - DS')
		applications.add_option('Resequencing', 'Resequencing')
		applications.add_option('Plasmids', 'Plasmids')
		applications.add_option('Assembly', 'Assembly')
		applications.add_option('Targeted RNA', 'Targeted RNA')
		applications.add_option('Small RNA', 'Small RNA')
		applications.add_option('RNA-Seq', 'RNA-Seq')
		applications.add_option('Library QC', 'Library QC')
		applications.add_option('FASTQ Only', 'FASTQ Only', selected=True)
		applications.add_option('ChIP-Seq', 'ChIP-Seq')

		assays = SelectField('assay')
		assays.add_option('Nextera', 'Nextera')
		assays.add_option('Nextera XT', 'Nextera XT', selected=True)
		assays.add_option('TruSeq LT', 'TruSeq LT')
		assays.add_option('Small RNA', 'Small RNA')

		chemistries = SelectField('chemistry')
		chemistries.add_option('Amplicon', 'Amplicon')
		chemistries.add_option('Default', 'Default', selected=True)

		widgets.append(dict(label='Investigator name',
							widget=TextField('investigator', 50, kwd.get('investigator', '')),
							helptext=''))
		widgets.append(dict(label='Project name',
							widget=TextField('project_name', 50, kwd.get('project_name', '')),
							helptext=''))
		widgets.append(dict(label='Experiment name',
							widget=TextField('experiment_name', 50, kwd.get('experiment_name', '')),
							helptext=''))
		widgets.append(dict(label='Date',
							widget=TextField('date', 50, kwd.get('date', '')),
							helptext=''))

		widgets.append(dict(label='Workflow', widget=workflows, helptext=''))
		widgets.append(dict(label='Application', widget=applications, helptext=''))
		widgets.append(dict(label='Assay', widget=assays, helptext=''))
		widgets.append(dict(label='Chemistry', widget=chemistries, helptext=''))

		widgets.append(dict(label='Forward read length',
							widget=TextField('forward_length', 50, kwd.get('forward_length', '')),
							helptext=''))
		widgets.append(dict(label='Reverse read length',
							widget=TextField('reverse_length', 50, kwd.get('reverse_length', '')),
							helptext=''))
		widgets.append(dict(label='Adapter',
							widget=TextField('adapter', 50, kwd.get('adapter', '')),
							helptext=''))

		widgets.append(dict(label='Preps',widget=HiddenField('preps', preps)))
		widgets.append(dict(label='Last Value', widget=HiddenField('last_value', last_value)))

		return trans.fill_template('/apl_tracking/preps/review_samplesheet.mako',
									cntrller=cntrller,
									widgets=widgets,
									message=message,
									status=status)


	def __write_samplesheet(self, trans, cntrller, **kwd):
		""" Write all of the SampleSheet data to a file
		"""
#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get('status', 'done')

		date = datetime.datetime.strptime(format_date(kwd.get('date', '')), '%Y-%m-%d')

		header = []
		header.append(dict(desc='Investigator Name', value=kwd.get('investigator', '')))
		header.append(dict(desc='Project Name', value=kwd.get('project_name', '')))
		header.append(dict(desc='Experiment Name', value=kwd.get('experiment_name', '')))
		header.append(dict(desc='Date', value=datetime.datetime.strftime(date, '%m/%d/%Y')))
		header.append(dict(desc='Workflow', value=kwd.get('workflow', '')))
		header.append(dict(desc='Application', value=kwd.get('application', '')))
		header.append(dict(desc='Assay', value=kwd.get('assay', '')))
		header.append(dict(desc='Chemistry', value=kwd.get('chemistry', '')))

		forward_length = int(kwd.get('forward_length', ''))
		reverse_length = int(kwd.get('reverse_length', ''))
		adapter = kwd.get('adapter', '')

		preps = literal_eval(kwd.get('preps', ''))
		last_value = int(kwd.get('last_value', ''))

		try:
			filepath = '/var/www/html/publicshare/samplesheets'
			filename = '%s/SampleSheet-' % filepath
			filename += datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
			filename += '.csv'
			f = open(filename, 'w')

			# write header
			f.write('[Header]\r\n')
			f.write('IEMFileVersion,4\r\n')
			for row in header:
				f.write('%s,%s\r\n' % (row['desc'], row['value']))
			f.write('\r\n')

			# write other sections
			f.write('[Reads]\r\n')
			f.write('%i\r\n' % forward_length)
			f.write('%i\r\n' % reverse_length)
			f.write('\r\n')
			f.write('[Settings]\r\n')
			f.write('Adapter,%s\r\n' % adapter)
			f.write('\r\n')

			# write data section
			f.write('[Data]\r\n')
			f.write('Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description\r\n')
			data = []
			for i, entry in enumerate(preps):
				prep = trans.sa_session.query(trans.model.APLPrep).get(last_value + i + 1)
				sample = trans.sa_session.query(trans.model.APLSample).get(prep.sample_id)
				sample_id = 'APL%09d' % prep.id
				# convert unicode characters to 'X'
				sample_name = re.sub(r"\\u\d+", "X", sample.name.encode('unicode_escape'))
				# convert spaces to underscores, convert special characters to 'X'
				sample_name = re.sub(r"[\?\(\)\[\]/\\=\+<>:;\"\',\*\^\|&\.]", "X", sample_name).replace(" ", "_")
				sample_plate = datetime.datetime.strftime(date, '%Y%m%d')
				sample_well = 'ABCDEFGH'[i % 8] + '%02d' % (i // 8 + 1,)
				i7_index_id = ''
				index = ''
				i5_index_id = ''
				index2 = ''
				sample_project = ''
				description = ''
				entry = [sample_id, sample_name, sample_plate, sample_well, i7_index_id, index, i5_index_id, index2, sample_project, description]
				data.append(entry)

			for entry in sorted(data, key=lambda item: item[0]):
				f.write('%s\r\n' % str(','.join((str(v) for v in entry))))

			f.close()
			return filename

		except Exception as e:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
			trans.sa_session.rollback()
			return str(e)


	@web.expose
	@web.require_login('Download SampleSheet')
	def download_samplesheet(self, trans, cntrller, **kwd):

#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get('status', 'done')

		if kwd.get('return_button', False):
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_preps',
															message='',
															status='done'))

		return trans.fill_template('/apl_tracking/preps/download_samplesheet.mako',
									cntrller=cntrller,
									message=message,
									status=status)

#=====================================================================================================================================================


	# ------------------------
	# Primer methods
	# ------------------------

	@web.expose
	@web.require_login("Add sample to Primers table")
	def create_primer(self, trans, cntrller, **kwd):
		message = ''
		status = 'done'

		# pull out variables that need format-checking
		description = kwd.get('description', '')
		sequence = kwd.get('sequence', '')
		design_date = kwd.get('design_date', '')
		primer_user = kwd.get('user_id', '')
		species = kwd.get('species', '')

		if kwd.get('create_primer_button', False):

			# check formatting for attributes that need format-checking

			# check that species exists in the organism table
			if not isNoneOrEmptyOrBlankString(species):
				try:
					test_species = trans.sa_session.query(trans.model.APLOrganism)\
								.filter(trans.model.APLOrganism.table.c.taxid == species).first()
					if test_species == None:
						message = 'Error: This taxid is not present in the Organism table: %s' % species
						status = 'error'
				except Exception as e:
						message = 'Error: %s' % e
						status = 'error'

			# check that sequence exists
			if isNoneOrEmptyOrBlankString(sequence):
				message = 'Error: Sequence cannot be left blank'
				status = 'error'

			# check that description exists
			if isNoneOrEmptyOrBlankString(description):
				message = 'Error: Description cannot be left blank'
				status = 'error'

			# check that user exists
			if isNoneOrEmptyOrBlankString(primer_user):
				message = 'Error: Username cannot be left blank'
				status = 'error'
			else:
				try:
					test = trans.sa_session.query(trans.model.User)\
												.filter(trans.model.User.table.c.username == primer_user)\
												.first()\
												.id
				except:
					message = 'Error: User does not exist: %s' % primer_user
					status = 'error'

			# check formatting of primer date
			try:
				test = format_date(design_date)
			except:
				if not isNoneOrEmptyOrBlankString(design_date):
					message = 'Error: Invalid date format: %s' % design_date
					status = 'error'

			# if all formatting checks out, save the results
			if status != 'error':
				request = self.__save_primer(trans, cntrller, **kwd)
				message = 'The sample has been created.'
				return trans.response.send_redirect(web.url_for(controller=cntrller,
																action='browse_primers',
																message=message,
																status="done"))

		# Widgets to be rendered on the request form
		# not sure why they call these widgets - I think these will basically end up being interactive features
		widgets = []

		widgets.append(dict(label='Date Designed',
							widget=TextField('design_date', 8, kwd.get('design_date', str(datetime.date.today()))),
							helptext='Format: YYYY-MM-DD (Required)'))
		widgets.append(dict(label='User',
							widget=TextField('user_id', 8, kwd.get('user_id', trans.sa_session.query(trans.model.User).get(trans.user.id).username)),
							helptext='(Required)'))
		widgets.append(dict(label='Description',
							widget=TextField('description', 100, kwd.get('description', '')),
							helptext='(Required)'))
		widgets.append(dict(label='Sequence',
							widget=TextField('sequence', 100, kwd.get('sequence', '')),
							helptext='(Required)'))
		widgets.append(dict(label='TaxID',
							widget=TextField('species', 8, kwd.get('species', '')),
							helptext='(Optional) Find taxids here: <a href="http://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi">http://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi</a>'))
		widgets.append(dict(label='Scale',
							widget=TextField('scale', 8, kwd.get('scale', '')),
							helptext='(Optional)'))
		widgets.append(dict(label='Purification',
							widget=TextField('purification', 100, kwd.get('purification', '')),
							helptext='(Optional)'))
		widgets.append(dict(label='Notes',
#							widget=	TextArea('notes', size="10x30", value=kwd.get('notes', primer.notes)),
							value=kwd.get('notes', ''),
							helptext='(Optional)'))

		return trans.fill_template('/apl_tracking/primer/create_primer.mako',
									cntrller=cntrller,
									widgets=widgets,
									message=message,
									status='done')


	@web.expose
	@web.require_login("Edit Primers")
	def edit_primer_info(self, trans, cntrller, **kwd):
		message = ''
		status = 'done'
		primer_id = kwd.get('id', None)

		# pull out variables that need format-checking
		design_date = kwd.get('design_date', '')
		primer_user = kwd.get('user_id', '')
		species = kwd.get('species', '')

		try:
			primer = trans.sa_session.query(trans.model.APLPrimer).get(trans.security.decode_id(primer_id))
		except:
			return invalid_id_redirect(trans, cntrller, primer_id)

		if kwd.get( 'edit_primer_info_button', False ):

			# check formatting for attributes that need format-checking

			# check that species exists in the organism table
			if not isNoneOrEmptyOrBlankString(species):
				try:
					test_species = trans.sa_session.query(trans.model.APLOrganism)\
								.filter(trans.model.APLOrganism.table.c.taxid == species).first()
					if test_species == None:
						message = 'Error: This taxid is not present in the Organism table: %s' % species
						status = 'error'
				except Exception as e:
						message = 'Error: %s' % e
						status = 'error'

			# check that sequence exists
			if isNoneOrEmptyOrBlankString(sequence):
				message = 'Error: Sequence cannot be left blank'
				status = 'error'

			# check that description exists
			if isNoneOrEmptyOrBlankString(description):
				message = 'Error: Description cannot be left blank'
				status = 'error'

			# check that user exists
			if isNoneOrEmptyOrBlankString(primer_user):
				message = 'Error: Username cannot be left blank'
				status = 'error'
			else:
				try:
					test = trans.sa_session.query(trans.model.User)\
												.filter(trans.model.User.table.c.username == primer_user)\
												.first()\
												.id
				except:
					message = 'Error: User does not exist: %s' % primer_user
					status = 'error'

			# check formatting of primer date
			try:
				test = format_date(design_date)
			except:
				if not isNoneOrEmptyOrBlankString(design_date):
					message = 'Error: Invalid date format: %s' % design_date
					status = 'error'

			# if all formatting checks out, save the results
			if status != 'error':
				primer = self.__save_primer( trans, cntrller, primer=primer, **kwd )
				message = 'The changes made to primer (PT_%05d) have been saved.' % primer.id
				return trans.response.send_redirect(web.url_for(controller=cntrller,
																action='browse_primers',
																message=message,
																status="done"))

		# Widgets to be rendered on the request form
		widgets = []

		widgets.append(dict(label='Date Designed',
							widget=TextField('design_date', 8, kwd.get('design_date', primer.design_date)),
							helptext='Format: YYYY-MM-DD (Required)'))
		widgets.append(dict(label='User',
							widget=TextField('user_id', 8, kwd.get('user_id', trans.sa_session.query(trans.model.User).get(primer.user_id).username)),
							helptext='(Required)'))
		widgets.append(dict(label='Description',
							widget=TextField('description', 100, kwd.get('description', primer.description)),
							helptext='(Required)'))
		widgets.append(dict(label='Sequence',
							widget=TextField('sequence', 100, kwd.get('sequence', primer.sequence)),
							helptext='(Required)'))
		widgets.append(dict(label='TaxID',
							widget=TextField('species', 8, kwd.get('species', trans.sa_session.query(trans.model.APLOrganism).get(primer.species).taxid)),
							helptext='(Optional) Find taxids here: <a href="http://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi">http://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi</a>'))
		widgets.append(dict(label='Scale',
							widget=TextField('scale', 8, kwd.get('scale', primer.scale)),
							helptext='(Optional)'))
		widgets.append(dict(label='Purification',
							widget=TextField('purification', 100, kwd.get('purification', primer.purification)),
							helptext='(Optional)'))
		widgets.append(dict(label='Notes',
#							widget=	TextArea('notes', size="10x30", value=kwd.get('notes', primer.notes)),
							value=kwd.get('notes', formatNullString(primer.notes)),
							helptext='(Optional)'))

		return trans.fill_template('/apl_tracking/primer/edit_primer_info.mako',
									cntrller=cntrller,
									primer=primer,
									widgets=widgets,
									message=message,
									status=status)


	def __save_primer( self, trans, cntrller, primer=None, **kwd ):
		""" Saves changes to an existing primer, or creates a new
			primer if primer is None.
		"""

#		is_admin = trans.user_is_admin()

		design_date = kwd.get('design_date', '')
		primer_user = kwd.get('user_id', '')
		description = kwd.get('description', '')
		sequence = kwd.get('sequence', '')
		species = kwd.get('species', '')
		scale = kwd.get('scale', '')
		purification = kwd.get('purification', '')
		notes = kwd.get('notes', '')

		# convert username to numerical ID
		primer_user_id = trans.sa_session.query(trans.model.User)\
									.filter(trans.model.User.table.c.username == primer_user)\
									.first()\
									.id

		# convert taxid to organism ID
		if isNoneOrEmptyOrBlankString(species):
			organism_id = None
		else:
			organism_id = trans.sa_session.query(trans.model.APLOrganism)\
									.filter(trans.model.APLOrganism.table.c.taxid == species)\
									.first()\
									.id

		data = [design_date, primer_user_id, description, sequence, organism_id, scale, purification, notes]

		# Deal with any empty strings or UTF-8 encoding
		for i in range(0, len(data)):
			if isNoneOrEmptyOrBlankString(data[i]):
				data[i] = None
			try:
				data[i] = data[i].decode('utf-8')
			except:
				pass

		# format design_date as a date
		try:
			data[0] = format_date(data[0])
		except:
			data[0] = None

		if primer is None:
			primer = trans.model.APLPrimer(design_date=data[0], user_id=data[1], description=data[2], sequence=data[3], species=data[4], scale=data[5], purification=data[6], notes=data[7])
			# These are SQLAlchemy methods, not galaxy methods!
			trans.sa_session.add(primer)
			trans.sa_session.flush()
			trans.sa_session.refresh(primer)

		else:
			# We're saving changes to an existing request
			primer.design_date = data[0]
			primer.user_id = data[1]
			primer.description = data[2]
			primer.sequence = data[3]
			primer.species = data[4]
			primer.scale = data[5]
			primer.purification = data[6]
			primer.notes = data[7]
			trans.sa_session.add(primer)
			trans.sa_session.flush()

		return primer


	@web.expose
	@web.require_login("View primer")
	def view_primer(self, trans, cntrller, **kwd):
#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get('status', 'done')
		primer_id = kwd.get('id', None)
		try:
			primer = trans.sa_session.query(trans.model.APLPrimer).get(trans.security.decode_id(primer_id))
		except:
			return invalid_id_redirect(trans, cntrller, primer_id)

		return trans.fill_template('/apl_tracking/primer/view_primer.mako',
									cntrller=cntrller,
									primer=primer,
									status=status,
									message=message)


	@web.expose
	@web.require_login("Import primers from text file")
	def import_primers(self, trans, cntrller, **kwd):
#		is_admin = trans.user_is_admin()
		message = ''
		status = 'done'
		file = kwd.get('file_data', '')
		sample_ids = kwd.get('sample_ids', '')

		# create template file
		filepath = '/var/www/html/publicshare/samplesheets'
		filename = '%s/import_primer_template.txt' % filepath
		f = open(filename, 'w')
		f.write('sample_id\tdesign_date\tnotes\n')
		f.close()

		if kwd.get('import_primers_button', False):
			try:
				if isNoneOrEmptyOrBlankString(str(file)):
					message="Please select a file"
					status="error"
				else:
					parameters = self.__import_primer(trans, cntrller, **kwd)
					return trans.fill_template('/apl_tracking/primer/review_primer_import.mako',
												cntrller=cntrller,
												parameters=parameters,
												message=None,
												status="done")

					return trans.response.send_redirect(web.url_for(controller=cntrller,
																	action='browse_primers',
																	message=message,
																	status='done'))
			except Exception as e:
				if str(e)[0:3] == '302':
					message = urllib.unquote_plus(str(e).split('message=')[1])
				else:
					message = str(e);
				status = 'error'

		if kwd.get('create_primer_group_button', False):
			if isNoneOrEmptyOrBlankString(str(sample_ids)):
				message="Please enter at least one Sample ID"
				status="error"
			elif isNoneOrEmptyOrBlankString(str(hyphen_range(sample_ids))):
				message="Check formatting of Sample IDs"
				status="error"
			else:
				parameters = self.__create_primer_group(trans, cntrller, **kwd)
				return trans.fill_template('/apl_tracking/primer/review_primer_import.mako',
											cntrller=cntrller,
											parameters=parameters,
											message=None,
											status="done")

				return trans.response.send_redirect(web.url_for(controller=cntrller,
																action='browse_primers',
																message=message,
																status='done'))

		widgets = []
		widgets.append(dict(label='Sample IDs',
							widget=TextField('sample_ids', 200, ''),
							helptext='Use commas and dashes for multiple samples / sample ranges'))
		widgets.append(dict(label='Date Designed',
							widget=TextField('design_date', 200, str(datetime.date.today())),
							helptext='This primer date will be used for every primer'))
		widgets.append(dict(label='Notes',
							widget=TextArea('notes', size='4x30', value=''),
							helptext='These notes will be used for every primer'))

		return trans.fill_template('/apl_tracking/primer/import_primers.mako',
									cntrller=cntrller,
									widgets=widgets,
									message=message,
									status=status)


	def __import_primer(self, trans, cntrller, **kwd):
		""" Reads a tab-separated file, checks the values, and sends the data to be reviewed
		"""

#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get( 'status', 'done' )

#		try:
#			user_id = trans.sa_session.query(trans.model.User)\
#										.filter(trans.model.User.table.c.username==user)\
#										.first()\
#										.id
#		except:
#			user_id = trans.user.id

		# get file object from file that was imported
		# file_obj.file is equivalent to what would be returned by open("filename", "rb")
		file_obj = kwd.get('file_data', '')

		try:
			if isNoneOrEmptyOrBlankString(str(file_obj.file)):
				raise Exception("File does not exist")
			else:
				# pull value of current pointer
				# open connection to the galaxy database - I'd rather not do this, but I can't figure out how using SQLAlchemy
				conn = pg.connect("host=odin port=5477 dbname=galaxy_database user=galaxy password=galaxy")
				cur = conn.cursor()
				cur.execute("SELECT last_value FROM apl_primer_id_seq;")
				conn.commit()
				last_value = int(cur.fetchone()[0])
				cur.close()
				conn.close()

				# read in input file as single string
				opened = file_obj.file.read()
				# split by any possible line endings, remove empty lines
				lines = filter(None, re.split(r'[\n\r]+', opened))

				# pull off header, make sure it is correct
				header = lines[0].rstrip().split('\t')
				lines = lines[1:]
				if sorted(header) != sorted(['sample_id', 'design_date', 'notes']):
					raise Exception('Header is not correct, make sure you use the provided template (your header: %s)' % header)

				new_primers = []

				# go through each line of input file
				for l,line in enumerate(lines):

					# make sure line is not entirely composed of whitespace
					if line.strip():

						# remove trailing whitespace, split input line, and nullify empty strings
						primer = line.rstrip().split('\t')
						for i in range(0, len(primer)):
							if isNoneOrEmptyOrBlankString(primer[i]):
								primer[i] = None
							else:
								# Deal with any UTF-8 encoding
								try:
									primer[i] = primer[i].rstrip().decode('utf-8')
								except:
									primer[i] = primer[i].rstrip()

						# make sure list is the correct length
						if len(primer) > 3:
							raise Exception('Primer in row %i contains %i columns (should contain 3)' % (l+1, len(primer)))
						while len(primer) < 3:
							primer.append(None)

						# check formatting for sample ID
						if not primer[0]:
							raise Exception('Sample ID cannot be left blank for primer in row %i' % (l+1))
						else:
							try:
								sample_id = int(re.sub('^SMP0*', '', primer[0]))
							except:
								raise Exception('Invalid sample ID (\'%s\') in row %i' % (primer[0], l+1))

							if trans.sa_session.query(trans.model.APLSample).get( int(re.sub('^SMP0*', '', primer[0])) ) == None:
								raise Exception("No sample in database with ID = %s" % primer[0])

						# check formatting for created date, make it today if it does not exist
						if primer[1] is not None:
							try:
								design_date = format_date(primer[1])
							except:
								raise Exception('Invalid primer date (\'%s\') in row %i' % (primer[1], l+1))
						else:
							design_date = str(datetime.date.today())

						# I don't believe these need any format checking
						if len(primer) == 3:
							notes = primer[2]
						else:
							notes = None

						new_primers.append([sample_id, design_date, notes])

				parameters = []
				parameters.append(dict(widget=HiddenField('last_value', last_value), value=last_value))
				parameters.append(dict(widget=HiddenField('primers', new_primers), value=new_primers))

				return parameters

		except Exception as e:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
			trans.sa_session.rollback()
			message = 'Error: %s.' % str( e )
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_primers',
															status='error',
															message=message))


	@web.expose
	@web.require_login("Review primers for import")
	def review_primer_import(self, trans, cntrller, **kwd):
#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get('status', 'done')
		last_value = int(kwd.get('last_value',''))
		primers = literal_eval(kwd.get('primers',''))

		if kwd.get('review_primer_import_button', False):
			# open connection to the galaxy database - I'd rather not do this, but I can't figure out how using SQLAlchemy
			conn = pg.connect("host=odin port=5477 dbname=galaxy_database user=galaxy password=galaxy")
			cur = conn.cursor()
			cur.execute("SELECT last_value FROM apl_primer_id_seq;")
			conn.commit()
			current_value = int(cur.fetchone()[0])
			cur.close()
			conn.close()

			# check to make sure last_value is still equal to the current_value
			if current_value != last_value:
				message = "The database has been modified since you began this edit.  Primer IDs have been updated.  Please try again."
				status = 'error'
				last_value = current_value
			else:
				message = self.__save_primer_import(trans, cntrller, **kwd)
				return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_primers',
															message=message,
															status='done'))

		if kwd.get('create_samplesheet_button', False):
			# open connection to the galaxy database - I'd rather not do this, but I can't figure out how using SQLAlchemy
			conn = pg.connect("host=odin port=5477 dbname=galaxy_database user=galaxy password=galaxy")
			cur = conn.cursor()
			cur.execute('SELECT last_value FROM apl_primer_id_seq;')
			conn.commit()
			current_value = int(cur.fetchone()[0])
			cur.close()
			conn.close()

			# check to make sure last_value is still equal to the current_value
			if current_value != last_value:
				message = 'The database has been modified since you began this edit.  Primer IDs have been updated.  Please try again.'
				status = 'error'
				last_value = current_value
			else:
				message = self.__save_primer_import(trans, cntrller, **kwd)
				widgets = self.__create_default_samplesheet(trans, cntrller, **kwd)
				return trans.fill_template('/apl_tracking/primer/review_samplesheet.mako',
											cntrller=cntrller,
											message=message,
											widgets=widgets,
											status='done')
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_primers',
															message=message,
															status='done'))

		if kwd.get('cancel_primer_import_button', False):
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_primers',
															message='Import canceled',
															status='done'))

		parameters = []
		parameters.append(dict(widget=HiddenField('last_value', last_value),
					value=last_value))
		parameters.append(dict(widget=HiddenField('primers', primers),
					value=primers))

		return trans.fill_template('/apl_tracking/primer/review_primer_import.mako',
									cntrller=cntrller,
									parameters=parameters,
									message=message,
									status=status)


	def __save_primer_import(self, trans, cntrller, **kwd):
		""" Saves a list of imported primers to the database
		"""

#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get( 'status', 'done' )

		last_value = int(kwd.get('last_value',''))
		primers = literal_eval(kwd.get('primers',''))

		try:
			# open connection to the galaxy database - I'd rather not do this, but I can't figure out how using SQLAlchemy
			conn = pg.connect("host=odin port=5477 dbname=galaxy_database user=galaxy password=galaxy")
			cur = conn.cursor()
			cur.execute("SELECT last_value FROM apl_primer_id_seq;")
			conn.commit()
			current_value = int(cur.fetchone()[0])
			cur.close()
			conn.close()

			# check to make sure last_value is still equal to the current_value
			if current_value != last_value:
				raise Exception("The database has been modified since you began this edit.  Please try again.")

			num_added = 0

			for primer in primers:
				for i,attr in enumerate(primer):
					try:
						primer[i] = primer[i].decode('utf-8')
					except:
						pass

				sample_id = primer[0]
				design_date = primer[1]
				user_id = trans.user.id
				notes = primer[2]

				this_primer = trans.model.APLPrimer(sample_id=sample_id, design_date=design_date, user_id=user_id, notes=notes)

				# These are SQLAlchemy methods, not galaxy methods!
				trans.sa_session.add(this_primer)
				trans.sa_session.flush()
				trans.sa_session.refresh(this_primer)

				num_added += 1

			message = '%i primers have been imported.' % num_added

			return message

		except Exception as e:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
			trans.sa_session.rollback()
			message = 'Error: %s.' % str( e )
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_primers',
															status='error',
															message=message))


	@web.expose
	@web.require_login("Edit a group of primers")
	def edit_primer_group(self, trans, cntrller, **kwd):
#		is_admin = trans.user_is_admin()
		message = ''
		status = 'done'

		primer_ids = kwd.get('primer_ids', '')
		attribute = kwd.get('attribute', '')
		new_value = kwd.get('new_value', None)
		try:
			primer_ids = primer_ids.decode('utf-8')
		except:
			pass
		try:
			new_value = new_value.decode('utf-8')
		except:
			pass

		if kwd.get('edit_primer_group_button', False):

			# check formatting for attributes that need format-checking

			# check to make sure user exists
			if attribute == 'user_id':
				try:
					user_id = trans.sa_session.query(trans.model.User)\
											.filter(trans.model.User.table.c.username==new_value)\
											.first()\
											.id
				except:
					message = 'Error: user does not exist: %s' % new_value
					status = 'error'

			# fix formatting of new_value in case it is a date
			if attribute == 'design_date':
				try:
					test = format_date(new_value)
				except:
					if not isNoneOrEmptyOrBlankString(new_value):
						message = 'Error: Invalid date format: %s' % new_value
						status = 'error'

			# check that primer IDs are formatted properly and exist in the database
			try:
				s = hyphen_range(primer_ids)
				good_ids = []
				problem_ids = []
				for i, id in enumerate(s):
					test_primer = trans.sa_session.query(trans.model.APLPrimer).get(id)
					if test_primer == None:
						problem_ids.append(id)
				if len(problem_ids) > 0:
					message = 'Error: These primer IDs do not exist (%s).' % problem_ids
					status = 'error'
			except:
				message = 'Error: Invalid format for primer IDs'
				status = 'error'

			if status != 'error':
				parameters = self.__edit_primer_group(trans, cntrller, **kwd)
				return trans.fill_template('/apl_tracking/primer/review_primer_group.mako',
											cntrller=cntrller,
											parameters=parameters,
											message=None,
											status="done")

				return trans.response.send_redirect(web.url_for(controller='apl_tracking',
																action='browse_primers',
																message=message,
																status='done'))

		attributes = SelectField('attribute', multiple=False)
		attributes.add_option('Date Designed', 'design_date')
		attributes.add_option('User', 'user_id')
		attributes.add_option('Notes', 'notes')

		widgets = []
		widgets.append(dict(label='Primer IDs',
							widget=TextField('primer_ids', 200, kwd.get('primer_ids', '')),
							helptext='Use commas and dashes for multiple primers / primer ranges'))
		widgets.append(dict(label='Attribute',
							widget=attributes,
							helptext='Select the attribute you want to edit'))
		widgets.append(dict(label='New Value',
							widget=TextField('new_value', 200, kwd.get('new_value', '')),
							helptext='Change the selected attribute to this value for all of the listed primer IDs'))

		return trans.fill_template('/apl_tracking/primer/edit_primer_group.mako',
									cntrller=cntrller,
									widgets=widgets,
									message=message,
									status=status)


	def __edit_primer_group(self, trans, cntrller, **kwd):
		""" Edit a large group of primers at once
		"""

#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get( 'status', 'done' )

		primer_ids = kwd.get('primer_ids', '')
		attribute = kwd.get('attribute', '')
		new_value = kwd.get('new_value', None)

#		try:
#			user_id = trans.sa_session.query(trans.model.User)\
#										.filter(trans.model.User.table.c.username==user)\
#										.first()\
#										.id
#		except:
#			user_id = trans.user.id

		if not isNoneOrEmptyOrBlankString(primer_ids):
			try:
				# split primer_ids
				s = hyphen_range(primer_ids)

				# fix formatting of new_value if not empty
				if not isNoneOrEmptyOrBlankString(new_value):

					# remove any trailing spaces
					try:
						new_value = new_value.strip()
					except:
						pass
					# fix formatting of new_value in case it is unicode
					try:
						new_value = new_value.decode('utf-8')
					except:
						pass
					# fix formatting of new_value in case it is a date
					if attribute == 'design_date':
						new_value = format_date(new_value)
					# fix formatting of new_value in case it is an integer
					if re.match('^[0-9]+$', new_value):
						new_value = int(new_value)

				parameters = []
				parameters.append(dict(widget=HiddenField('primer_ids', s),
							value=s))
				parameters.append(dict(widget=HiddenField('attribute', attribute),
							value=attribute))
				parameters.append(dict(widget=HiddenField('new_value', new_value),
							value=new_value))

				return parameters

			except Exception as e:
				exc_type, exc_value, exc_traceback = sys.exc_info()
				traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
				trans.sa_session.rollback()
				message = 'Error: %s.' % str( e )
				return trans.response.send_redirect(web.url_for(controller='apl_tracking',
																action='browse_primers',
																status='error',
																message=message))


	@web.expose
	@web.require_login("Edit a group of primers")
	def review_primer_group(self, trans, cntrller, **kwd):
#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get('status', 'done')

		if kwd.get('review_primer_group_button', False):
			message = self.__save_primer_group(trans, cntrller, **kwd)
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_primers',
															message=message,
															status='done'))

		if kwd.get('cancel_primer_group_button', False):
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_primers',
															message='Edit canceled',
															status='done'))

		return trans.fill_template('/apl_tracking/primer/review_primer_group.mako',
									cntrller=cntrller,
									parameters=parameters,
									message=None,
									status="done")


	def __save_primer_group(self, trans, cntrller, **kwd):
		""" Save changes to a large group of primers at once
		"""

#		is_admin = trans.user_is_admin()
		message = kwd.get('message', '')
		status = kwd.get( 'status', 'done' )

		primer_ids = kwd.get('primer_ids', '')
		attribute = kwd.get('attribute', '')
		new_value = kwd.get('new_value', None)

		# set new value to None if necessary
		if isNoneOrEmptyOrBlankString(new_value):
			new_value = None

		# deal with UTF-8 encoding
		try:
			new_value = new_value.decode('utf-8')
		except:
			pass

		# convert username to user ID if necessary
		if attribute == 'user_id':
			new_value = trans.sa_session.query(trans.model.User)\
										.filter(trans.model.User.table.c.username==new_value)\
										.first()\
										.id

		num_changed = 0

		# backup existing table
		backup_file = "/data/backups/apl-tables/apl_primer-%d" % (int(time.time()*1e9))
		args = shlex.split("pg_dump --port 5477 --username galaxy --format plain --ignore-version --verbose --file %s --table apl_primer galaxy_database" % (backup_file))
		p = subprocess.Popen(args)
		p.wait()

		try:
			for primer_id in literal_eval(primer_ids):

				# change attribute on all primer_ids to new_value
				primer = trans.sa_session.query(trans.model.APLPrimer).get(primer_id)
				setattr(primer, str(attribute), new_value)
				trans.sa_session.add(primer)
				trans.sa_session.flush()
				num_changed += 1

			message = '%i primers have been updated.' % num_changed

			return message

		except Exception as e:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
			trans.sa_session.rollback()
			message = 'Error: %s.' % str( e )
			return trans.response.send_redirect(web.url_for(controller='apl_tracking',
															action='browse_primers',
															status='error',
															message=message))
