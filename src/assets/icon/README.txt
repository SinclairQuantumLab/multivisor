M icon asset pack

Web integration:
- favicon/favicon.ico is the browser-tab icon source.
- Copy it to public/favicon.ico when updating the design, then run npm run build.
- index.html references /favicon.ico with a version query to refresh browser caches.
- Commit public/favicon.ico and the regenerated multivisor/server/dist/ together.
- The remaining exports are retained as source assets for future use.

Included:
- source/m-icon-master.svg
- source/m-icon-master.png
- favicon/favicon.ico
- favicon/favicon-16x16.png
- favicon/favicon-32x32.png
- favicon/favicon-48x48.png
- favicon/apple-touch-icon.png
- favicon/android-chrome-192x192.png
- favicon/android-chrome-512x512.png
- desktop/windows/m-icon.ico
- desktop/windows/*.png in common icon sizes
- desktop/linux/*.png in common icon sizes
- desktop/macos/*.png
- desktop/macos/m-icon.icns (when available)

Notes:
- The SVG is a clean vector recreation intended as the editable source.
- The PNG/ICO/ICNS assets were derived for practical use.
- Master raster source used: a_simple_graphic_logo_style_image_a_flat_square_c_1.png

macOS .icns status:
- Created m-icon.icns
