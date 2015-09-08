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
	filename = "new_prophecy_samples-%s.txt" % str(datetime.date.today())
%>

<br/><br/>
<ul class="manage-table-actions">
	<li><a class="action-button" href="${h.url_for( controller=cntrller, action='browse_prophecies' )}">Browse Prophecy samples</a></li>
</ul>

%if message:
	<br/>
	${render_msg( message, status )}
%endif

<div class="toolForm">
	<div class="toolFormTitle">Create Prophecy samples</div>
	<div class="toolFormBody">
	<form id="create_prophecy_group" name="create_prophecy_group" action="${h.url_for(controller='apl_tracking_common', action='create_prophecy_samples', cntrller=cntrller)}" enctype="multipart/form-data" method="post" >
		<div class="form-row">
			<h2>
				<a href="/publicshare/samplesheets/create_prophecy_template.txt" download="${filename}">
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
				Then upload the edited file here and click "Review sample creation".
			</p>
			</div>
			<input type="file" name="file_data" />
			<br/>
			<input type="submit" name="create_prophecy_samples_button" value="Review sample creation"/>
			<div class="toolParamHelp" style="clear: both;">
				<br/>
				This import tool creates new Prophecy samples (PRO_ prefix) for every Prophecy sample in the file,
				and also creates new samples (SMP index) that the PRO_ samples are linked to.
				<br/>
				<br/>
				Each line of the input file must have the following fields, separated by tabs:
				<br/>
				<ul>
					<li>Sample Name</li>
					<li>Species (optional)</li>
				</ul>
				<br/>
			</div>
		</div>
	</form>
</div>
</div>
