document.addEventListener("DOMContentLoaded", () => {
  // Dismiss flash messages
  document.querySelectorAll(".flash-close").forEach((btn) => {
    btn.addEventListener("click", () => {
      const flash = btn.closest(".flash");
      if (flash) flash.remove();
    });
  });

  // Auto-hide flash messages after 6s
  document.querySelectorAll(".flash").forEach((flash) => {
    setTimeout(() => {
      flash.style.transition = "opacity .4s ease";
      flash.style.opacity = "0";
      setTimeout(() => flash.remove(), 400);
    }, 6000);
  });

  // Confirm destructive actions
  document.querySelectorAll("[data-confirm]").forEach((el) => {
    el.addEventListener("submit", (e) => {
      const msg = el.getAttribute("data-confirm") || "Are you sure?";
      if (!confirm(msg)) e.preventDefault();
    });
  });

  // Auto-scroll message thread to bottom
  const thread = document.querySelector(".thread");
  if (thread) thread.scrollTop = thread.scrollHeight;
});
