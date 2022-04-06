chrome.runtime.onMessage.addListener(
    function (request, sender, sendResponse) {
        const url = new URL('http://127.0.0.1:8000/analytics/');
        url.search = new URLSearchParams(request).toString();
        fetch(url)
            .then(response => response.text())
            .then(text => sendResponse(text));
        return true;
    }
);