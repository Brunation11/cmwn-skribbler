'use strict';
const _     = require('lodash');
let jimp    = require('jimp');
const Asset = require('./asset').Asset;

const imageWidth = 1280;
const imageHeight = 720;

const rotateImage = (asset) => {
    const radians = asset.rotation;
    const degrees = radians * (180 / Math.PI);

    console.log('Scale image degrees:', asset.asset_id, asset.rotation, degrees);
    asset.img = asset.img.rotate(degrees, false);
    return asset;
};

const resizeImage = (asset) => {
    const assetWidth  = asset.img.bitmap.width;
    const assetHeight = asset.img.bitmap.height;
    const widthDiff   = imageWidth - assetWidth;
    const heightDiff  = imageHeight - assetHeight;

    let newWidth     = imageWidth;
    let newHeight    = imageHeight;

    console.log('Resize background',
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

const cropImage = (asset) => {
    const assetWidth  = asset.img.bitmap.width;
    const assetHeight = asset.img.bitmap.height;

    const left = Math.round((assetWidth - imageWidth) / 2);
    const top = Math.round((assetHeight - imageHeight) / 2);
    const right = imageWidth + left;
    const bottom = imageHeight + top;

    console.log('Cropping background:',
            '(h , w)', assetHeight, assetHeight,
            '(top, left, right, bottom)', left, top, right, bottom
    );

    asset.img = asset.img.crop(left, top, right, bottom);
    return asset;
};

const processBackground = (asset) => {
    if (asset.width < imageWidth || asset.height < imageHeight) {
        return resizeImage(asset);
    }

    return cropImage(asset);
};

const scaleImage = (asset) => {
    const scale          = parseFloat(asset.scale);
    const originalWidth  = asset.width;
    const originalHeight = asset.height;
    let newWidth         = originalWidth;
    let newHeight        = originalHeight;
    console.log('Scale Image:', asset.asset_id,
                'asset.scale', asset.scale,
                'local scale', scale,
                'asset type', asset.type);

    if (asset.type === 'background') {
        return processBackground(asset);
    }

    if (scale > 0) {
        console.log('Do Scale Image:', asset.asset_id, asset.scale, scale);
        asset.img = asset.img.scale(scale);
        newHeight = Math.round(originalHeight * scale);
        newWidth  = Math.round(originalWidth * scale);
    }

    // image has shrunk
    if ((originalHeight > newHeight) && (originalWidth > newWidth)) {
        console.log('Asset has shrunk:', asset.asset_id,
                    'original (h, w)', originalHeight, originalWidth,
                    'new (h, w)', newHeight, newWidth);

        const widthDiff  = originalWidth - newWidth;
        const heightDiff = originalWidth - newHeight;
        const newLeft    = parseFloat(asset.left) + (widthDiff / 2);
        const newTop     = parseFloat(asset.top) + (heightDiff / 2);

        console.log('New Position:', asset.asset_id,
                    'diff:', heightDiff, widthDiff,
                    '(top, left)', asset.top, asset.left,
                    'new (top, left):', newTop, newLeft);
        asset.left = newLeft;
        asset.top  = newTop;
    }

    console.log('Done Scale Image:', asset.asset_id, asset.scale, scale);
    return asset;
};

module.exports = {
    placeImage: (asset, baseAsset) => {
        const x = parseFloat(asset.left || 0);
        const y = parseFloat(asset.top || 0);

        return baseAsset.img.composite(asset.img, x, y);
    },

    getBaseImage: (resolve, reject) => {
        const asset = new Asset();
        return jimp.read('blank.png')
            .then(img => {
                asset.img    = img;
                asset.layer  = -1;
                asset.height = img.bitmap.height;
                asset.width  = img.bitmap.width;
                resolve(asset);
                return asset;
            })
            .catch(err => {
                console.error('Failed to open blank image:', err);
                reject(err);
                throw err;
            });
    },

    processImage: (asset, resolve, reject) => {
        return new Promise((imgResolve, imgReject) => {
            console.log('Processing asset', asset.asset_id);
            if (!_.has(asset, 'img') || asset.img === null) {
                imgReject('Cannot process asset without an image');
                throw Error('Cannot process asset without an image');
            }

            imgResolve(asset);
            return asset;
        })
            .then(asset => {
                return scaleImage(asset);
            })
            .then(asset => {
                return rotateImage(asset);
            })
            .then(image => {
                console.log('Done processing image');
                resolve(asset);
                return asset;
            })
            .catch(err => {
                console.log('Error processing asset:', asset.asset_id, 'reason', err);
                reject(err);
                throw err;
            });
    }
};

