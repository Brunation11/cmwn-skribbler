'use strict';

const winston    = require('winston');
const rollbar    = require('winston-rollbar').Rollbar;
const fs         = require('fs');
const path       = require('path');
const configFile = path.resolve(__dirname, '../config.json');
const config     = JSON.parse(fs.readFileSync(configFile, 'utf8')).rollbar;

const logger = new (winston.Logger)({
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
