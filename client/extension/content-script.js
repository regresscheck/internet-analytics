console.log("TEST");

chrome.runtime.sendMessage({}, function (response) {
    console.log(response);
});

const blah = document.createElement("div");
const blahText = document.createElement('p');
blahText.innerHTML = "TEST TEXT";
blah.appendChild(blahText);

document.body.prepend(blah);
console.log("DONE");