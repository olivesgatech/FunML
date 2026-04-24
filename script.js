const navToggle = document.querySelector('.nav-toggle');
const navMenu = document.querySelector('.nav-menu');
const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
const lectureItems = document.querySelectorAll('.lecture-item');
const lectureList = document.querySelector('.lecture-list');
const lectureFrame = document.getElementById('lecture-frame');
const lectureTitle = document.getElementById('lecture-title');
const lectureMeta = document.getElementById('lecture-meta');
const viewerFoot = document.querySelector('.viewer-actions .viewer-foot');
const notesLink = document.getElementById('notes-link');
const slidesLink = document.getElementById('slides-link');
const exerciseLink = document.getElementById('exercise-link');
const videoLinks = document.getElementById('video-links');
const demosLink = document.getElementById('demos-link');
const topDemosLink = document.getElementById('top-demos-link');
const topDisclaimerLink = document.getElementById('top-disclaimer-link');
const topSlidesMenu = document.getElementById('top-slides-menu');
const topNotesMenu = document.getElementById('top-notes-menu');
const topVideosMenu = document.getElementById('top-videos-menu');
const topExercisesMenu = document.getElementById('top-exercises-menu');
const topHandoutDemos = document.getElementById('top-handout-demos');
const topHandoutDisclaimer = document.getElementById('top-handout-disclaimer');
let lectureMedia = {};

const closeAllDropdowns = () => {
  dropdownToggles.forEach((toggle) => {
    toggle.setAttribute('aria-expanded', 'false');
    const menu = toggle.parentElement.querySelector('.dropdown-menu');
    if (menu) menu.style.display = 'none';
  });
};

const closeVideoDropdown = () => {
  const toggle = videoLinks?.querySelector('.video-trigger');
  const menu = videoLinks?.querySelector('.video-dropdown-menu');
  if (toggle) toggle.setAttribute('aria-expanded', 'false');
  if (menu) menu.style.display = 'none';
};

const updateResourceLink = (linkEl, href, label) => {
  if (!linkEl) return;
  if (href) {
    linkEl.classList.remove('disabled');
    linkEl.setAttribute('href', href);
    linkEl.textContent = label;
    return;
  }
  linkEl.classList.add('disabled');
  linkEl.setAttribute('href', '#');
  linkEl.textContent = label;
};

const escapeHtml = (value) => String(value || '')
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&#39;');

const toYouTubeEmbedUrl = (url) => {
  if (!url) return '';
  try {
    const parsed = new URL(url);
    if (parsed.hostname.includes('youtu.be')) {
      const id = parsed.pathname.replace('/', '');
      return id ? `https://www.youtube.com/embed/${id}?rel=0` : url;
    }
    if (parsed.hostname.includes('youtube.com')) {
      const id = parsed.searchParams.get('v');
      return id ? `https://www.youtube.com/embed/${id}?rel=0` : url;
    }
    return url;
  } catch {
    return url;
  }
};

const normalizeRecordingLabel = (label, idx) => {
  const base = (label || `Video ${idx + 1}`).trim();
  const cleaned = base
    .replace(/\b[Rr]ecording\b/gi, '')
    .replace(/\s{2,}/g, ' ')
    .replace(/\(\s*\)/g, '')
    .trim();
  return cleaned || `Video ${idx + 1}`;
};

const getActiveLectureItem = () => document.querySelector('.lecture-item.active');
const itemHasDisabledSlides = (item) => item?.dataset?.disableSlides === 'true';
const itemHidesViewerActions = (item) => item?.dataset?.hideViewerActions === 'true';

const syncViewerActionsVisibility = (item) => {
  if (!viewerFoot) return;
  const shouldHide = itemHidesViewerActions(item);
  viewerFoot.hidden = shouldHide;
  if (shouldHide) {
    closeVideoDropdown();
  }
};

const syncLandingPageChrome = (item) => {
  document.body.classList.toggle('landing-page-active', itemHidesViewerActions(item));
};

