document.addEventListener("DOMContentLoaded", function () {
  const menuBtn = document.querySelector(".menu-btn");
  const closeBtn = document.querySelector(".close-btn");
  const sidebar = document.querySelector("aside");

  // Open Sidebar
  menuBtn.addEventListener("click", function () {
    sidebar.classList.add("open");
  });

  // Close Sidebar
  closeBtn.addEventListener("click", function () {
    sidebar.classList.remove("open");
  });

  // Close Sidebar when clicking outside
  document.addEventListener("click", function (event) {
    if (!sidebar.contains(event.target) && !menuBtn.contains(event.target)) {
      sidebar.classList.remove("open");
    }
  });
});

// ========== navbar menu controls =========
const activePage = window.location.pathname.replace(/\/$/, ""); // Remove trailing slash
const links = document.querySelectorAll(".sidebar a");

links.forEach((link) => {
  const linkPath = new URL(link.href).pathname.replace(/\/$/, ""); // Remove trailing slash from href
  if (linkPath === activePage) {
    link.classList.add("active");
  }
});

// registration form ajax submission
// document.getElementById("signup-form").addEventListener("submit", function (e) {
//   e.preventDefault();

//   clearErrors();

//   // Get form data
//   const formData = new FormData(this);

//   // Sending AJAX request
//   fetch("/auth/signup", {
//     method: "POST",
//     headers: {
//       "X-Requested-With": "XMLHttpRequest",
//       //   "X-CSRFToken": document.querySelector('input[name="csrf_token"]').value,
//     },
//     body: formData,
//   })
//     .then((response) => response.json())
//     .then((data) => {
//       if (data.success) {
//         document.getElementById("success-message").textContent = data.message;

//         document.getElementById("signup-form").reset();
//       } else {
//         displayErrors(data.errors);
//       }
//     })
//     .catch((error) => {
//       //   console.error("Error:", error);
//       if (error.response) {
//         error.response.json().then((data) => {
//           if (data.errors) {
//             displayErrors(data.errors);
//           }
//         });
//       }
//     });
// });

// function displayErrors(errors) {
//   // shpowing each field error
//   for (const field in errors) {
//     const errorElement = document.getElementById(`${field}-error`);
//     if (errorElement) {
//       errorElement.textContent = errors[field][0];
//     }
//   }
// }

// function clearErrors() {
//   // Clear all error messages
//   const errorElements = document.querySelectorAll(".error");
//   errorElements.forEach((element) => {
//     element.textContent = "";
//   });

//   // Clear success message
//   document.getElementById("success-message").textContent = "";
// }

// ====== Signup Form

async function handleSignupSubmit(event) {
  event.preventDefault();

  const formData = {
    f_name: document.getElementById("firstname").value.trim(),
    surname: document.getElementById("surname").value.trim(),
    email: document.getElementById("email").value.trim(),
    password: document.getElementById("password").value.trim(),
    role: document.getElementById("role").value.trim(),
    gender: document.getElementById("gender").value.trim(),
  };

  // Clear previous error messages
  const errorElements = document.querySelectorAll(".error");
  errorElements.forEach((el) => (el.textContent = ""));

  try {
    const response = await fetch("/auth/signup", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(formData),
    });

    if (!response.ok) {
      const result = await response.json();
      if (result.errors) {
        for (const [field, message] of Object.entries(result.errors)) {
          document.getElementById(`${field}-error`).textContent = message;
        }
      }
    } else {
      const result = await response.json();
      document.getElementById("success-message").style.display = "block";
      if (result.redirect) {
        setTimeout(() => {
          window.location.href = result.redirect;
        }, 2000); // 2 seconds delay
      }
    }
  } catch (error) {
    console.error("Error:", error);
  }
}

// ====== Login Form Handling

async function handleLoginSubmit(event) {
  event.preventDefault();
  const formData = {
    email: document.getElementById("email").value.trim(),
    password: document.getElementById("password").value.trim(),
  };

  try {
    const response = await fetch("/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(formData),
      credentials: "include",
    });

    const result = await response.json(); // parse response JSON

    if (result.success) {
      document.getElementById("login-success").style.display = "block";
      document.getElementById("failed-login").style.display = "none";

      if (result.redirect) {
        setTimeout(() => {
          window.location.href = result.redirect;
        }, 2000);
      }
    } else {
      document.getElementById("failed-login").style.display = "block";
      document.getElementById("login-success").style.display = "none";
    }
  } catch (error) {
    console.error("Error:", error);
    document.getElementById("failed-login").style.display = "block";
    document.getElementById("login-success").style.display = "none";
  }
}

