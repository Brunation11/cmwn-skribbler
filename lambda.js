'use strict';
const _ = require('lodash');
const skribbleProcessor = require('./src/processor').skribbleProcessor;

exports.handler = (event, context, callback) => {
    const skribblePromises = _.map(event.Records, (record) => {
        const message = JSON.parse(record.Message);
        return skribbleProcessor(
            message.skribble_id,
            message.skribble_url,
            message.post_back
        );
    });

    return Promise.all(skribblePromises);
};