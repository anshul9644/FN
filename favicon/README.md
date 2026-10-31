# FreshNet Farms site icon (favicon)

These files replace the grey globe that Google shows next to freshnet.in in
search results. The icon is the FreshNet palm tree with a brown "FN", cut
from the FreshNet logo. `source/fn-icon-512.png` is the full-size original.

## 1. Upload

Put every file in this folder in the root of the website, so it is reachable at
`https://freshnet.in/favicon.ico`, `https://freshnet.in/favicon-48x48.png`, and so on.

## 2. Add these lines inside `<head>` on every page

```html
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="48x48" href="/favicon-48x48.png">
<link rel="icon" type="image/png" sizes="96x96" href="/favicon-96x96.png">
<link rel="icon" type="image/png" sizes="192x192" href="/favicon-192x192.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
```

On WordPress, skip step 2: go to Appearance → Customize → Site Identity →
Site Icon and upload `favicon-192x192.png`.

## 3. Ask Google to refresh

In Google Search Console, use URL Inspection on `https://freshnet.in/` and click
"Request indexing". The icon usually shows up in results within a few days to
a few weeks.
