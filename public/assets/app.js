// Comportements de la vitrine.
//
// Ce code était écrit en ligne dans <head>, en deux copies qui avaient
// déjà divergé : seuil 0,12 sur l'accueil contre 0,1 sur /career/, et le
// fond de nav présent d'un seul côté. Un fichier unique, chargé par les
// deux pages.
//
// Un script en ligne oblige aussi à ouvrir la CSP avec 'unsafe-inline',
// ce qui lui retire l'essentiel de son intérêt. Ici, script-src 'self'
// suffit.

// Apparition au défilement.
const observer = new IntersectionObserver((entries) => {
  entries.forEach((e) => {
    if (e.isIntersecting) {
      e.target.classList.add('visible');
      observer.unobserve(e.target);
    }
  });
}, { threshold: 0.12 });

document.querySelectorAll('.fade-up').forEach((el) => observer.observe(el));

// Fond de la barre de navigation : opaque dès qu'on a quitté le haut.
const nav = document.querySelector('nav');
if (nav) {
  const fond = () => {
    nav.style.background = window.scrollY > 60
      ? 'rgba(14,14,16,0.97)'
      : 'linear-gradient(to bottom, rgba(14,14,16,0.95), transparent)';
  };
  window.addEventListener('scroll', fond);
  fond();
}
