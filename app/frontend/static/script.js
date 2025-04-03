const { useState, useEffect, useRef } = React;

function LocalWebViewer({ projectName }) {
  const [loadError, setLoadError] = useState(false);

  function handleExport() {
    if (!projectName) {
      alert("Project name is required for export.");
      return;
    }

    fetch(`/export?project_name=${encodeURIComponent(projectName)}`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`Export failed: ${response.statusText}`);
        }
        return response.blob();
      })
      .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${projectName}_export.zip`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      })
      .catch(err => {
        alert(`Error exporting file: ${err.message}`);
        console.error(err);
      });
  }

  if (loadError) {
    return null;
  }

  return (
    <div className="web-viewer-container">
      <div style={{ marginBottom: '10px', textAlign: 'right' }}>
        <button className="btn btn-secondary" onClick={handleExport}>
          Export
        </button>
      </div>
      <iframe 
        src="http://127.0.0.1:8080/" 
        width="100%" 
        height="100%" 
        style={{ border: "none", borderRadius: "8px" }}
        onError={() => setLoadError(true)}
      ></iframe>
    </div>
  );
}



function LineNumbers({ code }) {
  const lines = code.split("\n");
  return (
    <div className="line-numbers">
      {lines.map((_, i) => (
        <div key={i} className="line-number">
          {i + 1}
        </div>
      ))}
    </div>
  );
}

/**
 * A code editor with line numbering (no "Ask AI" button).
 */
function CodeEditor({ code, setCode }) {
  return (
    <div className="code-editor-container">
      <LineNumbers code={code} />
      <textarea
        className="code-textarea"
        value={code}
        onChange={e => setCode(e.target.value)}
        spellCheck="false"
      />
    </div>
  );
}

/**
 * The "Code" view.
 */
function CodeViewer({ code, setCode, projectName, setProjectName, submitProject }) {
  return (
    <div className="code-section">
      <div className="project-name-group">
        <input
          type="text"
          className="form-control"
          placeholder="Enter project name"
          value={projectName}
          onChange={e => setProjectName(e.target.value)}
        />
        <button className="btn btn-primary" onClick={submitProject}>
          Submit
        </button>
      </div>
      <CodeEditor code={code} setCode={setCode} />
    </div>
  );
}

/**
 * Tabs on the right side: one for Code, one for SVG Viewer.
 */
function RightTabs({ code, setCode, projectName, setProjectName, submitProject }) {
  const [activeTab, setActiveTab] = useState("code");

  return (
    <div className="tabs-container">
      <div className="tabs-buttons">
        <button
          className={`tab-button ${activeTab === "code" ? "active" : ""}`}
          onClick={() => setActiveTab("code")}
        >
          Code
        </button>
        <button
          className={`tab-button ${activeTab === "schematic" ? "active" : ""}`}
          onClick={() => setActiveTab("schematic")}
        >
          Schematic
        </button>
      </div>
      <div className="tabs-content">
        {activeTab === "code" && (
          <CodeViewer 
            code={code} 
            setCode={setCode}
            projectName={projectName}
            setProjectName={setProjectName}
            submitProject={submitProject}
          />
        )}
        {activeTab === "schematic" && <LocalWebViewer projectName={projectName} />}
    </div>
    </div>
  );
}

function ChatWindow() {
  const [messages, setMessages] = useState([]);
  const [userInput, setUserInput] = useState("");

  const [systemPrompt, setSystemPrompt] = useState("");        // store front-end system_prompt.md
  const [hasSentSystemPrompt, setHasSentSystemPrompt] = useState(false);

  // Fetch system_prompt.md once on mount
  useEffect(() => {
    fetch("system_prompt.md")
      .then((r) => r.text())
      .then((txt) => setSystemPrompt(txt))
      .catch((err) => {
        console.error("Failed to load system_prompt.md:", err);
        setSystemPrompt(""); // fallback
      });
  }, []);

  async function sendMessage() {
    const trimmed = userInput.trim();
    if (!trimmed) return;

    setMessages((prev) => [...prev, { sender: "User", text: trimmed }]);
    setUserInput("");

    // Build combined message
    let combinedMsg;
    if (!hasSentSystemPrompt) {
      // First message includes system prompt + code + user prompt
      combinedMsg =
        "SYSTEM PROMPT:\n" +
        systemPrompt +
        "\n\nCURRENT CODE:\n" +
        (window.globalCodeRef || "") +
        "\n\nUSER MESSAGE:\n" +
        trimmed;
      setHasSentSystemPrompt(true);
    } else {
      // Subsequent messages: just code + user prompt
      combinedMsg =
        "CURRENT CODE:\n" +
        (window.globalCodeRef || "") +
        "\n\nUSER MESSAGE:\n" +
        trimmed;
    }

    try {
      const requestBody = { prompt: combinedMsg };

      const res = await fetch("/prompt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody)
      });

      if (!res.ok) {
        throw new Error(`Server error: ${res.status} ${await res.text()}`);
      }

      const data = await res.json();
      setMessages((prev) => [...prev, { sender: "AI", text: data.response }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { sender: "AI", text: `Error contacting server: ${err.message}` }
      ]);
      console.error("Fetch error:", err);
    }
  }


  return (
    <div className="chat-window">
      <div className="conversation-container mb-3">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.sender.toLowerCase()}`}
            dangerouslySetInnerHTML={{ __html: marked.parse(msg.text) }} />
        ))}
      </div>
      <div className="input-group mb-3">
        <input type="text" value={userInput}
          onChange={e => setUserInput(e.target.value)}
          className="form-control" placeholder="Type a message..."
          onKeyPress={e => { if (e.key === "Enter") sendMessage(); }} />
        <button className="btn btn-primary" onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
}

