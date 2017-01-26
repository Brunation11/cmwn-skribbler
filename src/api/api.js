var logger = require('../logger.js').logger;
var request        = require('request');
var _              = require('lodash');
var fs             = require('fs');
var path           = require('path');
var configFile     = path.resolve(__dirname, '../../config.json');
var config         = JSON.parse(fs.readFileSync(configFile, 'utf8'));
var CmwnApiRequest = request.defaults({
    auth: {
        user: config.cmwn_api.user,
        pass: config.cmwn_api.password
    },
    timeout: 30000,
    json: true
});

/**
 * Reports error status back to the API
 *
 * @param postBack
 */
var reportError = function(postBack) {
    return report(postBack, 'error');
};

/**
 * Reports compvare to skribble
 *
 * @param postBack
 */
var reportSuccess = function(postBack) {
    return report(postBack, 'success');
};

/**
 * Reports a status back to the API
 *
 * @param postBack
 * @param status
 */
var report = function(postBack, status) {
    logger.log('verbose', 'Reporting:', status, 'to:', postBack);
    CmwnApiRequest(
        postBack,
        {
            uri: postBack,
            method: 'POST',
            json: {status: status},
        },
        function (err, response, body) {
            if (err) {
                logger.error('Error reporting status: ', postBack, err);
                return;
            }

            if (response.statusCode !== 201) {
                logger.error('Incorrect response code: ', response.statusCode, 'to:', postBack);
                return;
            }

            logger.log('verbose', 'Reported status:', status, 'to:', postBack);
        }
    );
};

/**
 * Fetches the skribble data
 *
 * @param skribbleUrl
 * @param resolve
 * @param reject
 * @returns {Promise.<TResult>}
 */
var fetchSkribbleData = function(skribbleUrl, resolve, reject) {
    logger.log('info', 'Fetching skribble data from:', skribbleUrl);
    if (_.isEmpty(skribbleUrl)) {
        var err = Error('Missing Skribble url for fetchSkribbleData');
        reject(err);
        throw err;
    }

    return new Promise(function(apiResolve, apiReject) {
        CmwnApiRequest.get(skribbleUrl, (err, response, body) => {
            if (err) {
                logger.error('Error requesting:', skribbleUrl, err);
                return apiReject(err);
            }

            if (response.statusCode !== 200) {
                logger.error('Invalid response code:', response.statusCode, 'from:', skribbleUrl);
                return apiReject(Error('Invalid response code: ' + response.statusCode));
            }

            if (_.isEmpty(body)) {
                logger.error('Empty response body from:', skribbleUrl);
                return apiReject(Error('Empty response body from: ' + skribbleUrl));
            }

            logger.log('verbose', 'Successful skribble request');
            return apiResolve(body);
        });
    }).then(function(body) {
        resolve(body);
        return Promise.resolve(body);
    })
    .catch(function(err) {
        logger.error('Failed to fetch skribble data: ', err);
        reject(err);
        throw err;
    });
};

module.exports = {
    fetchSkribbleData,
    reportError,
    reportSuccess,
    report
};
