window.onscroll = function () {
  const backToTopButton = document.getElementById("back-to-top");
  if (
    document.body.scrollTop > 500 ||
    document.documentElement.scrollTop > 500
  ) {
    backToTopButton.classList.add("show");
  } else {
    backToTopButton.classList.remove("show");
  }
};

// Smooth scroll back to the top when the button is clicked
function scrollToTop() {
  window.scrollTo({ top: 0, behavior: "smooth" });
}