function App() {
  const [leftWidth, setLeftWidth] = useState(500);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef(null);

  const [code, setCode] = useState(`// Your code here\n`);
  const [projectName, setProjectName] = useState("");

  // Keep code in a global so ChatWindow can see it
  useEffect(() => {
    window.globalCodeRef = code;
  }, [code]);

  // Drag resizing logic
  useEffect(() => {
    function handleMouseMove(e) {
      if (!isDragging) return;
      const newWidth = Math.min(Math.max(e.clientX, 300), window.innerWidth - 200);
      setLeftWidth(newWidth);
    }

    function handleMouseUp() {
      setIsDragging(false);
    }

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isDragging]);

  function onMouseDownResizer() {
    setIsDragging(true);
  }

  function submitProject() {
    const trimmedProjectName = projectName.trim();
    if (!trimmedProjectName) {
      alert("Please enter a valid project name!");
      return;
    }
  
    // Step 1: Create the project
    fetch("/create_project", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        project_name: trimmedProjectName,
        source_ato: code   // <-- include the code here
      })
    })
      .then(async (res) => {
        if (!res.ok) {
          const errorText = await res.text();
          throw new Error(`Create project failed: ${errorText}`);
        }
        return res.json();
      })
      .then(data => {
        console.log("Project creation response:", data);
        alert("Project created successfully. Now building...");
  
        // Step 2: Only after successful creation, build & view
        return fetch("/build_view_project", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ 
            project_name: trimmedProjectName,
            source_ato: code
          })
        });
      })
      .then(async (res) => {
        if (!res.ok) {
          const errorText = await res.text();
          throw new Error(`Build/View failed: ${errorText}`);
        }
        return res.json();
      })
      .then(data => {
        console.log("Build & View response:", data);
        alert("Build and view started successfully. Check tmux viewer.");
      })
      .catch(err => {
        console.error("Submission error:", err);
        alert(`An error occurred: ${err.message}`);
      });
  }
  
  

  return (
    <div className="split-container" ref={containerRef}>
      <div className="left-pane" style={{ width: leftWidth }}>
        <ChatWindow />
      </div>
      <div className="resizer" onMouseDown={onMouseDownResizer} />
      <div className="right-pane" style={{ flex: 1 }}>
        <RightTabs
          code={code}
          setCode={setCode}
          projectName={projectName}
          setProjectName={setProjectName}
          submitProject={submitProject}
        />
      </div>
    </div>
  );
}

ReactDOM.render(<App />, document.getElementById("root"));