/**
 * insert into textarea, **without IE support**
 * @param val text to insert
 * @returns self
 */
$.fn.insertAtCaret = function (val) {
  return this.each(function () {
    var me = this;
    if (me.selectionStart || me.selectionStart == '0') {
      var startPos = me.selectionStart, endPos = me.selectionEnd, scrollTop = me.scrollTop;
      me.value = me.value.substr(0, startPos) + val + me.value.substr(endPos, me.value.length);
      me.focus();
      me.selectionStart = startPos + val.length;
      me.selectionEnd = startPos + val.length;
      me.scrollTop = scrollTop;
    } else {
      me.value += val;
      me.focus();
    }
  });
};

$(function () {
  // move upload button before detail text area
  $('#id_detail').parent().prepend($('#editor-toolbar').removeClass('hidden'));

  var jqXHR;
  var form = document.getElementById('image-upload');
  var $invalidPic = $('#error-invalid-picture'),
    $progress = $('#image-upload-progress'),
    $insert = $('#insert'),
    $dialog = $('#upload-dialog'),
    $imageFile = $('#image-file');

  $insert.click(function () {
    $invalidPic.hide();
    $progress.show();
    $insert.hide();

    var formData = new FormData(form);

    jqXHR = $.ajax({
      url: 'upload',
      type: 'POST',
      data: formData,
      cache: false,
      contentType: false,
      processData: false,
      xhr: function () {
        var xhr = $.ajaxSettings.xhr();
        if (xhr.upload) {
          xhr.upload.addEventListener('progress', function (e) {
            if (e.lengthComputable) {
              var percentComplete = e.loaded / e.total;
              $progress.val(percentComplete);
            } else {
              // todo
            }
          }, false);
        }
        return xhr;
      },
      success: function (data) {
        var content = '![](' + data.url + ')';
        $('#id_detail').insertAtCaret(content);
      },
      error: function () {
        alert('上传失败');
      },
      complete: function () {
        $insert.show();
        $dialog.modal('hide');
        jqXHR = null;
      }
    })
  });

  $dialog.on('hide.bs.modal', function () {
    // abort upload
    if (jqXHR)
      jqXHR.abort();

    // reset form
    form.reset();

    $progress.val(0).hide();
    $insert.show();
  }).on('show.bs.modal', function () {
    $insert.attr('disabled', 'disabled');
  });

  $imageFile.change(function () {
    var file = this.files[0];
    if (file.name.match(/(jpe?g|png|gif)$/i) && file.size < 1024 * 1024 &&
      file.type.match(/image\/(png|jpeg|gif)/i)) {
      $invalidPic.hide();
      $insert.removeAttr('disabled');
    } else {
      $invalidPic.fadeIn();
      $insert.attr('disabled', 'disabled');
    }
  });
});