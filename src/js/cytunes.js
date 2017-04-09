function cytunes() {
  $(function() {
    $('.more-or-less').each(function() {
      var more = $(this).find('.more').hide();
      if (more) {
        var less = $(this).find('.less').append('...');
        var show_more = $('<a href="#">')
          .text('show more')
          .on('click', function(event) {
            event.preventDefault();
            less.hide();
            more.show();
          });
        less.append('<br>').append(show_more);
        var show_less = $('<a href="#">')
          .text('show less')
          .on('click', function(event) {
            event.preventDefault();
            less.show();
            more.hide();
          });
        more.append('<br>').append(show_less);
      }
    });
  });
}
