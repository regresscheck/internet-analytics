chrome.runtime.onMessage.addListener(
    function (request, sender, sendResponse) {
        fetch('http://127.0.0.1')
            .then(response => response.text())
            .then(text => sendResponse(text));
        return true;
    }
);