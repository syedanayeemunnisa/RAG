// Elements
const pdfFileInput = document.getElementById("pdfFile");
const uploadBtn = document.getElementById("uploadBtn");
const uploadStatus = document.getElementById("uploadStatus");
const messagesContainer = document.getElementById("messages");
const questionInput = document.getElementById("questionInput");
const askBtn = document.getElementById("askBtn");
const indexerBadge = document.getElementById("indexerBadge");
const chatBadge = document.getElementById("chatBadge");

// Helper to escape HTML and format basic markdown (bold, inline code)
function formatMessage(text) {
  let html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  
  // Bold: **text** -> <strong>text</strong>
  html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  
  // Inline code: `code` -> <code>code</code>
  html = html.replace(/`(.*?)`/g, "<code>$1</code>");
  
  return html;
}

// Helper to add a message to the chat container
function addMessage(sender, text) {
  const msgDiv = document.createElement("div");
  msgDiv.className = `message ${sender}`;
  msgDiv.innerHTML = formatMessage(text);
  messagesContainer.appendChild(msgDiv);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Check backend status on load
async function checkStatus() {
  try {
    const response = await fetch("/api/status");
    if (!response.ok) throw new Error("Server error");
    
    const data = await response.json();
    if (data.indexed) {
      indexerBadge.textContent = "Cached";
      indexerBadge.style.color = "#38bdf8";
      indexerBadge.style.borderColor = "rgba(56, 189, 248, 0.3)";
      
      chatBadge.textContent = "Ready";
      chatBadge.className = "badge badge-pulse";
      
      addMessage("bot", `⚡ System ready! Automatically loaded contract.pdf from cache (${data.chunks} chunks indexed). Ask me anything about the document.`);
    } else {
      indexerBadge.textContent = "Empty";
      chatBadge.textContent = "Waiting";
      chatBadge.className = "badge";
      addMessage("bot", "👋 Welcome! Please upload/index a PDF document to begin asking questions.");
    }
  } catch (error) {
    indexerBadge.textContent = "Offline";
    indexerBadge.style.color = "#ef4444";
    indexerBadge.style.borderColor = "rgba(239, 68, 68, 0.3)";
    chatBadge.textContent = "Offline";
    chatBadge.className = "badge";
    addMessage("bot", "❌ Unable to connect to the backend server. Please make sure uvicorn is running on port 8000.");
    console.error("Status check failed:", error);
  }
}

// Upload PDF handler
uploadBtn.addEventListener("click", async () => {
  const file = pdfFileInput.files[0];
  if (!file) {
    uploadStatus.textContent = "⚠️ Please select a PDF file first.";
    return;
  }

  uploadStatus.textContent = "⏳ Uploading, chunking and indexing PDF...";
  uploadBtn.disabled = true;

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/api/upload", {
      method: "POST",
      body: formData
    });

    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.detail || "Upload failed");
    }

    const data = await response.json();
    uploadStatus.textContent = `✅ Success! Indexed ${data.chunks} chunks from "${file.name}".`;
    
    indexerBadge.textContent = "Indexed";
    indexerBadge.style.color = "#38bdf8";
    chatBadge.textContent = "Ready";
    chatBadge.className = "badge badge-pulse";
    
    addMessage("bot", `PDF indexed successfully. You can now ask questions about "${file.name}".`);
  } catch (error) {
    uploadStatus.textContent = `❌ Error: ${error.message}`;
    console.error("Upload error:", error);
  } finally {
    uploadBtn.disabled = false;
  }
});

// Ask query handler
async function handleQuery() {
  const queryText = questionInput.value.trim();
  if (!queryText) return;

  // Append user message
  addMessage("user", queryText);
  questionInput.value = "";
  askBtn.disabled = true;

  // Add loading/waiting indicator from bot
  const loadingDiv = document.createElement("div");
  loadingDiv.className = "message bot loading";
  loadingDiv.textContent = "Thinking...";
  messagesContainer.appendChild(loadingDiv);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  try {
    const response = await fetch("/api/query", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ question: queryText })
    });

    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.detail || "Query failed");
    }

    const data = await response.json();
    // Remove loading message
    loadingDiv.remove();
    // Add real answer
    addMessage("bot", data.answer);
  } catch (error) {
    loadingDiv.remove();
    addMessage("bot", `❌ Error retrieving answer: ${error.message}`);
    console.error("Query error:", error);
  } finally {
    askBtn.disabled = false;
  }
}

askBtn.addEventListener("click", handleQuery);

questionInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    handleQuery();
  }
});

// Initialize status check on load
window.addEventListener("DOMContentLoaded", checkStatus);
