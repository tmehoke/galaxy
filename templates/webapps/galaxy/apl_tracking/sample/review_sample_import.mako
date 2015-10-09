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
    <li><a class="action-button"  href="${h.url_for( controller=cntrller, action='browse_samples' )}">Browse samples</a></li>
</ul>

%if message:
	${render_msg( message, status )}
%endif

## pull out parameters
<%
	sample_id = parameters[0]['value']
	samples = parameters[1]['value']
%>

<div class="toolForm">
	<div class="toolFormTitle">Review import - save changes?</div>
	<div class="toolFormBody">
		<form name="review_sample_import" id="review_sample_import" action="${h.url_for(controller='apl_tracking_common', action='review_sample_import', cntrller=cntrller)}" method="post" >

			## pull out values in HiddenFields so the data can be passed through if 'Submit' is pressed
			%for i, field in enumerate(parameters):
				${field['widget'].get_html()}
			%endfor

			## Draw the table containing all of the import data
			<h2 style="padding-left:2%">Samples to be created</h2>
			<table class="review">
			<thead>
			%for attr in ['Sample ID', 'Parent ID', 'Name', 'Species', 'Host', 'Sample Type', 'Date Created', 'User', 'Lab', 'Project', 'Experiment Type', 'Notes']:
				<th>${attr}</th>
			%endfor
			</thead>
			%for i, sample in enumerate(samples):
				<% sample_id += 1 %>
				<tr>
				## display sample ID
				<td>${"SMP%09d" % int(sample_id)}</td>
				%for j, attr in enumerate(sample):
					<td>
					%if attr is not None:

						## display parent ID
						%if j == 0:
							${"SMP%09d" % int(attr)}

						## display username instead of user ID
						%elif j == 6:
							%try:
								${trans.user.username}
							%except:
								${attr}
							%endtry

						## UTF-8 decode text if necessary
						%else:
							%try:
								${attr.decode('utf-8')}
							%except:
								${attr}
							%endtry
						%endif
					%endif
					</td>
				%endfor
				</tr>
			%endfor
			</table>
			<br/>

			<div class="form-row">
				<input type="submit" name="cancel_sample_import_button" value="Cancel changes"/>
				<input type="submit" name="review_sample_import_button" value="Submit"/>
			</div>
		</form>
	</div>
</div>
