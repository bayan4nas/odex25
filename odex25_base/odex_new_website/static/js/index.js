$(document).ready(function () {

    // Header Slider
    const swiperHeader = new Swiper(".cta", {
        centeredSlides: false,
        spaceBetween: 40,
        grabCursor: true,
        loop: true,
        autoplay: {
            delay: 5000,
            disableOnInteraction: false,
        },
        autoplay: false,
        breakpoints: {
            1: {
                slidesPerView: 1,
            },
        },
        pagination: {
            el: ".swiper-pagination",
            clickable: true,
        },
    });

    const tabButtons = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");

    if (tabButtons.length > 0 && tabContents.length > 0) {
        function openTab(tabIndex) {
            tabContents.forEach((content) => {
                content.style.display = "none";
            });

            tabButtons.forEach((button) => {
                button.classList.remove("active");
            });

            tabContents[tabIndex].style.display = "flex";
            tabButtons[tabIndex].classList.add("active");
        }

        tabButtons.forEach((button, index) => {
            button.addEventListener("click", function () {
                openTab(index);
            });
        });

        openTab(0);
    }




    // course level
    // Function to update the indicator based on course level
    function setCourseLevel(level) {
        const bars = document.querySelectorAll(".bar");

        // Reset all bars
        bars.forEach((bar, index) => {
            if (index < level) {
                bar.classList.add("active");
            } else {
                bar.classList.remove("active");
            }
        });
    }

    setCourseLevel(3);


})