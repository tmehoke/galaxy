<%inherit file="/base.mako"/>
<%namespace file="/message.mako" import="render_msg" />

<%
	is_admin = trans.user_is_admin()
%>

<br/><br/>
<ul class="manage-table-actions">
	<li><a class="action-button" id="primer-${primer.id}-popup" class="menubutton">primer Actions</a></li>
	<div popupmenu="primer-${primer.id}-popup">
		<a class="action-button" href="${h.url_for(controller='apl_tracking_common', action='view_primer', cntrller=cntrller, id=trans.security.encode_id(primer.id))}">Browse this primer</a>
	</div>
</ul>

%if message:
	${render_msg( message, status )}
%endif

<div class="toolForm">
	<div class="toolFormTitle">Edit primer "${"PT_%05d" % primer.id}"</div>
	<div class="toolFormBody">
		<form name="edit_primer_info" id="edit_primer_info" action="${h.url_for(controller='apl_tracking_common', action='edit_primer_info', cntrller=cntrller, id=trans.security.encode_id(primer.id))}" method="post" >
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
				<input type="submit" name="edit_primer_info_button" value="Save"/>
			</div>
		</form>
	</div>
</div>
