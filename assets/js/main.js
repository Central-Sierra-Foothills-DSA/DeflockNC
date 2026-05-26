// Intersection observer for stat cells
const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((e) => {
      if (e.isIntersecting) {
        e.target.style.opacity = "1";
        e.target.style.transform = "translateY(0)";
      }
    });
  },
  { threshold: 0.1 },
);

document.querySelectorAll(".stat-cell, .demand-item, .agency-item").forEach((el) => {
  el.style.opacity = "0";
  el.style.transform = "translateY(16px)";
  el.style.transition = "opacity 0.5s, transform 0.5s";
  observer.observe(el);
});

// Short/long toggle for sample public comment
document.querySelectorAll(".comment-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    const target = tab.dataset.show;
    document
      .querySelectorAll(".comment-tab")
      .forEach((t) => t.classList.toggle("active", t === tab));
    document
      .querySelectorAll(".comment-box")
      .forEach((box) => box.classList.toggle("hidden", box.dataset.length !== target));
  });
});

// Mailing-list form: swap to success message after Google receives it
const signupForm = document.getElementById("signup-form");
const signupSuccess = document.getElementById("signup-success");
const signupSink = document.getElementById("signup-sink");
if (signupForm && signupSuccess && signupSink) {
  signupForm.addEventListener("submit", () => {
    const submit = signupForm.querySelector(".signup-submit");
    if (submit) {
      submit.disabled = true;
      submit.textContent = "Sending…";
    }
    // The form posts to a hidden iframe; when Google's response loads, swap UI.
    signupSink.addEventListener(
      "load",
      () => {
        signupForm.hidden = true;
        signupSuccess.hidden = false;
        signupSuccess.scrollIntoView({ behavior: "smooth", block: "center" });
      },
      { once: true },
    );
  });
}

// Copy-to-clipboard for sample public comment
document.querySelectorAll("[data-copy-target]").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const target = document.querySelector(btn.dataset.copyTarget);
    if (!target) return;
    const text = target.innerText.trim();
    try {
      await navigator.clipboard.writeText(text);
      const original = btn.textContent;
      btn.textContent = "Copied!";
      btn.classList.add("copied");
      setTimeout(() => {
        btn.textContent = original;
        btn.classList.remove("copied");
      }, 1800);
    } catch (e) {
      btn.textContent = "Copy failed — select & copy manually";
    }
  });
});
