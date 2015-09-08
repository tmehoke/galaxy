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
	prep_id = parameters[0]['value']
	preps = parameters[1]['value']
%>

<div class="toolForm">
	<div class="toolFormTitle">Review import - save changes?</div>
	<div class="toolFormBody">
		<form name="review_prep_import" id="review_prep_import" action="${h.url_for(controller='apl_tracking_common', action='review_prep_import', cntrller=cntrller)}" method="post" >

			## pull out values in HiddenFields so the data can be passed through if 'Submit' is pressed
			%for i, field in enumerate(parameters):
				${field['widget'].get_html()}
			%endfor

			## Draw the table containing all of the import data
			<h2 style="padding-left:2%">Preps to be created</h2>
			<table class="review">
			<thead>
			%for attr in ['Prep ID', 'Sample ID', 'Name', 'Lab', 'Project', 'Prep Date', 'User', 'Notes']:
				<th>${attr}</th>
			%endfor
			</thead>
			%for i, prep in enumerate(preps):
				<%
					prep_id += 1
					sample = trans.sa_session.query(trans.model.APLSample).get(prep[0])
				%>
				<tr>
					## display prep ID
					<td>${"APL%09d" % int(prep_id)}</td>
					## display sample ID
					<td>${"SMP%09d" % sample.id}</td>
					<td>${sample.name}</td>
					<td>${sample.lab}</td>
					<td>${sample.project}</td>
					## display prep date
					<td>${prep[1]}</td>
					## display username
					<td>${trans.user.username}</td>
					## display notes
					<td>
					%try:
						${prep[2].decode('utf-8')}
					%except:
						${prep[2]}
					%endtry
					</td>
				</tr>
			%endfor
			</table>
			<br/>

			<div class="form-row">
				<input type="submit" name="cancel_prep_import_button" value="Cancel changes"/>
				<input type="submit" name="review_prep_import_button" value="Submit"/>
				<input type="submit" name="create_samplesheet_button" value="Submit & make sample sheet"/>
			</div>
		</form>
	</div>
</div>
