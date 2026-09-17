---
layout: default
---
{% for post in site.posts limit: 30 %}
<article class="post">
  <h2><a href="{{ post.url | relative_url }}">{{ post.title }}</a></h2>
  <p class="meta">{{ post.date | date: "%Y-%m-%d" }} · {{ post.source }}</p>
  <a href="{{ post.url | relative_url }}"><img src="{{ post.image | relative_url }}" alt="{{ post.title }}" loading="lazy"></a>
</article>
{% endfor %}
