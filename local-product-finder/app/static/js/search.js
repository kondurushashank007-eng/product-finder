/**
 * Local Product Finder - Customer Search & Filtering Controller
 */

document.addEventListener("DOMContentLoaded", () => {
  initSearchSorting();
  initFilterToggles();
  initBarcodeHelper();
});

function initSearchSorting() {
  const sortSelect = document.getElementById("sortSelect");
  if (sortSelect) {
    sortSelect.addEventListener("change", function () {
      const url = new URL(window.location.href);
      url.searchParams.set("sort_by", this.value);
      url.searchParams.set("page", "1");
      window.location.href = url.toString();
    });
  }
}

function initFilterToggles() {
  const filterForm = document.getElementById("filterForm");
  const clearFiltersBtn = document.getElementById("clearFiltersBtn");

  if (clearFiltersBtn) {
    clearFiltersBtn.addEventListener("click", () => {
      const url = new URL(window.location.href);
      const query = url.searchParams.get("q") || "";
      const lat = url.searchParams.get("lat") || "";
      const lng = url.searchParams.get("lng") || "";
      const locName = url.searchParams.get("location_name") || "";

      let cleanUrl = `/search?q=${encodeURIComponent(query)}`;
      if (lat && lng) {
        cleanUrl += `&lat=${lat}&lng=${lng}&location_name=${encodeURIComponent(locName)}`;
      }
      window.location.href = cleanUrl;
    });
  }
}

function initBarcodeHelper() {
  const scanBtn = document.getElementById("barcodeSimulateBtn");
  const barcodeInput = document.getElementById("barcodeInput");

  if (scanBtn && barcodeInput) {
    scanBtn.addEventListener("click", () => {
      // Pick a sample demo barcode
      const sampleBarcodes = [
        "7350053850011", // Organic Milk
        "8901234567891", // Basmati Rice
        "0123456789021", // USB-C Charger
        "5012345678903", // Paracetamol
        "8859112345674"  // Cordless Drill
      ];
      const randomBarcode = sampleBarcodes[Math.floor(Math.random() * sampleBarcodes.length)];
      barcodeInput.value = randomBarcode;
      
      // Auto-submit search form if present
      const parentForm = barcodeInput.closest("form");
      if (parentForm) {
        parentForm.submit();
      }
    });
  }
}
