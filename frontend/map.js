/**
 * SMART FIR 360 - Leaflet & OpenStreetMap GIS Integration
 */

let crimeMapInstance = null;
let pickerMapInstance = null;
let pickerMarker = null;

const MapService = {
  // 1. Police GIS Crime Hotspot Map
  initCrimeMap(elementId, markers = [], onMarkerClick = null) {
    const container = document.getElementById(elementId);
    if (!container) return;

    if (crimeMapInstance) {
      crimeMapInstance.remove();
      crimeMapInstance = null;
    }

    // Default center: Delhi NCR
    const defaultCenter = [28.6250, 77.2300];
    const defaultZoom = 11;

    crimeMapInstance = L.map(elementId).setView(defaultCenter, defaultZoom);

    // OpenStreetMap Tile Layer
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19
    }).addTo(crimeMapInstance);

    const bounds = [];

    // Add markers
    markers.forEach(m => {
      if (!m.latitude || !m.longitude) return;

      const latLng = [parseFloat(m.latitude), parseFloat(m.longitude)];
      bounds.push(latLng);

      const color = m.urgency_level === "CRITICAL" ? "#dc2626"
                  : m.urgency_level === "HIGH" ? "#ea580c"
                  : m.urgency_level === "MEDIUM" ? "#f59e0b" : "#3b82f6";

      const iconHtml = `
        <div style="
          background-color: ${color};
          width: 24px;
          height: 24px;
          border-radius: 50%;
          border: 3px solid #ffffff;
          box-shadow: 0 0 10px rgba(0,0,0,0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          color: #fff;
          font-size: 11px;
          font-weight: bold;
        ">🚨</div>
      `;

      const customIcon = L.divIcon({
        className: "custom-gis-pin",
        html: iconHtml,
        iconSize: [26, 26],
        iconAnchor: [13, 13]
      });

      const marker = L.marker(latLng, { icon: customIcon }).addTo(crimeMapInstance);

      const popupContent = `
        <div style="font-family: inherit; min-width: 200px; color: #111;">
          <div style="font-weight: 800; font-size: 13px; color: #1e3a8a; margin-bottom: 4px;">${m.complaint_number}</div>
          <div style="font-weight: 700; font-size: 12px; margin-bottom: 4px;">${m.title}</div>
          <div style="font-size: 11px; color: #555; margin-bottom: 6px;">Category: <strong>${m.category}</strong></div>
          <div style="font-size: 11px; color: #555; margin-bottom: 6px;">Station: ${m.police_station}</div>
          <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px;">
            <span style="font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px; background: ${color}; color: #fff;">${m.urgency_level}</span>
            <button onclick="window.viewCaseFromMap(${m.id})" style="background: #1e3a8a; color: #fff; border: none; padding: 4px 10px; border-radius: 4px; font-size: 11px; cursor: pointer;">Open Case</button>
          </div>
        </div>
      `;

      marker.bindPopup(popupContent);
    });

    if (bounds.length > 0) {
      crimeMapInstance.fitBounds(bounds, { padding: [50, 50], maxZoom: 14 });
    }
  },

  // 2. Incident Location Picker for Citizen Complaint Form
  initLocationPicker(elementId, onSelectLocation) {
    const container = document.getElementById(elementId);
    if (!container) return;

    if (pickerMapInstance) {
      pickerMapInstance.remove();
      pickerMapInstance = null;
    }

    const defaultCenter = [28.6139, 77.2090]; // New Delhi
    pickerMapInstance = L.map(elementId).setView(defaultCenter, 13);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; OpenStreetMap',
      maxZoom: 19
    }).addTo(pickerMapInstance);

    pickerMarker = L.marker(defaultCenter, { draggable: true }).addTo(pickerMapInstance);

    const updateCoords = (lat, lng) => {
      pickerMarker.setLatLng([lat, lng]);
      if (onSelectLocation) {
        onSelectLocation(lat.toFixed(6), lng.toFixed(6));
      }
    };

    pickerMapInstance.on("click", (e) => {
      updateCoords(e.latlng.lat, e.latlng.lng);
    });

    pickerMarker.on("dragend", (e) => {
      const position = pickerMarker.getLatLng();
      updateCoords(position.lat, position.lng);
    });

    // Invalidate size in case of modal animation
    setTimeout(() => {
      if (pickerMapInstance) pickerMapInstance.invalidateSize();
    }, 300);
  }
};
