// State Management
let apiToken = localStorage.getItem("accessToken") || "";
let activeUsername = localStorage.getItem("activeUsername") || "";
let activeSessionId = "";
let currentSessionList = [];
let lastRagResponseSources = {}; // Caches RAG sources for the inspector

// DOM Elements
const authOverlay = document.getElementById("auth-overlay");
const loginPanel = document.getElementById("login-panel");
const registerPanel = document.getElementById("register-panel");
const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");
const authError = document.getElementById("auth-error");
const authSuccess = document.getElementById("auth-success");
const authTagline = document.getElementById("auth-tagline");

const workspaceContainer = document.getElementById("workspace-container");
const sidebar = document.querySelector(".sidebar");
const sessionsList = document.getElementById("sessions-list");
const userDisplayName = document.getElementById("user-display-name");
const logoutBtn = document.getElementById("logout-btn");
const newChatBtn = document.getElementById("new-chat-btn");

const currentChatTitle = document.getElementById("current-chat-title");
const chatWindow = document.getElementById("chat-window");
const welcomeSplash = document.getElementById("welcome-splash");
const messagesContainer = document.getElementById("messages-container");
const typingIndicator = document.getElementById("typing-indicator");
const chatInputForm = document.getElementById("chat-input-form");
const chatMessageInput = document.getElementById("chat-message-input");

const sidebarToggle = document.getElementById("sidebar-toggle");
const goToRegister = document.getElementById("go-to-register");
const goToLogin = document.getElementById("go-to-login");

// RAG Inspector Modal Elements
const ragInspectorModal = document.getElementById("rag-inspector-modal");
const closeInspectorBtn = document.getElementById("close-inspector-btn");
const ragChunksCount = document.getElementById("rag-chunks-count");
const ragTokensCount = document.getElementById("rag-tokens-count");
const inspectorSourcesContainer = document.getElementById("inspector-sources-container");

/* ==========================================================================
   Init & Setup
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
    // Configure marked options
    if (window.marked) {
        marked.setOptions({
            gfm: true,
            breaks: true,
            sanitize: false
        });
    }

    checkAuth();
    setupEventListeners();
});

function setupEventListeners() {
    // Auth Toggle tabs
    goToRegister.addEventListener("click", (e) => {
        e.preventDefault();
        showRegister();
    });
    goToLogin.addEventListener("click", (e) => {
        e.preventDefault();
        showLogin();
    });

    // Auth Form submissions
    loginForm.addEventListener("submit", handleLogin);
    registerForm.addEventListener("submit", handleRegister);
    logoutBtn.addEventListener("click", handleLogout);

    // Chat operations
    newChatBtn.addEventListener("click", () => startNewSession());
    chatInputForm.addEventListener("submit", handleSendMessage);

    // Mobile Sidebar toggle
    sidebarToggle.addEventListener("click", () => {
        sidebar.classList.toggle("open");
    });

    // Handle clicking starter query cards
    document.querySelectorAll(".clickable-starter").forEach(card => {
        card.addEventListener("click", () => {
            const query = card.getAttribute("data-query");
            chatMessageInput.value = query;
            chatInputForm.dispatchEvent(new Event("submit"));
        });
    });

    // Close RAG inspector
    closeInspectorBtn.addEventListener("click", () => {
        ragInspectorModal.classList.add("hide");
    });
    
    // Close inspector on overlay click
    ragInspectorModal.addEventListener("click", (e) => {
        if (e.target === ragInspectorModal) {
            ragInspectorModal.classList.add("hide");
        }
    });
}

/* ==========================================================================
   Authentication Flows
   ========================================================================== */

function checkAuth() {
    if (apiToken && activeUsername) {
        // Authenticated State
        authOverlay.classList.add("hide");
        workspaceContainer.classList.remove("hide");
        userDisplayName.textContent = activeUsername;
        loadSessions();
        startNewSession();
    } else {
        // Unauthenticated State
        authOverlay.classList.remove("hide");
        workspaceContainer.classList.add("hide");
        showLogin();
    }
}

