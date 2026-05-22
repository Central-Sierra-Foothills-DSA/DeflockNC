# DeFlock Nevada County

Static site documenting the scope and federal access of Flock Safety license plate cameras in Nevada County, CA. Built and maintained by the Central Sierra Foothills DSA · DeFlock Working Group. All underlying data was obtained via California Public Records Act requests.

Live concerns and demands are presented on the site itself — see `index.html`.

## Structure

```
.
├── index.html                Page markup
└── assets/
    ├── css/styles.css        Styles
    ├── js/main.js            Scroll-reveal animations
    └── images/               Evidence photos
```

No build step required to publish — plain HTML, CSS, and a few lines of vanilla JS. Optional dev tooling for formatting and linting is described below.

## Running locally

From the repo root:

```sh
python3 -m http.server 8000
```

Then open <http://localhost:8000>.

## Deploying

Any static host works (GitHub Pages, Netlify, Cloudflare Pages, S3 + CloudFront). Point the host at the repo root; `index.html` is the entry point. The dev tooling described below is not required for deployment.

## Dev tooling (optional)

Formatting and linting via npm. Install once:

```sh
npm install
```

Then:

```sh
npm run format        # apply Prettier
npm run format:check  # verify formatting
npm run lint:html     # html-validate
npm run lint:css      # stylelint
npm run lint          # all of the above
```

Config lives in `.prettierrc.json`, `.htmlvalidate.json`, and `.stylelintrc.json`. None of this is needed to publish the site.

## Contact

deflocknevadacounty@proton.me
