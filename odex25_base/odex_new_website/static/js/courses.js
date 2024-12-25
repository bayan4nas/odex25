$(document).ready(function () {

    gsap.registerPlugin(ScrollTrigger);

    const tabButtonsCourses = document.querySelectorAll(".courses_section .tab-btn");
    const trainingFieldContents = document.querySelectorAll(".training_field");
    const allCoursesLinks = document.querySelectorAll(".all_courses");

    function openTabCourses(tabIndex) {
        trainingFieldContents.forEach((content) => {
            content.style.display = "none";
        });

        tabButtonsCourses.forEach((button) => {
            button.classList.remove("active");
        });

        if (trainingFieldContents.length > 0) {
            if (tabIndex === 0) {
                trainingFieldContents[0].style.display = "block";
            } else {
                if (tabIndex < trainingFieldContents.length) {
                    trainingFieldContents[tabIndex].style.display = "block";
                }
            }

            tabButtonsCourses[tabIndex].classList.add("active");
        }

        ScrollTrigger.refresh();
    }

    tabButtonsCourses.forEach((button, index) => {
        button.addEventListener("click", function () {
            openTabCourses(index);
        });
    });

    allCoursesLinks.forEach((link) => {
        link.addEventListener("click", function (e) {
            e.preventDefault();
            openTabCourses(0);
        });
    });

    openTabCourses(0);


    function initGsapForLargeScreens() {
        if (window.innerWidth >= 1366) {
            gsap.to('.courses_categories_sidebar', {
                scrollTrigger: {
                    trigger: ".courses_list_container",
                    start: "top 20%",
                    end: "bottom",
                    pin: ".courses_categories_sidebar",
                }
            });
        }
    }
    
    initGsapForLargeScreens();
    window.addEventListener('resize', initGsapForLargeScreens);    

})