function showLogin() {
    loginPanel.classList.remove("hide");
    registerPanel.classList.add("hide");
    authTagline.textContent = "Secure Workspace Agent Verification";
    clearAuthAlerts();
}

function showRegister() {
    loginPanel.classList.add("hide");
    registerPanel.classList.remove("hide");
    authTagline.textContent = "Register a Secure Agent Account";
    clearAuthAlerts();
}

function clearAuthAlerts() {
    authError.classList.add("hide");
    authSuccess.classList.add("hide");
}

function showAuthError(msg) {
    authError.textContent = msg;
    authError.classList.remove("hide");
    authSuccess.classList.add("hide");
}

function showAuthSuccess(msg) {
    authSuccess.textContent = msg;
    authSuccess.classList.remove("hide");
    authError.classList.add("hide");
}

async function handleLogin(e) {
    e.preventDefault();
    clearAuthAlerts();
    
    const username = document.getElementById("login-username").value.trim();
    const password = document.getElementById("login-password").value;
    
    try {
        const response = await fetch("/api/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "Authentication validation failed");
        }
        
        // Save token and state
        apiToken = data.accessToken;
        activeUsername = data.username;
        localStorage.setItem("accessToken", apiToken);
        localStorage.setItem("activeUsername", activeUsername);
        
        loginForm.reset();
        checkAuth();
    } catch (err) {
        showAuthError(err.message);
    }
}

async function handleRegister(e) {
    e.preventDefault();
    clearAuthAlerts();
    
    const username = document.getElementById("reg-username").value.trim();
    const password = document.getElementById("reg-password").value;
    
    try {
        const response = await fetch("/api/auth/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "Registration processing failed");
        }
        
        showAuthSuccess("Registration successful! Redirecting to login...");
        registerForm.reset();
        setTimeout(() => {
            showLogin();
        }, 1500);
    } catch (err) {
        showAuthError(err.message);
    }
}

function handleLogout() {
    apiToken = "";
    activeUsername = "";
    activeSessionId = "";
    localStorage.removeItem("accessToken");
    localStorage.removeItem("activeUsername");
    checkAuth();
}

/* ==========================================================================
   Sessions & Chats Management
   ========================================================================== */

function generateUUID() {
    return 'session-' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
}

function startNewSession() {
    activeSessionId = generateUUID();
    currentChatTitle.textContent = "New Grounded RAG Chat";
    
    // Clear display state
    welcomeSplash.classList.remove("hide");
    messagesContainer.classList.add("hide");
    messagesContainer.innerHTML = "";
    
    // Render list active state
    renderActiveSessionInList();
    
    // Close sidebar on mobile after clicking
    sidebar.classList.remove("open");
}

async function loadSessions() {
    try {
        const response = await fetch("/api/chat/sessions", {
            method: "GET",
            headers: { "Authorization": `Bearer ${apiToken}` }
        });
        
        if (response.status === 401) {
            handleLogout();
            return;
        }
        
        const data = await response.json();
        currentSessionList = data;
        renderSessionsList();
    } catch (err) {
        console.error("Failed to load historical sessions", err);
    }
}

function renderSessionsList() {
    sessionsList.innerHTML = "";
    
    if (currentSessionList.length === 0) {
        sessionsList.innerHTML = `<div class="footer-fineprint" style="margin-top: 20px;">No historical sessions</div>`;
        return;
    }
    
    currentSessionList.forEach(session => {
        const node = document.createElement("div");
        node.className = `session-item ${session.id === activeSessionId ? 'active' : ''}`;
        node.setAttribute("data-id", session.id);
        
        // Format timestamp relative display
        const dateObj = new Date(session.created_at + "Z"); // Add Z to specify UTC representation
        const relativeTime = formatRelativeTime(dateObj);
        
        node.innerHTML = `
            <div class="session-info">
                <span class="session-title">${escapeHTML(session.title)}</span>
                <span class="session-time">${relativeTime}</span>
            </div>
            <button class="btn-delete-session" title="Delete Session"><i class="fa-solid fa-trash-can"></i></button>
        `;
        
        // Load session details on click
        node.addEventListener("click", (e) => {
            if (e.target.closest(".btn-delete-session")) {
                e.stopPropagation();
                handleDeleteSession(session.id);
            } else {
                selectSession(session.id, session.title);
            }
        });
        
        sessionsList.appendChild(node);
    });
}

