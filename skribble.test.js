var _ = require('lodash');
var skribbleProcessor = require('./src/processor').skribbleProcessor;
// require('./src/logger.js');

var processSkribble = (id, url, postback) => {
    return Promise.resolve(skribbleProcessor(id, url, postback));
};

processSkribble(
    "4da292e4-e18d-11e6-97fb-06569ea6affe",
    "https://api-qa.changemyworldnow.com/user/14bee4e8-55db-11e6-82b1-ded8a5ac776a/skribble/4da292e4-e18d-11e6-97fb-06569ea6affe",
    "https://api-qa.changemyworldnow.com/user/14bee4e8-55db-11e6-82b1-ded8a5ac776a/skribble/4da292e4-e18d-11e6-97fb-06569ea6affe/notice"
)
    .catch(console.error);

// processSkribble(
//     "7c6c7c2a-e197-11e6-89d3-06569ea6affe",
//     "https://api-qa.changemyworldnow.com/user/14bee4e8-55db-11e6-82b1-ded8a5ac776a/skribble/7c6c7c2a-e197-11e6-89d3-06569ea6affe",
//     "https://api-qa.changemyworldnow.com/user/14bee4e8-55db-11e6-82b1-ded8a5ac776a/skribble/7c6c7c2a-e197-11e6-89d3-06569ea6affe/notice"
// )
//     .catch(console.error);
