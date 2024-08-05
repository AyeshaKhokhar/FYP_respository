 // Get the modal
        var modal = document.getElementById("imageModal");

        // Get the gallery container inside the modal
        var modalGallery = document.querySelector('.modal-gallery');

        // Get the close button
        var span = document.getElementsByClassName("close")[0];

        // Get all images that should be part of the gallery
        var images = document.querySelectorAll('.small-images img, .big-image, .gallery img');

        // Function to open modal with gallery images
        function openModal() {
            // Clear any existing images in the modal gallery
            modalGallery.innerHTML = '';

            // Add all images to the modal gallery
            images.forEach(function(image) {
                var img = document.createElement('img');
                img.src = image.src;
                modalGallery.appendChild(img);
            });

            // Display the modal
            modal.style.display = "block";
        }

        // Add click event listeners to all images
        images.forEach(function(image) {
            image.addEventListener('click', openModal);
        });

        // When the user clicks on <span> (x), close the modal
        span.onclick = function() {
            modal.style.display = "none";
        }

        // When the user clicks anywhere outside of the modal, close it
        window.onclick = function(event) {
            if (event.target == modal) {
                modal.style.display = "none";
            }
        }


    document.getElementById('checkin-date').addEventListener('change', function () {
        var checkinDate = this.value;
        document.getElementById('checkout-date').setAttribute('min', checkinDate);
    });

    document.getElementById('checkout-date').addEventListener('change', function () {
        var checkoutDate = this.value;
        document.getElementById('checkin-date').setAttribute('max', checkoutDate);
    });


    
    document.addEventListener("DOMContentLoaded", () => {
      const bars = document.querySelectorAll(".progress-bar-container");
    
      bars.forEach(bar => {
        const valueElement = bar.querySelector(".progress-value");
        const fillElement = bar.querySelector(".progress-bar-fill");
        const iconElement = bar.querySelector(".warning-icon");
        const value = parseFloat(valueElement.innerText); // Convert to float
        const maxValue = 5; // Maximum value for the rating
        const percentage = (value / maxValue) * 100;
    
        // Set the width of the fill element based on the percentage
        fillElement.style.width = `${percentage}%`;
    
        // Change color and icon display based on the value
        if (value > 3.1) {
          fillElement.style.backgroundColor = "rgb(179, 125, 54)";
          if (iconElement) iconElement.style.display = "none";
        } else {
          fillElement.style.backgroundColor = "#BE0404";
          if (iconElement) iconElement.style.display = "inline-block";
        }
      });
    });

    document.addEventListener("DOMContentLoaded", () => {
      const container = document.querySelector('.reviews-container');
      const leftButton = document.querySelector('.scroll-button.left');
      const rightButton = document.querySelector('.scroll-button.right');
    
      leftButton.addEventListener('click', () => {
        container.scrollBy({ left: -container.offsetWidth / 3, behavior: 'smooth' });
      });
    
      rightButton.addEventListener('click', () => {
        container.scrollBy({ left: container.offsetWidth / 3, behavior: 'smooth' });
      });
    });
    document.querySelectorAll('.review-box').forEach(box => {
      const author = box.querySelector('.review-author').textContent;
      const initial = author.trim().charAt(0).toUpperCase(); // Get first letter and capitalize
      const initialBox = box.querySelector('.guest-initial');
      initialBox.textContent = initial; // Set the initial inside the circle
    });

    document.addEventListener("DOMContentLoaded", () => {
      const container = document.querySelector('.reviews-container');
      const leftButton = document.querySelector('.scroll-button.left');
      const rightButton = document.querySelector('.scroll-button.right');
    
      leftButton.addEventListener('click', () => {
        container.scrollBy({ left: -container.offsetWidth / 4, behavior: 'smooth' });
      });
    
      rightButton.addEventListener('click', () => {
        container.scrollBy({ left: container.offsetWidth / 4, behavior: 'smooth' });
      });
    });
    