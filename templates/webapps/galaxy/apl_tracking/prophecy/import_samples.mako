<%inherit file="/base.mako"/>
<%namespace file="/message.mako" import="render_msg" />
<%namespace file="/apl_tracking/common/common.mako" import="common_javascripts" />

<%def name="stylesheets()">
	${parent.stylesheets()}
	${h.css( "library" )}
</%def>

<%def name="javascripts()">
	${parent.javascripts()}
	${common_javascripts()}
</%def>

<head>
<style>
ul {
	list-style-type:square;
	margin-left:20px;
	padding-left:25px;
}
table {
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
	color:black;
	border:1px solid black;
	white-space:nowrap;
	padding:3px 3px 3px 3px;
}
</style>
</head>


<%
	import datetime
	last_week = datetime.date.today() - datetime.timedelta(days=7)
	next_week = datetime.date.today() + datetime.timedelta(days=7)
	filename = "new_samples-%s.txt" % str(datetime.date.today())
%>

<br/><br/>
<ul class="manage-table-actions">
	<li><a class="action-button"  href="${h.url_for( controller=cntrller, action='browse_prophecies' )}">Browse Prophecy samples</a></li>
</ul>

%if message:
	<br/>
	${render_msg( message, status )}
%endif

<div class="toolForm">
	<div class="toolFormTitle">Import Prophecy samples from text file</div>
	<div class="toolFormBody">
	<form id="import" name="import" action="${h.url_for(controller='apl_tracking_common', action='import_prophecy_samples', cntrller=cntrller)}" enctype="multipart/form-data" method="post" >
		<div class="form-row">
			<h2>
				<a href="/publicshare/samplesheets/import_prophecy_template.txt" download="${filename}">
				Download template file
				</a>
			</h2>
			<div class="toolParamHelp" style="clear: both;">
			<p style="padding-left:5px">
				Open this tab-delimited text file in Excel and fill in the fields for the new samples you want to add.
				<br/>
				When saving, select 'yes' you want to keep the workbook in this format, after you are warned about features that are not compatible wi$
				<br/>
				<br/>
				Then upload the edited file here and click "Review import".
			</p>
			</div>
			<input type="file" name="file_data" />
			<br/>
			<input type="submit" name="import_prophecy_samples_button" value="Review import"/>
			<div class="toolParamHelp" style="clear: both;">
				<br/>
				This import tool creates new Prophecy samples (PRO_ prefix) for every Prophecy sample in the file,
				and also creates new samples (SMP index) that the PRO_ samples are linked to.
				<br/>
				<br/>
				Each line of the input file must have the following fields, separated by tabs:
				<br/>
				<ul>
					<li>Prophecy ID (Notice: this value is ignored - the next available Prophecy ID in the database will be used)
					<li>Associated samples</li>
					<li>Sample Name</li>
					<li>Lab</li>
					<li>RG Transfected</li>
					<li>RG Amplification</li>
					<li>Bulk Experiment</li>
					<li>Droplet Experiment</li>
					<li>TCID50 Analysis</li>
					<li>qPCR Analysis</li>
					<li>RNA Isolation</li>
					<li>Sequencing</li>
					<li>Notes (optional)</li>
				</ul>
				<br/>
				<br/>
				These values will be color-coded on the <a href="http://redd-biosciences-ms1/wiki/doku.php?id=prophecy_worksheet">wiki</a>
				according to the following scheme:
				<br/>
				<br/>
				<table>
					<thead>
						<th>Description</th>
						<th>Text</th>
						<th>Displayed as</th>
					</thead>
				<tr>
					<td>completed text</td>
					<td>completed</td>
					<td style="background-color:#00FF00">completed</td>
				</tr>
				<tr>
					<td>completed date</td>
					<td>${last_week}</td>
					<td style="background-color:#00FF00">${last_week}</td>
				</tr>
				<tr>
					<td>scheduled text</td>
					<td>tbd</td>
					<td style="background-color:#FF0000">tbd</td>
				</tr>
				<tr>
					<td>scheduled date</td>
					<td>s${next_week}</td>
					<td style="background-color:#FF0000">${next_week}</td>
				</tr>
				<tr>
					<td>not applicable</td>
					<td>n/a</td>
					<td style="background-color:#C0C0C0">n/a</td>
				</tr>
				</table>
			</div>
		</div>
	</form>
</div>
</div>