function renderActiveSessionInList() {
    document.querySelectorAll(".session-item").forEach(node => {
        node.classList.remove("active");
        if (node.getAttribute("data-id") === activeSessionId) {
            node.classList.add("active");
        }
    });
}

async function selectSession(sessionId, sessionTitle) {
    activeSessionId = sessionId;
    currentChatTitle.textContent = sessionTitle;
    renderActiveSessionInList();
    
    welcomeSplash.classList.add("hide");
    messagesContainer.classList.remove("hide");
    messagesContainer.innerHTML = "";
    
    // Close sidebar on mobile
    sidebar.classList.remove("open");
    
    // Fetch and render historical messages
    try {
        typingIndicator.classList.remove("hide");
        const response = await fetch(`/api/chat/sessions/${sessionId}/messages`, {
            method: "GET",
            headers: { "Authorization": `Bearer ${apiToken}` }
        });
        
        const messages = await response.json();
        typingIndicator.classList.add("hide");
        
        if (messages.length > 0) {
            messages.forEach((msg, idx) => {
                // To support RAG auditing on historic loaded bubbles, we supply a dummy unique reference ID 
                const mockRef = `${sessionId}-${idx}`;
                
                // If it's assistant with retrieved chunks, save RAG references metadata placeholder
                if (msg.role === "assistant" && msg.retrievedChunks > 0) {
                    lastRagResponseSources[mockRef] = {
                        retrievedChunks: msg.retrievedChunks,
                        tokensUsed: msg.tokensUsed,
                        sources: [
                            {
                                title: "Archived Segment",
                                source: "Refer to active inspection parameters",
                                score: 1.0,
                                content: "Chunk content successfully archived inside database history. Perform a live query to examine dynamic embedding statistics."
                            }
                        ]
                    };
                }
                
                appendMessage(msg.role, msg.content, msg.retrievedChunks > 0 ? mockRef : null, new Date(msg.created_at + "Z"));
            });
            scrollToBottom();
        } else {
            startNewSession();
        }
    } catch (err) {
        typingIndicator.classList.add("hide");
        console.error("Failed to load message history for session", err);
    }
}

async function handleDeleteSession(sessionId) {
    if (!confirm("Are you sure you want to delete this conversation session?")) return;
    
    try {
        const response = await fetch(`/api/chat/sessions/${sessionId}`, {
            method: "DELETE",
            headers: { "Authorization": `Bearer ${apiToken}` }
        });
        
        if (response.ok) {
            if (activeSessionId === sessionId) {
                startNewSession();
            }
            loadSessions();
        } else {
            alert("Failed to delete chat session from database.");
        }
    } catch (err) {
        console.error("Failed to delete session", err);
    }
}

/* ==========================================================================
   Chat Prompting & RAG Core Rendering
   ========================================================================== */

