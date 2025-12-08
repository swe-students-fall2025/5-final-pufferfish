let educationCount = 1;
let experienceCount = 1;
let skillsCount = 1;
let projectsCount = 1;

// Add Education Entry
document.getElementById("addEducation")?.addEventListener("click", function () {
  const section = document.getElementById("educationSection");
  const newIndex = educationCount;
  educationCount++;

  const newEntry = document.createElement("div");
  newEntry.className = "education-entry";
  newEntry.setAttribute("data-index", newIndex);

  newEntry.innerHTML = `
        <div class="form-row">
            <div class="form-group">
                <label>School:<span class="required">*</span></label>
                <input type="text" name="education_${newIndex}_school" required>
            </div>
            <div class="form-group">
                <label>School Location:</label>
                <input type="text" name="education_${newIndex}_location">
            </div>
        </div>
        <div class="form-row">
            <div class="form-group">
                <label>Degree:</label>
                <input type="text" name="education_${newIndex}_degree" placeholder="e.g., BS, MS, PhD">
            </div>
            <div class="form-group">
                <label>Field of study:</label>
                <input type="text" name="education_${newIndex}_field" placeholder="e.g., Computer Science">
            </div>
        </div>
        <div class="form-row">
            <div class="form-group">
                <label>Graduation Date:</label>
                <div class="date-inputs">
                    <select name="education_${newIndex}_graduation_month" class="date-select">
                        <option value="">Month</option>
                        <option value="01">January</option>
                        <option value="02">February</option>
                        <option value="03">March</option>
                        <option value="04">April</option>
                        <option value="05">May</option>
                        <option value="06">June</option>
                        <option value="07">July</option>
                        <option value="08">August</option>
                        <option value="09">September</option>
                        <option value="10">October</option>
                        <option value="11">November</option>
                        <option value="12">December</option>
                    </select>
                    <input type="number" name="education_${newIndex}_graduation_year" class="date-input" placeholder="Year" min="1900" max="2100">
                </div>
            </div>
        </div>
        <button type="button" class="btn btn-small" onclick="removeEntry(this, 'education')">Remove</button>
    `;

  const addButton = document.getElementById("addEducation");
  section.insertBefore(newEntry, addButton);
  updateEducationCount();
  saveFormData();
});

// Add Experience Entry
document
  .getElementById("addExperience")
  ?.addEventListener("click", function () {
    const section = document.getElementById("experienceSection");
    const newIndex = experienceCount;
    experienceCount++;

    const newEntry = document.createElement("div");
    newEntry.className = "experience-entry";
    newEntry.setAttribute("data-index", newIndex);

    newEntry.innerHTML = `
        <div class="form-row">
            <div class="form-group">
                <label>Title:<span class="required">*</span></label>
                <input type="text" name="experience_${newIndex}_title" required>
            </div>
            <div class="form-group">
                <label>Company:<span class="required">*</span></label>
                <input type="text" name="experience_${newIndex}_company" required>
            </div>
        </div>
        <div class="form-row">
            <div class="form-group full-width">
                <label>Location:</label>
                <input type="text" name="experience_${newIndex}_location">
            </div>
        </div>
        <div class="form-row">
            <div class="form-group">
                <label>Start Date:</label>
                <div class="date-inputs">
                    <select name="experience_${newIndex}_start_month" class="date-select">
                        <option value="">Month</option>
                        <option value="01">January</option>
                        <option value="02">February</option>
                        <option value="03">March</option>
                        <option value="04">April</option>
                        <option value="05">May</option>
                        <option value="06">June</option>
                        <option value="07">July</option>
                        <option value="08">August</option>
                        <option value="09">September</option>
                        <option value="10">October</option>
                        <option value="11">November</option>
                        <option value="12">December</option>
                    </select>
                    <input type="number" name="experience_${newIndex}_start_year" class="date-input" placeholder="Year" min="1900" max="2100">
                </div>
            </div>
            <div class="form-group">
                <label>End Date:</label>
                <div class="date-inputs">
                    <select name="experience_${newIndex}_end_month" class="date-select">
                        <option value="">Month</option>
                        <option value="01">January</option>
                        <option value="02">February</option>
                        <option value="03">March</option>
                        <option value="04">April</option>
                        <option value="05">May</option>
                        <option value="06">June</option>
                        <option value="07">July</option>
                        <option value="08">August</option>
                        <option value="09">September</option>
                        <option value="10">October</option>
                        <option value="11">November</option>
                        <option value="12">December</option>
                    </select>
                    <input type="number" name="experience_${newIndex}_end_year" class="date-input" placeholder="Year" min="1900" max="2100">
                </div>
            </div>
        </div>
        <div class="form-row">
            <div class="form-group">
                <label class="checkbox-label">
                    <input type="checkbox" name="experience_${newIndex}_currently_working" value="true">
                    I currently work here
                </label>
            </div>
        </div>
        <div class="bullets-container" data-entry-index="${newIndex}">
            <div class="form-row" data-bullet-index="0">
                <div class="form-group full-width">
                    <label>Bullet point:</label>
                    <input type="text" name="experience_${newIndex}_bullet_0" placeholder="Describe your responsibilities and achievements...">
                </div>
                <div class="form-group" style="flex: 0 0 auto; align-self: flex-end; padding-top: 1.5rem;">
                    <button type="button" class="btn btn-small" onclick="removeBulletPoint(this, ${newIndex}, 'experience')">Delete</button>
                </div>
            </div>
            <div class="form-row" data-bullet-index="1">
                <div class="form-group full-width">
                    <label>Bullet point:</label>
                    <input type="text" name="experience_${newIndex}_bullet_1" placeholder="Describe your responsibilities and achievements...">
                </div>
                <div class="form-group" style="flex: 0 0 auto; align-self: flex-end; padding-top: 1.5rem;">
                    <button type="button" class="btn btn-small" onclick="removeBulletPoint(this, ${newIndex}, 'experience')">Delete</button>
                </div>
            </div>
        </div>
        <button type="button" class="btn btn-small" onclick="addBulletPoint(${newIndex}, 'experience')">Add bullet point</button>
        <button type="button" class="btn btn-small" onclick="removeEntry(this, 'experience')">Remove Experience</button>
    `;

    const addButton = document.getElementById("addExperience");
    section.insertBefore(newEntry, addButton);
    updateExperienceCount();
    saveFormData();
  });

