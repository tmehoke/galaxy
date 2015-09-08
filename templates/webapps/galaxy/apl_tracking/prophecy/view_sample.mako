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

   try:
		sample = trans.sa_session.query(trans.model.APLSample).get(prophecy.sample_id)
		can_delete = is_admin and not sample.deleted
		can_undelete = is_admin and sample.deleted
   except:
		sample = None
		can_delete = False
		can_undelete = False
%>

<br/><br/>

<ul class="manage-table-actions">
	<li><a class="action-button" id="sample-${prophecy.id}-popup" class="menubutton">Sample Actions</a></li>
	<div popupmenu="sample-${sample.id}-popup">
		%if can_delete and sample != None:
			<a class="action-button" href="${h.url_for(controller='apl_tracking_common', action='delete_sample', cntrller=cntrller, id=trans.security.encode_id(sample.id))}">Delete this sample</a>
		%endif
		%if can_undelete and sample != None:
			<a class="action-button" href="${h.url_for( controller='apl_tracking_common', action='undelete_sample', cntrller=cntrller, id=trans.security.encode_id(sample.id))}">Undelete this sample</a>
		%endif
		%if sample != None:
			<a class="action-button" href="${h.url_for(controller='apl_tracking_common', action='edit_sample_info', cntrller=cntrller, id=trans.security.encode_id(sample.id))}">Edit sample information</a>
		%endif
		<a class="action-button" href="${h.url_for(controller='apl_tracking_common', action='edit_prophecy_sample_info', cntrller=cntrller, id=trans.security.encode_id(prophecy.id))}">Edit Prophecy information</a>

	</div>
</ul>

<div class="toolForm">
	<div class="toolFormTitle">Prophecy sample: ${"PRO_" + "0"*(5 - len(str(prophecy.id))) + str(prophecy.id)}</div>
	<div class="toolFormBody">
		<div class="form-row">
			<label>Prophecy ID</label>
			${"PRO_" + "0"*(5 - len(str(prophecy.id))) + str(prophecy.id)}
			<div style="clear: both"></div>
		</div>
		<div class="form-row">
			<label>Associated Sample Information</label>
			${prophecy.associated_sample}
			<div style="clear: both"></div>
		</div>
		%if sample != None:
			<div class="form-row">
				<label>Sample ID:</label>
				<a href="${h.url_for(controller='apl_tracking_common', action='view_sample', cntrller=cntrller, id=trans.security.encode_id(sample.id))}">
					${"SMP" + "0"*(9 - len(str(sample.id))) + str(sample.id)}
				</a>
				<div style="clear: both"></div>
			</div>
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
		%else:
			The regular sample information is unavailable for some reason. Please check this Prophecy sample's sample_id value.
		%endif

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
	</div>
</div>
<p/>
