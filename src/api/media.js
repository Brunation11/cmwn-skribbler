var logger = require('../logger.js').logger;
var _                = require('lodash');
var fs               = require('fs');
var config           = JSON.parse(fs.readFileSync('config.json', 'utf8'));
var jimp             = require('jimp');
var crypto           = require('crypto');
var MediaFileRequest = require('request').defaults({ encoding: null });
var MediaApiRequests = require('request').defaults({
    timeout: 30000, // 30 secounds should be good enough
    strictSSL: true,
    json: true
});

// Local in memory cache
var assetDataCache = {};
var imageCache     = {};

/**
 * Populates the asset with data from the Media API
 *
 * @param {Asset} asset
 * @param {Object} mediaData
 */
function fillAssetData(asset, mediaData) {
    var media = _.defaults(mediaData, {can_overlap: false}, {check: {type: null, value: null}});

    logger.log('debug', 'Filling asset data:', media);
    asset.can_overlap = media.can_overlap;
    asset.hash_type   = media.check.type;
    asset.hash_value  = media.check.value;
    asset.type        = media.asset_type;
    asset.mime        = media.mime_type;
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
    fetchAssetData: function(asset, resolve, reject) {
        return new Promise((apiResolve, apiReject) => {
            logger.log('verbose', 'fetching media asset data for:', asset.asset_id);
            if (!_.has(asset, 'asset_id')) {
                var err = Error('Only Assets can be passed into MediaApi.fetchAssetData');
                reject(err);
                throw err;
            }

            if (_.has(assetDataCache, asset.asset_id)) {
                logger.log('debug', 'Cache hit for asset:', asset.asset_id);
                return resolve(fillAssetData(asset, assetDataCache[asset.asset_id]));
            }

            logger.log('debug', 'Cache miss for asset:', asset.asset_id);

            var assetUri = config.media_api.media_url + 'a/' + asset.asset_id;
            logger.log('verbose', 'Making request to:', assetUri);
            MediaApiRequests.get(
                assetUri,
                (err, response, body) => {
                    if (err) {
                        apiReject('Error fetching media asset:' + err);
                        throw Error('Error fetching media asset:' + err);
                    }

                    if (_.isEmpty(body)) {
                        var emptyErr = Error('Empty response from media API');
                        apiReject(emptyErr);
                        throw emptyErr;
                    }

                    logger.log('verbose', 'Successful media request for asset:', asset.asset_id);
                    assetDataCache[asset.asset_id] = body;
                    return apiResolve(fillAssetData(asset, body));
                });
        })
        .then(function(asset) {
            resolve(asset);
            return asset;
        })
        .catch(function(err) {
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
    downloadAsset: function(asset, resolve, reject) {
        if (!_.has(asset, 'asset_id') || !_.has(asset, 'asset_src')) {
            var err = Error('Cannot down load an asset with out the asset_id or src');
            reject(err);
            throw err;
        }

        logger.log('verbose', 'Downloading asset:', asset.asset_id);
        if (_.has(imageCache, asset.asset_id)) {
            logger.log('debug', 'Cache hit for downloading image:', asset.asset_id);
            return resolve(imageCache[asset.asset_id].clone());
        }

        logger.log('debug', 'Cache miss for downloading image:', asset.asset_src);
        return new Promise((dlResolve, dlReject) => {
            MediaFileRequest(
                asset.asset_src,
                function (err, response, data) {
                    if (err) {
                        logger.error('Error downloading asset:', asset.asset_src, err);
                        dlReject(err);
                        return;
                    }

                    var hashing;
                    var hash;

                    if (!config.media_api.validate_hash) {
                        logger.log('verbose', 'Not validating file hash');
                        return jimp.read(data).then(dlResolve);
                    }

                    logger.log('verbose', 'Validating file hash');
                    switch (asset.hash_type) {
                        case 'sha1':
                            logger.log('debug', 'Using SHA1');
                            hashing = crypto.createHash('sha1');
                            break;

                        default:
                        case 'md5':
                            logger.log('debug', 'Using MD5');
                            hashing = crypto.createHash('md5');
                            break;
                    }

                    hashing.update(data);
                    hash = hashing.digest('hex');
                    logger.log('debug', 'Checking hash:', asset.hash_value, 'to', hash);
                    if (asset.hash_value == hash) {
                        return jimp.read(data).then(dlResolve);
                    }

                    dlReject(Error('Hash mis-match!'));
                }
            );
        })
        .then(img => {
            imageCache[asset.asset_id] = img;
            asset.img = img;
            asset.height = img.bitmap.height;
            asset.width = img.bitmap.width;
            logger.log('verbose', 'Image downloaded for asset:', asset.asset_id);
            logger.log('debug', 'Data for asset_id (height, width):', asset.asset_id, asset.height, asset.width);
            resolve(asset);
            return asset;
        }).catch(function(err) {
            logger.error('Failed to download image for asset:', asset.asset_id, err);
            reject(err);
            throw err;
        });
    }
};
