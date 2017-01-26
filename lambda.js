const _ = require('lodash');
const skribbleProcessor = require('./src/processor').skribbleProcessor;
var logger = require('./src/logger.js').logger;

exports.handler = function(event, context, callback) {
    logger.log('debug', 'Lambda event' + event);
    var skribblePromises = _.map(event['Records'], function(record)  {
        logger.log('debug', 'Lambda record: ' + record);
        var message = JSON.parse(record['Sns']['Message']);
        logger.log('debug', 'Lambda message: ' + message);
        return skribbleProcessor(
            message.skribble_id,
            message.skribble_url,
            message.post_back
        );
    });

    return Promise.all(skribblePromises);
};