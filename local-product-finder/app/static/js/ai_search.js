/**
 * Local Product Finder - AI Natural Language Search Controller
 */

document.addEventListener("DOMContentLoaded", () => {
  initAiSearch();
});

function initAiSearch() {
  const aiSearchForm = document.getElementById("aiSearchForm");
  const aiInput = document.getElementById("aiSearchInput");
  const aiFeedbackArea = document.getElementById("aiFeedbackArea");
  const samplePrompts = document.querySelectorAll(".ai-sample-prompt");

  // Sample prompt clicks
  samplePrompts.forEach((btn) => {
    btn.addEventListener("click", () => {
      const promptText = btn.getAttribute("data-prompt");
      if (aiInput && promptText) {
        aiInput.value = promptText;
        executeAiSearch(promptText);
      }
    });
  });

  if (aiSearchForm) {
    aiSearchForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const query = aiInput.value.trim();
      if (query) {
        executeAiSearch(query);
      }
    });
  }

  async function executeAiSearch(query) {
    if (!aiFeedbackArea) return;

    // Show loading indicator
    aiFeedbackArea.innerHTML = `
      <div class="ai-breakdown-card" style="display:flex; align-items:center; gap:0.75rem;">
        <span class="badge badge-demo">AI Interpreter</span>
        <span>Analyzing query: <em>"${query}"</em>...</span>
      </div>
    `;

    // Retrieve lat/lng
    const lat = localStorage.getItem("lpf_user_lat") || 37.7749;
    const lng = localStorage.getItem("lpf_user_lng") || -122.4194;

    try {
      const response = await fetch("/api/ai-search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query, lat: lat, lng: lng })
      });

      const data = await response.json();

      if (!data.success) {
        aiFeedbackArea.innerHTML = `
          <div class="alert alert-danger">
            ${data.error || "Could not process AI search query."}
          </div>
        `;
        return;
      }

      // 1. Ambiguity handling
      if (data.is_ambiguous && data.clarification) {
        const clar = data.clarification;
        let optionsHtml = clar.options
          .map(
            (opt) => `
            <button type="button" class="btn btn-outline btn-sm ai-clarify-choice" data-choice="${opt}">
              ${opt}
            </button>
          `
          )
          .join("");

        aiFeedbackArea.innerHTML = `
          <div class="clarification-box">
            <strong>🤔 Clarification Needed:</strong>
            <p style="margin-top:0.25rem;">${clar.question}</p>
            <div class="clarification-options">
              ${optionsHtml}
            </div>
          </div>
        `;

        // Bind clarification choice clicks
        aiFeedbackArea.querySelectorAll(".ai-clarify-choice").forEach((btn) => {
          btn.addEventListener("click", () => {
            const chosen = btn.getAttribute("data-choice");
            if (aiInput) {
              aiInput.value = chosen;
              executeAiSearch(chosen);
            }
          });
        });
        return;
      }

      // 2. Clear breakdown with chips
      const parsed = data.parsed;
      let chipsHtml = "";
      if (parsed.product_keyword) {
        chipsHtml += `<span class="ai-chip">Keyword: <strong>${parsed.product_keyword}</strong></span>`;
      }
      if (parsed.brand) {
        chipsHtml += `<span class="ai-chip">Brand: <strong>${parsed.brand}</strong></span>`;
      }
      if (parsed.size) {
        chipsHtml += `<span class="ai-chip">Size: <strong>${parsed.size}</strong></span>`;
      }
      if (parsed.max_price) {
        chipsHtml += `<span class="ai-chip">Max Price: <strong>$${parsed.max_price.toFixed(2)}</strong></span>`;
      }
      if (parsed.in_stock_only) {
        chipsHtml += `<span class="ai-chip">Availability: <strong>In-Stock Only</strong></span>`;
      }
      if (parsed.sort_by === "price_asc") {
        chipsHtml += `<span class="ai-chip">Sort: <strong>Lowest Price First</strong></span>`;
      } else if (parsed.sort_by === "distance") {
        chipsHtml += `<span class="ai-chip">Sort: <strong>Nearest Shops</strong></span>`;
      }

      aiFeedbackArea.innerHTML = `
        <div class="ai-breakdown-card">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="display:flex; align-items:center; gap:0.5rem;">
              <span class="ai-query-badge">✨ AI Parsed Query</span>
              <span style="font-size:0.875rem; color:var(--text-sub);">${data.explanation}</span>
            </div>
            <a href="${data.redirect_url}" class="btn btn-primary btn-sm">
              View All ${data.total_results} Matches &rarr;
            </a>
          </div>
          <div class="ai-chips-container">
            ${chipsHtml}
          </div>
        </div>
      `;

      // Auto-redirect if enter was pressed or user wants direct view
      // Wait 1.2s so user can see what was parsed
      setTimeout(() => {
        window.location.href = data.redirect_url;
      }, 1200);

    } catch (err) {
      aiFeedbackArea.innerHTML = `
        <div class="alert alert-danger">Network error connecting to AI Search engine.</div>
      `;
    }
  }
}
