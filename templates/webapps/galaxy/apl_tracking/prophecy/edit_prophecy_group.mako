<%inherit file="/base.mako"/>
<%namespace file="/message.mako" import="render_msg" />

<%
	is_admin = trans.user_is_admin()
%>

<head>
<style>
table {
    border-collapse:collapse;
    border:1px solid black;
	margin-left:10px;
	margin-bottom:10px;
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


<br/><br/>
<ul class="manage-table-actions">
	<li><a class="action-button"  href="${h.url_for( controller=cntrller, action='browse_prophecies' )}">Browse Prophecy samples</a></li>
</ul>

%if message:
	${render_msg( message, status )}
%endif

<div class="toolForm">
	<div class="toolFormTitle">Edit Prophecy sample group</div>
	<div class="toolFormBody">
		<form name="edit_prophecy_group" id="edit_prophecy_group" action="${h.url_for(controller='apl_tracking_common', action='edit_prophecy_group', cntrller=cntrller)}" method="post" >
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
				<input type="submit" name="edit_prophecy_group_button" value="Review"/>
			</div>
		</form>
		<br/>
		<p style="padding:10px">
		These values will be color-coded on the <a href="http://redd-biosciences-ms1/wiki/doku.php?id=prophecy_worksheet">wiki</a>
		according to the following scheme:
		</p>
		<table>
			<thead>
				<th>Description</th>
				<th>Example</th>
				<th>Displayed as</th>
			</thead>
		<tr>
			<td>completed text</td>
			<td>completed</td>
			<td style="background-color:#00FF00">completed</td>
		</tr>
		<tr>
			<td>completed date</td>
			<td>2014-07-29</td>
			<td style="background-color:#00FF00">2014-07-29</td>
		</tr>
		<tr>
			<td>scheduled text</td>
			<td>tbd</td>
			<td style="background-color:#FF0000">tbd</td>
		</tr>
		<tr>
			<td>scheduled date</td>
			<td>s2014-07-29</td>
			<td style="background-color:#FF0000">2014-07-29</td>
		</tr>
		<tr>
			<td>not applicable</td>
			<td>n/a</td>
			<td style="background-color:#C0C0C0">n/a</td>
		</tr>
		</table>
	</div>
</div>
