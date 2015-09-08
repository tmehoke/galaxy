<%inherit file="/base.mako"/>
<%namespace file="/message.mako" import="render_msg" />

<head>
<style>
table {
	width:96%;
	margin-left:2%;
	margin-right:2%;
	border-collapse:collapse;
	border:1px solid black;
}
th {
	border:1px solid black;
	vertical-align:bottom;
	border-bottom:2px;
	background-color:gray;
	color:white;
	white-space:nowrap;
	padding-top:5px;
	padding-bottom:4px;
}
td {
	border:1px solid black;
	white-space:nowrap;
	padding:3px 3px 3px 3px;
}
</style>
</head>

<%
	is_admin = trans.user_is_admin()
%>

<br/><br/>
<ul class="manage-table-actions">
	<li><a class="action-button"  href="${h.url_for( controller=cntrller, action='browse_preps' )}">Browse preps</a></li>
</ul>

%if message:
	${render_msg( message, status )}
%endif

## pull out parameters
<%
%>

<div class="toolForm">
	<div class="toolFormTitle">Create SampleSheet</div>
	<div class="toolFormBody">
		<form name="review_samplesheet" id="review_samplesheet" action="${h.url_for(controller='apl_tracking_common', action='review_samplesheet', cntrller=cntrller)}" method="post" >

			%for i, field in enumerate( widgets ):
				<div class="form-row">
					<label>${field['label']}</label>
					${field['widget'].get_html()}
##					<div class="toolParamHelp" style="clear: both;">
##						${field['helptext']}
##					</div>
					<div style="clear: both"></div>
				</div>
			%endfor

			<div class="form-row">
				<input type="submit" name="cancel_samplesheet_button" value="Cancel"/>
				<input type="submit" name="submit_samplesheet_button" value="Create sample sheet"/>
			</div>
		</form>
	</div>
</div>