// ====== Adding User Via Admin Panel ======
async function handleAddUserSubmit(event) {
  event.preventDefault();

  const formData = {
    f_name: document.getElementById("firstname").value.trim(),
    surname: document.getElementById("surname").value.trim(),
    email: document.getElementById("email").value.trim(),
    password: document.getElementById("password").value.trim(),
    role: document.getElementById("role").value.trim(),
    gender: document.getElementById("gender").value.trim(),
  };

  // Clear previous error messages
  document.querySelectorAll(".error").forEach((el) => (el.textContent = ""));

  try {
    const response = await fetch("/user-management/add-user", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(formData),
    });

    if (!response.ok) {
      const result = await response.json();
      if (result.errors) {
        // Map backend field names to frontend IDs
        const fieldMap = {
          f_name: "firstname",
          surname: "surname",
          email: "email",
          role: "role",
          gender: "gender",
          password: "password",
        };

        for (const [field, message] of Object.entries(result.errors)) {
          const frontendField = fieldMap[field] || field;
          const errorElement = document.getElementById(
            `${frontendField}-error`
          );
          if (errorElement) {
            errorElement.textContent = message;
          }
        }
      }
      return; // Exit if there are errors
    }

    // On success:
    // 1. Close the modal
    const modal = bootstrap.Modal.getInstance(
      document.getElementById("add-user-Modal")
    );
    modal.hide();

    // 2. Show temporary success message (will auto-remove after 3 seconds)
    const successMessage = document.createElement("div");
    successMessage.className =
      "alert alert-success alert-dismissible fade show";
    successMessage.setAttribute("role", "alert");
    successMessage.innerHTML = `
      User added successfully!
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    // Add to the page (you might want to adjust the container)
    const container = document.getElementById("main-content") || document.body;
    container.prepend(successMessage);

    // Auto-remove after 3 seconds
    setTimeout(() => {
      const alert = bootstrap.Alert.getInstance(successMessage);
      if (alert) {
        alert.close();
      } else {
        successMessage.remove();
      }
      // reload the page after success
      location.reload();
    }, 3000);

    // 3. Reset the form
    event.target.reset();
  } catch (error) {
    console.error("Error:", error);
    // Show temporary error message
    const errorMessage = document.createElement("div");
    errorMessage.className = "alert alert-danger alert-dismissible fade show";
    errorMessage.setAttribute("role", "alert");
    errorMessage.innerHTML = `
      An error occurred. Please try again.
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.prepend(errorMessage);
    setTimeout(() => {
      const alert = bootstrap.Alert.getInstance(errorMessage);
      if (alert) {
        alert.close();
      } else {
        errorMessage.remove();
      }

    }, 3000);
  }
}

// Initialize the form submission handler
document
  .querySelector("#add-user-Modal form")
  .addEventListener("submit", handleAddUserSubmit);

// // ====== Prediction Form Handler ======
// document.addEventListener("DOMContentLoaded", function () {
//   // Form elements
//   const form = document.getElementById("uploadForm");
//   const dropZone = document.getElementById("dropZone");
//   const fileInput = document.getElementById("fileInput");
//   const fileInfo = document.getElementById("fileInfo");
//   const fileName = document.getElementById("fileName");
//   const removeFile = document.getElementById("removeFile");
//   const previewContainer = document.getElementById("previewContainer");
//   const submitBtn = document.getElementById("submitBtn");
//   const resultSection = document.getElementById("resultSection");
//   const firstnameInput = document.getElementById("firstname");
//   const surnameInput = document.getElementById("surname");
//   const userDOBInput = document.getElementById("userDOB");
//   const predictionDateInput = document.getElementById("predictionDate");

//   // Current image data URL for result display
//   let currentImageDataUrl = null;

//   // ====== Drag and Drop Handlers ======
//   dropZone.addEventListener("dragover", (e) => {
//     e.preventDefault();
//     dropZone.classList.add("drag-over");
//   });

//   dropZone.addEventListener("dragleave", (e) => {
//     e.preventDefault();
//     dropZone.classList.remove("drag-over");
//   });

