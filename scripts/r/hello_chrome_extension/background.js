function reddenPage() {
  document.body.style.backgroundColor = "green";
}

chrome.action.onClicked.addListener((tab) => {
  if (!tab.url.includes("chrome://")) {
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      function: reddenPage,
    });
  }

  chrome.runtime.reload();
});

// chrome.runtime.onInstalled.addListener(() => {
//   console.log("onInstalled...");
//   chrome.alarms.create("refresh", { when: Date.now() + 2000 });
// });

// chrome.alarms.onAlarm.addListener(() => {
//   chrome.runtime.reload();
// });
