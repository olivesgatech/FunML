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

const setNewTabAttributes = (linkEl) => {
  if (!linkEl) return;
  linkEl.setAttribute('target', '_blank');
  linkEl.setAttribute('rel', 'noopener noreferrer');
};

const clearNewTabAttributes = (linkEl) => {
  if (!linkEl) return;
  linkEl.removeAttribute('target');
  linkEl.removeAttribute('rel');
};

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
    linkEl.setAttribute('aria-disabled', 'false');
    setNewTabAttributes(linkEl);
    linkEl.textContent = label;
    return;
  }
  linkEl.classList.add('disabled');
  linkEl.setAttribute('href', '#');
  linkEl.setAttribute('aria-disabled', 'true');
  clearNewTabAttributes(linkEl);
  linkEl.textContent = label;
};

const escapeHtml = (value) => String(value || '')
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&#39;');

const normalizeVideoUrl = (url) => {
  if (!url) return '';
  try {
    const parsed = new URL(url);
    if (parsed.hostname.includes('youtu.be')) {
      const id = parsed.pathname.replace('/', '');
      return id ? `https://www.youtube.com/watch?v=${id}` : url;
    }
    if (parsed.hostname.includes('youtube.com')) {
      const id = parsed.searchParams.get('v');
      return id ? `https://www.youtube.com/watch?v=${id}` : url;
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
  const demoHref = media.demo || 'assets/demos.html';

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
      const href = normalizeVideoUrl(recording.url || '');
      const label = normalizeRecordingLabel(recording.label, idx);
      return `<a class="video-menu-link" href="${escapeHtml(href)}" role="menuitem" target="_blank" rel="noopener noreferrer" data-kind="Video" data-video-label="${escapeHtml(label)}">${escapeHtml(label)}</a>`;
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
    href: normalizeVideoUrl(recording.url || ''),
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
      `<a href="${entry.href}" role="menuitem" target="_blank" rel="noopener noreferrer" data-kind="${kind}" data-kind-label="${entry.kindLabel || kind}" data-lecture-key="${entry.lectureKey}">${entry.label}</a>`
    ))
    .join('');
  menuEl.innerHTML = links || '<a href="#" role="menuitem" aria-disabled="true">No items available</a>';
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

const keepDisabledLinksInactive = (event) => {
  const linkEl = event.currentTarget;
  const href = linkEl?.getAttribute('href');
  if (!linkEl || linkEl.classList.contains('disabled') || !href || href === '#') {
    event.preventDefault();
  }
};

const openLinkInNewTab = (linkEl) => {
  const href = linkEl?.getAttribute('href');
  if (!href || href === '#' || linkEl.classList.contains('disabled')) return;
  window.open(href, '_blank', 'noopener,noreferrer');
};

const configureLectureItemLink = (item) => {
  if (!item) return;
  const href = item.dataset.lecture || '#';
  item.setAttribute('href', href);
  if (href === '#') {
    clearNewTabAttributes(item);
    item.setAttribute('aria-disabled', 'true');
    return;
  }
  setNewTabAttributes(item);
  item.setAttribute('aria-disabled', 'false');
};

const setStaticLinkHref = (linkEl, href) => {
  if (!linkEl) return;
  linkEl.setAttribute('href', href);
  setNewTabAttributes(linkEl);
};

lectureItems.forEach(configureLectureItemLink);
setStaticLinkHref(topDemosLink, 'assets/demos.html');
setStaticLinkHref(topDisclaimerLink, 'assets/disclaimer.html');
setStaticLinkHref(topHandoutDemos, 'assets/demos.html');
setStaticLinkHref(topHandoutDisclaimer, 'assets/disclaimer.html');

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
  slidesLink.addEventListener('click', keepDisabledLinksInactive);
}

if (exerciseLink) {
  exerciseLink.addEventListener('click', keepDisabledLinksInactive);
}

if (notesLink) {
  notesLink.addEventListener('click', keepDisabledLinksInactive);
}

if (demosLink) {
  demosLink.addEventListener('click', keepDisabledLinksInactive);
}

if (navMenu) {
  navMenu.addEventListener('click', (event) => {
    const link = event.target.closest('.dropdown-menu a[data-kind][data-lecture-key]');
    if (!link) return;
    const lectureKey = link.dataset.lectureKey;
    const item = findLectureItemByKey(lectureKey);
    if (item) {
      setActiveLecture(item);
    }
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
    openLinkInNewTab(link);
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