//   dropZone.addEventListener("drop", (e) => {
//     e.preventDefault();
//     dropZone.classList.remove("drag-over");
//     handleDroppedFiles(e.dataTransfer.files);
//   });

//   // ====== File Input Change Handler ======
//   fileInput.addEventListener("change", (e) => {
//     if (e.target.files.length > 0) {
//       handleFileSelect(e.target.files[0]);
//     }
//   });

//   // ====== Remove File Handler ======
//   removeFile.addEventListener("click", (e) => {
//     e.preventDefault();
//     resetForm();
//   });

//   // ====== Form Submission Handler ======
//   form.addEventListener("submit", async (e) => {
//     e.preventDefault();

//     // Validate form
//     if (!validateForm()) return;

//     // Prepare form data
//     const formData = prepareFormData();

//     // Submit form
//     await submitPredictionForm(formData);
//   });

//   // ====== Helper Functions ======

//   function handleDroppedFiles(files) {
//     if (files.length > 0) {
//       const file = files[0];
//       if (file.type.startsWith("image/")) {
//         handleFileSelect(file);
//       } else {
//         showError("Please select an image file only.");
//       }
//     }
//   }

//   function handleFileSelect(file) {
//     // Clear previous results/errors
//     clearResults();

//     // Store file in input
//     const dt = new DataTransfer();
//     dt.items.add(file);
//     fileInput.files = dt.files;

//     // Show file info
//     fileName.textContent = file.name;
//     fileInfo.style.display = "block";

//     // Read and display image preview
//     const reader = new FileReader();
//     reader.onload = (e) => {
//       currentImageDataUrl = e.target.result;
//       previewContainer.innerHTML = `
//         <img src="${currentImageDataUrl}" class="preview-image rounded-3 shadow-sm"
//              alt="Preview" style="max-width: 30%; height: auto;">
//       `;
//     };
//     reader.readAsDataURL(file);
//   }

//   function validateForm() {
//     if (!fileInput.files || fileInput.files.length === 0) {
//       showError("Please select an image file.");
//       return false;
//     }

//     if (!firstnameInput.value.trim()) {
//       showError("Please enter your first name.");
//       return false;
//     }

//     if (!surnameInput.value.trim()) {
//       showError("Please enter your surname.");
//       return false;
//     }

//     if (!userDOBInput.value) {
//       showError("Please enter your date of birth.");
//       return false;
//     }

//     if (!predictionDateInput.value) {
//       showError("Please enter the prediction date.");
//       return false;
//     }

//     const dob = new Date(userDOBInput.value);
//     const predDate = new Date(predictionDateInput.value);
//     const age = predDate.getFullYear() - dob.getFullYear();
//     const monthDiff = predDate.getMonth() - dob.getMonth();
//     const dayDiff = predDate.getDate() - dob.getDate();

//     const isUnder21 =
//       age < 21 ||
//       (age === 21 && monthDiff < 0) ||
//       (age === 21 && monthDiff === 0 && dayDiff < 0);

//     if (isUnder21) {
//       showError(
//         "Patient age must be at least 21 years at the time of prediction."
//       );
//       return false;
//     }

//     return true;
//   }

//   function prepareFormData() {
//     const formData = new FormData();
//     formData.append("firstname", firstnameInput.value.trim());
//     formData.append("surname", surnameInput.value.trim());
//     formData.append("userDOB", userDOBInput.value);
//     formData.append("predictionDate", predictionDateInput.value);
//     formData.append("image", fileInput.files[0]);
//     return formData;
//   }

//   async function submitPredictionForm(formData) {
//     // Show loading state
//     setLoadingState(true);

//     try {
//       const response = await fetch("/prediction", {
//         method: "POST",
//         body: formData,
//       });

//       const data = await response.json();

//       if (!response.ok) {
//         throw new Error(data.error || "Unknown error occurred");
//       }

//       // Display results
//       displayResults(data, currentImageDataUrl);

//       // Reset form (but keep results visible)
//       resetForm(false);
//     } catch (error) {
//       showError(error.message);
//     } finally {
//       setLoadingState(false);
//     }
//   }

//   function displayResults(data, imageDataUrl) {
//     resultSection.innerHTML = createResultCard(data, imageDataUrl);
//     resultSection.style.display = "block";

