function getTJournalEntityUrl(element) {
    const TJOURNAL_USER_HREF_PREFIX = 'https://tjournal.ru/u/'
    if (element.tagName === 'DIV' && element.classList.contains('content-header-author__name')
        && element.parentElement.href.startsWith(TJOURNAL_USER_HREF_PREFIX)) {
        return element.parentElement.href;
    }
    if (element.tagName === 'A' && element.classList.contains('comment__author')
        && element.href.startsWith(TJOURNAL_USER_HREF_PREFIX)) {
        return element.href;
    }
    return null;
}


function getPikabuEntityUrl(element) {
    if (element.tagName == 'A' && element.classList.contains('story__user-link')) {
        return element.href;
    }
    const parent = element.parentElement;
    if (
        element.tagName === 'SPAN'
        && element.classList.contains('user__nick')
        && parent !== null
        && parent.tagName === 'A'
    ) {
        return parent.href;
    }
    return null;
}

const domainToResolver = {
    'tjournal.ru': getTJournalEntityUrl,
    'pikabu.ru': getPikabuEntityUrl
}

function getEntityUrlIfExists(element) {
    const domain = window.location.hostname;
    if (!domainToResolver.hasOwnProperty(domain)) {
        return null;
    }
    const getUrlFunction = domainToResolver[domain];
    return getUrlFunction(element);
}