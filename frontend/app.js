// Frontend JavaScript - Resume Parser & Job Matcher

const API_ROOT = "http://localhost:8000";
const API_URL = `${API_ROOT}/api`;
const SESSION_RESUME_KEY = "resumePilot.resumeId";
const USER_SESSION_KEY = "resumePilot.googleUser";

let currentResumeId = null;
let currentResume = null;
let currentMatches = [];
let hasSearchedJobs = false;

const elements = {
    apiStatus: document.getElementById("apiStatus"),
    alert: document.getElementById("appAlert"),
    fileInput: document.getElementById("fileInput"),
    uploadArea: document.getElementById("uploadArea"),
    uploadProgress: document.getElementById("uploadProgress"),
    uploadStatus: document.getElementById("uploadStatus"),
    profilePreview: document.getElementById("profilePreview"),
    clearResume: document.getElementById("clearResumeButton"),
    jobsList: document.getElementById("jobsList"),
    selectedJob: document.getElementById("selectedJob"),
};

function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (character) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    })[character]);
}

function showAlert(message) {
    elements.alert.textContent = message;
    elements.alert.hidden = false;
}

function clearAlert() {
    elements.alert.textContent = "";
    elements.alert.hidden = true;
}

async function request(path, options = {}) {
    let response;
    try {
        response = await fetch(`${API_URL}${path}`, options);
    } catch {
        throw new Error("Could not reach the API. Start the FastAPI server at http://localhost:8000 and try again.");
    }

    const result = await response.json().catch(() => ({}));
    if (!response.ok) {
        const detail = typeof result.detail === "string" ? result.detail : "The request could not be completed.";
        throw new Error(detail);
    }
    return result;
}

function setApiStatus(connected) {
    elements.apiStatus.classList.toggle("online", connected);
    elements.apiStatus.classList.toggle("offline", !connected);
    elements.apiStatus.innerHTML = `<span class="status-dot"></span>${connected ? "API connected" : "API unavailable"}`;
}

function restoreGoogleAccount() {
    const accountChip = document.getElementById("accountChip");
    const accountName = document.getElementById("accountName");
    const accountAvatar = document.getElementById("accountAvatar");
    let profile;

    try {
        profile = JSON.parse(sessionStorage.getItem(USER_SESSION_KEY) || "null");
    } catch {
        sessionStorage.removeItem(USER_SESSION_KEY);
    }

    if (!profile?.email) return;
    accountName.textContent = profile.name || profile.email;
    accountAvatar.textContent = (profile.name || profile.email).trim().charAt(0).toUpperCase();
    accountChip.hidden = false;
}

function logOut() {
    sessionStorage.removeItem(USER_SESSION_KEY);
    sessionStorage.removeItem(SESSION_RESUME_KEY);
    window.location.assign("login.html");
}

async function checkApi() {
    try {
        const response = await fetch(`${API_ROOT}/health`);
        setApiStatus(response.ok);
    } catch {
        setApiStatus(false);
    }
}

function setView(viewName) {
    document.querySelectorAll(".view").forEach((view) => {
        const isActive = view.id === `view-${viewName}`;
        view.classList.toggle("active", isActive);
        view.hidden = !isActive;
    });
    document.querySelectorAll(".nav-item").forEach((button) => {
        const isActive = button.dataset.view === viewName;
        button.classList.toggle("active", isActive);
        button.setAttribute("aria-current", isActive ? "page" : "false");
    });
    const title = document.querySelector(`[data-view="${viewName}"]`)?.textContent.trim().replace(/^\d+/, "").trim();
    document.getElementById("currentSection").textContent = title || "Overview";
    clearAlert();
}

function getResumeSkills(parsed) {
    const skills = parsed?.skills;
    if (Array.isArray(skills)) return skills;
    if (!skills || typeof skills !== "object") return parsed?.primary_skills || [];
    return [...new Set(Object.values(skills).flatMap((value) => Array.isArray(value) ? value : []))];
}

function renderResume(parsed, filename = "Resume ready") {
    currentResume = parsed || {};
    const personal = currentResume.personal_info || {};
    const skills = getResumeSkills(currentResume).slice(0, 10);
    const experience = currentResume.years_of_experience;
    const meta = [personal.location, Number.isFinite(Number(experience)) ? `${experience} years’ experience` : null, currentResume.experience_level]
        .filter(Boolean).map(escapeHtml).join(" <span>·</span> ");

    elements.profilePreview.innerHTML = `
        <div class="profile-top">
            <div><p class="profile-name">${escapeHtml(personal.name || filename)}</p><p class="profile-meta">${meta || escapeHtml(filename)}</p></div>
            <button class="profile-clear" id="profileClearButton" type="button">Remove</button>
        </div>
        ${currentResume.professional_summary ? `<p class="profile-summary">${escapeHtml(currentResume.professional_summary)}</p>` : ""}
        ${skills.length ? `<div class="profile-skills">${skills.map((skill) => `<span class="skill-tag">${escapeHtml(skill)}</span>`).join("")}</div>` : ""}
    `;
    elements.profilePreview.hidden = false;
    elements.uploadArea.hidden = true;
    elements.clearResume.hidden = false;
    elements.uploadProgress.hidden = true;
    document.getElementById("resumeStepState").textContent = "Ready";
    document.getElementById("profileClearButton").addEventListener("click", clearResume);
}

