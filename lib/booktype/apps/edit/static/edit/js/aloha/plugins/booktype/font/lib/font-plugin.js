//BK-796
define(
['aloha', 'aloha/plugin','aloha/ephemera', 'jquery','jquery19', 'ui/ui', 'ui/button' ],
        function(Aloha, Plugin, Ephemera, jQuery, jQuery19, UI, Button ){
                var html_list_fonts = "";
                var GENTICS = window.GENTICS;

                function changeFont(font_name, $editable){
                    console.log('change font');
                        var activeEditable = Aloha.activeEditable;
                        var range = Aloha.Selection.getRangeObject();

                        var selection_start = range.startOffset;
                        var selection_end = range.endOffset;

                        if ((selection_end===0)||(selection_end===undefined)){ // nothing selected
                            console.log('*ERROR* Nothing was selected');
                                return;
                        }

                        // This is range and not editable
                        var editable = range;                                        
                        var element_selected = range.endContainer.data;

                        console.log('ovdje prije ifova');
                        console.log('editable ', $editable);
                        console.log('jesu li jednaki ', range.startContainer == range.endContainer);
                        console.log('startContainer ', range.startContainer);
                        console.log('endContainer ', range.endContainer);
                        console.log('node name na ', range.startContainer.nodeName.toLowerCase());

                        console.log('element_selected ', element_selected);

/*
                        if((selection_start===0)&&(selection_end===jQuery(element_selected).text().length)){
                        if(selection_start === 0) {
                                console.log("change whole css");

                                var node_name_editable = range.commonAncestorContainer.nodeName;
                                var node_attributes_list = range.commonAncestorContainer.attributes;
                                var new_values_node_attributes = "<"+node_name_editable+" ";

                                jQuery.each(node_attributes_list,function(cnt,el){
                                        if(el.name!='style'){
                                                new_values_node_attributes+=el.name+"='"+el.value+"' ";
                                        } else {
                                                new_values_node_attributes+="style='font-family:"+font_name+";"+el.value+"'";
                                        }
                                }); 
                                // adding style if there is no style already added
                                if (new_values_node_attributes.indexOf("style")==-1){
                                    new_values_node_attributes+="style='font-family:"+font_name+"'";
                                }
                                new_values_node_attributes +=">";
                                console.log(new_values_node_attributes);
                                var $span_add = jQuery(new_values_node_attributes).append(element_selected);                          

                                //GENTICS.Utils.Dom.removeRange(range);
                                GENTICS.Utils.Dom.insertIntoDOM($span_add,range, jQuery($editable.obj));

                        } else {
*/                            
                                console.log("insert span");
                                var $span_add = jQuery("<span style='font-family:"+font_name+"'>");

                                GENTICS.Utils.Dom.addMarkup(range, $span_add, false);
                                range.select();
                        //}                                   
                }

                Aloha.bind('aloha-editable-created', function($event, editable) {
                    // inject value to hmtl
                    jQuery(".contentHeader .btn-toolbar .font-dropdown").html(html_list_fonts); 
                    jQuery(".contentHeader .btn-toolbar .font-dropdown a").on('click', function (event) {
                        console.log('-----------------------------------');
                        console.log('CLICKED ON FONT OPTION');
                        console.log('-----------------------------------');
                        console.log('event ', event);
                        var font_selected = jQuery(event.currentTarget).text();
                        console.log('selected font ', font_selected);
                        console.log('-----------------------------------');

                        changeFont(font_selected, editable);

                        //event.preventDefault();
                        return true;
                    });                    
                    jQuery(".contentHeader .btn-toolbar .font-dropdown").on('change', function(event) {
                    });
                });

                return Plugin.create("font", {                        
                        init: function() {
                                var list_of_fonts = Aloha.settings.plugins.font; // get settings from aloha_header.html                                

                                jQuery.each(list_of_fonts.fontlist,function(cnt,el){
                                        html_list_fonts+="<li role=\"presentation\"><a role=\"menuitem\" href='#' class='' data-tagname='"+list_of_fonts.fontpaths[el]+"' data-placement='bottom'>"+el+"</a></li>"
                                //        html_list_fonts+="<li><a href='#' class='action font' data-tagname='"+list_of_fonts.fontpaths[el]+"' data-placement='bottom'>"+el+"</a></li>"                                    
                                });

                                
                                // UI.adopt('font', null, {
                                //         click: function() {  
                                //         }
                                // });                                
                }
        });
});