//     // Add retry button event listener if needed
//     document.getElementById("retry-btn")?.addEventListener("click", () => {
//       resetForm(true);
//     });
//   }

//   function createResultCard(data, imageDataUrl) {
//     return `
//     <div class="prediction-result-container">
//       <div class="prediction-header">
//         <div class="header-content">
//           <h3><i class="fas fa-microscope"></i> Cervical Analysis Report</h3>
//           <div class="status-badge ${
//             data.ood_status === "accepted" ? "reliable" : "unreliable"
//           }">
//             <i class="fas ${
//               data.ood_status === "accepted"
//                 ? "fa-check-circle"
//                 : "fa-exclamation-triangle"
//             }"></i>
//             ${
//               data.ood_status === "accepted"
//                 ? "Reliable Prediction"
//                 : "Unreliable Prediction"
//             }
//           </div>
//         </div>
//         <div class="patient-id">
//           <span>${new Date().toLocaleDateString()}</span>
//           <span>${data.first_name.substring(
//             0,
//             3
//           )}${data.surname.substring(0, 3)}${Math.floor(Math.random() * 9000) + 1000}</span>
//         </div>
//       </div>

//       <div class="image-display-section">
//         <div class="image-container">
//           <img src="${imageDataUrl}" alt="Cervical Sample" class="medical-image" style="max-width: 30%; height: auto;">
//         </div>
//         <div class="image-meta">
//           <div class="meta-item">
//             <label>Patient:</label>
//             <span>${data.first_name} ${data.surname}</span>
//           </div>
//           <div class="meta-item">
//             <label>Age:</label>
//             <span>${data.age}</span>
//           </div>
//         </div>
//       </div>

//       <div class="results-grid">
//         <div class="result-card primary">
//           <div class="card-header">
//             <i class="fas fa-diagnoses"></i>
//             <h4>Prediction</h4>
//           </div>
//           <div class="card-content">
//             <div class="prediction-value ${data.result.toLowerCase()}">
//               ${data.result || "N/A"}
//             </div>
//             <div class="prediction-description">
//               ${getPredictionDescription(data.result)}
//             </div>
//           </div>
//         </div>

//         <div class="result-card">
//           <div class="card-header">
//             <i class="fas fa-chart-line"></i>
//             <h4>Confidence</h4>
//           </div>
//           <div class="card-content">
//             <div class="confidence-meter">
//               <div class="meter-bar" style="width: ${(
//                 data.confidence * 100
//               ).toFixed(0)}%">
//                 <span>${(data.confidence * 100).toFixed(2)}%</span>
//               </div>
//             </div>
//             <div class="confidence-description">
//               ${getConfidenceLevel(data.confidence)}
//             </div>
//           </div>
//         </div>
//       </div>

//       <div class="clinical-notes">
//         <div class="notes-header">
//           <i class="fas fa-clipboard-check"></i>
//           <h4>Clinical Notes</h4>
//         </div>
//         <div class="notes-content">
//           ${
//             data.ood_status === "accepted"
//               ? `
//             <p>This prediction shows <strong>${
//               data.result
//             }</strong> with <strong>${(data.confidence * 100).toFixed(
//                   2
//                 )}% confidence</strong>.</p>
//           `
//               : `
//             <p class="warning">The prediction for <strong>${
//               data.result
//             }</strong> with <strong>${(data.confidence * 100).toFixed(
//                   2
//                 )}% confidence</strong> does not meet reliability standards.</p>
//             <p>Recommend recollecting the sample with proper technique and resubmitting for analysis.</p>
//           `
//           }
//         </div>
//       </div>

//       <div class="action-buttons">
//         ${
//           data.ood_status === "accepted"
//             ? `
//           <a href="/appointments/schedule" class="btn-action primary">
//             <i class="fas fa-calendar-check"></i> Schedule Follow-up
//           </a>
//         `
//             : `
//           <button id="retry-btn" class="btn-action warning">
//             <i class="fas fa-redo"></i> Retest Sample
//           </button>
//         `
//         }
//       </div>
//     </div>
//     `;
//   }

//   function resetForm(clearResults = true) {
//     form.reset();
//     fileInput.value = "";
//     fileInfo.style.display = "none";
//     previewContainer.innerHTML = "";
//     currentImageDataUrl = null;

//     if (clearResults) {
//       resultSection.style.display = "none";
//       resultSection.innerHTML = "";
//     }
//   }

