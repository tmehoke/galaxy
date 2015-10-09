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
		<form name="review_prophecy_import" id="review_prophecy_import" action="${h.url_for(controller='apl_tracking_common', action='review_prophecy_import', cntrller=cntrller)}" method="post" >

			## pull out values in HiddenFields so the data can be passed through if 'Submit' is pressed
			%for i, field in enumerate(parameters):
				${field['widget'].get_html()}
			%endfor

			## Draw the table containing all of the samples to be created
			<h2 style="padding-left:2%">Samples to be created</h2>
			<table class="review">
			<thead>
			%for attr in ['Sample ID', 'Parent ID', 'Name', 'Species', 'Sample Type', 'Date Created', 'User', 'Lab', 'Project', 'Experiment Type', 'Notes']:
				<th>${attr}</th>
			%endfor
			</thead>
			<%
				sample_id = last_sample
				prophecy_id = last_prophecy
			%>
			%for i, prophecy in enumerate(prophecies):
				<% sample_id += 1 %>
				<tr>
				## display sample ID
				<td>${"SMP%09d" % int(sample_id)}</td>
				<td></td>
				<td>
				%try:
					${prophecy[1].decode('utf-8')}
				%except:
					${prophecy[1]}
				%endtry
				</td>
				<td></td>
				<td></td>
				<td>${str(datetime.date.today())}</td>
				<td>${trans.user.username}</td>
				<td>
				%try:
					${prophecy[2].decode('utf-8')}
				%except:
					${prophecy[2]}
				%endtry
				</td>
				<td>prophecy</td>
				<td></td>
				<td></td>
				</tr>
			%endfor
			</table>
			<br/>

			## Draw the table containing all of the Prophecy samples to be created
			<h2 style="padding-left:2%">Prophecy samples to be created</h2>
			<table class="review">
			<thead>
			%for attr in ['Prophecy ID', 'Sample ID', 'Associated Sample', 'RG Transfection', 'RG Amplification', 'Bulk Experiment', 'Droplet Experiment', 'TCID50 Analysis', 'qPCR Analysis', 'RNA Isolation', 'Sequencing']:
				<th>${attr}</th>
			%endfor
			</thead>
			<%
				sample_id = last_sample
				prophecy_id = last_prophecy
			%>
			%for i, prophecy in enumerate(prophecies):
				<% sample_id += 1 %>
				<% prophecy_id += 1 %>
				<tr>
				## display sample ID
				<td>${"PRO_%05d" % int(prophecy_id)}</td>
				<td>${"SMP%09d" % int(sample_id)}</td>
				%for j, attr in enumerate(prophecy):
					%if j != 1 and j != 2 and j != 11:
						%if attr is None:
							<td></td>
						%elif attr == "completed" or re.match('^[0-9]{4}-[0-9]{2}-[0-9]{2}$', attr):
							<td style="background-color:#00FF00">${attr}</td>
						%elif attr == "tbd":
							<td style="background-color:#FF0000">${attr}</td>
						%elif re.match('^s[0-9]{4}-[0-9]{2}-[0-9]{2}$', attr):
							<td style="background-color:#FF0000">${attr[1:]}</td>
						%elif attr == "n/a":
							<td style="background-color:#C0C0C0">${attr}</td>
						%else:
							<td>${attr}</td>
						%endif
					%endif
				%endfor
				</tr>
			%endfor
			</table>
			<br/>
			<div class="form-row">
				<input type="submit" name="cancel_prophecy_import_button" value="Cancel changes"/>
				<input type="submit" name="review_prophecy_import_button" value="Submit"/>
			</div>
		</form>
	</div>
</div>
