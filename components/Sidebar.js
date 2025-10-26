'use client';

export default function Sidebar({ userName, setUserName, totalLikes, totalComments, onRefresh }) {
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>👤 User Settings</h2>
      </div>

      <div className="user-settings">
        <label htmlFor="userName">Your Name:</label>
        <input
          id="userName"
          type="text"
          className="user-name-input"
          value={userName}
          onChange={(e) => setUserName(e.target.value)}
          placeholder="Enter your name"
        />
        <p className="help-text">This will be shown with your comments</p>
      </div>

      <div className="sidebar-divider"></div>

      <button className="btn btn-refresh" onClick={onRefresh}>
        🔄 Refresh Data
      </button>

      <div className="stats-section">
        <h3>📊 Your Activity</h3>
        <div className="stat-item">
          <div className="stat-label">Total Likes Given</div>
          <div className="stat-value">{totalLikes}</div>
        </div>
        <div className="stat-item">
          <div className="stat-label">Total Comments</div>
          <div className="stat-value">{totalComments}</div>
        </div>
      </div>
    </div>
  );
}
