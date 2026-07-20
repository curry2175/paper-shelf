let metadata = null;
let bookshelfUrl = "";

/**
 * This function is injected into the active webpage.
 * It must be fully self-contained because Chrome serializes only this function,
 * not helper functions declared in the extension popup context.
 */
function extractPaperMetadataFromPage() {
  function firstMeta(selectors) {
    for (const selector of selectors) {
      const element = document.querySelector(selector);
      if (!element) continue;
      const value = element.getAttribute("content") || element.textContent || "";
      if (value.trim()) return value.trim();
    }
    return "";
  }

  function normalizeDoi(value) {
    return String(value || "")
      .trim()
      .replace(/^https?:\/\/(?:dx\.)?doi\.org\//i, "")
      .replace(/^doi:\s*/i, "")
      .trim();
  }

  function cleanTitle(value) {
    return String(value || "")
      .replace(/\s*[|\-–—]\s*PubMed\s*$/i, "")
      .replace(/\s+/g, " ")
      .trim();
  }

  const sourceUrl = location.href;
  const pubmedMatch = sourceUrl.match(/pubmed\.ncbi\.nlm\.nih\.gov\/(\d+)/i);
  const legacyPubmedMatch = sourceUrl.match(/ncbi\.nlm\.nih\.gov\/pubmed\/(\d+)/i);

  const pmid =
    (pubmedMatch && pubmedMatch[1]) ||
    (legacyPubmedMatch && legacyPubmedMatch[1]) ||
    firstMeta([
      'meta[name="citation_pmid"]',
      'meta[name="pmid"]',
      'meta[name="ncbi_pmid"]'
    ]);

  let doi = firstMeta([
    'meta[name="citation_doi"]',
    'meta[name="dc.identifier"]',
    'meta[name="DC.Identifier"]',
    'meta[property="bepress_citation_doi"]',
    'meta[name="prism.doi"]'
  ]);

  if (!doi) {
    const doiLink = document.querySelector('a[href*="doi.org/"]');
    doi = doiLink?.href || "";
  }
  doi = normalizeDoi(doi);

  const title = cleanTitle(
    firstMeta([
      'meta[name="citation_title"]',
      'meta[property="og:title"]',
      'meta[name="dc.title"]',
      'meta[name="DC.Title"]',
      'meta[name="twitter:title"]',
      'main h1',
      'article h1',
      'h1'
    ]) || document.title
  );

  const journal = firstMeta([
    'meta[name="citation_journal_title"]',
    'meta[name="prism.publicationName"]',
    'meta[name="dc.source"]',
    'meta[name="DC.Source"]'
  ]);

  return {
    pmid: String(pmid || "").trim(),
    doi,
    title,
    journal: String(journal || "").trim(),
    source_url: sourceUrl
  };
}

function parsePmidFromUrl(url) {
  const match = String(url || "").match(
    /(?:pubmed\.ncbi\.nlm\.nih\.gov\/|ncbi\.nlm\.nih\.gov\/pubmed\/)(\d+)/i
  );
  return match ? match[1] : "";
}

function cleanTabTitle(value) {
  return String(value || "")
    .replace(/\s*[|\-–—]\s*PubMed\s*$/i, "")
    .replace(/\s+/g, " ")
    .trim();
}

function setStatus(message, type = "") {
  const status = document.getElementById("status");
  status.textContent = message;
  status.className = type;
}

async function readCurrentTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) throw new Error("현재 탭을 확인하지 못했습니다.");

  const tabUrl = tab.url || "";
  if (/^(chrome|edge|about|chrome-extension):/i.test(tabUrl)) {
    throw new Error("Chrome 설정 페이지에서는 논문 정보를 읽을 수 없습니다. PubMed 또는 저널 논문 페이지를 열어주세요.");
  }

  const fallback = {
    pmid: parsePmidFromUrl(tabUrl),
    doi: "",
    title: cleanTabTitle(tab.title),
    journal: "",
    source_url: tabUrl
  };

  try {
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: extractPaperMetadataFromPage
    });
    const pageMetadata = results[0]?.result || {};

    return {
      pmid: pageMetadata.pmid || fallback.pmid,
      doi: pageMetadata.doi || fallback.doi,
      title: pageMetadata.title || fallback.title,
      journal: pageMetadata.journal || fallback.journal,
      source_url: pageMetadata.source_url || fallback.source_url
    };
  } catch (error) {
    // PubMed can still be saved using the PMID parsed from the address bar.
    if (fallback.pmid) return fallback;
    throw new Error(`현재 페이지 내용을 읽지 못했습니다: ${error.message}`);
  }
}

async function loadPaper() {
  try {
    metadata = await readCurrentTab();
    if (!metadata || (!metadata.pmid && !metadata.doi && !metadata.title)) {
      throw new Error("이 페이지에서 논문 정보를 찾지 못했습니다.");
    }

    document.getElementById("paper-box").classList.remove("loading");
    document.getElementById("paper-title").textContent = metadata.title || "제목은 저장할 때 PubMed에서 확인합니다.";

    const identifiers = [
      metadata.journal,
      metadata.pmid ? `PMID ${metadata.pmid}` : "",
      metadata.doi ? `DOI ${metadata.doi}` : ""
    ].filter(Boolean);

    document.getElementById("paper-meta").textContent =
      identifiers.join(" · ") || "제목으로 PubMed에서 논문을 확인합니다.";
    document.getElementById("save-button").disabled = false;
    setStatus("");
  } catch (error) {
    document.getElementById("paper-title").textContent = "논문 정보를 찾지 못했습니다.";
    document.getElementById("paper-meta").textContent = "PubMed 논문 페이지 또는 DOI 메타데이터가 있는 저널 페이지에서 다시 시도해주세요.";
    setStatus(error.message, "error");
  }
}

async function savePaper() {
  const { siteUrl = "", apiToken = "" } = await chrome.storage.local.get(["siteUrl", "apiToken"]);
  if (!siteUrl || !apiToken) {
    setStatus("먼저 연결 설정에서 웹사이트 주소와 토큰을 저장해주세요.", "error");
    return;
  }

  const button = document.getElementById("save-button");
  button.disabled = true;
  button.textContent = "책장에 저장 중…";
  setStatus("");

  try {
    const endpoint = `${siteUrl.replace(/\/$/, "")}/papers/api/reading-records/`;
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiToken}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        ...metadata,
        note: document.getElementById("note").value.trim(),
        read_at: new Date().toISOString()
      })
    });

    let result;
    try {
      result = await response.json();
    } catch (_) {
      throw new Error(`웹사이트가 올바른 응답을 보내지 않았습니다. (${response.status})`);
    }

    if (!response.ok || !result.ok) {
      throw new Error(result.error || `저장에 실패했습니다. (${response.status})`);
    }

    bookshelfUrl = result.bookshelf_url || `${siteUrl.replace(/\/$/, "")}/papers/bookshelf/`;
    setStatus(result.message, "success");
    button.textContent = result.created ? "책장에 추가됨 ✓" : "이미 책장에 있음 ✓";
    document.getElementById("bookshelf-button").hidden = false;
  } catch (error) {
    setStatus(error.message, "error");
    button.disabled = false;
    button.textContent = "다시 저장하기";
  }
}

document.getElementById("save-button").addEventListener("click", savePaper);
document.getElementById("settings-button").addEventListener("click", () => chrome.runtime.openOptionsPage());
document.getElementById("bookshelf-button").addEventListener("click", () => {
  if (bookshelfUrl) chrome.tabs.create({ url: bookshelfUrl });
});

loadPaper();
