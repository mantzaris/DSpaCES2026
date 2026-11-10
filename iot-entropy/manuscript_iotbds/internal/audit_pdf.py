#!/usr/bin/env python3
"""Audit the rendered anonymous PDF; run from any working directory.

python3 internal/audit_pdf.py [--pdf paper.pdf] [--out internal/validation]
Requires pdftotext and PyMuPDF (vendored locally in internal/python).
This is an estimate, not a conference-certified character measurement.
"""
from pathlib import Path
import argparse
from collections import Counter
import hashlib
import json
import re
import subprocess
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "internal/python"))
import fitz


def normalize(text):
    return unicodedata.normalize("NFKC", text)


def chars(text):
    return "".join(c for c in normalize(text) if not c.isspace())


def spans(page):
    return [s for b in page.get_text("dict")["blocks"] if "lines" in b
            for line in b["lines"] for s in line["spans"]]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def poppler(path):
    return subprocess.run(["pdftotext", "-enc", "UTF-8", "-nopgbrk", str(path), "-"],
                          check=True, capture_output=True).stdout.decode("utf-8")


IDENTITY = re.compile(
    r"Mantzaris|Korris|Alexander|University\s+of\s+Central\s+Florida|"
    r"Creative\s+Technologies|ucf\.edu|cretecinc\.com|"
    r"Orlando|Hollywood|DSpaCES2026|\bresort\b|ORCID|"
    r"https?://(?:www\.)?(?:github\.com|gitlab\.com)/[^\s<>\])]+|"
    r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", re.I)


def matches(text):
    return [{"match": m.group(),
             "context": text[max(0, m.start()-65):m.end()+85].replace("\n", " ")}
            for m in IDENTITY.finditer(text)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", default="paper.pdf")
    parser.add_argument("--out", default="internal/validation")
    args = parser.parse_args()
    pdf = (ROOT / args.pdf).resolve()
    out = (ROOT / args.out).resolve()
    if ROOT not in out.parents:
        parser.error("Output must remain inside manuscript_iotbds")
    out.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf)
    page_text = [page.get_text("text", sort=True) for page in doc]
    mupdf_text = "\n".join(page_text)
    poppler_text = poppler(pdf)
    (out / "paper-pymupdf.txt").write_text(mupdf_text)
    (out / "paper-pdftotext.txt").write_text(poppler_text)
    (out / "paper-pymupdf-nfkc.txt").write_text(normalize(mupdf_text))
    (out / "paper-pdftotext-nfkc.txt").write_text(normalize(poppler_text))

    figures = []
    figure_fonts = set()
    original_figure_characters = Counter()
    original_files = ["architecture.pdf", "theory.pdf", "performance.pdf",
                      "traces.pdf", "availability.pdf", "dashboard_cost.pdf"]
    for name in original_files:
        path = ROOT / "figures-v2" / name
        fig = fitz.open(path)
        text = "\n".join(p.get_text() for p in fig)
        ps = [s for p in fig for s in spans(p)]
        figure_fonts.update(s["font"] for s in ps)
        original_figure_characters.update(chars(text))
        images = []
        for page in fig:
            for item in page.get_images(full=True):
                xref, _, width, height = item[:4]
                data = fig.extract_image(xref)
                file = f"{path.stem}-raster-{xref}.{data['ext']}"
                (out / file).write_bytes(data["image"])
                images.append({"xref": xref, "width": width, "height": height,
                               "extracted_file": file})
        (out / f"figure-{path.stem}.txt").write_text(text)
        figures.append({"file": str(path.relative_to(ROOT)), "sha256": sha(path),
                        "pages": len(fig), "pymupdf_chars_nfkc": len(chars(text)),
                        "pdftotext_chars_nfkc": len(chars(poppler(path))),
                        "fonts": sorted(set(s["font"] for s in ps)),
                        "embedded_raster_images": images,
                        "original_min_font_pt": min(s["size"] for s in ps)})

    page_stats, figure_chars, figure_spans = [], Counter(), []
    links, annotations, widgets = [], [], []
    for n, page in enumerate(doc, 1):
        all_spans = spans(page)
        fs = [s for s in all_spans if s["font"] in figure_fonts]
        figure_chars.update(chars("".join(s["text"] for s in fs)))
        figure_spans += [{"page": n, "text": s["text"], "font": s["font"],
                          "size_pt": s["size"], "bbox": s["bbox"]} for s in fs]
        page_stats.append({"page": n, "chars_nfkc": len(chars(page_text[n-1])),
                           "width_pt": page.rect.width, "height_pt": page.rect.height,
                           "figure_text_chars_nfkc": len(chars("".join(s["text"] for s in fs))),
                           "figure_min_font_pt": min((s["size"] for s in fs), default=None),
                           "figure_max_font_pt": max((s["size"] for s in fs), default=None)})
        for link in page.get_links():
            links.append({"page": n, **link})
        for ann in page.annots() or []:
            annotations.append({"page": n, "type": ann.type, "info": ann.info,
                                "file_info": ann.file_info if ann.type[0] == 17 else None})
        for widget in page.widgets() or []:
            widgets.append({"page": n, "name": widget.field_name,
                            "value": widget.field_value, "type": widget.field_type_string})

    toc = doc.get_toc(simple=False)
    xmp = doc.get_xml_metadata()
    embedded = [{"name": name, "info": doc.embfile_info(name)} for name in doc.embfile_names()]
    actions = []
    for xref in range(1, doc.xref_length()):
        obj = doc.xref_object(xref)
        flags = re.findall(r"/(?:JavaScript|JS|Launch|EmbeddedFile|AcroForm)\b", obj)
        if flags:
            actions.append({"xref": xref, "flags": flags, "object": obj})
    hidden = {"metadata": doc.metadata, "xmp": xmp, "bookmarks": toc,
              "non_link_annotations": annotations, "embedded_files": embedded,
              "form_widgets": widgets, "active_or_attachment_objects": actions,
              "external_links": [x for x in links if "uri" in x or "file" in x]}
    (out / "pdf-structure.json").write_text(json.dumps(hidden, indent=2, default=str)+"\n")
    references = re.search(r"(?m)^References\s*$", mupdf_text)
    body = mupdf_text[:references.start()] if references else mupdf_text
    bibliography = mupdf_text[references.end():] if references else ""
    exempt = [m for m in matches(bibliography) if m["match"].lower() == "mantzaris"]
    other_reference_hits = [m for m in matches(bibliography) if m not in exempt]
    hidden_hits = matches(json.dumps(hidden, default=str))
    a, b = len(chars(poppler_text)), len(chars(mupdf_text))
    figure_original_count = sum(original_figure_characters.values())
    figure_extracted_count = sum(figure_chars.values())
    adjusted = b - figure_extracted_count + figure_original_count
    crop_evidence = ROOT / "internal/figure-review/crop-verification.json"
    crop_checks = json.loads(crop_evidence.read_text()) if crop_evidence.exists() else None
    report = {
        "pdf": str(pdf.relative_to(ROOT)), "pdf_sha256": sha(pdf), "pages": len(doc),
        "method": "Extract PDF text using pdftotext and PyMuPDF; Unicode NFKC normalizes ligatures; count code points with str.isspace()==False. Raw totals include all pages, captions, tables, references, extracted figure text and page numbers. Also calculate a rendered estimate by subtracting all figure-font text spans from the PyMuPDF full-document total and adding the six original figure assets' text exactly once: this corrects invisible text retained by repeated clipped-PDF inclusion.",
        "count_is_estimate_not_conference_certified": True,
        "characters": {"pdftotext_nfkc_nonwhitespace": a,
                       "pymupdf_nfkc_nonwhitespace": b,
                       "figure_adjusted_rendered_estimate": adjusted,
                       "adjustment_formula": f"{b} full-PDF - {figure_extracted_count} extracted figure-font + {figure_original_count} original figures once = {adjusted}",
                       "invisible_figure_extraction_surplus": figure_extracted_count-figure_original_count,
                       "absolute_difference": abs(a-b),
                       "relative_difference_percent": 100*abs(a-b)/max(a,b),
                       "pdftotext_raw_nonwhitespace": sum(not c.isspace() for c in poppler_text),
                       "pymupdf_raw_nonwhitespace": sum(not c.isspace() for c in mupdf_text),
                       "pdftotext_replacement_characters": poppler_text.count("\ufffd"),
                       "pymupdf_replacement_characters": mupdf_text.count("\ufffd"),
                       "raw_and_adjusted_estimates_within_10000_50000": all(10000 <= x <= 50000 for x in (a,b,adjusted)),
                       "distance_to_50000_using_larger_estimate": 50000-max(a,b)},
        "pages_at_or_below_intended_25_page_full_publication_target": len(doc) <= 25,
        "page_measurements": page_stats,
        "figures": figures,
        "figure_text_coverage": {
            "classification": "Rendered text spans whose fonts match the original six figure assets; these fonts are distinct from manuscript fonts in this conversion.",
            "fonts": sorted(figure_fonts),
            "original_total_nonwhitespace": figure_original_count,
            "full_pdf_extracted_figure_text_including_invisible_clipped_objects": figure_extracted_count,
            "original_character_multiset_missing_from_rendered": dict(original_figure_characters-figure_chars),
            "rendered_character_multiset_extra": dict(figure_chars-original_figure_characters),
            "warning": "Multiset coverage is a diagnostic, not proof of correct panel order, clipping, or glyph identity. Visual inspection remains necessary. Cropped PDF reuse can retain invisible text objects in extraction.",
            "separate_crop_geometry_verification": crop_checks,
            "all_figure_spans_at_least_6_pt": all(s["size_pt"] >= 5.99 for s in figure_spans)},
        "anonymity": {"visible_body_identity_candidates": matches(body),
                      "ordinary_third_person_reference_name_hits_exempt": exempt,
                      "other_reference_identity_candidates": other_reference_hits,
                      "metadata_and_structural_identity_candidates": hidden_hits,
                      "blank_author_metadata": not doc.metadata.get("author"),
                      "bookmarks": len(toc), "non_link_annotations": len(annotations),
                      "embedded_attachments": len(embedded), "form_widgets": len(widgets),
                      "javascript_launch_attachment_or_form_objects": len(actions),
                      "internal_links": len(links)-len(hidden["external_links"]),
                      "external_links": len(hidden["external_links"])},
        "limitations": [
            "Rendered character counts include mathematical glyphs as extracted; glyph-to-Unicode maps, super/subscripts, accents and mathematical operators can differ by engine.",
            "NFKC expands fi/fl ligatures and some compatibility characters; it is a reproducible convention, not a conference counting algorithm.",
            "Line-break hyphens and page numbers are retained conservatively. Reading order does not affect total characters.",
            "Raw PDF extraction includes invisible clipped-out text from repeated figure inclusion; raw totals therefore conservatively overcount. The adjusted estimate replaces all extracted figure-font text with the six original assets counted once. This depends on every original panel being visibly preserved once; the separate crop geometry checks and full-page visual review establish that premise.",
            "The sole raster inside the original six figures is a 9-by-173-pixel color gradient in dashboard_cost.pdf; it was visually inspected and contains no letters or numbers.",
            "Font sizes are PDF text-span measurements; rotated/superscript labels and scaling can affect interpretation. Visual inspection is still required.",
            "Identity matches are candidates requiring context; necessary cited-author surnames in ordinary bibliography entries are not authorship declarations."]}
    (out / "figure-spans.json").write_text(json.dumps(figure_spans, indent=2)+"\n")
    (out / "audit.json").write_text(json.dumps(report, indent=2, default=str)+"\n")
    print(json.dumps({"pages": len(doc), "characters": report["characters"],
                      "figure_text_coverage": report["figure_text_coverage"],
                      "anonymity": report["anonymity"]}, indent=2))


if __name__ == "__main__":
    main()
