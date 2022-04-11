var currentUITarget = null;

const analyticsDiv = document.createElement("div");
analyticsDiv.setAttribute("id", "analytics-info")
analyticsDiv.innerHTML = '<table id="analytics-table"><thead><tr><th>Property</th><th>Value</th></tr></thead><tbody id="analytics-table-body"></tbody></table>'
document.body.append(analyticsDiv);
const analyticsTableBody = document.getElementById('analytics-table-body');

function isTJournalAuthorDIV(element) {
    return element.tagName === 'DIV' && element.classList.contains(TJOURNAL_AUTHOR_DIV_CLASS)
        && element.parentElement.href.startsWith(TJOURNAL_USER_HREF_PREFIX);;
}

function isTJournalAuthorA(element) {
    return element.tagName === 'A' && element.classList.contains(TJOURNAL_AUTHOR_A_CLASS)
        && element.href.startsWith(TJOURNAL_USER_HREF_PREFIX);
}

function clearUI() {
    analyticsDiv.style.display = "none";
    currentUITarget = null;
}

function createRow(values) {
    const tr = document.createElement('tr');
    for (var i = 0; i < values.length; i++) {
        const td = document.createElement('td');
        td.innerText = values[i];
        tr.append(td);
    }
    return tr;
}

function updateTable(data) {
    analyticsTableBody.innerHTML = ''
    for (const [key, value] of Object.entries(data)) {
        analyticsTableBody.append(createRow([key, value]));
    }
}

function enableUI(element, url) {
    clearUI();
    currentUITarget = element;
    const request = {
        "entity_url": url,
    }
    chrome.runtime.sendMessage(request, function (response) {
        analyticsDiv.style.display = "block";
        updateTable(JSON.parse(response));

        const elementPosition = element.getBoundingClientRect();
        const absoluteTop = window.pageYOffset + elementPosition.top;
        const absoluteLeft = window.pageXOffset + elementPosition.left;
        analyticsDiv.style.top = (absoluteTop - analyticsDiv.offsetHeight - 15) + "px";
        analyticsDiv.style.left = absoluteLeft + "px";
    })
}

document.addEventListener('mousemove', function (e) {
    var target = e.target;
    if (target === currentUITarget) {
        return;
    }
    const url = getEntityUrlIfExists(target);
    if (url !== null) {
        enableUI(target, url);
    } else {
        clearUI();
    }
}, false);