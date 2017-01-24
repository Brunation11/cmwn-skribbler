'use strict';
const request = require('request');
const _       = require('lodash');
const fs      = require('fs');
const config  = JSON.parse(fs.readFileSync('config.json', 'utf8'));
const jimp    = require('jimp');

const MediaApiRequests = request.defaults({
    timeout: 30000,
    strictSSL: false,
    json: true
});

// Local in memory cache
let assetDataCache = {};
let imageCache = {};

/**
 * Populates the asset with data from the Media API
 *
 * @param {Asset} asset
 * @param {Object} mediaData
 */
function fillAssetData(asset, mediaData) {
    const media = _.defaults(mediaData, {can_overlap: false}, {check: {type: null, value: null}});

    asset.can_overlap = media.can_overlap;
    asset.hash_type   = media.check.type;
    asset.hash_value  = media.check.value;
    asset.type        = media.asset_type;
    return asset;
}

module.exports = {
    fetchAssetData: (asset, resolve, reject) => {
        return new Promise((apiResolve, apiReject) => {
            console.log('fetching media asset data for:', asset.asset_id);
            if (!_.has(asset, 'asset_id')) {
                const err = Error('Only Assets can be passed into MediaApi.fetchAssetData');
                reject(err);
                throw err;
            }

            if (_.has(assetDataCache, asset.asset_id)) {
                console.log('Cache hit');
                return resolve(fillAssetData(asset, assetDataCache[asset.asset_id]));
            }

            const assetUri = config.media_api.media_url + 'a/' + asset.asset_id;
            console.log('Media request:', assetUri);
            MediaApiRequests.get(
                assetUri,
                (err, response, body) => {
                    if (err) {
                        console.error('Error fetching media asset:', err);
                        apiReject('Error fetching media asset:' + err);
                        throw Error('Error fetching media asset:' + err);
                    }

                    if (_.isEmpty(body)) {
                        const emptyErr = Error('Empty response from media API:');
                        console.error(emptyErr);
                        apiReject(emptyErr);
                        throw emptyErr;
                    }

                    console.log('Successful media request');
                    assetDataCache[asset.asset_id] = body;
                    return apiResolve(fillAssetData(asset, body));
                });
        })
        .then(asset => {
            resolve(asset);
            return asset;
        })
        .catch(err => {
            reject(err);
            throw err;
        });
    },

    downloadAsset: (asset, resolve, reject) => {
        console.log('Downloading asset:', asset.asset_id);
        if (!_.has(asset, 'asset_id') || !_.has(asset, 'asset_src')) {
            const err = Error('Cannot down load an asset with out the asset_id or src');
            console.error(err);
            reject(err);
            throw err;
        }

        if (_.has(imageCache, asset.asset_id)) {
            console.log('Cache hit for downloading image');
            return resolve(imageCache[asset.asset_id].clone());
        }

        return jimp.read(asset.asset_src)
            .then(img => {

                imageCache[asset.asset_id] = img;
                asset.img = img;
                asset.height = img.bitmap.height;
                asset.width = img.bitmap.width;
                console.log('Image downloaded (height, width):', asset.height, asset.width);
                resolve(asset);
                return asset;
            }).catch(err => {
                console.error('Failed to download image:', err);
                reject(err);
                throw err;
            });
    }
};
