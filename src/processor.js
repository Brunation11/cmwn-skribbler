'use strict';
var logger = require('./logger.js').logger;
var _           = require('lodash');
const Asset       = require('./asset').Asset;
var utils       = require('skribble-utils');
var skribbleApi = require('./api/api');
var MediaApi    = require('./api/media');
var Images      = require('./image.js');
var jimp        = require('jimp');
var aws         = require('./aws.js');

/**
 * Builds a asset object from the skribble json spec
 *
 * can_overlap, corners, height and width will all be filled with default values
 * the media Api will populate those items
 *
 * @param {Array|Object} skribbleJson
 * @param {Number} layerMul keeps all the assets sequential in the layering
 *      since each asset is processed in layer order
 * @returns {Array|Object}
 */
function grabAssets(skribbleJson, layerMul) {
    return _.map(skribbleJson, (function (assetData, assetIdx) {
        logger.log('info','Mapping asset with data');
        assetData = _.defaults(assetData, {state: {left: 0, top: 0, scale: 0, layer: 0}});
        return new Asset(
            assetData.media_id,
            assetData.src,
            assetData.state.left,
            assetData.state.top,
            assetData.state.scale,
            assetData.state.rotation,
            (assetData.state.layer * layerMul) + (assetIdx / 1000)
        );
    }));
}

module.exports = {
    /**
     * Processes the skribble
     *
     * @param id
     * @param url
     * @param postBack
     * @returns {Promise}
     */
    skribbleProcessor: function(id, url, postBack) {
        return new Promise((resolve, reject) => {
            if (_.isEmpty(id) ||_.isEmpty(url) || _.isEmpty(postBack)) {
                return reject(Error('Missing required parameters to process'));
            }

            logger.info('Processing skribble:', id);
            return skribbleApi.fetchSkribbleData(url, resolve, reject)
                .then(function(skribbleJson) {
                    logger.log('info','Building asset list');
                    var assetSpecs = [];
                    if (skribbleJson.rules.background) {
                        assetSpecs.push(grabAssets([skribbleJson.rules.background], 1));
                    }
                    assetSpecs.push(grabAssets(skribbleJson.rules.items, 2));
                    assetSpecs.push(grabAssets(skribbleJson.rules.messages, 3));

                    return _.flatten(assetSpecs);
                })
                .then(function(assets) {
                    logger.log('info', 'Fetching asset data from media API');
                    var assetPromises = _.map(assets, (asset) => {
                        return MediaApi.fetchAssetData(asset, resolve, reject);
                    });

                    return Promise.all(assetPromises);
                })
                .then(function(assets) {
                    logger.log('info', 'Downloading assets from media server');
                    var assetPromises = _.map(assets, (asset) => {
                        return MediaApi.downloadAsset(asset, resolve, reject);
                    });

                    return Promise.all(assetPromises);
                })

                .then(function(assets) {
                    logger.log('info', 'Processing assets');
                    var imagePromises = _.map(assets, (asset) => {
                        return Images.processImage(asset, resolve, reject);
                    });

                    imagePromises.unshift(Images.getBaseImage(resolve, reject));
                    return Promise.all(imagePromises);
                })
                .then(function(assets) {
                    logger.log('info', 'Checking collision');
                    var assetsOk = true;
                    _.each(assets, (asset) => {
                        if (utils.checkItem(assets, asset)) {
                            logger.log('info','Asset is colliding:', asset.asset_id);
                            assetsOk = false;
                        }
                    });

                    if (!assetsOk) {
                        throw Error('Assets are colliding');
                    }

                    logger.log('debug', 'Assets are fine');

                    return assets;
                })
                .then(function(assets) {
                    logger.log('info','Merging assets');
                    assets = _.sortBy(assets, ['layer']);
                    var baseAsset = assets[0];
                    _.each(assets, (asset) => {
                        if (asset === baseAsset) {
                            return;
                        }

                        Images.placeImage(asset, baseAsset);
                    });

                    return baseAsset;
                })
                .then(function(completeAsset) {
                    logger.log('info', 'Making web safe');
                    completeAsset.img = completeAsset.img.rgba(false)
                        .filterType(jimp.PNG_FILTER_AVERAGE)
                        .deflateLevel(9)
                        .deflateStrategy(3);

                    return completeAsset;
                })
                .then(function(completeAsset) {
                    logger.log('info', 'Uploading file to s3');
                    completeAsset.asset_id = id;
                    aws.uploadAsset(completeAsset);
                    return completeAsset;
                })
                .then(function(completeAsset) {
                    logger.log('info', 'Reporting success to api');
                    skribbleApi.reportSuccess(postBack);
                })
                .catch(err => {
                    logger.error('Failure during skramble:', err);
                    skribbleApi.reportError(postBack);
                    logger.error(err);
                    throw err;
                });
        });
    }
};
