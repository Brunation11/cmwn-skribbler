'use strict';
const logger = require('../logger.js').logger;
const request          = require('request');
const _                = require('lodash');
const fs               = require('fs');
const config           = JSON.parse(fs.readFileSync('config.json', 'utf8'));
const jimp             = require('jimp');
const MediaApiRequests = request.defaults({
    timeout: 30000,
    strictSSL: false,
    json: true
});

// Local in memory cache
let assetDataCache = {};
let imageCache     = {};

/**
 * Populates the asset with data from the Media API
 *
 * @param {Asset} asset
 * @param {Object} mediaData
 */
function fillAssetData(asset, mediaData) {
    const media = _.defaults(mediaData, {can_overlap: false}, {check: {type: null, value: null}});

    logger.log('debug', 'Filling asset data:', media);
    asset.can_overlap = media.can_overlap;
    asset.hash_type   = media.check.type;
    asset.hash_value  = media.check.value;
    asset.type        = media.asset_type;
    return asset;
}

module.exports = {
    /**
     * Fetches the asset data using the /a endpoint
     *
     * @param asset
     * @param resolve
     * @param reject
     * @returns {Promise.<TResult>}
     */
    fetchAssetData: (asset, resolve, reject) => {
        return new Promise((apiResolve, apiReject) => {
            logger.log('verbose', 'fetching media asset data for:', asset.asset_id);
            if (!_.has(asset, 'asset_id')) {
                const err = Error('Only Assets can be passed into MediaApi.fetchAssetData');
                reject(err);
                throw err;
            }

            if (_.has(assetDataCache, asset.asset_id)) {
                logger.log('debug', 'Cache hit for asset:', asset.asset_id);
                return resolve(fillAssetData(asset, assetDataCache[asset.asset_id]));
            }

            logger.log('debug', 'Cache miss for asset:', asset.asset_id);

            const assetUri = config.media_api.media_url + 'a/' + asset.asset_id;
            logger.log('verbose', 'Making request to:', assetUri);
            MediaApiRequests.get(
                assetUri,
                (err, response, body) => {
                    if (err) {
                        apiReject('Error fetching media asset:' + err);
                        throw Error('Error fetching media asset:' + err);
                    }

                    if (_.isEmpty(body)) {
                        const emptyErr = Error('Empty response from media API');
                        apiReject(emptyErr);
                        throw emptyErr;
                    }

                    logger.log('verbose', 'Successful media request for asset:', asset.asset_id);
                    assetDataCache[asset.asset_id] = body;
                    return apiResolve(fillAssetData(asset, body));
                });
        })
        .then(asset => {
            resolve(asset);
            return asset;
        })
        .catch(err => {
            logger.error('Exception when fetching media data for asset:', asset.asset_id, err);
            reject(err);
            throw err;
        });
    },

    /**
     * Downloads the asset
     *
     * Checks local cache to not make the call again
     *
     * @param asset
     * @param resolve
     * @param reject
     * @returns {*}
     */
    downloadAsset: (asset, resolve, reject) => {
        if (!_.has(asset, 'asset_id') || !_.has(asset, 'asset_src')) {
            const err = Error('Cannot down load an asset with out the asset_id or src');
            reject(err);
            throw err;
        }

        logger.log('verbose', 'Downloading asset:', asset.asset_id);
        if (_.has(imageCache, asset.asset_id)) {
            logger.log('debug', 'Cache hit for downloading image:', asset.asset_id);
            return resolve(imageCache[asset.asset_id].clone());
        }

        logger.log('debug', 'Cache miss for downloading image:', asset.asset_id);

        return jimp.read(asset.asset_src)
            .then(img => {
                imageCache[asset.asset_id] = img;
                asset.img = img;
                asset.height = img.bitmap.height;
                asset.width = img.bitmap.width;
                logger.log('verbose', 'Image downloaded for asset:', asset.asset_id);
                logger.log('debug', 'Data for asset_id (height, width):', asset.asset_id, asset.height, asset.width);
                resolve(asset);
                return asset;
            }).catch(err => {
                logger.error('Failed to download image for asset:', asset.asset_id, err);
                reject(err);
                throw err;
            });
    }
};
