---
layout: default
title: Subjects
permalink: /subjects/
---
<h1>Subjects</h1>
<p>The daily pick rotates through three subjects. Here's the latest digest for each, and the raw feeds behind it.</p>

<div class="subject-grid">
{% for subject in site.data.subjects %}
  {% assign latest = site.posts | where: "subject", subject.name | first %}
  <article class="subject-card">
    <h2>{{ subject.name }}</h2>
    {% if latest %}
    <a href="{{ latest.url | relative_url }}">
      <img src="{{ latest.image | relative_url }}" alt="{{ latest.title }}" loading="lazy">
    </a>
    <p class="meta">{{ latest.date | date: "%Y-%m-%d" }} &middot; {{ latest.panels }} images</p>
    <p><a href="{{ latest.url | relative_url }}">{{ latest.title }}</a></p>
    {% else %}
    <p class="meta">No digest yet.</p>
    {% endif %}
    <p class="explore">Explore:
      {% for explorer in subject.explorers %}<a href="{{ '/debug/' | append: explorer.source | append: '.html' | relative_url }}">{{ explorer.label }}</a>{% unless forloop.last %} &middot; {% endunless %}{% endfor %}
    </p>
  </article>
{% endfor %}
</div>
