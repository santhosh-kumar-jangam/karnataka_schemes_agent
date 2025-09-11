import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

export default function App() {
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [conversations, setConversations] = useState({});
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]); // file upload
  const messagesEndRef = useRef(null);

  // scroll to bottom when messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversations, activeSession, loading]);

  // create new session
  async function handleNewChat() {
    try {
      const res = await axios.post(`${API_URL}/create-new-session`);
      const sessionId = res.data.session_id;
      setSessions((prev) => [sessionId, ...prev]);
      setActiveSession(sessionId);
      setConversations((prev) => ({ ...prev, [sessionId]: [] }));
    } catch (err) {
      console.error("Error creating session:", err);
      alert("Could not create session");
    }
  }

  // select existing session
  async function handleSelectSession(sessionId) {
    setActiveSession(sessionId);
    // conversations are already in memory
  }

  // delete session
  async function handleDeleteSession(sessionId) {
    try {
      await axios.delete(`${API_URL}/delete-session/${sessionId}`);
      setSessions((prev) => prev.filter((s) => s !== sessionId));
      setConversations((prev) => {
        const copy = { ...prev };
        delete copy[sessionId];
        return copy;
      });
      if (activeSession === sessionId) {
        setActiveSession(null);
      }
    } catch (err) {
      console.error("Error deleting session:", err);
      alert("Could not delete session on server");
    }
  }

  // send user message
  async function handleSend(e) {
    e.preventDefault();
    if ((!input.trim() && selectedFiles.length === 0) || !activeSession) return;

    const userText = input.trim();
    const fileNames = selectedFiles.map((f) => f.name).join(", ");
    const combinedMsg = userText + (fileNames ? `\n📎 Files: ${fileNames}` : "");

    const userMsg = { sender: "user", text: combinedMsg };
    setConversations((prev) => ({
      ...prev,
      [activeSession]: [...(prev[activeSession] || []), userMsg],
    }));

    const query = combinedMsg;
    setInput("");
    setSelectedFiles([]); // clear uploaded files
    setLoading(true);

    try {
      const payload = { query, session_id: activeSession };
      const res = await axios.post(`${API_URL}/agent/run`, payload, {
        timeout: 60000,
      });

      const botMsg = {
        sender: "bot",
        text: res.data.response || "No response",
      };

      setConversations((prev) => ({
        ...prev,
        [activeSession]: [...(prev[activeSession] || []), botMsg],
      }));
    } catch (err) {
      console.error("Error sending message:", err);
      setConversations((prev) => ({
        ...prev,
        [activeSession]: [
          ...(prev[activeSession] || []),
          { sender: "bot", text: "Sorry, something went wrong." },
        ],
      }));
    } finally {
      setLoading(false);
    }
  }

  const activeMessages = conversations[activeSession] || [];

  return (
    <div className="layout">
      {/* Top Header */}
      <div className="topbar">Karnataka Seva Sindhu</div>

      <div className="app">
        {/* Sidebar */}
        <aside className="sidebar">
          <div className="sidebar-header">
            <h3>Sessions</h3>
            <button className="new-btn" onClick={handleNewChat} disabled={loading}>
              + New
            </button>
          </div>
          <div className="session-list">
            {sessions.length === 0 && <div className="empty-note">No sessions yet</div>}
            {sessions.map((sid) => (
              <div
                key={sid}
                className={`session-item ${sid === activeSession ? "active" : ""}`}
                onClick={() => handleSelectSession(sid)}
              >
                <div className="session-title">
                  {conversations[sid] && conversations[sid].length > 0
                    ? conversations[sid][0].text.split("\n")[0].slice(0, 25) + "..."  // first message snippet
                    : sid}
                </div>
                <div className="session-actions">
                  <button
                    className="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteSession(sid);
                    }}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        </aside>

        {/* Main Chat Panel */}
        <main className="chat-panel">
          <div className="chat-header">
            <h2>{activeSession ? `Session: ${activeSession}` : "No session selected"}</h2>
            {loading && <div className="loading-indicator">Thinking…</div>}
          </div>

          <div className="messages">
            {activeMessages.length === 0 && !loading && (
              <div className="empty-chat">Start the conversation — say hi!</div>
            )}
            {activeMessages.map((m, i) => (
              <div key={i} className={`message-row ${m.sender}`}>
                <div className={`bubble ${m.sender}-bubble`}>{m.text}</div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* File preview before send */}
          {selectedFiles.length > 0 && (
            <div className="selected-files">
              {selectedFiles.map((file, i) => (
                <div key={i} className="file-chip">
                  {file.name}
                  <button
                    type="button"
                    className="remove-file"
                    onClick={() =>
                      setSelectedFiles((prev) => prev.filter((_, idx) => idx !== i))
                    }
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Composer */}
          <form className="composer" onSubmit={handleSend}>
            {/* File Upload + Button */}
            <label className="file-btn">
              +
              <input
                type="file"
                style={{ display: "none" }}
                multiple
                onChange={(e) => {
                  const files = Array.from(e.target.files || []);
                  setSelectedFiles((prev) => [...prev, ...files]);
                }}
              />
            </label>

            {/* Chat Input */}
            <input
              placeholder="Type a message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={!activeSession || loading}
            />

            {/* Send Button */}
            <button
              type="submit"
              disabled={(!input.trim() && selectedFiles.length === 0) || loading}
            >
              Send
            </button>
          </form>
        </main>
      </div>
    </div>
  );
}