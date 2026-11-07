'use strict';

const toggle = document.querySelector('.menu-toggle');
const nav = document.querySelector('#navigation');

if (toggle && nav) {
  toggle.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') !== 'true';
    toggle.setAttribute('aria-expanded', String(open));
    nav.classList.toggle('is-open', open);
  });

  nav.addEventListener('click', (event) => {
    if (event.target.closest('a')) {
      nav.classList.remove('is-open');
      toggle.setAttribute('aria-expanded', 'false');
    }
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
      nav.classList.remove('is-open');
      toggle.setAttribute('aria-expanded', 'false');
      toggle.focus();
    }
  });
}

const bar = document.querySelector('.mobile-project');
const hero = document.querySelector('#hero');
const work = document.querySelector('#work');
const project = document.querySelector('#project');

if (bar && hero && project && 'IntersectionObserver' in window) {
  let heroVisible = true;
  let workVisible = true;
  let projectVisible = false;
  const update = () => bar.classList.toggle('visible', !heroVisible && !workVisible && !projectVisible);
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.target === hero) heroVisible = entry.isIntersecting;
      if (entry.target === work) workVisible = entry.isIntersecting;
      if (entry.target === project) projectVisible = entry.isIntersecting;
    });
    update();
  });
  observer.observe(hero);
  if (work) observer.observe(work);
  observer.observe(project);
}

const copyButton = document.querySelector('#copy-btc');
if (copyButton) {
  copyButton.addEventListener('click', async () => {
    const address = document.getElementById('btc-address').textContent.trim();
    const status = document.getElementById('btc-status');
    try {
      await navigator.clipboard.writeText(address);
      status.textContent = 'Bitcoin address copied.';
    } catch (error) {
      status.textContent = 'Copy failed. Select the address and copy it manually.';
    }
  });
}
