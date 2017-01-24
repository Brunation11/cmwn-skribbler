'use strict';
const logger     = require('./logger.js').logger;
const _          = require('lodash');
const fs         = require('fs');
const path       = require('path');
const configFile = path.resolve(__dirname, '../config.json');
const config     = JSON.parse(fs.readFileSync(configFile, 'utf8'));
const AWS        = require('aws-sdk');
const s3         = new AWS.S3();
const bucketName = config.aws.bucket_name;
const jimp       = require('jimp');

module.exports = {
    /**
     * Uploads the asset to aws
     * @param asset
     * @param resolve
     * @param reject
     * @returns {Promise.<T>}
     */
    uploadAsset: (asset, resolve, reject) => {
        return new Promise((awsResolve, awsReject) => {
            asset.img.getBuffer(jimp.MIME_PNG, (err, buffer) => {
                if (err) {
                    throw Error(err);
                }

                const params = {
                    Bucket: bucketName,
                    Key: asset.asset_id + '.png',
                    Body: buffer,
                    ContentType: jimp.MIME_PNG,
                    CacheControl: 'max-age=345600',
                    ACL: 'public-read'
                };

                s3.putObject(params, (err, data) => {
                    if (err) {
                        awsReject(Error(err));
                        throw Error(err);
                    }

                    console.log('info', 'Successfully uploaded data to s3');
                    awsResolve(asset);
                });
            });

        })
        .then(resolve)
        .catch(err => {
            logger.error('Failed to upload asset to s3: ', err);
            reject(err);
            throw err;
        });
    }
};