const toExerciseHref = (notesHref) => {
  const match = (notesHref || '').match(/([^/]+)\.html$/);
  return match ? `assets/exercises/${match[1]}.html` : '';
};

const getDisplayLectureNumber = (notesHref) => {
  const match = (notesHref || '').match(/Lecture(\d+)_/);
  return match ? match[1] : '';
};

const toDemosHref = (notesHref, title) => {
  const lectureNum = getDisplayLectureNumber(notesHref);
  if (!lectureNum) return 'assets/demos.html';
  const params = new URLSearchParams({ lecture: lectureNum });
  if (title) params.set('title', title);
  return `assets/demos.html?${params.toString()}`;
};

const getActiveLectureKey = () => {
  const activeItem = getActiveLectureItem();
  const explicitKey = activeItem?.dataset?.lectureKey;
  if (explicitKey) return explicitKey;
  const src = activeItem?.dataset?.lecture || '';
  const match = src.match(/([^/]+)\.html$/);
  return match ? match[1] : '';
};

const getLectureKeyFromItem = (item) => {
  const explicitKey = item?.dataset?.lectureKey;
  if (explicitKey) return explicitKey;
  const src = item?.dataset?.lecture || '';
  const match = src.match(/([^/]+)\.html$/);
  return match ? match[1] : '';
};

const findLectureItemByKey = (lectureKey) => (
  Array.from(lectureItems).find((item) => getLectureKeyFromItem(item) === lectureKey)
);

const updateLectureMedia = () => {
  const activeItem = getActiveLectureItem();
  syncLandingPageChrome(activeItem);
  syncViewerActionsVisibility(activeItem);
  const lectureNotesHref = activeItem?.dataset?.lecture || '';
  const lectureKey = getActiveLectureKey();
  const media = lectureMedia[lectureKey] || {};
  const localSlide = lectureKey && !itemHasDisabledSlides(activeItem) ? `assets/slides/${lectureKey}.pdf` : '';
  const slideEmbed = media.slide_local || localSlide || (media.slide ? `https://docs.google.com/gview?embedded=1&url=${encodeURIComponent(media.slide)}` : '');
  const exerciseHref = toExerciseHref(lectureNotesHref) || (lectureKey ? `assets/exercises/${lectureKey}.html` : '');
  const lectureLabel = activeItem?.dataset?.title || activeItem?.querySelector('.lecture-title')?.textContent || '';
  const demoHref = media.demo || toDemosHref(lectureNotesHref, lectureLabel);

  updateResourceLink(notesLink, lectureNotesHref, lectureNotesHref ? 'Lecture Notes' : 'No notes');
  updateResourceLink(slidesLink, slideEmbed, slideEmbed ? 'Slides' : 'No slides posted');
  updateResourceLink(exerciseLink, exerciseHref, 'Exercises');
  updateResourceLink(demosLink, demoHref, 'Demos');
  if (!videoLinks) return;

  const recordings = media.recordings || [];
  if (!recordings.length) {
    videoLinks.textContent = 'No video posted';
    return;
  }
  const items = recordings
    .map((recording, idx) => {
      const href = toYouTubeEmbedUrl(recording.url || '');
      const label = normalizeRecordingLabel(recording.label, idx);
      return `<a class="video-menu-link" href="${escapeHtml(href)}" role="menuitem" data-kind="Video" data-video-label="${escapeHtml(label)}">${escapeHtml(label)}</a>`;
    })
    .join('');
  videoLinks.innerHTML = `<div class="video-dropdown"><a class="resource-link video-trigger" aria-expanded="false" href="#">Video</a><div class="dropdown-menu video-dropdown-menu" role="menu">${items}</div></div>`;
  closeVideoDropdown();
};

