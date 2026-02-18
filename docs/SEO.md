# SEO controls

- **robots.txt** — served by Whitenoise from `public/robots.txt`. Disallows `/admin/`, `/api/`, `/healthz`.
- **noindex** — login and registration pages have `<meta name="robots" content="noindex, nofollow">`.
- **Open Graph tags** — `base_minimal.html` has a `{% block meta_tags %}` with `og:title`, `og:description`, `og:site_name`, and `og:type`.
- Maintainer-only pages don't need `noindex` — `LoginRequiredMiddleware` returns 302 redirects, and search engines don't index those.

## Adding `meta_description` to views

Public-facing views should set `meta_description` in `get_context_data()` for search engine and social media previews:

```python
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context["meta_description"] = "Description for search results and social previews."
    return context
```

For detail views with user content, truncate to 155 characters:

```python
from django.utils.text import Truncator

context["meta_description"] = Truncator(self.object.text).chars(155)
```
