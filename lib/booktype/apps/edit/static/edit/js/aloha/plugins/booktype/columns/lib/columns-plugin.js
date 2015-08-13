  define(['aloha', 'aloha/plugin', 'jquery',  'jquery19', 'ui/ui', 'aloha/ephemera', 'block/block', 'block/blockmanager', 'underscore', 'PubSub', 'booktype', 'toolbar/toolbar-plugin'], 
      function(Aloha, Plugin, jQuery,  jQuery19, UI, Ephemera, block, BlockManager, _, PubSub, booktype, toolbar) {
        var selected = null;;

        var setStyle = function ($elem, columns) {
          $elem.css("column-count", columns);
          $elem.css("-webkit-column-count", columns);
          $elem.css("-mz-column-count", columns);          
          $elem.css("-webkit-column-width", Math.round(1 / columns))
          $elem.css("column-width", Math.round(1 / columns));
        };

       var ColumnsBlock = block.AbstractBlock.extend({
              title: 'ColumnsTable',
              isDraggable: function() { return false; },
              init: function($element, postProcessFn) {      
                var that = this;
                var ed = jQuery($element).find('.aloha-editable');

                ed.before('<div class="bk-columns-info"><a class="bk-help" href=""><span class="icon-question-sign"></span></a>\
COLUMNS <a class="bk-action bk-remove" href=""><span class="icon-trash"></span></a>\
<a class="bk-action bk-settings" href=""><span class="icon-cog"></span></a>  </div>');

                jQuery19($element).find('.bk-settings').on('click', function () {
                  selected = $element;

                  jQuery19('#columnsDialog').modal('show');
                  return false;
                });

                jQuery19($element).find('.bk-help').on('click', function () {
                  return false;
                });

                jQuery19($element).find('.bk-remove').on('click', function () {
                  if (confirm("Do you want to remove the columns?")) {
                    var $content = $element.find('.aloha-editable').contents().unwrap();;
                    $element.mahaloBlock();                  
                    $element.replaceWith($content);
                  }
                  return false;
                });

                var column = jQuery($element).attr('data-column');

                setStyle(ed, column);
                // jQuery($element).find('td').each(function() {
                //   var $td = jQuery(this);

                //   $td.wrapInner('<div class="aloha-editable"></div>');
                // });

                return postProcessFn();
              },
              update: function($element, postProcessFn) {
                  // jQuery($element).find('td').each(function() {
                  //   var $td = jQuery(this);

                  //   if(!jQuery($td.children().get(0)).hasClass('aloha-editable')) {
                  //     $td.wrapInner('<div class="aloha-editable">&nbsp;</div>');
                  //   }
                  // });
                  
                  return postProcessFn();
                  }
          });   


      var _initColumns = function(editable) {
          var $tables = editable.obj.find('div.bk-columns').each(function (idx, bl) {
            var $block = jQuery(bl);
            var $content = $block.html();

            $block.addClass('aloha-columns');
            $block.empty();

            if (_.isUndefined($block.attr("data-column"))) {
              $block.attr("data-column", "3");
            }

            if (_.isUndefined($block.attr("data-gap"))) {
              $block.attr("data-gap", "");
            }

            if (_.isUndefined($block.attr("data-valign"))) {
              $block.attr("data-valign", "");
            }

            var $b = jQuery('<div class="aloha-editable"></div>');
            $b.append($content);
            $block.append($b);

            $block.alohaBlock({'aloha-block-type': 'ColumnsBlock'});
          });
      }

        return Plugin.create('columns', {
          defaultSettings: {
            enabled: true
          }, 
          init: function () {
              var self = this;

              self.settings = jQuery.extend(true, self.defaultSettings, self.settings);               

              if(!self.settings.enabled) { return; }

              Ephemera.attributes('data-aloha-block-type', 'contenteditable');
          
              BlockManager.registerBlockType('ColumnsBlock', ColumnsBlock);

              Aloha.bind('aloha-my-undo', function(event, args) {
                _initColumns(args.editable);
              });

              Aloha.bind('aloha-editable-created', function($event, editable) {
                _initColumns(editable);              
              });

              var $dialog = jQuery19('#columnsDialog');

              $dialog.find('.btn-ok').on('click', function () {
                var dataColumn = $dialog.find('input[name="columnsNumber"]').val();
                var valignColumn = $dialog.find('select[name="valign"]').val();
                var gapColumn = $dialog.find('input[name="gap"]').val();

                setStyle(selected.find('.aloha-editable'), dataColumn);

                selected.attr("data-column", dataColumn);
                selected.attr("data-gap", gapColumn);
                selected.attr("data-valign", valignColumn);

                $dialog.modal('hide');

                setTimeout(function () {
                  var b1 = BlockManager.getBlock(selected.attr('id')); 
                  b1.activate();
                }, 500);

              });

              $dialog.on('show.bs.modal', function () {
                var dataColumn = selected.attr("data-column");
                var valignColumn = selected.attr("data-valign");
                var gapColumn = selected.attr("data-gap");

                $dialog.find('input[name="columnsNumber"]').val(dataColumn);
                $dialog.find('input[name="valign"]').val(valignColumn);
                $dialog.find('input[name="gap"]').val(gapColumn);
              });

              UI.adopt('columns-insert', null, {
                click: function() {        
                         editable = Aloha.activeEditable;
                         range = Aloha.Selection.getRangeObject();

                         var $a = jQuery('<div class="aloha-columns" data-column="3" data-valign="" data-gap="5"><div class="aloha-editable"><p>  </p></div></div>');
                         $a.alohaBlock({'aloha-block-type': 'ColumnsBlock'});                       

                         GENTICS.Utils.Dom.insertIntoDOM($a, range, editable.obj);
                         return true;
                      }
              });
              UI.adopt('column-break-insert', null, {
                click: function() {        
                         editable = Aloha.activeEditable;
                         range = Aloha.Selection.getRangeObject();


                         var $a = jQuery('<div class="bk-column-break"></div>');

                         GENTICS.Utils.Dom.insertIntoDOM($a, range, editable.obj);
                         return true;
                      }
              });

            },            
            makeClean: function(obj) {    
                  jQuery('.aloha-block-ColumnsBlock', jQuery(obj)).each(function() {
                    var $block = jQuery(this); 
                    var $content = $block.find('.aloha-editable').contents().unwrap();

                    var dataColumn = $block.attr("data-column");
                    var gapColumn = $block.attr("data-gap");
                    var valignColumn = $block.attr("data-valign");

                    if (_.isUndefined(dataColumn)) {
                      dataColumn = 1;
                    }

                    if (_.isUndefined(gapColumn)) {
                      gapColumn = 5;
                    }

                    if (_.isUndefined(valignColumn)) {
                      valignColumn = "";
                    }

                    var $elem = jQuery('<div class="bk-columns" data-column="' + dataColumn + 
                      '" data-gap="' + gapColumn + '" data-valign="' + valignColumn + '"></div>');
                    $elem.append($content);

                    $block.replaceWith($elem);
                  });
            }
        });
      }
);