// Add Skill Entry
document.getElementById("addSkill")?.addEventListener("click", function () {
  const section = document.getElementById("skillsSection");
  const newIndex = skillsCount;
  skillsCount++;

  const newEntry = document.createElement("div");
  newEntry.className = "skill-entry";
  newEntry.setAttribute("data-index", newIndex);

  newEntry.innerHTML = `
        <div class="form-row">
            <div class="form-group">
                <label>Skill Category:</label>
                <input type="text" name="skill_${newIndex}_category" placeholder="e.g., Programming Languages, Frameworks, Spoken Languages">
            </div>
            <div class="form-group">
                <label>Skills:</label>
                <input type="text" name="skill_${newIndex}_skills" placeholder="Comma-separated list (e.g., Python, Java, JavaScript)">
            </div>
        </div>
        <button type="button" class="btn btn-small" onclick="removeEntry(this, 'skill')">Remove</button>
    `;

  const addButton = document.getElementById("addSkill");
  section.insertBefore(newEntry, addButton);
  updateSkillsCount();
  saveFormData();
});

// Add Project Entry
document.getElementById("addProject")?.addEventListener("click", function () {
  const section = document.getElementById("projectsSection");
  const newIndex = projectsCount;
  projectsCount++;

  const newEntry = document.createElement("div");
  newEntry.className = "project-entry";
  newEntry.setAttribute("data-index", newIndex);

  newEntry.innerHTML = `
        <div class="form-row">
            <div class="form-group">
                <label>Title:</label>
                <input type="text" name="project_${newIndex}_title">
            </div>
            <div class="form-group">
                <label>Name:</label>
                <input type="text" name="project_${newIndex}_name" placeholder="e.g., CS Senior Capstone, Personal Project">
            </div>
        </div>
        <div class="bullets-container" data-entry-index="${newIndex}">
            <div class="form-row" data-bullet-index="0">
                <div class="form-group full-width">
                    <label>Bullet point:</label>
                    <input type="text" name="project_${newIndex}_bullet_0" placeholder="Describe the project...">
                </div>
                <div class="form-group" style="flex: 0 0 auto; align-self: flex-end; padding-top: 1.5rem;">
                    <button type="button" class="btn btn-small" onclick="removeBulletPoint(this, ${newIndex}, 'project')">Delete</button>
                </div>
            </div>
            <div class="form-row" data-bullet-index="1">
                <div class="form-group full-width">
                    <label>Bullet point:</label>
                    <input type="text" name="project_${newIndex}_bullet_1" placeholder="Describe the project...">
                </div>
                <div class="form-group" style="flex: 0 0 auto; align-self: flex-end; padding-top: 1.5rem;">
                    <button type="button" class="btn btn-small" onclick="removeBulletPoint(this, ${newIndex}, 'project')">Delete</button>
                </div>
            </div>
        </div>
        <button type="button" class="btn btn-small" onclick="addBulletPoint(${newIndex}, 'project')">Add bullet point</button>
        <button type="button" class="btn btn-small" onclick="removeEntry(this, 'project')">Remove Project</button>
    `;

  const addButton = document.getElementById("addProject");
  section.insertBefore(newEntry, addButton);
  updateProjectsCount();
  saveFormData();
});

