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
</style>
</head>

<%
	import datetime
	filename = "new_samples-%s.txt" % str(datetime.date.today())
%>

<br/><br/>
<ul class="manage-table-actions">
    <li><a class="action-button"  href="${h.url_for( controller=cntrller, action='browse_samples' )}">Browse samples</a></li>
</ul>

%if message:
	<br/>
	${render_msg( message, status )}
%endif

<div class="toolForm">
	<div class="toolFormTitle">Import samples from text file</div>
	<div class="toolFormBody">
	<form id="import" name="import" action="${h.url_for(controller='apl_tracking_common', action='import_samples', cntrller=cntrller)}" enctype="multipart/form-data" method="post" >
		<div class="form-row">
			<h2>
				<a href="/publicshare/samplesheets/import_sample_template.txt" download="${filename}">
				Download template file
				</a>
			</h2>
			<div class="toolParamHelp" style="clear: both;">
			<p style="padding-left:5px">
				Open this tab-delimited text file in Excel and fill in the fields for the new samples you want to add.
				<br/>
				When saving, select 'yes' you want to keep the workbook in this format, after you are warned about features that are not compatible with Text (Tab-delimited).
				<br/>
				<br/>
				Then upload the edited file here and click "Review import".
			</p>
			</div>
			<input type="file" name="file_data" />
			<br/>
			<input type="submit" name="import_samples_button" value="Review import"/>
			<div class="toolParamHelp" style="clear: both;">
				<br/>
				<br/>
				<p>Each line of the input file must have the following fields, separated by tabs:</p>
				<br/>
				<ul>
					<li>Parent ID (an integer that references the SMP ID of the parent)</li>
					<li>Sample Name</li>
					<li>Species</li>
					<li>Host species</li>
					<li>Sample Type (e.g. drops, bulk, mouse)</li>
					<li>Created date (defaults to today's date if left blank)</li>
					<li>Lab</li>
					<li>Project (e.g. prophecy)</li>
					<li>Experiment type (e.g. evolution, library, ySTR)
					<li>Notes (optional)</li>
				</ul>
			</div>
		</div>
	</form>
</div>
</div>
