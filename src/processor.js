'use strict';
const _           = require('lodash');
const Asset       = require('./asset').Asset;
const utils       = require('skribble-utils');
const skribbleApi = require('./api/api');
const MediaApi    = require('./api/media');
const Images      = require('./image.js');
// require('request').debug = true;

/**
 * Builds a asset object from the skribble json spec
 *
 * can_overlap, corners, height and width will all be filled with default values
 * the media Api will have to populate those items
 *
 * @param {Array|Object} skribbleJson
 * @param {Number} layerMul keeps all the assets sequential in the layering
 *      since each asset is processed in layer order
 * @returns {Array|Object}
 */
function grabAssets(skribbleJson, layerMul) {
    return _.map(skribbleJson, ((assetData, assetIdx) => {
        console.log('Mapping asset with data');
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
    skribbleProcessor: (id, url, postBack) => {
        return new Promise((resolve, reject) => {
            if (_.isEmpty(id) ||_.isEmpty(url) || _.isEmpty(postBack)) {
                return reject(Error('Missing required parameters to process'));
            }

            console.info('Processing skribble:', id);
            return skribbleApi.fetchSkribbleData(url, resolve, reject)
                .then(skribbleJson => {
                    // build list of all assets specs
                    let assetSpecs = [];
                    assetSpecs.push(grabAssets([skribbleJson.rules.background], 1));
                    assetSpecs.push(grabAssets(skribbleJson.rules.items, 2));
                    assetSpecs.push(grabAssets(skribbleJson.rules.messages, 3));

                    return _.flatten(assetSpecs);
                })
                .then(assets => {
                    console.log('Fetching asset data');
                    let assetPromises = _.map(assets, (asset) => {
                        return MediaApi.fetchAssetData(asset, resolve, reject);
                    });

                    return Promise.all(assetPromises);
                })
                .then(assets => {
                    console.log('Downloading assets from media server');
                    let assetPromises = _.map(assets, (asset) => {
                        return MediaApi.downloadAsset(asset, resolve, reject);
                    });

                    return Promise.all(assetPromises);
                })
                .then(assets => {
                    console.log('Adding corners');

                    assets       = _.map(assets, (asset) => {
                        asset.corners = utils.getAssetCorners(asset);
                        return asset;
                    });

                    return assets;
                }).then(assets => {
                    console.log('Checking collision');
                    let assetsOk = true;
                    _.each(assets, (asset) => {
                        if (utils.checkItem(assets, asset)) {
                            console.log('Asset is colliding:', asset.asset_id);
                            assetsOk = false;
                        }
                    });

                    if (!assetsOk) {
                        console.log('Assets are colliding');
                        throw Error('Assets are colliding');
                    }

                    return assets;
                })
                .then(assets => {
                    console.log('Done downloading assets');
                    let imagePromises = _.map(assets, (asset) => {
                        return Images.processImage(asset, resolve, reject);
                    });

                    imagePromises.unshift(Images.getBaseImage(resolve, reject));
                    return Promise.all(imagePromises);
                })
                .then(assets => {
                    console.log('Merging assets');
                    assets = _.sortBy(assets, ['layer']);
                    const baseAsset = assets[0];
                    _.each(assets, (asset) => {
                        if (asset === baseAsset) {
                            return;
                        }

                        Images.placeImage(asset, baseAsset);
                    });

                    baseAsset.img.write('./complete.png');
                })
                .catch(err => {
                    console.error('Failure during skramble');
                    skribbleApi.reportError(postBack);
                    console.error(err);
                    throw err;
                });
        });
    }
};