// Add Bullet Point
function addBulletPoint(entryIndex, type) {
  // Find the specific container by looking for the parent entry first, then the bullets container
  const parentEntry = document.querySelector(
    `.${type}-entry[data-index="${entryIndex}"]`
  );
  if (!parentEntry) return;

  const container = parentEntry.querySelector(
    `.bullets-container[data-entry-index="${entryIndex}"]`
  );
  if (!container) return;

  const bulletIndex = container.querySelectorAll(".form-row").length;

  const newBullet = document.createElement("div");
  newBullet.className = "form-row";
  newBullet.setAttribute("data-bullet-index", bulletIndex);

  const placeholder =
    type === "experience"
      ? "Describe your responsibilities and achievements..."
      : "Describe the project...";

  newBullet.innerHTML = `
        <div class="form-group full-width">
            <label>Bullet point:</label>
            <input type="text" name="${type}_${entryIndex}_bullet_${bulletIndex}" placeholder="${placeholder}">
        </div>
        <div class="form-group" style="flex: 0 0 auto; align-self: flex-end; padding-top: 1.5rem;">
            <button type="button" class="btn btn-small" onclick="removeBulletPoint(this, ${entryIndex}, '${type}')">Delete</button>
        </div>
    `;

  container.appendChild(newBullet);
  saveFormData();
}

// Remove Bullet Point
function removeBulletPoint(button, entryIndex, type) {
  const bulletRow = button.closest(".form-row");
  if (bulletRow) {
    bulletRow.remove();
    saveFormData();
  }
}

// Remove Entry
function removeEntry(button, type) {
  const entry = button.closest(`.${type}-entry`);
  if (entry) {
    entry.remove();

    // Update counts
    if (type === "education") {
      updateEducationCount();
    } else if (type === "experience") {
      updateExperienceCount();
    } else if (type === "skill") {
      updateSkillsCount();
    } else if (type === "project") {
      updateProjectsCount();
    }
    saveFormData();
  }
}

// Update Count Functions
function updateEducationCount() {
  const count = document.querySelectorAll(".education-entry").length;
  document.getElementById("education_count").value = count;
}

function updateExperienceCount() {
  const count = document.querySelectorAll(".experience-entry").length;
  document.getElementById("experience_count").value = count;
}

function updateSkillsCount() {
  const count = document.querySelectorAll(".skill-entry").length;
  document.getElementById("skills_count").value = count;
}

function updateProjectsCount() {
  const count = document.querySelectorAll(".project-entry").length;
  document.getElementById("projects_count").value = count;
}

// URL and Email Validation
function validateURL(url) {
  if (!url) return true; // Empty is OK (not required)
  // Accept URLs with or without http://, https://, or www.
  // Just check if it looks like a URL (has at least a domain)
  const urlPattern =
    /^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}(\/.*)?$|^https?:\/\/.+/i;
  return urlPattern.test(url.trim());
}

function validateEmail(email) {
  const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  return emailPattern.test(email);
}

