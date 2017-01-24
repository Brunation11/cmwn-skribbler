'use strict';
const request = require('request');
const _ = require('lodash');
const fs = require('fs');
const path = require('path');
const configFile = path.resolve(__dirname, '../../config.json');
const config = JSON.parse(fs.readFileSync(configFile, 'utf8'));

const CmwnApiRequest = request.defaults({
    auth: {
        user: config.cmwn_api.user,
        pass: config.cmwn_api.password
    },
    timeout: 30000,
    json: true
});

const reportError = (postBack) => {
    return report(postBack, 'error');
};

const reportSuccess = (postBack) => {
    return report(postBack, 'success');
};

const report = (postBack, status) => {
    console.log('Reporting:', status, 'to:', postBack);
    CmwnApiRequest(
        postBack,
        {
            uri: postBack,
            method: 'POST',
            json: {status: status},
        },
        (err, response, body) => {
            if (err) {
                console.error('Error reporting status:', postBack, err);
                return;
            }

            if (response.statusCode !== 201) {
                console.error('Incorrect response code:', response.statusCode, 'to:', postBack);
                return;
            }

            console.log('Reported status:', status, 'to:', postBack);
        }
    );
};

const fetchSkribbleData = (skribbleUrl, resolve, reject) => {
    console.info('Fetching skribble data from:', skribbleUrl);
    if (_.isEmpty(skribbleUrl)) {
        const err = Error('Missing Skribble url for fetchSkribbleData');
        reject(err);
        throw err;
    }

    return new Promise((apiResolve, apiReject) => {
        CmwnApiRequest.get(skribbleUrl, (err, response, body) => {
            if (err) {
                console.log('Error requesting:', skribbleUrl, err);
                return apiReject(err);
            }

            if (response.statusCode !== 200) {
                console.error('Invalid response code:', response.statusCode, 'from:', skribbleUrl);
                return apiReject(Error('Invalid response code: ' + response.statusCode));
            }

            if (_.isEmpty(body)) {
                console.error('Empty response body:', 'from:', skribbleUrl);
                return apiReject(Error('Empty response body from: ' + skribbleUrl));
            }

            console.log('Successful skribble request');
            return apiResolve(body);
        });
    }).then(body => {
        resolve(body);
        return Promise.resolve(body);
    })
    .catch(err => {
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
