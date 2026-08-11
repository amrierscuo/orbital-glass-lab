const tabs = [...document.querySelectorAll('.project-tab')];
const panels = [...document.querySelectorAll('.project-panel')];
const videos = [...document.querySelectorAll('video')];

function selectProject(targetId) {
  tabs.forEach((tab) => {
    const active = tab.dataset.target === targetId;
    tab.classList.toggle('is-active', active);
    tab.setAttribute('aria-selected', String(active));
  });

  panels.forEach((panel) => {
    const active = panel.id === targetId;
    panel.hidden = !active;
    panel.classList.toggle('is-active', active);
    if (!active) panel.querySelector('video')?.pause();
  });
}

tabs.forEach((tab) => tab.addEventListener('click', () => selectProject(tab.dataset.target)));

document.addEventListener('keydown', (event) => {
  if (event.target.matches('input, textarea, button')) return;
  if (event.key === '1') selectProject('glass-panel');
  if (event.key === '2') selectProject('ocean-panel');
  if (event.key === ' ') {
    event.preventDefault();
    const video = document.querySelector('.project-panel:not([hidden]) video');
    if (video) video.paused ? video.play() : video.pause();
  }
});

videos.forEach((video) => {
  video.addEventListener('play', () => videos.filter((item) => item !== video).forEach((item) => item.pause()));
});

const auroras = document.querySelectorAll('.aurora');
window.addEventListener('pointermove', (event) => {
  const x = (event.clientX / window.innerWidth - 0.5) * 18;
  const y = (event.clientY / window.innerHeight - 0.5) * 18;
  auroras.forEach((aurora, index) => {
    const direction = index ? -1 : 1;
    aurora.style.transform = `translate(${x * direction}px, ${y * direction}px)`;
  });
}, { passive: true });
