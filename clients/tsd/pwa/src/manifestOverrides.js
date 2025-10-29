export async function applyManifestOverrides() {
  const manifestLink = document.querySelector('link[rel="manifest"]');
  if (!manifestLink || manifestLink.dataset.dynamicManifest === "true") {
    return;
  }

  try {
    const manifestUrl = new URL(manifestLink.href, window.location.href);
    const response = await fetch(manifestUrl.href, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Failed to fetch manifest: ${response.status}`);
    }

    const manifest = await response.json();

    const path = window.location.pathname.replace(/\/+$/, "") || "/";
    const scopePath = path === "/" ? "/" : `${path}/`;
    const startUrl = `${path}${window.location.search}`;

    const updatedManifest = {
      ...manifest,
      start_url: startUrl,
      scope: scopePath,
      icons: Array.isArray(manifest.icons)
        ? manifest.icons.map((icon) => {
            const iconUrl = new URL(icon.src, manifestUrl);
            return {
              ...icon,
              src: iconUrl.href,
            };
          })
        : manifest.icons,
    };

    const blob = new Blob([JSON.stringify(updatedManifest)], {
      type: "application/manifest+json",
    });

    const objectUrl = URL.createObjectURL(blob);
    manifestLink.setAttribute("href", objectUrl);
    manifestLink.dataset.dynamicManifest = "true";

    window.addEventListener(
      "beforeunload",
      () => {
        URL.revokeObjectURL(objectUrl);
      },
      { once: true }
    );
  } catch (error) {
    console.warn("Failed to update manifest dynamically", error);
  }
}
