# Scam Museum — Museum Gallery V2

## Status

Implemented on `museum-v2-gallery` as the next product direction after the HackSocial submission freeze.

## Product shift

Scam Museum is no longer presented primarily as an analyzer wearing museum language.

The interface is structured as an actual digital museum:

1. **Museum Entrance** — a full-screen gallery hero with a featured framed artifact.
2. **The Collection** — a browsable, filterable catalog of curated scam-pattern exhibits.
3. **Exhibit Record** — each catalog item opens as a museum record with accession number, source type, observed artifacts, and curatorial note.
4. **Examination Room** — the existing text and screenshot analyzer becomes a private room inside the museum.
5. **Related Exhibits** — after a visitor analyzes a message, the interface can surface curated exhibits that share detected evidence patterns.
6. **Methodology / Curatorial Statement** — explains the hybrid ML + evidence + uncertainty contract and the collection's privacy boundary.

## Collection policy

The public gallery does **not** automatically publish visitor-submitted messages.

The initial collection uses reconstructed demonstrations based on documented scam patterns. Each exhibit is explicitly labeled `Reconstructed demonstration` and uses synthetic message text.

This separation exists for three reasons:

- visitor messages may contain names, phone numbers, financial details, or private conversation context;
- the classifier and decision layer can still produce false positives;
- a public museum record should have an explicit provenance and curation decision rather than being generated automatically from private input.

A future community-submission workflow would require explicit opt-in, redaction, moderation, provenance tracking, and a review step before publication.

## Visual direction

The interface aims to feel like entering a physical museum rather than opening a SaaS dashboard.

Visual language:

- black / deep burgundy gallery walls;
- warm ivory typography;
- aged-brass borders and accession metadata;
- framed message artifacts;
- editorial serif display typography;
- compact mono catalog metadata;
- minimal corner rounding;
- restrained spotlight and wall-depth effects;
- ecommerce-like browsing mechanics without ecommerce semantics.

The collection borrows familiar catalog interactions such as filters, cards, detail records, and related items, but renames them into museum language: exhibits, accession numbers, collections, records, and curatorial notes.

## Existing system preserved

The V2 gallery does not replace the core Scam Museum analysis stack.

Preserved components:

- frozen v0.5 classifier;
- evidence rules;
- contextual / protective evidence;
- uncertainty-aware risk resolver;
- exhibit-title generation;
- browser-side OCR;
- screenshot clipboard paste;
- share-card workflow;
- FastAPI API contract.

The change is primarily information architecture, presentation, and the addition of a curated public collection layer.