const getLectureResources = (item) => {
  const lectureKey = getLectureKeyFromItem(item);
  const media = lectureMedia[lectureKey] || {};
  const localSlide = lectureKey && !itemHasDisabledSlides(item) ? `assets/slides/${lectureKey}.pdf` : '';
  const slideHref = media.slide_local || localSlide || (media.slide ? `https://docs.google.com/gview?embedded=1&url=${encodeURIComponent(media.slide)}` : '');
  const notesHref = item?.dataset?.lecture || (lectureKey ? `lectures/${lectureKey}.html` : '');
  const exercisesHref = toExerciseHref(notesHref) || (lectureKey ? `assets/exercises/${lectureKey}.html` : '');
  const recordings = media.recordings || [];
  const videos = recordings.map((recording, idx) => ({
    href: toYouTubeEmbedUrl(recording.url || ''),
    label: normalizeRecordingLabel(recording.label, idx),
  }));
  return {
    lectureKey,
    title: item.dataset.title || item.querySelector('.lecture-title')?.textContent || lectureKey,
    notesHref,
    slideHref,
    exercisesHref,
    videos,
  };
};

const renderTopMenu = (menuEl, entries, kind) => {
  if (!menuEl) return;
  const links = entries
    .map((entry) => (
      `<a href="${entry.href}" role="menuitem" data-kind="${kind}" data-kind-label="${entry.kindLabel || kind}" data-lecture-key="${entry.lectureKey}">${entry.label}</a>`
    ))
    .join('');
  menuEl.innerHTML = links || '<a href="#" role="menuitem">No items available</a>';
};

const updateTopMenus = () => {
  const resources = Array.from(lectureItems).map(getLectureResources);
  renderTopMenu(
    topNotesMenu,
    resources.map((r) => ({ lectureKey: r.lectureKey, href: r.notesHref || '#', label: r.title })),
    'Lecture Notes',
  );
  renderTopMenu(
    topSlidesMenu,
    resources
      .filter((r) => r.slideHref)
      .map((r) => ({ lectureKey: r.lectureKey, href: r.slideHref, label: r.title })),
    'Slides',
  );
  renderTopMenu(
    topVideosMenu,
    resources
      .flatMap((r) => r.videos
        .filter((v) => v.href)
        .map((v) => ({
          lectureKey: r.lectureKey,
          href: v.href,
          label: `${r.title} - ${v.label}`,
          kindLabel: `Video (${v.label})`,
        }))),
    'Video',
  );
  renderTopMenu(
    topExercisesMenu,
    resources.map((r) => ({ lectureKey: r.lectureKey, href: r.exercisesHref || '#', label: r.title })),
    'Exercises',
  );
};

const openResourceHref = (href, kindLabel) => {
  if (!href || href === '#') return;
  const activeItem = document.querySelector('.lecture-item.active');
  const context = !activeItem
    ? { title: 'Lecture', meta: '' }
    : {
      title: activeItem.dataset.title || activeItem.querySelector('.lecture-title')?.textContent || 'Lecture',
      meta: activeItem.dataset.meta || activeItem.querySelector('.lecture-meta')?.textContent || '',
    };
  if (lectureFrame) lectureFrame.src = href;
  if (lectureTitle) lectureTitle.textContent = `${context.title} - ${kindLabel}`;
  if (lectureMeta) lectureMeta.textContent = context.meta || '';
};

const openResourceInViewer = (event, kindLabel) => {
  const linkEl = event.currentTarget;
  event.preventDefault();
  if (!linkEl || linkEl.classList.contains('disabled')) return;
  const href = linkEl.getAttribute('href');
  openResourceHref(href, kindLabel);
};

if (navToggle && navMenu) {
  navToggle.addEventListener('click', () => {
    const isOpen = navMenu.classList.toggle('open');
    navToggle.setAttribute('aria-expanded', String(isOpen));
  });
}

const setActiveLecture = (item) => {
  if (!item || !lectureFrame) return;
  lectureItems.forEach((entry) => entry.classList.remove('active'));
  item.classList.add('active');

  const src = item.dataset.lecture;
  const title = item.dataset.title || item.querySelector('.lecture-title')?.textContent || 'Lecture';
  const meta = item.dataset.meta || item.querySelector('.lecture-meta')?.textContent || '';

  lectureFrame.src = src;
  if (lectureTitle) lectureTitle.textContent = title;
  if (lectureMeta) lectureMeta.textContent = meta || '';
  updateLectureMedia();
};

