<%inherit file="/base.mako"/>
<%namespace file="/message.mako" import="render_msg" />

<head>
<style>
## from: http://www.sitepoint.com/forums/css.php?sheet=bbcode.css
.bbcode_container {
	margin:20px;
	margin-top:5px;
	display:block;
}

.bbcode_container div.bbcode_code,
.bbcode_container pre.bbcode_code,
.bbcode_container object.bbcode_code {
	margin:0;
	padding:10px;
	border:1px inset;
	text-align:left;
	overflow:scroll;
	direction:ltr;
	background:#f1f1f1 none;
	font-size:12px;
}
</style>
</head>

<%
	is_admin = trans.user_is_admin()
%>

<br/><br/>
<ul class="manage-table-actions">
	<li><a class="action-button"  href="${h.url_for( controller=cntrller, action='browse_preps' )}">Browse preps</a></li>
</ul>

%if message:
	${render_msg( message, status )}
%endif

## pull out parameters
<%
	import re
	download_link = re.sub('/var/www/html', 'http://odin', download_file)
	content = []
	with open(download_file, 'r') as f:
		opened = f.read()
		lines = re.split(r'\r\n', opened)
		for line in lines:
			content.append(line.strip());
	content.pop(-1)
%>

<div class="toolForm">
	<div class="toolFormTitle">Download SampleSheet</div>
	<div class="toolFormBody">
        <form name="download_samplesheet" id="review_samplesheet" action="${h.url_for(controller='apl_tracking_common', action='download_samplesheet', cntrller=cntrller)}" method="post" >

			<h2 style="padding-left:10px">Link to download</h2>
			<a style="padding-left:10px" href="${download_link}" download="SampleSheet.csv">
				Download SampleSheet
			</a>
			<br/>
			<br/>
			<div class="bbcode_container">
				<div>SampleSheet.csv:</div>
				<pre class="bbcode_code" style="height:300px; width:1000px;">
					%for i, line in enumerate(content):
<span>${line}</span>
					%endfor
				</pre>
			</div>

			<div class="form-row">
				<input type="submit" name="return_button" value="Return"/>
			</div>
		</form>
	</div>
</div>
