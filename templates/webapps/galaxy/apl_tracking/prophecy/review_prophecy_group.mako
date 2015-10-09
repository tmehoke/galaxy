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
	<li><a class="action-button"  href="${h.url_for( controller=cntrller, action='browse_prophecies' )}">Browse Prophecy samples</a></li>
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
	<div class="toolFormTitle">Review edits - save changes?</div>
	<div class="toolFormBody">
		<form name="review_prophecy_group" id="review_prophecy_group" action="${h.url_for(controller='apl_tracking_common', action='review_prophecy_group', cntrller=cntrller)}" method="post" >

			## make HiddenFields so the data can be passed through if 'Submit' is pressed
			<input type="hidden" name="sample_ids" value="${str(sample_ids)}">
			<input type="hidden" name="attribute" value="${str(attribute)}">
			## if new_value contains unicode text, the get_html() method fails
			<input type="hidden" name="new_value" value="${new_value}">

			<%
				attributes = dict(rg_transfected='RG Transfection', rg_amplification='RG Amplification', expt_bulk='Bulk Experiment',\
								expt_droplet='Droplet Experiment', analysis_tcid50='TCID50 Analysis', analysis_qpcr='qPCR Analysis',\
								rna_isolation='RNA Isolation', analysis_sequencing='Sequencing', notes='Notes')
			%>

			## Draw the old table
			<h2 style="padding-left:2%">Existing table</h2>
			<table class="review">
			<thead>
			%for attr in ['Prophecy ID', 'Sample ID', 'Associated Sample', 'Name', 'Lab']:
				<th>${attr}</th>
			%endfor
			%if attribute != 'associated_sample':
				<th>${attributes[attribute]}</th>
			%endif
			</thead>
			%for i, id in enumerate(sample_ids):
				<%
					prophecy = trans.sa_session.query(trans.model.APLProphecySample).get(id)
					sample = trans.sa_session.query(trans.model.APLSample).get(prophecy.sample_id)
				%>
				<tr>
				<td>${"PRO_%05d" % id}</td>
				<td>${"SMP%09d" % prophecy.sample_id}</td>
				%if attribute == 'associated_sample':
					<td style="background-color:#FF9999">${getattr(prophecy, attribute)}</td>
				%else:
					<td>${prophecy.associated_sample}</td>
				%endif
				<td style="white-space:normal">${sample.name}</td>
				<td>${sample.lab}</td>
				%if attribute == 'notes':
					<td style="white-space:normal;background-color:#FF9999">${getattr(prophecy, attribute)}</td>
				%elif attribute != 'associated_sample':
					<td style="background-color:#FF9999">${getattr(prophecy, attribute)}</td>
				%endif
				</tr>
			%endfor
			</table>

			## Draw the new table
			<h2 style="padding-left:2%">Updated table</h2>
			<table class="review">
			<thead>
			%for attr in ['Prophecy ID', 'Sample ID', 'Associated Sample', 'Name', 'Lab']:
				<th>${attr}</th>
			%endfor
			%if attribute != 'associated_sample':
				<th>${attributes[attribute]}</th>
			%endif
			</thead>
			%for i, id in enumerate(sample_ids):
				<%
					prophecy = trans.sa_session.query(trans.model.APLProphecySample).get(id)
					sample = trans.sa_session.query(trans.model.APLSample).get(prophecy.sample_id)
				%>
				<tr>
				<td>${"PRO_%05d" % id}</td>
				<td>${"SMP%09d" % prophecy.sample_id}</td>
				%if attribute == 'associated_sample':
					<td style="background-color:#99FF99">${new_value}</td>
				%else:
					<td>${prophecy.associated_sample}</td>
				%endif
				<td style="white-space:normal">${sample.name}</td>
				<td>${sample.lab}</td>
				%if attribute == 'notes':
					<td style="white-space:normal;background-color:#99FF99">${new_value}</td>
				%elif attribute != 'associated_sample':
					<td style="background-color:#99FF99">${new_value}</td>
				%endif
				</tr>
			%endfor
			</table>
			<br/>

			<div class="form-row">
				<input type="submit" name="cancel_prophecy_group_button" value="Cancel changes"/>
				<input type="submit" name="review_prophecy_group_button" value="Submit"/>
			</div>
		</form>
	</div>
</div>
