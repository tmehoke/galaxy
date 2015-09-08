<%inherit file="/base.mako"/>
<%namespace file="/message.mako" import="render_msg" />

<%
	is_admin = trans.user_is_admin()
%>

<br/><br/>
<ul class="manage-table-actions">
	<li><a class="action-button" id="prep-${prep.id}-popup" class="menubutton">Prep Actions</a></li>
	<div popupmenu="prep-${prep.id}-popup">
		<a class="action-button" href="${h.url_for(controller='apl_tracking_common', action='view_prep', cntrller=cntrller, id=trans.security.encode_id(prep.id))}">Browse this prep</a>
	</div>
</ul>

%if message:
	${render_msg( message, status )}
%endif

<div class="toolForm">
	<div class="toolFormTitle">Edit Prep "${prep.id}"</div>
	<div class="toolFormBody">
		<form name="edit_prep_info" id="edit_prep_info" action="${h.url_for(controller='apl_tracking_common', action='edit_prep_info', cntrller=cntrller, id=trans.security.encode_id(prep.id))}" method="post" >
			%for i, field in enumerate(widgets):
				<div class="form-row">
					<label>${field['label']}</label>
					%if field['label'] == "Notes":
						<textarea name="notes" rows="10" cols="30">${field['value']}</textarea>
					%else:
						${field['widget'].get_html()}
					%endif
					<div class="toolParamHelp" style="clear: both;">
						${field['helptext']}
					</div>
					<div style="clear: both"></div>
				</div>
			%endfor
			<div class="form-row">
				<input type="submit" name="edit_prep_info_button" value="Save"/>
			</div>
		</form>
	</div>
</div>