async function handleSendMessage(e) {
    e.preventDefault();
    const text = chatMessageInput.value.trim();
    if (!text) return;
    
    // Clear input
    chatMessageInput.value = "";
    
    // Display user bubble immediately
    welcomeSplash.classList.add("hide");
    messagesContainer.classList.remove("hide");
    appendMessage("user", text);
    scrollToBottom();
    
    // Display loading skeletons
    typingIndicator.classList.remove("hide");
    
    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "Authorization": `Bearer ${apiToken}`
            },
            body: JSON.stringify({
                sessionId: activeSessionId,
                message: text
            })
        });
        
        typingIndicator.classList.add("hide");
        
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "Connection failure from RAG backend API");
        }
        
        // Cache response sources for RAG Modal inspector
        const refId = `msg-ref-${Date.now()}`;
        if (data.retrievedChunks > 0) {
            lastRagResponseSources[refId] = {
                retrievedChunks: data.retrievedChunks,
                tokensUsed: data.tokensUsed,
                sources: data.sources
            };
        }
        
        // Append response bubble
        appendMessage("assistant", data.reply, data.retrievedChunks > 0 ? refId : null);
        scrollToBottom();
        
        // Refresh sidebar sessions to reflect updated ordering and names
        loadSessions();
    } catch (err) {
        typingIndicator.classList.add("hide");
        appendMessage("assistant", `**Critical Error:** ${err.message}. Please verify your API key configurations inside the system environment files.`);
        scrollToBottom();
    }
}

function appendMessage(role, text, refId = null, timestamp = null) {
    const bubble = document.createElement("div");
    bubble.className = `message-bubble ${role}`;
    
    const timeToDisplay = timestamp ? formatTimeOnly(timestamp) : formatTimeOnly(new Date());
    
    let avatarMarkup = "";
    if (role === "user") {
        avatarMarkup = `<span class="avatar-icon"><i class="fa-solid fa-user"></i></span>`;
    } else {
        avatarMarkup = `<span class="avatar-icon"><i class="fa-solid fa-robot"></i></span>`;
    }
    
    // Format text using markdown library if loaded, else fallback to basic HTML escaping
    let bodyTextMarkup = "";
    if (window.marked) {
        bodyTextMarkup = marked.parse(text);
    } else {
        bodyTextMarkup = `<p>${escapeHTML(text).replace(/\n/g, "<br>")}</p>`;
    }
    
    let inspectorBadgeMarkup = "";
    if (role === "assistant" && refId) {
        inspectorBadgeMarkup = `
            <div class="rag-meta">
                <button class="btn-inspect-rag" onclick="openRagInspector('${refId}')">
                    <i class="fa-solid fa-square-poll-vertical"></i> View RAG Context Chunks
                </button>
            </div>
        `;
    }
    
    bubble.innerHTML = `
        ${avatarMarkup}
        <div class="bubble-content">
            <div class="body">${bodyTextMarkup}</div>
            ${inspectorBadgeMarkup}
            <span class="message-timestamp">${timeToDisplay}</span>
        </div>
    `;
    
    messagesContainer.appendChild(bubble);
}

// Global RAG inspector trigger function
window.openRagInspector = function(refId) {
    const data = lastRagResponseSources[refId];
    if (!data) return;
    
    ragChunksCount.textContent = data.retrievedChunks;
    ragTokensCount.textContent = data.tokensUsed;
    
    inspectorSourcesContainer.innerHTML = "";
    
    data.sources.forEach(src => {
        const card = document.createElement("div");
        card.className = "source-card";
        card.innerHTML = `
            <div class="card-head">
                <span class="title">${escapeHTML(src.title)}</span>
                <span class="badge badge-cyan">Similarity: ${src.score.toFixed(4)}</span>
            </div>
            <span class="doc-src">Source Ref: ${escapeHTML(src.source)}</span>
            <p class="content-extract">${escapeHTML(src.content)}</p>
        `;
        inspectorSourcesContainer.appendChild(card);
    });
    
    ragInspectorModal.classList.remove("hide");
};

/* ==========================================================================
   Formatting & Visual Layout Helpers
   ========================================================================== */

function scrollToBottom() {
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function escapeHTML(str) {
    return str.replace(/[&<>'"]/g, 
        tag => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            "'": '&#39;',
            '"': '&quot;'
        }[tag] || tag)
    );
}

function formatTimeOnly(date) {
    let hours = date.getHours();
    let minutes = date.getMinutes();
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12; // the hour '0' should be '12'
    minutes = minutes < 10 ? '0'+minutes : minutes;
    return `${hours}:${minutes} ${ampm}`;
}

function formatRelativeTime(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays === 1) return "Yesterday";
    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}