//   function clearResults() {
//     resultSection.style.display = "none";
//     resultSection.innerHTML = "";
//   }

//   function showError(message) {
//     resultSection.innerHTML = `
//       <div class="alert alert-danger" role="alert">
//         ${message}
//       </div>`;
//     resultSection.style.display = "block";
//   }

//   function setLoadingState(isLoading) {
//     submitBtn.disabled = isLoading;
//     submitBtn.innerHTML = isLoading
//       ? '<i class="fas fa-spinner fa-spin"></i> Processing...'
//       : '<i class="fas fa-chart-line"></i> Predict';
//   }

//   // Helper functions for result display
//   function getPredictionDescription(prediction) {
//     const descriptions = {
//       Normal: "No abnormal cells detected",
//       Koilocytotic: "Possible HPV-related changes",
//       Dysplastic: "Abnormal cell growth detected",
//       CIN1: "Mild dysplasia",
//       CIN2: "Moderate dysplasia",
//       CIN3: "Severe dysplasia",
//     };
//     return descriptions[prediction] || "Consult physician for interpretation";
//   }

//   function getConfidenceLevel(confidence) {
//     if (confidence >= 0.9) return "Very High Confidence";
//     if (confidence >= 0.7) return "High Confidence";
//     if (confidence >= 0.5) return "Moderate Confidence";
//     return "Low Confidence";
//   }
// });

// @@@@@@ USER PROFILE MANAGEMENT
// Toggle edit mode
// const editToggle = document.getElementById("editToggle");
// const formInputs = document.querySelectorAll(
//   ".profile-form input, .profile-form select, .profile-form textarea"
// );

// if (editToggle) {
//   editToggle.addEventListener("change", function () {
//     formInputs.forEach((input) => {
//       input.disabled = !this.checked;
//     });

//     // Add animation to form elements when enabling edit mode
//     if (this.checked) {
//       document.querySelectorAll(".floating-label").forEach((label, index) => {
//         label.style.animation = `fadeInUp 0.4s ease ${index * 0.1}s forwards`;
//       });
//     }
//   });
// }

// // Avatar upload preview
// const avatarUpload = document.getElementById("avatarUpload");
// if (avatarUpload) {
//   avatarUpload.addEventListener("change", function (e) {
//     const file = e.target.files[0];
//     if (file) {
//       const reader = new FileReader();
//       reader.onload = function (event) {
//         document.getElementById(
//           "avatarPreview"
//         ).style.backgroundImage = `url(${event.target.result})`;

//         // Add success animation
//         const avatarPreview = document.getElementById("avatarPreview");
//         avatarPreview.style.animation = "pulse 0.5s ease";
//         setTimeout(() => {
//           avatarPreview.style.animation = "";
//         }, 500);
//       };
//       reader.readAsDataURL(file);
//     }
//   });
// }

// // Toggle password visibility
// document.querySelectorAll(".toggle-password").forEach((button) => {
//   button.addEventListener("click", function () {
//     const input = this.parentElement.querySelector("input");
//     const icon = this.querySelector("i");

//     if (input.type === "password") {
//       input.type = "text";
//       icon.classList.replace("fa-eye", "fa-eye-slash");
//     } else {
//       input.type = "password";
//       icon.classList.replace("fa-eye-slash", "fa-eye");
//     }

//     // Add animation
//     this.style.animation = "bounce 0.3s ease";
//     setTimeout(() => {
//       this.style.animation = "";
//     }, 300);
//   });
// });

// // Password strength meter
// const newPasswordInput = document.getElementById("newPassword");
// if (newPasswordInput) {
//   newPasswordInput.addEventListener("input", function () {
//     const password = this.value;
//     const strengthBar = document.querySelector(".strength-bar");
//     const strengthLabels = document.querySelectorAll(".strength-labels span");
//     const requirements = {
//       length: document.querySelector(".req-length"),
//       uppercase: document.querySelector(".req-uppercase"),
//       number: document.querySelector(".req-number"),
//       special: document.querySelector(".req-special"),
//     };

//     let strength = 0;

//     // Check password requirements
//     const hasLength = password.length >= 8;
//     const hasUppercase = /[A-Z]/.test(password);
//     const hasNumber = /\d/.test(password);
//     const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password);

