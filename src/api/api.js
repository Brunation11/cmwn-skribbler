'use strict';
const logger = require('../logger.js').logger;
const request        = require('request');
const _              = require('lodash');
const fs             = require('fs');
const path           = require('path');
const configFile     = path.resolve(__dirname, '../../config.json');
const config         = JSON.parse(fs.readFileSync(configFile, 'utf8'));
const CmwnApiRequest = request.defaults({
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
const reportError = (postBack) => {
    return report(postBack, 'error');
};

/**
 * Reports complete to skribble
 *
 * @param postBack
 */
const reportSuccess = (postBack) => {
    return report(postBack, 'success');
};

/**
 * Reports a status back to the API
 *
 * @param postBack
 * @param status
 */
const report = (postBack, status) => {
    logger.log('verbose', 'Reporting:', status, 'to:', postBack);
    CmwnApiRequest(
        postBack,
        {
            uri: postBack,
            method: 'POST',
            json: {status: status},
        },
        (err, response, body) => {
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
const fetchSkribbleData = (skribbleUrl, resolve, reject) => {
    logger.log('info', 'Fetching skribble data from:', skribbleUrl);
    if (_.isEmpty(skribbleUrl)) {
        const err = Error('Missing Skribble url for fetchSkribbleData');
        reject(err);
        throw err;
    }

    return new Promise((apiResolve, apiReject) => {
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
    }).then(body => {
        resolve(body);
        return Promise.resolve(body);
    })
    .catch(err => {
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
