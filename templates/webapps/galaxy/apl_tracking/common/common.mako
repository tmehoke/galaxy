<!-- Can I destroy this file? Are these remaining functions and methods worth it? Do I want to add any more common methods? -->

<%namespace file="/message.mako" import="render_msg" />

<%def name="javascripts()">
   ${self.common_javascripts()}
</%def>


<%def name="common_javascripts()">
    <script type="text/javascript">
        function showContent(vThis)
        {
            // http://www.javascriptjunkie.com
            // alert(vSibling.className + " " + vDef_Key);
            vParent = vThis.parentNode;
            vSibling = vParent.nextSibling;
            while (vSibling.nodeType==3) { 
                // Fix for Mozilla/FireFox Empty Space becomes a TextNode or Something
                vSibling = vSibling.nextSibling;
            };
            if(vSibling.style.display == "none")
            {
                vThis.src="/static/images/silk/resultset_bottom.png";
                vThis.alt = "Hide";
                vSibling.style.display = "block";
            } else {
                vSibling.style.display = "none";
                vThis.src="/static/images/silk/resultset_next.png";
                vThis.alt = "Show";
            }
            return;
        }
        $(document).ready(function(){
            //hide the all of the element with class msg_body
            $(".msg_body").hide();
            //toggle the component with class msg_body
            $(".msg_head").click(function(){
                $(this).next(".msg_body").slideToggle(0);
            });
        });

        function checkAllFields()
        {
            var chkAll = document.getElementById('checkAll');
            var checks = document.getElementsByTagName('input');
            var boxLength = checks.length;
            var allChecked = false;
            var totalChecked = 0;
            if ( chkAll.checked == true )
            {
                for ( i=0; i < boxLength; i++ )
                {
                    if ( checks[i].name.indexOf( 'select_sample_' ) != -1)
                    {
                       checks[i].checked = true;
                    }
                }
            }
            else
            {
                for ( i=0; i < boxLength; i++ )
                {
                    if ( checks[i].name.indexOf( 'select_sample_' ) != -1)
                    {
                       checks[i].checked = false
                    }
                }
            }
        }
	</script>
</%def>


<!-- What does this do? Do I need to get rid of it? -->
<%def name="transfer_status_updater()">
    <%
        can_update = False
        if query.count():
            # Get the first sample dataset to get to the parent sample
            sample_dataset = query[0]
            sample = sample_dataset.sample
            is_complete = sample.request.is_complete
            is_submitted = sample.request.is_submitted
            can_update = is_complete or is_submitted and sample.untransferred_dataset_files
    %>
    %if can_update:
        <script type="text/javascript">
            // Sample dataset transfer status updater
            dataset_transfer_status_updater( {${ ",".join( [ '"%s" : "%s"' % ( trans.security.encode_id( sd.id ), sd.status ) for sd in query ] ) }});
        </script>
    %endif
</%def>

