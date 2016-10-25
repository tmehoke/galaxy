<%inherit file="/base.mako"/>
<%namespace file="/message.mako" import="render_msg" />

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

<div class="toolForm">
    <div class="toolFormTitle">Edit sample group</div>
    <div class="toolFormBody">
        <form name="edit_sample_group" id="edit_sample_group" action="${h.url_for(controller='apl_tracking_common', action='edit_sample_group', cntrller=cntrller)}" method="post" >
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
                <input type="submit" name="edit_sample_group_button" value="Review"/>
            </div>
        </form>
    </div>
</div>