// Auto-format URLs to add https:// if missing (optional, doesn't require it)
function formatURL(url) {
  if (!url) return url;
  url = url.trim();
  // Only auto-add https:// if it looks like a domain (has a dot and looks like a URL)
  // But don't force it - user can leave it without https://
  if (
    url &&
    !url.match(/^https?:\/\//i) &&
    url.match(/^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\./)
  ) {
    // Optional: uncomment below to auto-add https://
    // return "https://" + url;
  }
  return url;
}

// Real-time validation for email and URLs
document.addEventListener(
  "blur",
  function (e) {
    if (e.target.type === "email") {
      const email = e.target.value;
      if (email && !validateEmail(email)) {
        e.target.setCustomValidity(
          "Please enter a valid email address (e.g., user@example.com)"
        );
        e.target.reportValidity();
      } else {
        e.target.setCustomValidity("");
      }
    } else if (e.target.id === "linkedin" || e.target.id === "website") {
      let url = e.target.value;
      if (url) {
        url = url.trim();
        // Optional: auto-format URL (commented out to allow URLs without https://)
        // const formattedURL = formatURL(url);
        // if (formattedURL !== url) {
        //   e.target.value = formattedURL;
        //   url = formattedURL;
        // }
      }
      if (url && !validateURL(url)) {
        e.target.setCustomValidity(
          "Please enter a valid URL (e.g., linkedin.com/in/profile or https://linkedin.com/in/profile)"
        );
        e.target.reportValidity();
      } else {
        e.target.setCustomValidity("");
      }
    }
  },
  true
);

// Handle currently working checkbox - disable end date
document.addEventListener("change", function (e) {
  if (
    e.target.type === "checkbox" &&
    e.target.name.includes("currently_working")
  ) {
    const entry = e.target.closest(".experience-entry");
    const entryIndex = entry.getAttribute("data-index");
    const endMonth = document.querySelector(
      `select[name="experience_${entryIndex}_end_month"]`
    );
    const endYear = document.querySelector(
      `input[name="experience_${entryIndex}_end_year"]`
    );

    if (e.target.checked) {
      if (endMonth) endMonth.disabled = true;
      if (endYear) endYear.disabled = true;
    } else {
      if (endMonth) endMonth.disabled = false;
      if (endYear) endYear.disabled = false;
    }
  }
});

// Save form data to localStorage
function saveFormData() {
  const form = document.getElementById("resumeForm");
  if (!form) return;

  const formData = new FormData(form);
  const data = {};

  // Save all form fields
  for (let [key, value] of formData.entries()) {
    if (data[key]) {
      // Handle multiple values (like checkboxes)
      if (Array.isArray(data[key])) {
        data[key].push(value);
      } else {
        data[key] = [data[key], value];
      }
    } else {
      data[key] = value;
    }
  }

  // Also save all input values directly
  const inputs = form.querySelectorAll("input, textarea, select");
  const inputData = {};
  inputs.forEach((input) => {
    if (input.type === "checkbox") {
      inputData[input.name] = input.checked;
    } else {
      inputData[input.name] = input.value;
    }
  });

  localStorage.setItem("resumeFormData", JSON.stringify(inputData));
}

// Load form data from localStorage
function loadFormData() {
  const savedData = localStorage.getItem("resumeFormData");
  if (!savedData) return;

  try {
    const data = JSON.parse(savedData);
    const form = document.getElementById("resumeForm");
    if (!form) return;

    Object.keys(data).forEach((name) => {
      const input = form.querySelector(`[name="${name}"]`);
      if (input) {
        if (input.type === "checkbox") {
          input.checked = data[name];
        } else {
          input.value = data[name];
        }
      }
    });
  } catch (e) {
    console.error("Error loading form data:", e);
  }
}

// Clear form data from localStorage
function clearFormData() {
  localStorage.removeItem("resumeFormData");
}

// Auto-save form data as user types
document.addEventListener("input", function (e) {
  if (e.target.closest("#resumeForm")) {
    saveFormData();
  }
});

// Auto-save on change (for checkboxes, selects)
document.addEventListener("change", function (e) {
  if (e.target.closest("#resumeForm")) {
    saveFormData();
  }
});

// Load saved data when page loads
document.addEventListener("DOMContentLoaded", function () {
  loadFormData();
});

// Form submission handler
document.getElementById("resumeForm")?.addEventListener("submit", function (e) {
  // Validate email
  const emailInput = document.getElementById("email");
  if (emailInput && !validateEmail(emailInput.value)) {
    e.preventDefault();
    emailInput.setCustomValidity("Please enter a valid email address");
    emailInput.reportValidity();
    return false;
  }

  // Validate URLs if provided (lenient - allows with or without https://)
  const linkedinInput = document.getElementById("linkedin");
  if (
    linkedinInput &&
    linkedinInput.value &&
    !validateURL(linkedinInput.value)
  ) {
    e.preventDefault();
    linkedinInput.setCustomValidity(
      "Please enter a valid URL (e.g., linkedin.com/in/profile or https://linkedin.com/in/profile)"
    );
    linkedinInput.reportValidity();
    return false;
  }

  const websiteInput = document.getElementById("website");
  if (websiteInput && websiteInput.value && !validateURL(websiteInput.value)) {
    e.preventDefault();
    websiteInput.setCustomValidity(
      "Please enter a valid URL (e.g., yourwebsite.com or https://yourwebsite.com)"
    );
    websiteInput.reportValidity();
    return false;
  }

  // Update all counts before submission
  updateEducationCount();
  updateExperienceCount();
  updateSkillsCount();
  updateProjectsCount();

  // Count bullets for each entry
  document.querySelectorAll(".experience-entry").forEach((entry, expIndex) => {
    const bullets = entry.querySelectorAll(
      ".bullets-container .form-row input"
    );
    const countInput = document.createElement("input");
    countInput.type = "hidden";
    countInput.name = `experience_${expIndex}_bullet_count`;
    countInput.value = bullets.length;
    entry.appendChild(countInput);
  });

  document.querySelectorAll(".project-entry").forEach((entry, projIndex) => {
    const bullets = entry.querySelectorAll(
      ".bullets-container .form-row input"
    );
    const countInput = document.createElement("input");
    countInput.type = "hidden";
    countInput.name = `project_${projIndex}_bullet_count`;
    countInput.value = bullets.length;
    entry.appendChild(countInput);
  });

  // Clear saved form data after successful submission
  clearFormData();
});
