
// Secure Trade AI - Dashboard JavaScript

document.addEventListener("DOMContentLoaded", function () {

    // Sidebar Toggle
    const menuBtn = document.getElementById("menuBtn");
    const sidebar = document.getElementById("sidebar");

    if (menuBtn && sidebar) {

        menuBtn.addEventListener("click", function () {
            sidebar.classList.toggle("show");
        });

    }

    // Close sidebar when clicking outside
    document.addEventListener("click", function (event) {

        if (
            sidebar &&
            menuBtn &&
            !sidebar.contains(event.target) &&
            !menuBtn.contains(event.target)
        ) {
            sidebar.classList.remove("show");
        }

    });

    // Close sidebar using Escape key
    document.addEventListener("keydown", function (event) {

        if (event.key === "Escape" && sidebar) {
            sidebar.classList.remove("show");
        }

    });

});
