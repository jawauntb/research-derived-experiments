const navLinks = [...document.querySelectorAll(".nav a")];
const sections = navLinks
  .map((link) => document.querySelector(link.getAttribute("href")))
  .filter(Boolean);

function syncNav() {
  let activeId = sections[0]?.id;
  for (const section of sections) {
    if (section.getBoundingClientRect().top <= 120) {
      activeId = section.id;
    }
  }

  for (const link of navLinks) {
    link.setAttribute("aria-current", link.getAttribute("href") === `#${activeId}` ? "true" : "false");
  }
}

window.addEventListener("scroll", syncNav, { passive: true });
window.addEventListener("load", syncNav);
syncNav();