function handleFileUpload(file) {
    if (!file) return;
    const extension = file.name.split(".").pop()?.toLowerCase();
    if (!["pdf", "docx", "txt"].includes(extension)) {
        showAlert("Choose a PDF, DOCX or TXT resume.");
        elements.fileInput.value = "";
        return;
    }

    clearAlert();
    elements.uploadProgress.hidden = false;
    elements.uploadStatus.textContent = "Uploading and parsing your resume…";
    elements.uploadArea.setAttribute("aria-busy", "true");
    const data = new FormData();
    data.append("file", file);

    request("/resume/upload", { method: "POST", body: data })
        .then((result) => {
            currentResumeId = result.resume_id;
            sessionStorage.setItem(SESSION_RESUME_KEY, currentResumeId);
            renderResume(result.parsed_data, result.filename || file.name);
            currentMatches = [];
            hasSearchedJobs = false;
            renderMatches([]);
        })
        .catch((error) => {
            elements.uploadProgress.hidden = true;
            showAlert(error.message);
        })
        .finally(() => {
            elements.uploadArea.removeAttribute("aria-busy");
            elements.fileInput.value = "";
        });
}

async function restoreResume() {
    const savedId = sessionStorage.getItem(SESSION_RESUME_KEY);
    if (!savedId) return;
    try {
        const result = await request(`/resume/parse/${encodeURIComponent(savedId)}`);
        currentResumeId = savedId;
        currentMatches = [];
        hasSearchedJobs = false;
        renderResume(result.parsed_data, result.filename || "Resume ready");
        document.getElementById("resumeStepState").textContent = "Restored";
    } catch {
        sessionStorage.removeItem(SESSION_RESUME_KEY);
    }
}

async function clearResume() {
    if (currentResumeId) {
        try {
            await request(`/resume/${encodeURIComponent(currentResumeId)}`, { method: "DELETE" });
        } catch (error) {
            showAlert(error.message);
            return;
        }
    }
    currentResumeId = null;
    currentResume = null;
    currentMatches = [];
    hasSearchedJobs = false;
    sessionStorage.removeItem(SESSION_RESUME_KEY);
    elements.profilePreview.hidden = true;
    elements.profilePreview.replaceChildren();
    elements.uploadArea.hidden = false;
    elements.clearResume.hidden = true;
    document.getElementById("resumeStepState").textContent = "Start";
    renderMatches([]);
    document.getElementById("jobsEmpty").hidden = false;
    document.getElementById("resultCount").textContent = "Ready when you are";
    document.getElementById("careerResults").hidden = true;
    document.getElementById("careerEmpty").hidden = false;
    document.getElementById("interviewResults").hidden = true;
    document.getElementById("interviewEmpty").hidden = false;
    showAlert("Resume removed from the current session.");
}

function renderMatches(matches) {
    elements.jobsList.replaceChildren();
    const select = elements.selectedJob;
    select.replaceChildren(new Option(matches.length ? "Choose a matched role" : "Find matches first", ""));

    matches.forEach((job) => {
        const card = document.createElement("article");
        card.className = "job-card";
        const salary = Array.isArray(job.salary_range) && job.salary_range.length === 2
            ? `$${Number(job.salary_range[0]).toLocaleString()} – $${Number(job.salary_range[1]).toLocaleString()}` : null;
        const strengths = Array.isArray(job.strengths) ? job.strengths : [];
        const gaps = Array.isArray(job.gaps) ? job.gaps : [];
        const match = Number(job.match_percentage ?? job.match_score ?? 0);
        const safeUrl = safeExternalUrl(job.apply_url);
        card.innerHTML = `
            <div class="job-card-main">
                <h3 class="job-title">${escapeHtml(job.position || "Role")}</h3>
                <div class="job-meta"><span>${escapeHtml(job.company || "")}</span><span>${escapeHtml(job.location || "Location not listed")}</span>${salary ? `<span>${escapeHtml(salary)}</span>` : ""}</div>
                <p class="job-reasoning">${escapeHtml(job.reasoning || "No match explanation was returned.")}</p>
            </div>
            <div class="match-chip"><strong>${escapeHtml(Math.round(match))}%</strong><span>MATCH</span></div>
            <div class="job-details">
                <div><div class="detail-label">YOUR STRENGTHS</div><div class="tag-list">${renderTags(strengths)}</div></div>
                <div><div class="detail-label">SKILLS TO BUILD</div><div class="tag-list">${renderTags(gaps)}</div></div>
            </div>
            ${safeUrl ? `<a class="job-action" href="${escapeHtml(safeUrl)}" target="_blank" rel="noopener noreferrer">View application ↗</a>` : ""}
        `;
        elements.jobsList.append(card);
        select.add(new Option(`${job.position || "Role"} at ${job.company || "Company"}`, job.job_id));
    });

    document.getElementById("jobsEmpty").hidden = matches.length > 0;
    const emptyCopy = document.querySelector("#jobsEmpty p");
    emptyCopy.textContent = !currentResumeId
        ? "Upload a resume to see how your experience lines up with available roles."
        : hasSearchedJobs
            ? "No roles matched those filters. Try broadening your role or location search."
            : "Your resume is ready. Search available roles to see how your experience lines up.";
    document.getElementById("resultCount").textContent = matches.length
        ? `${matches.length} role${matches.length === 1 ? "" : "s"} found`
        : hasSearchedJobs ? "No matching roles" : currentResumeId ? "Ready to search" : "Ready when you are";
}

