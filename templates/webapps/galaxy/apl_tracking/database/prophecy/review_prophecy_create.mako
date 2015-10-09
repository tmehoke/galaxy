<%inherit file="/base.mako"/>
<%namespace file="/message.mako" import="render_msg" />

<%
	import re
%>

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
	<li><a class="action-button"  href="${h.url_for( controller=cntrller, action='browse_prophecies' )}">Browse Prophecy samples</a></li>
</ul>

%if message:
	${render_msg( message, status )}
%endif

## pull out parameters
<%
	import datetime
	last_sample = parameters[0]['value']
	last_prophecy = parameters[1]['value']
	prophecies = parameters[2]['value']
%>

<div class="toolForm">
	<div class="toolFormTitle">Review import - save changes?</div>
	<div class="toolFormBody">
		<form name="review_prophecy_create" id="review_prophecy_create" action="${h.url_for(controller='apl_tracking_common', action='review_prophecy_create', cntrller=cntrller)}" method="post" >

			## pull out values in HiddenFields so the data can be passed through if 'Submit' is pressed
			%for i, field in enumerate(parameters):
				${field['widget'].get_html()}
			%endfor

			## Draw the table containing all of the samples to be created
			<h2 style="padding-left:2%">Samples to be created</h2>
			<table class="review">
			<thead>
			%for attr in ['Sample ID', 'Prophecy ID', 'Name', 'Species', 'Date Created', 'User', 'Lab', 'Project']:
				<th>${attr}</th>
			%endfor
			</thead>
			<%
				sample_id = last_sample
				prophecy_id = last_prophecy
			%>
			%for i, prophecy in enumerate(prophecies):
				<%
					sample_id += 1
					prophecy_id += 1
				%>
				<tr>
				## display sample ID
				<td>${"SMP%09d" % int(sample_id)}</td>
				<td>${"PRO_%05d" % int(prophecy_id)}</td>
				<td>
				%try:
					${prophecy[0].decode('utf-8')}
				%except:
					${prophecy[0]}
				%endtry
				</td>
				<td>
				%try:
					${prophecy[1].decode('utf-8')}
				%except:
					${prophecy[1]}
				%endtry
				</td>
				<td>${str(datetime.date.today())}</td>
				<td>${trans.user.username}</td>
				<td>APL</td>
				<td>prophecy</td>
				</tr>
			%endfor
			</table>
			<br/>
			<br/>
			<div class="form-row">
				<input type="submit" name="cancel_prophecy_create_button" value="Cancel changes"/>
				<input type="submit" name="review_prophecy_create_button" value="Submit"/>
			</div>
		</form>
	</div>
</div>
