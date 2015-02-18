 /*
  This file is part of Booktype.
  Copyright (c) 2013 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
 
  Booktype is free software: you can redistribute it and/or modify
  it under the terms of the GNU Affero General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.
 
  Booktype is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU Affero General Public License for more details.
 
  You should have received a copy of the GNU Affero General Public License
  along with Booktype.  If not, see <http://www.gnu.org/licenses/>.
*/

(function (win, jquery, _) {
  'use strict';

	jquery.namespace('win.booktype.editor.publish');

  win.booktype.editor.publish = (function () {

    var PublishRouter = Backbone.Router.extend({
      routes: {
        "publish":      "publish",
      },

      publish: function () {
        var activePanel = win.booktype.editor.getActivePanel();

        activePanel.hide(function () {
          win.booktype.editor.data.activePanel = win.booktype.editor.data.panels["publish"];
          win.booktype.editor.data.activePanel.show();
        });
      }
    });

    var router = new PublishRouter();


    var enableButton = function (state) {
      if (state) {
        jquery("#content button.btn-publish").attr('aria-disabled', true).removeClass('disabled');
      } else {
        jquery("#content button.btn-publish").attr('aria-disabled', true).addClass('disabled');        
      }

    };

    var showProgress = function () {
      var $container = jquery("#content .publish_history");

      var $div = jquery('<div class="publishing-message box gray">Publishing....</div>');
      $container.prepend($div);
    };

    /*******************************************************************************/
    /* SHOW                                                                        */
    /*******************************************************************************/    

    var _show = function () {
      // set toolbar
      var t = win.booktype.ui.getTemplate('templatePublishHeader');
      jquery('DIV.contentHeader').html(t);

      var t2 = win.booktype.ui.getTemplate('templatePublishContent');
      jquery('#content').html(t2);

      // Show tooltips
      jquery('DIV.contentHeader [rel=tooltip]').tooltip({container: 'body'});

      jquery("#content .publish_history").empty();

      enableButton(false);

      jquery("#content input[type=checkbox]").on('change', function () {
        if (jquery("#content input[type=checkbox]:checked").length === 0) {
          enableButton(false);
        } else {
          enableButton(true);
        }
      });

      jquery('#content button.btn-publish').on('click', function () {
        win.booktype.ui.notify('Publishing book');
        showProgress();
        enableButton(false);

        var formats = jquery.map(jquery("#content input[type=checkbox]:checked"), function (v) { return jquery(v).attr("name");});

        win.booktype.sendToCurrentBook({'command': 'publish_book', 
          'book_id': win.booktype.currentBookID,
          'formats': formats},
          function (data) {
            console.log(data);

            if (data.result === false) {
              // Show some kind of error message
            }
            win.booktype.ui.notify();
          });
      });

      window.scrollTo(0, 0);

      // Trigger events
      jquery(document).trigger('booktype-ui-panel-active', ['publish', this]);
    };

    /*******************************************************************************/
    /* HIDE                                                                        */
    /*******************************************************************************/

    var _hide = function (callback) {
      // Destroy tooltip
      jquery('DIV.contentHeader [rel=tooltip]').tooltip('destroy');

      // Clear content
      jquery('#content').empty();
      jquery('DIV.contentHeader').empty();

      if (!_.isUndefined(callback)) {
        callback();
      }
    };

    /*******************************************************************************/
    /* INIT                                                                        */
    /*******************************************************************************/

    var _init = function () {      
      jquery('#button-publish').on('click', function (e) { Backbone.history.navigate('publish', true); });

      win.booktype.subscribeToChannel('/booktype/book/' + win.booktype.currentBookID + '/' + win.booktype.currentVersion + '/',
        function (message) {
          var funcs = {
            'book_published': function () {
              if (message.state == 'SUCCESS') {
                jquery("#content .publish_history .publishing-message").fadeOut().remove();
                jquery("#content .publish_history").prepend('<div class="box"><a target="_blank" href="'+message.url+'">download</a></div>');

                if (jquery("#content input[type=checkbox]:checked").length !== 0) {
                  enableButton(true);
                }
              }
            }
          };

          if (funcs[message.command]) {
            funcs[message.command]();
          }
        }
      );

    };

    /*******************************************************************************/
    /* EXPORT                                                                      */
    /*******************************************************************************/

    return {
      'init': _init,
      'show': _show,
      'hide': _hide,
      'name': 'publish'
    };
  })();

  
})(window, jQuery, _);