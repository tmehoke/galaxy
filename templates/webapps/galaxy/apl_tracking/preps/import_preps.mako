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
	filename = "new_preps-%s.txt" % str(datetime.date.today())
%>

<br/><br/>
<ul class="manage-table-actions">
	<li><a class="action-button"  href="${h.url_for( controller=cntrller, action='browse_preps' )}">Browse preps</a></li>
</ul>

%if message:
	<br/>
	${render_msg( message, status )}
%endif

<div class="toolForm">
	<div class="toolFormTitle">Import preps from text file</div>
	<div class="toolFormBody">
	<form id="import" name="import" action="${h.url_for(controller='apl_tracking_common', action='import_preps', cntrller=cntrller)}" enctype="multipart/form-data" method="post" >
		<div class="form-row">
			<h2>
				<a href="/publicshare/samplesheets/import_prep_template.txt" download="${filename}">
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
			<input type="submit" name="import_preps_button" value="Review import"/>
			<div class="toolParamHelp" style="clear: both;">
				<br/>
				Each line of the input file must have the following fields, separated by tabs:
				<br/>
				<ul>
					<li>Sample ID (SMP prefix)</li>
					<li>Date prepared (defaults to today's date if left blank)</li>
					<li>Notes (optional)</li>
				</ul>
			</div>
		</div>
		<h2 style="padding-left:10px">OR</h2>
		<p style="padding-left:10px">You can use these input fields if all of your preps have the same prep date and the same notes</p>
		<div class="form-row">
			%for i, field in enumerate(widgets):
				<div class="form-row">
					<label>${field['label']}</label>
					${field['widget'].get_html()}
					<div class="toolParamHelp" style="clear: both;">
						${field['helptext']}
					</div>
					<div style="clear: both"></div>
				</div>
			%endfor
			<div class="form-row">
				<input type="submit" name="create_prep_group_button" value="Review"/>
			</div>
		</div>
	</form>
</div>
</div>
