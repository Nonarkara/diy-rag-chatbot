// script.js — vanilla JS, no deps. Drop interactivity here.
// Keep it small. Anything that needs a server belongs in a
// sibling project scaffolded from templates/chatbot/ or
// templates/dashboard/.

(() => {
  // Smooth-scroll for the nav links (no library, just a one-liner).
  document.querySelectorAll('nav a[href^="#"]').forEach((a) => {
    a.addEventListener('click', (e) => {
      const id = a.getAttribute('href').slice(1);
      const t = document.getElementById(id);
      if (t) {
        e.preventDefault();
        t.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
})();
