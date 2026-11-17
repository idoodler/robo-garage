# Vendored libraries

The simulator page loads these from its own files instead of a CDN, so the 3D view and the downloads work even where a CDN is blocked.

| Library | Version | Files | License |
|---|---|---|---|
| three.js | 0.170.0 (npm `three`) | `three/three.module.min.js` (`build/`), `three/addons/…` (`examples/jsm/`: OrbitControls, RoundedBoxGeometry, GLTFLoader + its BufferGeometryUtils) | MIT, `three/LICENSE` |
| JSZip | 3.10.1 (npm `jszip`) | `jszip/jszip.min.js` (`dist/`) | MIT or GPLv3, `jszip/LICENSE.markdown` |

Update: `npm pack three@<version> jszip@<version>`, copy the same files, change the version here. A new `three/addons/` import in the page needs its file here too.

Publishing: upload this folder with the page as `vendor/…` (licenses as `LICENSE.txt`).
