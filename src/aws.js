var logger     = require('./logger.js').logger;
var _          = require('lodash');
var fs         = require('fs');
var path       = require('path');
var configFile = path.resolve(__dirname, '../config.json');
var config     = JSON.parse(fs.readFileSync(configFile, 'utf8'));
var AWS        = require('aws-sdk');
var s3         = new AWS.S3();
var bucketName = config.aws.bucket_name;
var jimp       = require('jimp');

module.exports = {
    /**
     * Uploads the asset to aws
     * @param asset
     * @param resolve
     * @param reject
     * @returns {Promise.<T>}
     */
    uploadAsset: function(asset, resolve, reject) {
        return new Promise((awsResolve, awsReject) => {
            asset.img.getBuffer(jimp.MIME_PNG, (err, buffer) => {
                if (err) {
                    throw Error(err);
                }

                var params = {
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
        .catch(function(err) {
            logger.error('Failed to upload asset to s3: ', err);
            reject(err);
            throw err;
        });
    }
};