document.addEventListener('DOMContentLoaded', () => {
    // Select the hamburger menu element
    const mobileMenu = document.getElementById('mobile-menu');
    // Select the nav links container
    const navLinks = document.querySelector('.nav-links');

    if (mobileMenu && navLinks) {
        mobileMenu.addEventListener('click', () => {
            // Toggle the 'active' class on the links container
            navLinks.classList.toggle('active');
            
            // Toggle the icon between Hamburger (☰) and Close (✕)
            if (navLinks.classList.contains('active')) {
                mobileMenu.textContent = '✕';
            } else {
                mobileMenu.textContent = '☰';
            }
        });
    }
});
