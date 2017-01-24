var logger = require('./logger.js').logger;
var _           = require('lodash');
var Asset       = require('./asset').Asset;
var utils       = require('skribble-utils');
var jimp        = require('jimp');
var imageWidth  = 1280;
var imageHeight = 720;

/**
 * Rotates the image in the asset
 *
 * @param asset
 * @returns {*}
 */
var rotateImage = function(asset) {
    var radians = asset.rotation;
    var degrees = radians * (180 / Math.PI);

    logger.log('debug','Scale image degrees:', asset.asset_id, asset.rotation, degrees);
    asset.img = asset.img.rotate(degrees, false);
    return asset;
};

/**
 * Resizes the image in the asset
 *
 * @param asset
 * @returns {*}
 */
var resizeImage = function(asset) {
    var assetWidth  = asset.img.bitmap.width;
    var assetHeight = asset.img.bitmap.height;
    var widthDiff   = imageWidth - assetWidth;
    var heightDiff  = imageHeight - assetHeight;

    var newWidth     = imageWidth;
    var newHeight    = imageHeight;

    logger.log('debug','Resize background',
                '(h, w)', assetWidth, assetHeight,
                'diff:', widthDiff, heightDiff);

    if (widthDiff > heightDiff) {
        newHeight = Math.round((assetHeight * imageHeight) / assetWidth);
    } else {
        newWidth = Math.round((assetWidth * imageWidth) / assetHeight);
    }

    asset.img    = asset.img.resize(newWidth, newHeight, jimp.RESIZE_BICUBIC);
    asset.height = newHeight;
    asset.width  = newWidth;
    return asset;
};

/**
 * Crops the asset in the image
 *
 * @param asset
 * @returns {*}
 */
var cropImage = function(asset) {
    var assetWidth  = asset.img.bitmap.width;
    var assetHeight = asset.img.bitmap.height;

    var left = Math.round((assetWidth - imageWidth) / 2);
    var top = Math.round((assetHeight - imageHeight) / 2);
    var right = imageWidth + left;
    var bottom = imageHeight + top;

    logger.log('debug','Cropping background:',
            '(h , w)', assetHeight, assetHeight,
            '(top, left, right, bottom)', left, top, right, bottom
    );

    asset.img = asset.img.crop(left, top, right, bottom);
    return asset;
};

/**
 * Background needs some special processing to fill the canvas correctly
 *
 * This will either scale or crop the background to fill the canvas
 *
 * @param asset
 */
var processBackground = function(asset) {
    if (asset.width < imageWidth || asset.height < imageHeight) {
        return resizeImage(asset);
    }

    return cropImage(asset);
};

/**
 * Scales the asset image
 *
 * @param asset
 * @returns {*}
 */
var scaleImage = function(asset) {
    var scale          = parseFloat(asset.scale);
    var originalWidth  = asset.width;
    var originalHeight = asset.height;
    var newWidth         = originalWidth;
    var newHeight        = originalHeight;
    logger.log('debug', 'Scale Image:', asset.asset_id,
                'asset.scale', asset.scale,
                'local scale', scale,
                'asset type', asset.type);

    if (asset.type === 'background') {
        return processBackground(asset);
    }

    if (scale > 0) {
        logger.log('debug','Do Scale Image:', asset.asset_id, asset.scale, scale);
        asset.img = asset.img.scale(scale);
        newHeight = Math.round(originalHeight * scale);
        newWidth  = Math.round(originalWidth * scale);
    }

    // image has shrunk
    if ((originalHeight > newHeight) && (originalWidth > newWidth)) {
        logger.log('debug','Asset has shrunk:', asset.asset_id,
                    'original (h, w)', originalHeight, originalWidth,
                    'new (h, w)', newHeight, newWidth);

        var widthDiff  = originalWidth - newWidth;
        var heightDiff = originalWidth - newHeight;
        var newLeft    = parseFloat(asset.left) + (widthDiff / 2);
        var newTop     = parseFloat(asset.top) + (heightDiff / 2);

        logger.log('debug','New Position:', asset.asset_id,
                    'diff:', heightDiff, widthDiff,
                    '(top, left)', asset.top, asset.left,
                    'new (top, left):', newTop, newLeft);
        asset.left = newLeft;
        asset.top  = newTop;
    }

    logger.log('verbose', 'Done Scaling asset:', asset.asset_id);
    return asset;
};

module.exports = {
    /**
     * Puts an image on another iamge
     * @param asset
     * @param baseAsset
     * @returns {this}
     */
    placeImage: function(asset, baseAsset) {
        var x = parseFloat(asset.left || 0);
        var y = parseFloat(asset.top || 0);

        return baseAsset.img.composite(asset.img, x, y);
    },

    /**
     * Gets the base image we will be using
     *
     * @param resolve
     * @param reject
     * @returns {Promise.<TResult>}
     */
    getBaseImage: function(resolve, reject) {
        var asset = new Asset();
        return jimp.read('blank.png')
            .then(function(img) {
                asset.img    = img;
                asset.layer  = -1;
                asset.height = img.bitmap.height;
                asset.width  = img.bitmap.width;
                resolve(asset);
                return asset;
            })
            .catch(function(err) {
                logger.error('Failed to open blank image:', err);
                reject(err);
                throw err;
            });
    },

    /**
     * Scale and rotate the image
     *
     * @param asset
     * @param resolve
     * @param reject
     * @returns {Promise.<TResult>}
     */
    processImage: (asset, resolve, reject) => {
        return new Promise((imgResolve, imgReject) => {
            logger.log('info','Processing asset', asset.asset_id);
            if (!_.has(asset, 'img') || asset.img === null) {
                imgReject('Cannot process asset without an image');
                throw Error('Cannot process asset without an image');
            }

            imgResolve(asset);
            return asset;
        })
            .then(function(asset) {
                return scaleImage(asset);
            })
            .then(function(asset) {
                return rotateImage(asset);
            })
            .then(function(asset) {
                logger.log('verbose','Adding corners:', asset.asset_id);

                asset.corners = utils.getAssetCorners(asset);
                return asset;
            })
            .then(function(asset) {
                logger.log('verbose','Done Processing asset', asset.asset_id);
                resolve(asset);
                return asset;
            })
            .catch(function(err) {
                logger.error('Error processing asset:', asset.asset_id, 'reason', err);
                reject(err);
                throw err;
            });
    }
};

