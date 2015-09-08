<%inherit file="/base.mako"/>
<%namespace file="/message.mako" import="render_msg" />

<%def name="javascripts()">
   ${parent.javascripts()}
   ${h.js("libs/jquery/jquery.autocomplete", "galaxy.autocom_tagging" )}
</%def>

<%def name="stylesheets()">
	${parent.stylesheets()}
	${h.css("autocomplete_tagging")}
</%def>

<br/><br/>
<ul class="manage-table-actions">
	<li><a class="action-button"  href="${h.url_for( controller=cntrller, action='browse_primers' )}">Browse primers</a></li>
</ul>

%if message:
	${render_msg( message, status )}
%endif

<div class="toolForm">
	<div class="toolFormTitle">Create a new primer</div>
	<div class="toolFormBody">
		<form name="create_sample" id="create_primer" action="${h.url_for( controller='apl_tracking_common', action='create_primer', cntrller=cntrller )}" method="post" >
			%for i, field in enumerate( widgets ):
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
				<input type="submit" name="create_primer_button" value="Save"/> 
			</div>
		</form>
	</div>
</div>
