var _ = require('lodash');
var gulp = require('gulp');
var fs = require('fs');
var buildTask = [
    'build'
];

gulp.task('default', buildTask);
gulp.task('build', buildTask);
gulp.task('b', buildTask);

var zipTheBuild = function () {
    var zip = require('gulp-zip');
    return gulp.src(['**/*.js', 'blank.png'])
        .pipe(zip('build.zip'))
        .pipe(gulp.dest('./'));
};

gulp.task('build', zipTheBuild);
