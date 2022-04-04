console.log("TEST");

const blah = document.createElement("div");
const blahText = document.createElement('p');
blahText.innerHTML = "TEST TEXT";
blah.appendChild(blahText);

document.body.prepend(blah);
console.log("DONE");