document.addEventListener('DOMContentLoaded', () => {
    const galleryItems = document.querySelectorAll('.gallery-item');
    const prevButton = document.querySelector('.prev');
    const nextButton = document.querySelector('.next');
    const gallery = document.querySelector('.gallery');
    let currentIndex = 0;

    if (!galleryItems.length || !prevButton || !nextButton) {
        return;
    }

    function showImage(index) {
        // slide the gallery to the left or right
        gallery.style.transform = `translateX(-${index * 100}%)`;

        // toggling active class
        galleryItems.forEach((item, i) => {
            if (i === index) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }

    prevButton.addEventListener('click', () => {
        currentIndex = (currentIndex - 1 + galleryItems.length) % galleryItems.length;
        showImage(currentIndex);
    });

    nextButton.addEventListener('click', () => {
        currentIndex = (currentIndex + 1) % galleryItems.length;
        showImage(currentIndex);
    });

    showImage(currentIndex);
});