/**
 * Local Product Finder - Global Application Script
 */

document.addEventListener("DOMContentLoaded", () => {
  initAlertDismissal();
  initLocationManagement();
  initMobileNav();
});

// Auto-dismiss or manual dismiss for flash alerts
function initAlertDismissal() {
  document.querySelectorAll(".alert-close").forEach((btn) => {
    btn.addEventListener("click", function () {
      const alert = this.closest(".alert");
      if (alert) {
        alert.style.opacity = "0";
        setTimeout(() => alert.remove(), 200);
      }
    });
  });
}

// User Location & Geolocation Manager
function initLocationManagement() {
  const locationPill = document.getElementById("navLocationBtn");
  const modal = document.getElementById("locationModal");
  const closeBtn = document.getElementById("closeLocationModal");
  const useGeoBtn = document.getElementById("useGeoBtn");
  const geoStatus = document.getElementById("geoStatus");
  const manualForm = document.getElementById("manualLocationForm");

  // Load stored location if available
  const savedLat = localStorage.getItem("lpf_user_lat");
  const savedLng = localStorage.getItem("lpf_user_lng");
  const savedCity = localStorage.getItem("lpf_user_city");

  if (savedCity && document.getElementById("navLocationText")) {
    document.getElementById("navLocationText").textContent = savedCity;
  }

  if (locationPill && modal) {
    locationPill.addEventListener("click", () => {
      modal.classList.add("active");
    });
  }

  if (closeBtn && modal) {
    closeBtn.addEventListener("click", () => {
      modal.classList.remove("active");
    });
  }

  // HTML5 Geolocation API
  if (useGeoBtn) {
    useGeoBtn.addEventListener("click", () => {
      if (!navigator.geolocation) {
        showGeoStatus("Geolocation is not supported by your browser.", "danger");
        return;
      }

      showGeoStatus("Requesting location access...", "info");
      useGeoBtn.disabled = true;

      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const lat = pos.coords.latitude;
          const lng = pos.coords.longitude;
          showGeoStatus("Location detected! Updating...", "success");

          localStorage.setItem("lpf_user_lat", lat);
          localStorage.setItem("lpf_user_lng", lng);
          localStorage.setItem("lpf_user_city", "Current Location");

          // Update current URL params and reload
          updateLocationParams(lat, lng, "Current Location");
        },
        (err) => {
          useGeoBtn.disabled = false;
          let msg = "Could not obtain location. Please enter your neighborhood manually below.";
          if (err.code === err.PERMISSION_DENIED) {
            msg = "Location permission was denied. Please type your neighborhood or zip code below.";
          }
          showGeoStatus(msg, "warning");
        },
        { timeout: 10000, enableHighAccuracy: true }
      );
    });
  }

  // Manual Address / Neighborhood Geocoding
  if (manualForm) {
    manualForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const input = document.getElementById("manualAddressInput");
      const address = input.value.trim();
      if (!address) return;

      try {
        const res = await fetch("/api/geocode", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ address: address })
        });
        const data = await res.json();
        if (data.success) {
          localStorage.setItem("lpf_user_lat", data.lat);
          localStorage.setItem("lpf_user_lng", data.lng);
          localStorage.setItem("lpf_user_city", data.formatted_address);

          updateLocationParams(data.lat, data.lng, data.formatted_address);
        } else {
          showGeoStatus("Could not find that neighborhood. Try 'Castro', 'Mission', or 'Downtown'.", "danger");
        }
      } catch (err) {
        showGeoStatus("Network error looking up location.", "danger");
      }
    });
  }

  function showGeoStatus(text, type) {
    if (!geoStatus) return;
    geoStatus.className = `alert alert-${type}`;
    geoStatus.textContent = text;
    geoStatus.style.display = "block";
  }

  function updateLocationParams(lat, lng, name) {
    const url = new URL(window.location.href);
    url.searchParams.set("lat", lat);
    url.searchParams.set("lng", lng);
    url.searchParams.set("location_name", name);
    url.searchParams.set("page", "1");
    window.location.href = url.toString();
  }
}

// Mobile Navbar Toggle
function initMobileNav() {
  const toggleBtn = document.getElementById("mobileToggle");
  const navMenu = document.getElementById("navLinks");
  if (toggleBtn && navMenu) {
    toggleBtn.addEventListener("click", () => {
      const isVisible = navMenu.style.display === "flex";
      navMenu.style.display = isVisible ? "none" : "flex";
      if (!isVisible) {
        navMenu.style.flexDirection = "column";
        navMenu.style.position = "absolute";
        navMenu.style.top = "4.25rem";
        navMenu.style.left = "0";
        navMenu.style.width = "100%";
        navMenu.style.background = "#fff";
        navMenu.style.padding = "1rem";
        navMenu.style.borderBottom = "1px solid var(--border)";
      }
    });
  }
}
