// Burger Menu Toggle Functionality
document.addEventListener('DOMContentLoaded', function() {
    const burgerMenu = document.getElementById('burgerMenu');
    const navbarMenu = document.getElementById('navbarMenu');

    if (burgerMenu && navbarMenu) {
        burgerMenu.addEventListener('click', function() {
            burgerMenu.classList.toggle('active');
            navbarMenu.classList.toggle('active');
        });

        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!burgerMenu.contains(event.target) && !navbarMenu.contains(event.target)) {
                burgerMenu.classList.remove('active');
                navbarMenu.classList.remove('active');
            }
        });

        // Close menu when clicking on a link
        const navLinks = navbarMenu.querySelectorAll('a');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                burgerMenu.classList.remove('active');
                navbarMenu.classList.remove('active');
            });
        });
    }



    // Profile Dropdown Toggle Functionality
    const profileToggle = document.getElementById('profileToggle');
    const profileMenu = document.getElementById('profileMenu');

    if (profileToggle && profileMenu) {
        profileToggle.addEventListener('click', function(event) {
            event.stopPropagation();
            profileMenu.classList.toggle('active');
        });

        // Close profile menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!profileToggle.contains(event.target) && !profileMenu.contains(event.target)) {
                profileMenu.classList.remove('active');
            }
        });

        // Close profile menu when clicking on a link
        const profileLinks = profileMenu.querySelectorAll('a');
        profileLinks.forEach(link => {
            link.addEventListener('click', function() {
                profileMenu.classList.remove('active');
            });
        });
    }
});
