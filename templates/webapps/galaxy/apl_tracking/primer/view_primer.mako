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
%>

<br/><br/>

<ul class="manage-table-actions">
	<li><a class="action-button" id="primer-${primer.id}-popup" class="menubutton">primer Actions</a></li>
	<div popupmenu="primer-${primer.id}-popup">
		<a class="action-button" href="${h.url_for(controller='apl_tracking_common', action='edit_primer_info', cntrller=cntrller, id=trans.security.encode_id(primer.id))}">Edit primer information</a>
	</div>
</ul>

<div class="toolForm">
	<div class="toolFormTitle">primer ${"PT_%05d" % primer.id}</div>
	<div class="toolFormBody">
		<div class="form-row">
			<label>primer ID:</label>
			${"PT_%05d" % primer.id}
			<div style="clear: both"></div>
		</div>
		<div class="form-row">
			<label>Design date:</label>
			${primer.design_date}
			<div style="clear: both"></div>
		</div>
		<div class="form-row">
			<label>User:</label>
			${trans.sa_session.query(trans.model.User).get(primer.user_id).username}
			<div style="clear: both"></div>
		</div>
		<div class="form-row">
			<label>Description:</label>
			${primer.description}
			<div style="clear: both"></div>
		</div>
		<div class="form-row">
			<label>Sequence:</label>
			${primer.sequence}
			<div style="clear: both"></div>
		</div>
		<div class="form-row">
			<label>Species:</label>
			${trans.sa_session.query(trans.model.APLOrganism).get(primer.species).name}
			<div style="clear: both"></div>
		</div>
		<div class="form-row">
			<label>Scale:</label>
			${primer.scale}
			<div style="clear: both"></div>
		</div>
		<div class="form-row">
			<label>Purification:</label>
			${primer.purification}
			<div style="clear: both"></div>
		</div>
		<div class="form-row">
			<label>Notes:</label>
			${primer.notes}
			<div style="clear: both"></div>
		</div>
	</div>
</div>
<p/>
