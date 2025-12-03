(function(){
  const carousel = document.getElementById('breachCarousel');
  if(!carousel) return;
  const track = carousel.querySelector('.carousel-track');
  const slides = Array.from(track.children);
  const prevBtn = carousel.querySelector('.carousel-control.prev');
  const nextBtn = carousel.querySelector('.carousel-control.next');

  let index = 0;
  function update(){
    const slideWidth = slides[0]?.getBoundingClientRect().width || 300;
    track.style.transform = `translateX(-${index * slideWidth}px)`;
  }

  function next(){
    index = (index + 1) % slides.length;
    update();
  }
  function prev(){
    index = (index - 1 + slides.length) % slides.length;
    update();
  }

  // Resize handler to keep images fitting and track translating correctly
  window.addEventListener('resize', update);

  nextBtn.addEventListener('click', next);
  prevBtn.addEventListener('click', prev);

  // Auto-rotate every 5s
  let timer = setInterval(next, 5000);
  carousel.addEventListener('mouseenter', () => clearInterval(timer));
  carousel.addEventListener('mouseleave', () => timer = setInterval(next, 5000));

  // Ensure images have fallback
  slides.forEach(slide => {
    const img = slide.querySelector('img');
    if(!img) return;
    img.addEventListener('error', () => {
      img.src = img.dataset.fallback || img.src;
    });
  });

  // Initial update
  update();
})();

