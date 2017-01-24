'use strict';

const util = require('util');
const rollbar = require('rollbar');
const fs = require('fs');
const path = require('path');
const configFile = path.resolve(__dirname, '../config.json');
const config = JSON.parse(fs.readFileSync(configFile, 'utf8'));

rollbar.init(config.token, {
    environment: config.env,
    minimumLevel: config.level || 'error',
    enabled: false
});

function formatArgs(args){
    return [util.format.apply(util.format, Array.prototype.slice.call(args))];
}

function doLog(level, args) {

}

(() => {
    // Save the original method in a private variable
    var _log = console.log;
    var _error = console.error;
    var _warning = console.warning;

    // Redefine console.log method with a custom function
    console.log = () => {
        // Here execute something with the given message or arguments variable
        // alert("Our Custom Log Says: " + message);

        /**
         Note: If you want to preserve the same action as the original method does
         then use the following line :

         we use apply to invoke the method on console using the original arguments.
         Simply calling _privateLog(message) would fail because LOG depends on the console
         */
        _log.apply(console, arguments);
    };
})();