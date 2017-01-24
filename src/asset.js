'use strict';
const _     = require('lodash');

/**
 * A Specification of an asset
 *
 * @param {String} asset_id
 * @param {String} asset_src
 * @param {Number} left
 * @param {Number} top
 * @param {Number} scale
 * @param {Number} rotation
 * @param {Number} layer
 * @param {Boolean} can_overlap
 * @param {Number} height
 * @param {Number} width
 * @param {Number[]} corners
 * @param {String} hash_type
 * @param {String} hash_value
 * @param {Object} img
 */
let Asset = function(
    asset_id,
    asset_src,
    left,
    top,
    scale,
    rotation,
    layer,
    can_overlap,
    height,
    width,
    corners,
    hash_type,
    hash_value,
    img,
    type
) {
    this.asset_id    = _.defaultTo(asset_id, null);
    this.asset_src   = _.defaultTo(asset_src, null);
    this.left        = _.defaultTo(left, 0);
    this.top         = _.defaultTo(top, 0);
    this.scale       = _.defaultTo(scale, 0);
    this.rotation    = _.defaultTo(rotation, 0);
    this.layer       = _.defaultTo(layer, 0);
    this.can_overlap = _.defaultTo(can_overlap, false);
    this.height      = _.defaultTo(height, 0);
    this.width       = _.defaultTo(width, 0);
    this.corners     = _.defaultTo(corners, []);
    this.hash_type   = _.defaultTo(hash_type, 'md5');
    this.hash_value  = _.defaultTo(hash_value, null);
    this.img         = _.defaultTo(img, null);
    this.type        = _.defaultTo(type, null);
};

module.exports = {
    Asset
};
