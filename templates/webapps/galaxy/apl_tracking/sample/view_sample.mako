<%inherit file="/base.mako"/>
<%namespace file="/message.mako" import="render_msg" />
<%namespace file="/apl_tracking/common/common.mako" import="common_javascripts" />

<%def name="stylesheets()">
	${parent.stylesheets()}
	${h.css( "library" )}
</%def>

<%def name="javascripts()">
	${parent.javascripts()}
	${common_javascripts()}
</%def>

<%
	from galaxy.web.framework.helpers import time_ago

	is_admin = trans.user_is_admin()
	can_delete = is_admin and not sample.deleted
	can_undelete = is_admin and sample.deleted

	try:
		prophecy = trans.sa_session.query(trans.model.APLProphecySample)\
								.filter(trans.model.APLProphecySample.table.c.sample_id == sample.id)\
								.first()
	except:
		prophecy = None

%>

<br/><br/>

<ul class="manage-table-actions">
	<li><a class="action-button" id="sample-${sample.id}-popup" class="menubutton">Sample Actions</a></li>
	<div popupmenu="sample-${sample.id}-popup">
		%if can_delete:
			<a class="action-button" href="${h.url_for(controller='apl_tracking_common', action='delete_sample', cntrller=cntrller, id=trans.security.encode_id(sample.id))}">Delete this sample</a>
		%endif
		%if can_undelete:
			<a class="action-button" href="${h.url_for( controller='apl_tracking_common', action='undelete_sample', cntrller=cntrller, id=trans.security.encode_id(sample.id))}">Undelete this sample</a>
		%endif
		<a class="action-button" href="${h.url_for(controller='apl_tracking_common', action='edit_sample_info', cntrller=cntrller, id=trans.security.encode_id(sample.id))}">Edit sample information</a>
		%if prophecy != None:
			<a class="action-button" href="${h.url_for(controller='apl_tracking_common', action='edit_prophecy_sample_info', cntrller=cntrller, id=trans.security.encode_id(prophecy.id))}">Edit Prophecy information</a>
		%endif
	</div>
</ul>

<div class="toolForm">
	<div class="toolFormTitle">Sample: ${"SMP" + "0"*(9 - len(str(sample.id))) + str(sample.id)}</div>
	<div class="toolFormBody">
		<div class="form-row">
			<label>Parent ID:</label>
			%if sample.parent_id != None:
				<a href="${h.url_for(controller='apl_tracking_common', action='view_sample', cntrller=cntrller, id=trans.security.encode_id(sample.parent_id))}">
					${"SMP" + "0"*(9 - len(str(sample.parent_id))) + str(sample.parent_id)}
				</a>
			%else:
				${sample.parent_id}
			%endif
			<div style="clear: both"></div>
		</div>
		<div class="form-row">
			<label>Name:</label>
			${sample.name}
			<div style="clear: both"></div>
		</div>
		<div class="form-row">
			<label>Species:</label>
			${sample.species}
			<div style="clear: both"></div>
		</div>
		<div class="form-row">
			<label>Host:</label>
			${sample.host}
			<div style="clear: both"></div>
		</div>
		<div class="form-row">
			<label>Sample Type:</label>
			${sample.sample_type}
			<div style="clear: both"></div>
		</div>
		<div class="form-row">
			<label>Date of Creation</label>
			${sample.created}
			<div style="clear: both"></div>
		</div>
		<div class="form-row">
			<label>User:</label>
			${trans.sa_session.query(trans.model.User).get(sample.user_id).username}
			<div style="clear: both"></div>
		</div>
		<div class="form-row">
			<label>Lab:</label>
			${sample.lab}
			<div style="clear: both"></div>
		</div>
		<div class="form-row">
			<label>Project</label>
			${sample.project}
			<div style="clear: both"></div>
		</div>
		<div class="form-row">
			<label>Experiment Type:</label>
			${sample.experiment_type}
			<div style="clear: both"></div>
		</div>
		<div class="form-row">
			<label>Notes</label>
			${sample.notes}
			<div style="clear: both"></div>
		</div>

		%if prophecy != None:
			<div class="form-row">
				<label>Prophecy ID</label>
				<a href="${h.url_for(controller='apl_tracking_common', action='view_prophecy_sample', cntrller=cntrller, id=trans.security.encode_id(prophecy.id))}">
					${"PRO_" + "0"*(5 - len(str(prophecy.id))) + str(prophecy.id)}
				</a>
				<div style="clear: both"></div>
			</div>
			<div class="form-row">
				<label>Associated Sample Information</label>
				${prophecy.associated_sample}
				<div style="clear: both"></div>
			</div>
			<div class="form-row">
				<label>RG Transcription</label>
				${prophecy.rg_transcribed}
				<div style="clear: both"></div>
			</div>
			<div class="form-row">
				<label>RG Transfection</label>
				${prophecy.rg_transfected}
				<div style="clear: both"></div>
			</div>
			<div class="form-row">
				<label>RG Amplification</label>
				${prophecy.rg_amplification}
				<div style="clear: both"></div>
			</div>
			<div class="form-row">
				<label>Bulk Experiment</label>
				${prophecy.expt_bulk}
				<div style="clear: both"></div>
			</div>
			<div class="form-row">
				<label>Droplet Experiment</label>
				${prophecy.expt_droplet}
				<div style="clear: both"></div>
			</div>
			<div class="form-row">
				<label>TCID50 Analysis</label>
				${prophecy.analysis_tcid50}
				<div style="clear: both"></div>
			</div>
			<div class="form-row">
				<label>QPCR Analysis</label>
				${prophecy.analysis_qpcr}
				<div style="clear: both"></div>
			</div>
			<div class="form-row">
				<label>RNA Isolation</label>
				${prophecy.rna_isolation}
				<div style="clear: both"></div>
			</div>
			<div class="form-row">
				<label>Sequencing Analysis</label>
				${prophecy.analysis_sequencing}
				<div style="clear: both"></div>
			</div>
			<div class="form-row">
				<label>Notes (Prophecy-specific)</label>
				${prophecy.notes}
				<div style="clear: both"></div>
			</div>
		%endif
	</div>
</div>
<p/>
