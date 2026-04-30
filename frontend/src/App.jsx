import React, { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { setFormField, syncState, addMessage } from './store';
import axios from 'axios';
import './App.css';

export default function App() {
  const state = useSelector((s) => s.interaction);
  const dispatch = useDispatch();
  const [input, setInput] = useState('');

  // --- Chat Logic ---
  const handleChat = async () => {
    if (!input.trim()) return;
    
    // Add user message to UI
    dispatch(addMessage({ role: 'user', text: input }));
    
    try {
      // Send to LangGraph FastAPI backend
      const res = await axios.post('http://localhost:8000/chat', {
        message: input,
        state: state
      });
      
      // Update form state and AI chat history
      dispatch(syncState(res.data.updated_form));
      dispatch(addMessage({ role: 'ai', text: res.data.ai_message }));
    } catch (error) {
      console.error("Backend Error:", error);
      dispatch(addMessage({ role: 'ai', text: "Error: Backend connection failed." }));
    }
    setInput('');
  };

  // --- Save to Database Logic ---
  const handleSaveToDatabase = async () => {
    try {
      const res = await axios.post('http://localhost:8000/save', state);
      alert(`✅ ${res.data.message}`);
      
      // Tell the AI it was saved successfully
      dispatch(addMessage({ role: 'ai', text: 'Form data successfully saved to the database.' }));
    } catch (error) {
      console.error("Save Error:", error);
      alert("❌ Failed to save to database. Make sure the backend is running.");
    }
  };

  return (
    <div className="container">
      {/* ============================== */}
      {/* LEFT PANEL: MAIN CRM FORM      */}
      {/* ============================== */}
      <div className="form-panel">
        <h2 className="page-title">Log HCP Interaction</h2>
        
        <div className="form-section">
          <h4 className="section-header">Interaction Details</h4>
          <div className="grid-2-col">
            <div className="input-group">
              <label>HCP Name</label>
              <input 
                placeholder="Search or select HCP..." 
                value={state.hcp_name || ''} 
                onChange={(e) => dispatch(setFormField({field: 'hcp_name', value: e.target.value}))}
              />
            </div>
            <div className="input-group">
              <label>Interaction Type</label>
              <select 
                value={state.interaction_type || 'Meeting'}
                onChange={(e) => dispatch(setFormField({field: 'interaction_type', value: e.target.value}))}
              >
                <option>Meeting</option>
                <option>Email</option>
                <option>Phone Call</option>
                <option>Event</option>
              </select>
            </div>
            <div className="input-group">
              <label>Date</label>
              <input 
                type="date" 
                value={state.date || ''} 
                onChange={(e) => dispatch(setFormField({field: 'date', value: e.target.value}))}
              />
            </div>
            <div className="input-group">
              <label>Time</label>
              <input 
                type="time" 
                value={state.time || ''} 
                onChange={(e) => dispatch(setFormField({field: 'time', value: e.target.value}))}
              />
            </div>
          </div>

          <div className="input-group">
            <label>Attendees</label>
            <input 
              placeholder="Enter names or search..." 
              value={state.attendees || ''} 
              onChange={(e) => dispatch(setFormField({field: 'attendees', value: e.target.value}))}
            />
          </div>

          <div className="input-group">
            <label>Topics Discussed</label>
            <div className="textarea-wrapper">
              <textarea 
                placeholder="Enter key discussion points..." 
                rows="3" 
                value={state.topics || ''}
                onChange={(e) => dispatch(setFormField({field: 'topics', value: e.target.value}))}
              />
              <span className="icon-mic">🎤</span>
            </div>
          </div>
          
          <button className="btn-voice-note">
            ✨ Summarize from Voice Note (Requires Consent)
          </button>
        </div>

        <div className="form-section">
          <h4 className="section-header">Materials Shared / Samples Distributed</h4>
          <div className="asset-box">
            <div className="asset-header">
              <span>Materials Shared</span>
              <button className="btn-outline">🔍 Search/Add</button>
            </div>
            <p className="empty-text">No materials added.</p>
          </div>
          <div className="asset-box">
            <div className="asset-header">
              <span>Samples Distributed</span>
              <button className="btn-outline">📦 Add Sample</button>
            </div>
            <p className="empty-text">No samples added.</p>
          </div>
        </div>

        <div className="form-section">
          <label className="section-header block-label">Observed/Inferred HCP Sentiment</label>
          <div className="sentiment-radio-group">
            {['Positive', 'Neutral', 'Negative'].map((s) => (
              <label key={s} className="radio-label">
                <input 
                  type="radio" 
                  name="sentiment" 
                  checked={state.sentiment === s}
                  onChange={() => dispatch(setFormField({field: 'sentiment', value: s}))}
                />
                {s === 'Positive' ? '😀' : s === 'Neutral' ? '😐' : '😞'} {s}
              </label>
            ))}
          </div>
        </div>

        <div className="form-section">
          <div className="input-group">
            <label>Outcomes</label>
            <textarea 
              placeholder="Key outcomes or agreements..." 
              rows="2" 
              value={state.outcomes || ''}
              onChange={(e) => dispatch(setFormField({field: 'outcomes', value: e.target.value}))}
            />
          </div>
          <div className="input-group">
            <label>Follow-up Actions</label>
            <textarea 
              placeholder="Enter next steps or tasks..." 
              rows="2" 
              value={state.follow_ups || ''}
              onChange={(e) => dispatch(setFormField({field: 'follow_ups', value: e.target.value}))}
            />
          </div>
        </div>

        <div className="ai-suggestions">
          <h5>AI Suggested Follow-ups:</h5>
          <ul>
            <li>+ Schedule follow-up meeting in 2 weeks</li>
            <li>+ Send OncoBoost Phase III PDF</li>
            <li>+ Add Dr. Sharma to advisory board invite list</li>
          </ul>
        </div>

        {/* --- SAVE TO DATABASE BUTTON --- */}
        <div style={{ marginTop: '35px', paddingBottom: '20px', borderTop: '1px solid #e5e7eb', paddingTop: '20px', textAlign: 'right' }}>
          <button 
            className="log-btn" 
            style={{ background: '#2563eb', padding: '12px 24px', fontSize: '1rem', cursor: 'pointer', transition: 'background 0.2s' }}
            onClick={handleSaveToDatabase}
            onMouseOver={(e) => e.target.style.background = '#1d4ed8'}
            onMouseOut={(e) => e.target.style.background = '#2563eb'}
          >
            💾 Submit
          </button>
        </div>

      </div>

      {/* ============================== */}
      {/* RIGHT PANEL: AI ASSISTANT      */}
      {/* ============================== */}
      <div className="ai-panel">
        <div className="ai-header">
          <span className="ai-icon">🤖</span>
          <div>
            <h3>AI Assistant</h3>
            <span className="ai-subtitle">Log interaction details here via chat</span>
          </div>
        </div>
        
        <div className="chat-window">
          {(!state.messages || state.messages.length === 0) && (
            <div className="msg ai-default">
              Log interaction details here (e.g., "Met Dr. Smith, discussed Prodo-X efficacy, positive sentiment, shared brochure") or ask for help.
            </div>
          )}
          {state.messages && state.messages.map((m, i) => (
            <div key={i} className={`msg ${m.role}`}>
              {m.text}
            </div>
          ))}
        </div>

        <div className="chat-input-area">
          <input 
            placeholder="Describe interaction..." 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleChat()}
          />
          <button className="log-btn" onClick={handleChat}>AI Log</button>
        </div>
      </div>
    </div>
  );
}