function renderTags(values) {
    if (!values.length) return `<span class="profile-meta">None listed</span>`;
    return values.map((value) => `<span class="skill-tag">${escapeHtml(value)}</span>`).join("");
}

function safeExternalUrl(value) {
    if (!value) return null;
    try {
        const url = new URL(value);
        return ["https:", "http:"].includes(url.protocol) && url.hostname !== "example.com" ? url.href : null;
    } catch {
        return null;
    }
}

async function searchJobs() {
    if (!currentResumeId) {
        setView("overview");
        showAlert("Upload a resume before searching for matching roles.");
        return;
    }

    const button = document.getElementById("searchButton");
    const loading = document.getElementById("loadingJobs");
    button.disabled = true;
    loading.hidden = false;
    document.getElementById("jobsEmpty").hidden = true;
    elements.jobsList.replaceChildren();
    clearAlert();
    const payload = {
        resume_id: currentResumeId,
        job_title: document.getElementById("jobTitle").value.trim() || null,
        location: document.getElementById("location").value.trim() || null,
    };

    try {
        const result = await request("/matching/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        hasSearchedJobs = true;
        currentMatches = result.matches || [];
        renderMatches(currentMatches);
        document.getElementById("resultCount").textContent = `${result.matches_count ?? currentMatches.length} role${currentMatches.length === 1 ? "" : "s"} found`;
    } catch (error) {
        document.getElementById("jobsEmpty").hidden = false;
        showAlert(error.message);
    } finally {
        loading.hidden = true;
        button.disabled = false;
    }
}

function renderList(values) {
    if (!Array.isArray(values) || !values.length) return `<p class="profile-meta">No details returned.</p>`;
    return `<ul class="plain-list">${values.map((item) => `<li>${escapeHtml(typeof item === "string" ? item : item.skill || item.name || JSON.stringify(item))}</li>`).join("")}</ul>`;
}

async function getCareerAdvice() {
    if (!requireResume()) return;
    const button = document.getElementById("careerButton");
    const loading = document.getElementById("careerLoading");
    button.disabled = true;
    loading.hidden = false;
    document.getElementById("careerEmpty").hidden = true;
    document.getElementById("careerResults").hidden = true;
    clearAlert();

    try {
        const [advice, skillGaps] = await Promise.all([
            request(`/career/advice/${encodeURIComponent(currentResumeId)}`),
            request(`/career/skill-gaps/${encodeURIComponent(currentResumeId)}`).catch(() => null),
        ]);
        const paths = (advice.career_paths || []).map((path) => `
            <div class="career-path"><h3>${escapeHtml(path.path || "Career path")}</h3><p class="path-time">${escapeHtml(path.estimated_timeline || "Timeline not specified")}</p><p>${escapeHtml(path.description || "")}</p>${path.required_skills?.length ? `<div class="tag-list">${renderTags(path.required_skills)}</div>` : ""}</div>
        `).join("") || `<p class="profile-meta">No career paths returned.</p>`;
        const salary = advice.salary_insights || {};
        document.getElementById("careerResults").innerHTML = `
            <div class="career-grid">
                <section class="result-panel"><h2>Recommendations</h2>${renderList(advice.recommendations)}</section>
                <section class="result-panel"><h2>Next steps</h2>${renderList(advice.next_steps)}</section>
                <section class="result-panel"><h2>Career paths</h2>${paths}</section>
                <section class="result-panel"><h2>Skills to develop</h2>${renderList(skillGaps?.skill_gaps || skillGaps?.gaps || [])}${skillGaps?.estimated_learning_time ? `<p class="profile-summary">Estimated learning time: ${escapeHtml(skillGaps.estimated_learning_time)}</p>` : ""}</section>
                <section class="result-panel market-panel"><h2>Market context</h2><div class="insight-grid">
                    <div class="insight"><span>CURRENT MARKET RANGE</span><strong>${escapeHtml(salary.current_market_range || "Not available")}</strong></div>
                    <div class="insight"><span>POTENTIAL IN TWO YEARS</span><strong>${escapeHtml(salary.potential_range_in_2_years || "Not available")}</strong></div>
                    <div class="insight"><span>GROWTH POTENTIAL</span><strong>${escapeHtml(salary.salary_growth_potential || "Not available")}</strong></div>
                </div></section>
            </div>
        `;
        document.getElementById("careerResults").hidden = false;
    } catch (error) {
        document.getElementById("careerEmpty").hidden = false;
        showAlert(error.message);
    } finally {
        loading.hidden = true;
        button.disabled = false;
    }
}

async function getInterviewPrep() {
    if (!requireResume()) return;
    const jobId = elements.selectedJob.value;
    if (!jobId) {
        showAlert("Find matching roles and choose one before building interview prep.");
        return;
    }
    const button = document.getElementById("interviewButton");
    const loading = document.getElementById("interviewLoading");
    button.disabled = true;
    loading.hidden = false;
    document.getElementById("interviewEmpty").hidden = true;
    document.getElementById("interviewResults").hidden = true;
    clearAlert();

    try {
        const [prep, tips] = await Promise.all([
            request(`/interview/questions/${encodeURIComponent(jobId)}/${encodeURIComponent(currentResumeId)}`),
            request(`/interview/tips/${encodeURIComponent(jobId)}/${encodeURIComponent(currentResumeId)}`).catch(() => null),
        ]);
        const questionSection = (title, items) => `
            <section class="result-panel"><h2>${escapeHtml(title)}</h2><div class="question-list">${(items || []).map((item) => `
                <article class="question-item"><strong>${escapeHtml(item.question || item)}</strong>${item.topic || item.difficulty ? `<p>${escapeHtml([item.topic, item.difficulty].filter(Boolean).join(" · "))}</p>` : ""}${item.expected_answer ? `<p><strong>Consider:</strong> ${escapeHtml(item.expected_answer)}</p>` : ""}</article>
            `).join("") || `<p class="profile-meta">No questions returned.</p>`}</div></section>`;
        const tipList = tips?.tips || prep.tips || [];
        const askList = tips?.questions_to_ask || prep.company_questions || [];
        document.getElementById("interviewResults").innerHTML = `
            ${questionSection("Technical questions", prep.technical_questions)}
            ${questionSection("Behavioral questions", prep.behavioral_questions)}
            ${questionSection("Company and role questions", prep.company_questions)}
            <div class="tip-layout"><section class="result-panel"><h2>Preparation tips</h2>${renderList(tipList)}</section><section class="result-panel"><h2>Questions to ask</h2>${renderList(askList)}</section></div>
        `;
        document.getElementById("interviewResults").hidden = false;
    } catch (error) {
        document.getElementById("interviewEmpty").hidden = false;
        showAlert(error.message);
    } finally {
        loading.hidden = true;
        button.disabled = false;
    }
}

function requireResume() {
    if (currentResumeId) return true;
    setView("overview");
    showAlert("Upload a resume before opening this tool.");
    return false;
}

function bindEvents() {
    document.querySelectorAll("[data-view]").forEach((button) => button.addEventListener("click", () => setView(button.dataset.view)));
    document.querySelectorAll("[data-go]").forEach((button) => button.addEventListener("click", () => setView(button.dataset.go)));
    elements.fileInput.addEventListener("change", (event) => handleFileUpload(event.target.files?.[0]));
    elements.clearResume.addEventListener("click", clearResume);
    document.getElementById("logoutButton").addEventListener("click", logOut);
    document.getElementById("searchButton").addEventListener("click", searchJobs);
    document.getElementById("careerButton").addEventListener("click", getCareerAdvice);
    document.getElementById("interviewButton").addEventListener("click", getInterviewPrep);
    ["dragenter", "dragover"].forEach((eventName) => elements.uploadArea.addEventListener(eventName, (event) => {
        event.preventDefault();
        elements.uploadArea.classList.add("dragover");
    }));
    ["dragleave", "drop"].forEach((eventName) => elements.uploadArea.addEventListener(eventName, (event) => {
        event.preventDefault();
        elements.uploadArea.classList.remove("dragover");
    }));
    elements.uploadArea.addEventListener("drop", (event) => handleFileUpload(event.dataTransfer?.files?.[0]));
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") clearAlert();
    });
}

document.addEventListener("DOMContentLoaded", () => {
    bindEvents();
    restoreGoogleAccount();
    checkApi();
    restoreResume();
});
