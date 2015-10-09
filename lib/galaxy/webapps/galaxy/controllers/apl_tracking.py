# apl_tracking.py
# User controller

from __future__ import absolute_import

from galaxy.web.base.controller import *
from galaxy.web.framework.helpers import grids
from galaxy.model.orm import *
from galaxy.web.form_builder import *
from .apl_tracking_common import SamplesGrid, ProphecySamplesGrid, PrepsGrid, RunsGrid, PrimerGrid
import logging

log = logging.getLogger( __name__ )


class UserSamplesGrid(SamplesGrid):
	# operations may be enacted on any sample in the table
	operations = [operation for operation in SamplesGrid.operations]
	operations.append(grids.GridOperation("View", allow_multiple=False))
	operations.append(grids.GridOperation("Edit", allow_multiple=False, condition=(lambda item: not item.deleted)))
	operations.append(grids.GridOperation("Delete", allow_multiple=False, condition=(lambda item: not item.deleted)))
	operations.append(grids.GridOperation("Undelete", allow_multiple=False, condition=(lambda item: item.deleted)))
	# By defult, show all samples that have not been deleted
	def apply_query_filter(self, trans, query, **kwd):
		return query.filter_by(deleted=False)


class UserProphecySamplesGrid(ProphecySamplesGrid):
	# we do not allow deletion and undeletion here
	# Prophecy samples should be deleted at the same time as their non-Prophecy counterparts
	operations = [operation for operation in ProphecySamplesGrid.operations]
	operations.append(grids.GridOperation("View", allow_multiple=False))
	operations.append(grids.GridOperation("Edit", allow_multiple=False, condition=(lambda item: not item.deleted)))
	def apply_query_filter(self, trans, query, **kwd):
		return query.filter_by(deleted=False)


class UserPrepsGrid(PrepsGrid):
	operations = [operation for operation in PrepsGrid.operations]
	operations.append(grids.GridOperation("View", allow_multiple=False))	
	operations.append(grids.GridOperation("Edit", allow_multiple=False, condition=(lambda item: not item.deleted)))
	operations.append(grids.GridOperation("Delete", allow_multiple=False, condition=(lambda item: not item.deleted)))
	operations.append(grids.GridOperation("Undelete", allow_multiple=False, condition=(lambda item: item.deleted)))
	def apply_query_filter(self, trans, query, **kwd):
		return query.filter_by(deleted=False)


class UserRunsGrid( RunsGrid ):
#	operations = [operation for operation in RunsGrid.operations]
#	operations.append(grids.GridOperation("View", allow_multiple=False))	
#	operations.append(grids.GridOperation("Edit", allow_multiple=False, condition=(lambda item: not item.deleted)))
#	operations.append(grids.GridOperation("Delete", allow_multiple=False, condition=(lambda item: not item.deleted)))
#	operations.append(grids.GridOperation("Undelete", allow_multiple=False, condition=(lambda item: item.deleted)))
	def apply_query_filter(self, trans, query, **kwd):
		return query.filter_by(deleted=False)


class UserPrimerGrid(PrimerGrid):
	operations = [operation for operation in PrimerGrid.operations]
	operations.append(grids.GridOperation("View", allow_multiple=False))	
	operations.append(grids.GridOperation("Edit", allow_multiple=False, condition=(lambda item: not item.deleted)))
#	operations.append(grids.GridOperation("Delete", allow_multiple=False, condition=(lambda item: not item.deleted)))
#	operations.append(grids.GridOperation("Undelete", allow_multiple=False, condition=(lambda item: item.deleted)))
	def apply_query_filter(self, trans, query, **kwd):
		return query.filter_by(deleted=False)


