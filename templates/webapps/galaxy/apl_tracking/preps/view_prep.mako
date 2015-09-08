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
		sample = trans.sa_session.query(trans.model.APLSample).get(prep.sample_id)
		can_delete = is_admin and not sample.deleted
		can_undelete = is_admin and sample.deleted
   except:
		sample = None
		can_delete = False
		can_undelete = False
%>

<br/><br/>

<ul class="manage-table-actions">
	<li><a class="action-button" id="prep-${prep.id}-popup" class="menubutton">Prep Actions</a></li>
	<div popupmenu="prep-${prep.id}-popup">
		%if can_delete and prep != None:
			<a class="action-button" href="${h.url_for(controller='apl_tracking_common', action='delete_prep', cntrller=cntrller, id=trans.security.encode_id(prep.id))}">Delete this prep</a>
		%endif
		%if can_undelete and prep != None:
			<a class="action-button" href="${h.url_for( controller='apl_tracking_common', action='undelete_prep', cntrller=cntrller, id=trans.security.encode_id(prep.id))}">Undelete this prep</a>
		%endif
		%if prep != None:
			<a class="action-button" href="${h.url_for(controller='apl_tracking_common', action='edit_prep_info', cntrller=cntrller, id=trans.security.encode_id(prep.id))}">Edit prep information</a>
		%endif
		<a class="action-button" href="${h.url_for(controller='apl_tracking_common', action='edit_prep_info', cntrller=cntrller, id=trans.security.encode_id(prep.id))}">Edit prep information</a>
	</div>
</ul>

<div class="toolForm">
	<div class="toolFormTitle">Prep ${"APL" + "0"*(9 - len(str(prep.id))) + str(prep.id)}</div>
	<div class="toolFormBody">
		<div class="form-row">
			<label>Prep ID:</label>
			${"APL" + "0"*(9 - len(str(prep.id))) + str(prep.id)}
			<div style="clear: both"></div>
		</div>
		<div class="form-row">
			<label>Date Prepared:</label>
			${prep.prep_date}
			<div style="clear: both"></div>
		</div>
		<div class="form-row">
			<label>User:</label>
			${trans.sa_session.query(trans.model.User).get(prep.user_id).username}
			<div style="clear: both"></div>
		</div>
		<div class="form-row">
			<label>Notes (Prep-specific):</label>
			${prep.notes}
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
				<label>Project:</label>
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
			The regular sample information is unavailable for some reason. Please check this prep's sample_id value.
		%endif
	</div>
</div>
<p/>
