/**
 * Local Product Finder - Shop Owner Dashboard Controller
 */

document.addEventListener("DOMContentLoaded", () => {
  initQuickStockAdjusters();
  initTableLiveFilter();
  initDeleteConfirmations();
});

function initQuickStockAdjusters() {
  document.querySelectorAll(".quick-stock-btn").forEach((btn) => {
    btn.addEventListener("click", async function (e) {
      e.preventDefault();
      const productId = this.getAttribute("data-product-id");
      const delta = parseInt(this.getAttribute("data-delta"), 10);
      if (!productId || isNaN(delta)) return;

      const row = document.getElementById(`product-row-${productId}`);
      const qtyElem = row ? row.querySelector(".stock-qty-display") : null;
      const badgeElem = row ? row.querySelector(".stock-badge-display") : null;
      const updatedElem = row ? row.querySelector(".stock-updated-display") : null;

      // Disable button briefly
      this.disabled = true;

      try {
        const formData = new FormData();
        formData.append("delta", delta);

        const res = await fetch(`/dashboard/product/${productId}/stock`, {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest"
          },
          body: formData
        });

        const data = await res.json();
        if (data.success) {
          if (qtyElem) qtyElem.textContent = data.new_quantity;
          if (badgeElem) {
            badgeElem.className = `badge ${data.badge_class} stock-badge-display`;
            badgeElem.textContent = data.status_label;
          }
          if (updatedElem) {
            updatedElem.textContent = data.relative_updated;
          }
        }
      } catch (err) {
        console.error("Failed to update stock:", err);
      } finally {
        this.disabled = false;
      }
    });
  });
}

function initTableLiveFilter() {
  const filterInput = document.getElementById("tableSearchInput");
  if (filterInput) {
    filterInput.addEventListener("input", function () {
      const term = this.value.toLowerCase().trim();
      const rows = document.querySelectorAll(".inventory-table-row");
      rows.forEach((row) => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(term) ? "" : "none";
      });
    });
  }
}

function initDeleteConfirmations() {
  document.querySelectorAll(".delete-product-form").forEach((form) => {
    form.addEventListener("submit", function (e) {
      const productName = this.getAttribute("data-product-name") || "this product";
      if (!confirm(`Are you sure you want to remove "${productName}" from your shop's inventory?`)) {
        e.preventDefault();
      }
    });
  });
}
