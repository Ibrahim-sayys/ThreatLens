// Initialize carousel with infinite loop support
function initCarousel(carouselId) {
  const carousel = document.getElementById(carouselId);
  if(!carousel) return;
  const track = carousel.querySelector('.carousel-track');
  const slides = Array.from(track.children);
  const prevBtn = carousel.querySelector('.carousel-control.prev');
  const nextBtn = carousel.querySelector('.carousel-control.next');

  if(slides.length === 0) return;

  // Clone all slides and append to track for infinite loop
  slides.forEach(slide => {
    const clone = slide.cloneNode(true);
    track.appendChild(clone);
  });

  // Update slides array to include clones
  const allSlides = Array.from(track.children);
  let index = 0;
  let isTransitioning = false;

  function getSlideWidth(){
    return allSlides[0]?.getBoundingClientRect().width || 300;
  }

  function update(withTransition = true){
    const slideWidth = getSlideWidth();
    if(withTransition){
      track.style.transition = 'transform 0.4s ease';
    } else {
      track.style.transition = 'none';
    }
    track.style.transform = `translateX(-${index * slideWidth}px)`;
  }

  function next(){
    if(isTransitioning) return;
    isTransitioning = true;
    index++;
    update(true);

    // If we reach the cloned set, jump back to the real first slide
    if(index >= slides.length){
      setTimeout(() => {
        index = 0;
        update(false);
        isTransitioning = false;
      }, 400);
    } else {
      setTimeout(() => { isTransitioning = false; }, 400);
    }
  }

  function prev(){
    if(isTransitioning) return;
    isTransitioning = true;

    // If at the start, jump to the last real slide
    if(index === 0){
      index = slides.length;
      update(false);
      setTimeout(() => {
        index--;
        update(true);
        setTimeout(() => { isTransitioning = false; }, 400);
      }, 20);
    } else {
      index--;
      update(true);
      setTimeout(() => { isTransitioning = false; }, 400);
    }
  }

  // Resize handler to keep images fitting and track translating correctly
  window.addEventListener('resize', () => update(false));

  nextBtn.addEventListener('click', next);
  prevBtn.addEventListener('click', prev);

  // Auto-rotate every 5s
  let timer = setInterval(next, 5000);
  carousel.addEventListener('mouseenter', () => clearInterval(timer));
  carousel.addEventListener('mouseleave', () => timer = setInterval(next, 5000));

  // Ensure images have fallback
  allSlides.forEach(slide => {
    const img = slide.querySelector('img');
    if(!img) return;
    img.addEventListener('error', () => {
      img.src = img.dataset.fallback || img.src;
    });
  });

  // Initial update
  update(false);
}

// Initialize both carousels
(function(){
  initCarousel('breachCarousel');
  initCarousel('documentCarousel');
})();



