const siteUrlInput = document.getElementById("site-url");
const tokenInput = document.getElementById("api-token");
const status = document.getElementById("status");

chrome.storage.local.get(["siteUrl", "apiToken"]).then(({ siteUrl = "", apiToken = "" }) => {
  siteUrlInput.value = siteUrl;
  tokenInput.value = apiToken;
});

document.getElementById("save-button").addEventListener("click", async () => {
  const siteUrl = siteUrlInput.value.trim().replace(/\/$/, "");
  const apiToken = tokenInput.value.trim();
  if (!/^https?:\/\//i.test(siteUrl)) {
    status.textContent = "웹사이트 주소는 http:// 또는 https://로 시작해야 합니다.";
    return;
  }
  const currentToken = /^ps\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/.test(apiToken);
  const legacyToken = /^ps_.+$/.test(apiToken);
  if (!currentToken && !legacyToken) {
    status.textContent = "올바른 연결 토큰을 입력해주세요. 새 토큰은 ps.으로 시작합니다.";
    return;
  }
  await chrome.storage.local.set({ siteUrl, apiToken });
  status.textContent = "연결 설정을 저장했습니다.";
});
