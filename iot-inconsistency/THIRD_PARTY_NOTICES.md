# Source and template notices

The acquisition manifest `data/manifests/acquisition.json` pins source URLs, repository revisions and archive hashes. The starting-paper records and method comparisons are in `literature/sources.json` and `literature/NOVELTY_MATRIX.md`.

- SKAB is obtained from `waico/SKAB` at the pinned revision. Its repository license is preserved in `licenses/SKAB-GPL-3.0.txt`. Source experiment names and hashes accompany the derived measurement windows. Refer to that upstream license for SKAB material.
- Intel Berkeley measurements come from the official MIT-hosted laboratory dataset. Its source description and acknowledgment request are preserved by the acquisition script. The paper acknowledges the dataset contributors. The official page supplies no comprehensive sensor-fault labels.
- GDN and CSDI reference repositories use MIT licenses. Their notices are retained in `licenses/GDN-MIT.txt` and `licenses/CSDI-LICENSE.txt`. The GDN attention implementation follows the published architecture; the evaluation protocol is explicitly adapted. The conditional model uses the established CSDI noise-training objective with a different architecture.
- The inspected DiffAD snapshot has no license file. Its code is not vendored or copied into this project. The comparator is an independent, documented implementation of the paper's method, with stated density-estimation, state-space and evaluation adaptations.
- `paper/IEEEtran.cls` and `paper/IEEEtran.bst` retain the original IEEE template authors' notices and licenses. `paper/template_provenance.json` records the local source and exact hashes. Only formatting assets were reused from the neighboring project. Its research prose, results and figures were not reused.

Raw source archives and downloaded literature are caches and are excluded from Git. This notice does not replace or broaden upstream licenses, nor does it assign a new license to the user's original work.
