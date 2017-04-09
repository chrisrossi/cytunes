var gulp = require('gulp');
var less = require('gulp-less');
var path = require('path');

gulp.task('default', function() {
  gulp.src('src/less/cytunes.less')
    .pipe(less({
      paths: ['src/vendor/bootstrap-3.3.7/less']
    }))
    .pipe(gulp.dest('wwwdata/css'));
  gulp.src('src/js/*.js')
    .pipe(gulp.dest('wwwdata/js'));
  gulp.src('src/vendor/bootstrap-3.3.7/fonts/*')
    .pipe(gulp.dest('wwwdata/fonts'));
  gulp.src('src/favicon.ico')
    .pipe(gulp.dest('wwwdata'));
});