//     // Update requirement indicators
//     if (requirements.length) {
//       requirements.length.querySelector("i").style.color = hasLength
//         ? "#00b894"
//         : "#ff4757";
//     }
//     if (requirements.uppercase) {
//       requirements.uppercase.querySelector("i").style.color = hasUppercase
//         ? "#00b894"
//         : "#ff4757";
//     }
//     if (requirements.number) {
//       requirements.number.querySelector("i").style.color = hasNumber
//         ? "#00b894"
//         : "#ff4757";
//     }
//     if (requirements.special) {
//       requirements.special.querySelector("i").style.color = hasSpecial
//         ? "#00b894"
//         : "#ff4757";
//     }

//     // Calculate strength
//     if (hasLength) strength += 25;
//     if (hasUppercase) strength += 25;
//     if (hasNumber) strength += 25;
//     if (hasSpecial) strength += 25;

//     // Update strength bar
//     if (strengthBar) {
//       strengthBar.style.width = strength + "%";

//       // Update strength color and label
//       if (strengthLabels) {
//         strengthLabels.forEach((label) => (label.style.color = ""));

//         if (strength < 50) {
//           strengthBar.style.backgroundColor = "#ff4757";
//           if (strengthLabels[0]) strengthLabels[0].style.color = "#ff4757";
//         } else if (strength < 75) {
//           strengthBar.style.backgroundColor = "#ffa502";
//           if (strengthLabels[1]) strengthLabels[1].style.color = "#ffa502";
//         } else if (strength < 100) {
//           strengthBar.style.backgroundColor = "#2ed573";
//           if (strengthLabels[2]) strengthLabels[2].style.color = "#2ed573";
//         } else {
//           strengthBar.style.backgroundColor = "#00b894";
//           if (strengthLabels[3]) strengthLabels[3].style.color = "#00b894";
//         }
//       }
//     }
//   });
// }

// // Add animations
// const animateOnScroll = () => {
//   const cards = document.querySelectorAll(".card");

//   cards.forEach((card, index) => {
//     const cardPosition = card.getBoundingClientRect().top;
//     const screenPosition = window.innerHeight / 1.2;

//     if (cardPosition < screenPosition) {
//       card.style.animation = `fadeInUp 0.6s ease ${index * 0.1}s forwards`;
//     }
//   });
// };

// window.addEventListener("scroll", animateOnScroll);
// animateOnScroll(); // Run once on page load

// // Keyframe animations
// const style = document.createElement("style");
// style.textContent = `
//   @keyframes fadeInUp {
//     from {
//       opacity: 0;
//       transform: translateY(20px);
//     }
//     to {
//       opacity: 1;
//       transform: translateY(0);
//     }
//   }

//   @keyframes pulse {
//     0% { transform: scale(1); }
//     50% { transform: scale(1.05); }
//     100% { transform: scale(1); }
//   }

//   @keyframes bounce {
//     0%, 100% { transform: translateY(0); }
//     50% { transform: translateY(-5px); }
//   }
// `;
// document.head.appendChild(style);

// // Handle form submission
// const profileForm = document.querySelector(".profile-form");
// if (profileForm) {
//   profileForm.addEventListener("submit", function (e) {
//     e.preventDefault();

//     // Here you would typically send the form data to your server
//     // For demonstration, we'll just show a success message
//     alert("Profile updated successfully!");

//     // Disable edit mode after submission
//     if (editToggle) {
//       editToggle.checked = false;
//       formInputs.forEach((input) => {
//         input.disabled = true;
//       });
//     }
//   });
// }

// // Handle password change form
// const passwordForm = document.querySelector(".password-form");
// if (passwordForm) {
//   passwordForm.addEventListener("submit", function (e) {
//     e.preventDefault();

//     const currentPassword = document.getElementById("currentPassword").value;
//     const newPassword = document.getElementById("newPassword").value;
//     const confirmPassword = document.getElementById("confirmPassword").value;

//     // Basic validation
//     if (newPassword !== confirmPassword) {
//       alert("New password and confirmation do not match!");
//       return;
//     }

//     // Here you would typically send the password change request to your server
//     // For demonstration, we'll just show a success message
//     alert("Password changed successfully!");

//     // Close the modal
//     const modal = bootstrap.Modal.getInstance(
//       document.getElementById("passwordModal")
//     );
//     if (modal) {
//       modal.hide();
//     }

//     // Clear the form
//     passwordForm.reset();
//   });
// }
