/* Passive availability checks. ES5 syntax, no dynamic code or resource loading. */
(function () {
    'use strict';
    var d = window.document;
    var run = d.getElementById('run');
    var output = d.getElementById('output');
    var status = d.getElementById('status');
    function safe(test) {
        try { return Boolean(test()); } catch (ignore) { return 'error'; }
    }
    function available(name, kind) {
        return safe(function () { return typeof window[name] === kind; });
    }
    run.onclick = function () {
        var firmware = d.getElementById('firmware').value;
        output.value = '';
        d.getElementById('summary').textContent = '';
        if (!/^\d{1,2}\.\d{2}$/.test(firmware)) {
            status.textContent = 'Correct the firmware label, for example 14.10.';
            return;
        }
        status.textContent = 'Checking passive capabilities...';
        var features = {};
        var functions = ['Promise', 'Map', 'Set', 'Symbol', 'BigInt', 'ArrayBuffer', 'Uint8Array', 'TextEncoder', 'FontFace', 'TransformStream'];
        var i, ua = 'unavailable';
        for (i = 0; i < functions.length; i += 1) {
            features[functions[i]] = available(functions[i], 'function');
        }
        features.WebAssembly = safe(function () { return !!window.WebAssembly; });
        features.fontSet = safe(function () { return !!d.fonts && typeof d.fonts.check === 'function'; });
        features.cssGrid = safe(function () { return !!window.CSS && typeof window.CSS.supports === 'function' && window.CSS.supports('display', 'grid'); });
        features.cssFontFamily = safe(function () { return !!window.CSS && typeof window.CSS.supports === 'function' && window.CSS.supports('font-family', 'sans-serif'); });
        features.secureContext = safe(function () { return window.isSecureContext === true; });
        try { ua = String(window.navigator.userAgent).slice(0, 1024); } catch (ignore) {}
        var record = {schema: 'ps5-browser-diagnostic/1', diagnostic_version: '1.0', status: 'complete',
            firmware_label: firmware, captured_at: new Date().toISOString(), user_agent: ua, features: features};
        var lines = ['PASSIVE CHECKS COMPLETE', 'Firmware label: ' + firmware, 'UA: ' + ua];
        for (var key in features) {
            if (Object.prototype.hasOwnProperty.call(features, key)) { lines.push(key + ': ' + features[key]); }
        }
        lines.push('Capability observations only. Target patch state and native/kernel execution UNKNOWN.');
        output.value = JSON.stringify(record, null, 2);
        d.getElementById('summary').textContent = lines.join('\n');
        status.textContent = 'Complete. Photograph the summary or copy JSON. Nothing was uploaded.';
    };
    d.getElementById('select').onclick = function () { output.focus(); output.select(); };
}());