if (lectureList) {
  lectureList.addEventListener('click', (event) => {
    const item = event.target.closest('.lecture-item');
    if (!item) return;
    event.preventDefault();
    setActiveLecture(item);
  });
}

const frameHasInitialSrc = Boolean(
  lectureFrame && lectureFrame.getAttribute('src') && lectureFrame.getAttribute('src') !== '#',
);
const defaultLecture = document.querySelector('.lecture-item.active') || (!frameHasInitialSrc ? lectureItems[0] : null);
if (defaultLecture) {
  if (frameHasInitialSrc) {
    updateLectureMedia();
  } else {
    setActiveLecture(defaultLecture);
  }
}
updateTopMenus();

fetch('assets/media_resources.json')
  .then((response) => (response.ok ? response.json() : {}))
  .then((data) => {
    lectureMedia = data || {};
    updateLectureMedia();
    updateTopMenus();
  })
  .catch(() => {
    lectureMedia = {};
    updateLectureMedia();
    updateTopMenus();
  });

if (slidesLink) {
  slidesLink.addEventListener('click', (event) => openResourceInViewer(event, 'Slides'));
}

if (exerciseLink) {
  exerciseLink.addEventListener('click', (event) => openResourceInViewer(event, 'Exercises'));
}

if (notesLink) {
  notesLink.addEventListener('click', (event) => openResourceInViewer(event, 'Lecture Notes'));
}

if (demosLink) {
  demosLink.addEventListener('click', (event) => openResourceInViewer(event, 'Demos'));
}

if (topDemosLink) {
  topDemosLink.addEventListener('click', (event) => {
    event.preventDefault();
    openResourceHref('assets/demos.html', 'Demos');
  });
}

if (topDisclaimerLink) {
  topDisclaimerLink.addEventListener('click', (event) => {
    event.preventDefault();
    openResourceHref('assets/disclaimer.html', 'Disclaimer');
  });
}

if (topHandoutDemos) {
  topHandoutDemos.addEventListener('click', (event) => {
    event.preventDefault();
    openResourceHref('assets/demos.html', 'Demos');
  });
}

if (topHandoutDisclaimer) {
  topHandoutDisclaimer.addEventListener('click', (event) => {
    event.preventDefault();
    openResourceHref('assets/disclaimer.html', 'Disclaimer');
  });
}

if (navMenu) {
  navMenu.addEventListener('click', (event) => {
    const link = event.target.closest('.dropdown-menu a[data-kind][data-lecture-key]');
    if (!link) return;
    event.preventDefault();
    const lectureKey = link.dataset.lectureKey;
    const href = link.getAttribute('href');
    const kind = link.dataset.kind || 'Lecture Notes';
    const kindLabel = link.dataset.kindLabel || kind;
    const item = findLectureItemByKey(lectureKey);
    if (item) {
      setActiveLecture(item);
    }
    openResourceHref(href, kindLabel);
    closeAllDropdowns();
  });
}

if (videoLinks) {
  videoLinks.addEventListener('click', (event) => {
    const toggle = event.target.closest('.video-trigger');
    if (toggle) {
      event.preventDefault();
      event.stopPropagation();
      const menu = videoLinks.querySelector('.video-dropdown-menu');
      const expanded = toggle.getAttribute('aria-expanded') === 'true';
      closeVideoDropdown();
      toggle.setAttribute('aria-expanded', String(!expanded));
      if (menu) menu.style.display = expanded ? 'none' : 'block';
      return;
    }

    const link = event.target.closest('.video-menu-link');
    if (!link) return;
    event.preventDefault();
    const kind = link.dataset.kind || 'Video';
    const label = link.dataset.videoLabel;
    openResourceHref(link.getAttribute('href'), label ? `${kind} (${label})` : kind);
    closeVideoDropdown();
  });
}

