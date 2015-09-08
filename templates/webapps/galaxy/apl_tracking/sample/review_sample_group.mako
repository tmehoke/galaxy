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
	sample_ids = parameters[0]['value']
	attribute = parameters[1]['value']
	new_value = parameters[2]['value']
	try:
		new_value = new_value.decode('utf-8')
	except:
		pass
%>

<div class="toolForm">
	<div class="toolFormTitle">Review edit - save changes?</div>
	<div class="toolFormBody">
		<form name="review_sample_group" id="review_sample_group" action="${h.url_for(controller='apl_tracking_common', action='review_sample_group', cntrller=cntrller)}" method="post" >

			## make HiddenFields so the data can be passed through if 'Submit' is pressed
			<input type="hidden" name="sample_ids" value="${str(sample_ids)}">
			<input type="hidden" name="attribute" value="${str(attribute)}">
			## if new_value contains unicode text, the get_html() method fails
			<input type="hidden" name="new_value" value="${new_value}">

			## Draw the old table
			<h2 style="padding-left:2%">Existing table</h2>
			<table class="review">
			<thead>
			%for attr in ['Sample ID', 'Parent ID', 'Name', 'Species', 'Host', 'Sample Type', 'Date Created', 'User', 'Lab', 'Project', 'Experiment Type', 'Notes']:
				<th>${attr}</th>
			%endfor
			</thead>
			%for i, id in enumerate(sample_ids):
				<%
					sample = trans.sa_session.query(trans.model.APLSample).get(id)
				%>
				<tr>
				<td>${"SMP%09d" % id}</td>
				%for attr in ['parent_id', 'name', 'species', 'host', 'sample_type', 'created', 'user_id', 'lab', 'project', 'experiment_type', 'notes']:
					%if attr == attribute:
						<td style="background-color:#FF9999">
							%if attr == 'user_id':
								${trans.sa_session.query(trans.model.User).get(sample.user_id).username}
							%else:
								${getattr(sample, attr)}
							%endif
						</td>
					%elif attr == 'name' or attr == 'notes':
						<td style="white-space:normal">${getattr(sample, attr)}</td>
					%else:
						<td>
							%if attr == 'user_id':
								${trans.sa_session.query(trans.model.User).get(sample.user_id).username}
							%else:
								${getattr(sample, attr)}
							%endif
						</td>
					%endif
				%endfor
				</tr>
			%endfor
			</table>

			## Draw the new table
			<h2 style="padding-left:2%">Updated table</h2>
			<table class="review">
			<thead>
			%for attr in ['Sample ID', 'Parent ID', 'Name', 'Species', 'Host', 'Sample Type', 'Date Created', 'User', 'Lab', 'Project', 'Experiment Type', 'Notes']:
				<th>${attr}</th>
			%endfor
			</thead>
			%for i, id in enumerate(sample_ids):
				<%
					sample = trans.sa_session.query(trans.model.APLSample).get(id)
				%>
				<tr>
				<td>${"SMP%09d" % id}</td>
				%for attr in ['parent_id', 'name', 'species', 'host', 'sample_type', 'created', 'user_id', 'lab', 'project', 'experiment_type', 'notes']:
					%if attr == attribute:
						<td style="background-color:#99FF99">${new_value}</td>
					%elif attr == 'name' or attr == 'notes':
						<td style="white-space:normal">${getattr(sample, attr)}</td>
					%else:
						<td>
							%if attr == 'user_id':
								${trans.sa_session.query(trans.model.User).get(sample.user_id).username}
							%else:
								${getattr(sample, attr)}
							%endif
						</td>
					%endif
				%endfor
				</tr>
			%endfor
			</table>
			<br/>

			<div class="form-row">
				<input type="submit" name="cancel_sample_group_button" value="Cancel changes"/>
				<input type="submit" name="review_sample_group_button" value="Submit"/>
			</div>
		</form>
	</div>
</div>
