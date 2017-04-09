function cytunes() {
  $(function() {
    /**
     * More or less
     */
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

    /**
     * Player
     */
    function player() {
      var album = $(this),
          songs = album.find('.song'),
          player = album.find('.player'),
          play_button = player.find('.play-button'),
          pause_button = player.find('.pause-button'),
          duration_element = player.find('.duration'),
          title_element = player.find('.title'),
          current = 0,
          duration = 0,
          position = 0,
          playing = false;

      function format_seconds(n) {
        var minutes = Math.floor(n / 60),
            seconds = Math.floor(n % 60);
        if (seconds < 10) seconds = '0' + seconds;
        return minutes + ':' + seconds;
      }

      function refresh() {
        songs.each(function() {
          $(this).find('.pause-button').hide();
          $(this).find('.play-button').show();
        });

        var song = $(songs[current]);
        title = song.find('.track-title').text();
        tracknum = song.data('tracknum');
        if (tracknum) title = tracknum + '. ' + title;
        title_element.text(title).show();

        track = song.find('audio')
        duration = track[0].duration;
        if (duration) {
          duration_element.text(format_seconds(position) + ' / ' + 
              format_seconds(duration)).show();
        }
        else {
          track.on('durationchange', function(event) {
            console.log('woo, look at me!');
            duration = this.duration;
            duration_element.text(format_seconds(position) + ' / ' + 
                format_seconds(duration)).show();
          });
        }

        if (playing) {
          song.find('.play-button').hide();
          song.find('.pause-button').show();
          play_button.hide();
          pause_button.show();
        }
        else {
          play_button.show();
          pause_button.hide();
        }
      }

      function play_song(track) {
        $('audio').each(function() { this.pause(); });

        var $audio = $(songs[track]).find('audio'),
            audio = $audio[0];
        $audio
          .on('ended', function(event) {
            var next_track = current + 1;
            if (next_track < songs.length)
              play_song(next_track);
            else
              stop();
          })
          .on('timeupdate', function(event) {
            position = this.currentTime;
            refresh();
          })
          .on('pause', function(event) {
            var audios = album.find('audio');
            for (var i = 0; i < audios.length; i++)
              if (!audios[i].paused)
                return
              
            playing = false;
            refresh();
          });

        current = track;

        playing = true;
        audio.play();
        
        refresh();
      }

      function pause() {
        $(songs[current]).find('audio')[0].pause();
        playing = false;
        refresh();
      }

      function stop() {
        current = position = 0;
        playing = false;
        refresh();
      }

      play_button.on('click', function(event) {
        event.preventDefault();
        play_song(current);
      });

      pause_button.on('click', function(event) {
        event.preventDefault();
        pause();
      });

      songs.find('.play-button').on('click', function(event) {
        event.preventDefault();
        play_song($(this).parents('tr').data('index'));
      });

      songs.find('.pause-button').on('click', function(event) {
        event.preventDefault();
        pause();
      });

      refresh();
    }

    $('.album').each(player);
    $('.single').each(player);

  }); // end cytunes()
}