class APLTracking(BaseUIController):
	# Once work with Samples tables is completed, class instances of UserPrepsGrid and UserRunsGrid will need to be added
	samples_grid = UserSamplesGrid()
	prophecy_samples_grid = UserProphecySamplesGrid()
	preps_grid = UserPrepsGrid()
	runs_grid = UserRunsGrid()
	primer_grid = UserPrimerGrid()

	# Displays index for APLSample table
	@web.expose
	@web.require_login("View samples table")
	def sample(self, trans):
		return trans.fill_template("/apl_tracking/sample/index.mako")

	# While browsing samples, the user can activate several methods
	# Any transfer that needs to occur thus happens through the "operation" keyword
	@web.expose
	def browse_samples(self, trans, **kwd):
		if 'operation' in kwd:
			operation = kwd['operation'].lower()
			if operation == "edit" or operation == "edit_sample_info":
				return trans.response.send_redirect(web.url_for(controller='apl_tracking_common',
																action='edit_sample_info',
																cntrller='apl_tracking',
																**kwd))
			if operation == "view" or operation == "view_sample":
				return trans.response.send_redirect(web.url_for(controller='apl_tracking_common',
																action='view_sample',
																cntrller='apl_tracking',
																**kwd))
			if operation == "import" or operation == "import_samples":
				return trans.response.send_redirect(web.url_for(controller='apl_tracking_common',
																action='import_samples',
																cntrller='apl_tracking',
																**kwd))
			if operation == "delete" or operation == "delete_samples":
				return trans.response.send_redirect(web.url_for(controller='apl_tracking_common',
																action='delete_samples',
																cntrller='apl_tracking',
																**kwd))
			if operation == "undelete" or operation == "undelete_samples":
				return trans.response.send_redirect(web.url_for(controller='apl_tracking_common',
																action='undelete_samples',
																cntrller='apl_tracking',
																**kwd))
		# global_actions can be activated not through a particular sample, but from outside the table
		# Each GridAction creates a button that the user can then press to create or import samples
		self.samples_grid.global_actions = [
#											grids.GridAction("Create sample", dict(controller='apl_tracking_common',
#																					action='create_sample',
#																					cntrller='apl_tracking')),
											grids.GridAction("Import samples", dict(controller='apl_tracking_common',
																							action='import_samples',
																							cntrller='apl_tracking')),
											grids.GridAction("Edit group of samples", dict(controller='apl_tracking_common',
																					action='edit_sample_group',
																					cntrller='apl_tracking')),
											]
		# Render the list view
		return self.samples_grid(trans, **kwd)


	# These two methods need to be repeated for each table
	@web.expose
	@web.require_login("View samples table")
	def prophecy(self, trans):
		return trans.fill_template("/apl_tracking/prophecy/prophecy_index.mako")

	@web.expose
	@web.require_login("View Prophecy-specific samples table")
	def browse_prophecies(self, trans, **kwd):
		if 'operation' in kwd:
			operation = kwd['operation'].lower()
			if operation == "edit" or operation == "edit_sample_info":
				return trans.response.send_redirect(web.url_for(controller='apl_tracking_common',
																action='edit_prophecy_sample_info',
																cntrller='apl_tracking',
																**kwd))
			if operation == "view" or operation == "view_prophecy_sample":
				return trans.response.send_redirect(web.url_for(controller='apl_tracking_common',
																action='view_prophecy_sample',
																cntrller='apl_tracking',
																**kwd))
			if operation == "view_sample":
				return trans.response.send_redirect(web.url_for(controller='apl_tracking_common',
																action='view_sample',
																cntrller='apl_tracking',
																**kwd))
			if operation == "import" or operation == "import_samples":
				return trans.response.send_redirect(web.url_for(controller='apl_tracking_common',
																action='import_prophecy_samples',
																cntrller='apl_tracking',
																**kwd))
		self.prophecy_samples_grid.global_actions = [
#											grids.GridAction("Create Prophecy sample", dict(controller='apl_tracking_common',
#																					action='create_prophecy_sample',
#																					cntrller='apl_tracking')),
											grids.GridAction("Create samples", dict(controller='apl_tracking_common',
																							action='create_prophecy_samples',
																							cntrller='apl_tracking')),
#											grids.GridAction("Import Prophecy samples", dict(controller='apl_tracking_common',
#																							action='import_prophecy_samples',
#																							cntrller='apl_tracking')),
											grids.GridAction("Edit group of Prophecy samples", dict(controller='apl_tracking_common',
																							action='edit_prophecy_group',
																							cntrller='apl_tracking'))
											]
		# Render the list view
		return self.prophecy_samples_grid(trans, **kwd)


	# These two methods need to be repeated for each table
	@web.expose
	@web.require_login("View preps table")
	def prep(self, trans):
		return trans.fill_template("/apl_tracking/preps/preps_index.mako")

	@web.expose
	@web.require_login("View preps table")
	def browse_preps(self, trans, **kwd):
		if 'operation' in kwd:
			operation = kwd['operation'].lower()
			if operation == "edit" or operation == "edit_prep_info":
				return trans.response.send_redirect(web.url_for(controller='apl_tracking_common',
																action='edit_prep_info',
																cntrller='apl_tracking',
																**kwd))
			if operation == "view" or operation == "view_prep":
				return trans.response.send_redirect(web.url_for(controller='apl_tracking_common',
																action='view_prep',
																cntrller='apl_tracking',
																**kwd))
			if operation == "view_sample":
				return trans.response.send_redirect(web.url_for(controller='apl_tracking_common',
																action='view_sample',
																cntrller='apl_tracking',
																**kwd))
			if operation == "import" or operation == "import_preps":
				return trans.response.send_redirect(web.url_for(controller='apl_tracking_common',
																action='import_preps',
																cntrller='apl_tracking',
																**kwd))
			if operation == "delete" or operation == "delete_preps":
				return trans.response.send_redirect(web.url_for(controller='apl_tracking_common',
																action='delete_preps',
																cntrller='apl_tracking',
																**kwd))
			if operation == "undelete" or operation == "undelete_preps":
				return trans.response.send_redirect(web.url_for(controller='apl_tracking_common',
																action='undelete_preps',
																cntrller='apl_tracking',
																**kwd))
		self.preps_grid.global_actions = [
											grids.GridAction("Create prep pool", dict(controller='apl_tracking_common',
																					action='create_prep_pool',
																					cntrller='apl_tracking')),
											grids.GridAction("Import preps", dict(controller='apl_tracking_common',
																							action='import_preps',
																							cntrller='apl_tracking')),
											grids.GridAction("Edit group of preps", dict(controller='apl_tracking_common',
																							action='edit_prep_group',
																							cntrller='apl_tracking'))
											]
		# Render the list view
		return self.preps_grid(trans, **kwd)


	# These two methods need to be repeated for each table
	@web.expose
	@web.require_login("View runs table")
	def run(self, trans):
		return trans.fill_template("/apl_tracking/run/run_index.mako")

	@web.expose
	@web.require_login("View runs table")
	def browse_runs(self, trans, **kwd):
		# Render the list view
		return self.runs_grid(trans, **kwd)


	# These two methods need to be repeated for each table
	@web.expose
	@web.require_login("View primer table")
	def primer(self, trans):
		return trans.fill_template("/apl_tracking/primer/primer_index.mako")

	@web.expose
	@web.require_login("View primer table")
	def browse_primers(self, trans, **kwd):
		if 'operation' in kwd:
			operation = kwd['operation'].lower()
			if operation == "edit" or operation == "edit_primer_info":
				return trans.response.send_redirect(web.url_for(controller='apl_tracking_common',
																action='edit_primer_info',
																cntrller='apl_tracking',
																**kwd))
			if operation == "view" or operation == "view_primer":
				return trans.response.send_redirect(web.url_for(controller='apl_tracking_common',
																action='view_primer',
																cntrller='apl_tracking',
																**kwd))
#			if operation == "delete" or operation == "delete_primers":
#				return trans.response.send_redirect(web.url_for(controller='apl_tracking_common',
#																action='delete_primers',
#																cntrller='apl_tracking',
#																**kwd))
#			if operation == "undelete" or operation == "undelete_primers":
#				return trans.response.send_redirect(web.url_for(controller='apl_tracking_common',
#																action='undelete_primers',
#																cntrller='apl_tracking',
#																**kwd))
		self.primer_grid.global_actions = [
											grids.GridAction("Create primer", dict(controller='apl_tracking_common',
																					action='create_primer',
																					cntrller='apl_tracking'))#,
#											grids.GridAction("Import preps", dict(controller='apl_tracking_common',
#																							action='import_preps',
#																							cntrller='apl_tracking')),
#											grids.GridAction("Edit group of preps", dict(controller='apl_tracking_common',
#																							action='edit_prep_group',
#																							cntrller='apl_tracking'))
											]
		# Render the list view
		return self.primer_grid(trans, **kwd)
