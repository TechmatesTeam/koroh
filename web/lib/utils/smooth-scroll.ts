export function smoothScrollTo(elementId: string, offset: number = 0) {
  const element = document.getElementById(elementId);
  if (element) {
    const elementPosition = element.getBoundingClientRect().top;
    const offsetPosition = elementPosition + window.pageYOffset - offset;

    window.scrollTo({
      top: offsetPosition,
      behavior: 'smooth'
    });
  }
}

export function smoothScrollToTop() {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  });
}

export function addSmoothScrollToLinks() {
  const links = document.querySelectorAll('a[href^="#"]');
  
  links.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const href = link.getAttribute('href');
      if (href && href.startsWith('#')) {
        const targetId = href.substring(1);
        smoothScrollTo(targetId, 80); // 80px offset for fixed header
      }
    });
  });
}

// Parallax scroll effect
export function addParallaxEffect(selector: string, speed: number = 0.5) {
  const elements = document.querySelectorAll(selector);
  
  function updateParallax() {
    const scrolled = window.pageYOffset;
    
    elements.forEach((element) => {
      const rate = scrolled * -speed;
      (element as HTMLElement).style.transform = `translateY(${rate}px)`;
    });
  }
  
  window.addEventListener('scroll', updateParallax);
  
  return () => {
    window.removeEventListener('scroll', updateParallax);
  };
}