const tabs = [...document.querySelectorAll('.project-tab')];
const panels = [...document.querySelectorAll('.project-panel')];
const videos = [...document.querySelectorAll('video')];

const versions = {
  glass: {
    v3: {
      video: 'media/glass-orbit-v3.mp4',
      poster: 'media/glass-orbit-v3-poster.png',
      gif: 'media/glass-orbit-v3.gif',
      label: 'V3 · Latest',
      copy: 'V3 elimina i bordi della base, aggiunge superfici texturizzate e un cielo atmosferico dinamico al cubo di vetro orbitale.',
    },
    v2: {
      video: 'media/glass-orbit-v2.mp4',
      poster: 'media/glass-orbit-v2-poster.png',
      gif: 'media/glass-orbit-v2.gif',
      label: 'V2 · Glass pass',
      copy: 'V2 separa il nucleo dalla scocca trasparente, rifinisce l’orbita e introduce la sequenza notturna con LED.',
    },
    v1: {
      video: 'media/glass-orbit-v1.mp4',
      poster: 'media/glass-orbit-v1-poster.png',
      gif: 'media/glass-orbit-v1.gif',
      label: 'V1 · Prototype',
      copy: 'V1 è il primo prototipo procedurale: geometria, luci, orbita e camere costruite interamente via Python.',
    },
  },
  ocean: {
    v3: {
      video: 'media/ocean-jump-v3.mp4',
      poster: 'media/ocean-jump-v3-poster.png',
      gif: 'media/ocean-jump-v3.gif',
      label: 'V3 · Latest',
      copy: 'V3 trasforma il piano d’acqua in un oceano continuo fino all’orizzonte, con onde, texture, nuvole e piattaforme materiche.',
    },
    v2: {
      video: 'media/ocean-jump-v2.mp4',
      poster: 'media/ocean-jump-v2-poster.png',
      gif: 'media/ocean-jump-v2.gif',
      label: 'V2 · Character pass',
      copy: 'V2 introduce Manny animato, il cambio prima/terza persona e il salto completo sopra la prima superficie ondulata.',
    },
    v1: {
      video: 'media/ocean-jump-v1.mp4',
      poster: 'media/ocean-jump-v1-poster.png',
      gif: 'media/ocean-jump-v1.gif',
      label: 'V1 · Prototype',
      copy: 'V1 definisce il blocking iniziale delle piattaforme, delle camere e della traiettoria prima del personaggio definitivo.',
    },
  },
};

function unloadGif(panel) {
  const preview = panel.querySelector('.gif-preview');
  const image = preview.querySelector('img');
  const button = panel.querySelector('.gif-toggle');
  image.removeAttribute('src');
  preview.hidden = true;
  button.textContent = 'Carica GIF';
  button.classList.remove('is-loaded');
}

function selectVersion(panel, version) {
  const config = versions[panel.dataset.project][version];
  const video = panel.querySelector('video');
  const source = video.querySelector('source');

  video.pause();
  source.src = config.video;
  video.poster = config.poster;
  video.load();
  panel.querySelector('[data-version-copy]').textContent = config.copy;
  panel.querySelector('[data-version-label]').textContent = config.label;
  panel.dataset.version = version;
  unloadGif(panel);

  panel.querySelectorAll('.version-button').forEach((button) => {
    const active = button.dataset.version === version;
    button.classList.toggle('is-active', active);
    button.setAttribute('aria-pressed', String(active));
  });
}

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

panels.forEach((panel) => {
  panel.dataset.version = 'v3';
  panel.querySelectorAll('.version-button').forEach((button) => {
    button.addEventListener('click', () => selectVersion(panel, button.dataset.version));
  });

  panel.querySelector('.gif-toggle').addEventListener('click', () => {
    const preview = panel.querySelector('.gif-preview');
    const image = preview.querySelector('img');
    const button = panel.querySelector('.gif-toggle');
    if (!preview.hidden) {
      unloadGif(panel);
      return;
    }
    image.src = versions[panel.dataset.project][panel.dataset.version].gif;
    preview.hidden = false;
    button.textContent = 'Rimuovi GIF';
    button.classList.add('is-loaded');
  });
});

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
