const TJOURNAL_AUTHOR_TAG = 'content-header-author__name';
const TJOURNAL_USER_HREF_PREFIX = 'https://tjournal.ru/u/'

var currentUITarget = null;

const analyticsDiv = document.createElement("div");
analyticsDiv.setAttribute("id", "analytics-info")
document.body.append(analyticsDiv);


function isTJournalUserElement(element) {
    if (element.tagName !== 'DIV' || !element.classList.contains(TJOURNAL_AUTHOR_TAG)) {
        return false;
    }
    const url = element.parentElement.href;
    return url.startsWith(TJOURNAL_USER_HREF_PREFIX);
}

function clearUI() {
    analyticsDiv.style.display = "none";
    currentUITarget = null;
}

function enableUI(element, url) {
    clearUI();
    currentUITarget = element;
    const request = {
        "entity_url": url,
    }
    chrome.runtime.sendMessage(request, function (response) {
        analyticsDiv.innerText = response;
        analyticsDiv.style.display = "block";

        const elementPosition = element.getBoundingClientRect();
        const absoluteTop = window.pageYOffset + elementPosition.top;
        const absoluteLeft = window.pageXOffset + elementPosition.left;
        analyticsDiv.style.top = (absoluteTop - 50) + "px";
        analyticsDiv.style.left = absoluteLeft + "px";
    })
}

document.addEventListener('mousemove', function (e) {
    var target = e.target;
    if (target === currentUITarget) {
        return;
    }
    if (isTJournalUserElement(target)) {
        // Parent element is a link to a user
        const url = target.parentElement.href;
        console.log(url);
        enableUI(target, url);
    } else {
        clearUI();
    }
}, false);