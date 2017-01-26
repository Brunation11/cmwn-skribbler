var winston    = require('winston');
var rollbar    = require('winston-rollbar').Rollbar;
var fs         = require('fs');
var path       = require('path');
var configFile = path.resolve(__dirname, '../config.json');
var config     = JSON.parse(fs.readFileSync(configFile, 'utf8')).rollbar;

var logger = new (winston.Logger)({
    exitOnError: false,
    transports: [
        new (winston.transports.Console)({
            colorize: true
        }),
        new (winston.transports.Rollbar)({
            rollbarAccessToken: config.token,
            rollbarConfig: config,
            level: config.level,
            handleExceptions: true
        })
    ],
    level: 'debug'
});

module.exports = {
    logger
};