document.querySelectorAll('.click-card').forEach((card) => {
  card.addEventListener('click', (event) => {
    if (event.target.closest('a')) return;
    const videoToggle = card.querySelector('#video-links .video-trigger');
    if (videoToggle) {
      videoToggle.click();
      return;
    }
    const link = card.querySelector('a.resource-link:not(.disabled)');
    if (!link) return;
    const kind = link.id === 'slides-link'
      ? 'Slides'
      : link.id === 'exercise-link'
        ? 'Exercises'
        : link.id === 'notes-link'
          ? 'Lecture Notes'
          : link.id === 'demos-link'
            ? 'Demos'
            : 'Video';
    openResourceHref(link.getAttribute('href'), kind);
  });
});

dropdownToggles.forEach((toggle) => {
  toggle.addEventListener('click', (event) => {
    event.stopPropagation();
    const isExpanded = toggle.getAttribute('aria-expanded') === 'true';
    closeAllDropdowns();
    toggle.setAttribute('aria-expanded', String(!isExpanded));
    const menu = toggle.parentElement.querySelector('.dropdown-menu');
    if (menu) menu.style.display = isExpanded ? 'none' : 'block';
  });
});

document.addEventListener('click', () => {
  closeAllDropdowns();
  closeVideoDropdown();
});

window.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') {
    closeAllDropdowns();
    closeVideoDropdown();
    if (navMenu) navMenu.classList.remove('open');
    if (navToggle) navToggle.setAttribute('aria-expanded', 'false');
  }
});

// --- Demo back-button: shown in viewer when a notebook is opened from demos.html.
let demoReturnUrl = '';

const createDemoBackButton = () => {
  const wrap = document.querySelector('.viewer-frame-wrap');
  if (!wrap || document.getElementById('demo-back-btn')) return document.getElementById('demo-back-btn');
  const bar = document.createElement('div');
  bar.id = 'demo-return-bar';
  bar.setAttribute('aria-label', 'Demo navigation');

  const btn = document.createElement('button');
  btn.id = 'demo-back-btn';
  btn.type = 'button';
  btn.textContent = 'Back to Demos';
  btn.addEventListener('click', () => {
    if (!demoReturnUrl) return;
    if (lectureFrame) lectureFrame.src = demoReturnUrl;
    hideDemoBackButton();
  });
  bar.appendChild(btn);
  wrap.prepend(bar);
  return btn;
};

const showDemoBackButton = (returnUrl, demoTitle) => {
  demoReturnUrl = returnUrl || 'assets/demos.html';
  document.querySelector('.viewer-frame-wrap')?.classList.add('demo-return-active');
  const btn = createDemoBackButton();
  const bar = document.getElementById('demo-return-bar');
  if (bar) bar.hidden = false;
  if (btn) btn.hidden = false;
  if (demoTitle && lectureTitle) lectureTitle.textContent = `${demoTitle} - Demo`;
};

const hideDemoBackButton = () => {
  demoReturnUrl = '';
  document.querySelector('.viewer-frame-wrap')?.classList.remove('demo-return-active');
  const bar = document.getElementById('demo-return-bar');
  if (bar) bar.hidden = true;
  const btn = document.getElementById('demo-back-btn');
  if (btn) btn.hidden = true;
};

window.addEventListener('message', (event) => {
  const data = event.data || {};
  if (data.type !== 'demo-open') return;
  showDemoBackButton(data.returnUrl, data.title);
});

// Hide the back button when the iframe navigates to anything that isn't a
// notebook. We read contentWindow.location.href (not getAttribute('src'))
// because target="lecture-frame" links don't update the src attribute.
if (lectureFrame) {
  lectureFrame.addEventListener('load', () => {
    let url = '';
    try { url = lectureFrame.contentWindow.location.href; } catch (e) {}
    if (!url.includes('/notebooks/')) hideDemoBackButton();
  });
}
