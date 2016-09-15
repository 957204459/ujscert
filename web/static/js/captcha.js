$(function() {
  // captcha hack

  $('[data-captcha=captcha]').each(function(i, e) {
    var me = $(e);
    $img = me.children('img.captcha').css('cursor', 'pointer').click(function() {
      $.getJSON('/captcha/refresh', function(data) {
        $img.attr('src', data['image_url']);
        me.children('input[type=hidden]').val(data['key']);
      });
    });
  });
});