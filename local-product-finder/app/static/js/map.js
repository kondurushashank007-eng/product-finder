/**
 * Local Product Finder - Interactive Store & Coordinate Map Visualizer
 */

function renderShopMap(containerId, shopLat, shopLng, shopName, shopAddress, userLat, userLng) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const encodedDest = encodeURIComponent(`${shopLat},${shopLng}`);
  const mapsUrl = `https://www.google.com/maps/dir/?api=1&destination=${encodedDest}`;

  // Build clean SVG visual map with grid, radar circle, and shop pin
  container.innerHTML = `
    <div style="position:relative; width:100%; height:100%; background:#e2e8f0; border-radius:inherit; overflow:hidden; display:flex; flex-direction:column; justify-content:space-between;">
      <svg width="100%" height="100%" style="position:absolute; top:0; left:0;" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse">
            <path d="M 30 0 L 0 0 0 30" fill="none" stroke="#cbd5e1" stroke-width="1"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="#f1f5f9"/>
        <rect width="100%" height="100%" fill="url(#grid)" />
        
        <!-- Distance concentric circles around shop -->
        <circle cx="50%" cy="45%" r="45" fill="rgba(15, 118, 110, 0.06)" stroke="#0f766e" stroke-width="1" stroke-dasharray="3,3" />
        <circle cx="50%" cy="45%" r="90" fill="rgba(15, 118, 110, 0.03)" stroke="#94a3b8" stroke-width="1" stroke-dasharray="4,4" />

        <!-- Shop Location Pin -->
        <g transform="translate(-16, -36)">
          <path d="M 50% 45% m 16 0 C 16 -8 0 -8 0 -16 C 0 -25 7 -32 16 -32 C 25 -32 32 -25 32 -16 C 32 -8 16 0 16 0 Z" fill="#0f766e"/>
          <circle cx="50%" cy="45%" r="6" fill="#ffffff" transform="translate(16, -16)"/>
        </g>
      </svg>

      <!-- Pin Label Overlay -->
      <div style="position:relative; z-index:10; padding:1rem; pointer-events:none;">
        <span class="badge badge-demo" style="box-shadow:var(--shadow-sm); pointer-events:auto;">📍 ${shopName}</span>
      </div>

      <!-- Bottom Directions Action Bar -->
      <div style="position:relative; z-index:10; background:rgba(255,255,255,0.92); backdrop-filter:blur(4px); padding:0.75rem 1rem; border-top:1px solid #cbd5e1; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem;">
        <div>
          <div style="font-weight:700; font-size:0.875rem; color:#0f172a;">${shopAddress}</div>
          <div style="font-size:0.75rem; color:#64748b;">GPS: ${shopLat.toFixed(4)}, ${shopLng.toFixed(4)}</div>
        </div>
        <a href="${mapsUrl}" target="_blank" rel="noopener noreferrer" class="btn btn-primary btn-sm" style="pointer-events:auto;">
          Get Directions &rarr;
        </a>
      </div>
    </div>
  `;
}
