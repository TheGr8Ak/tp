'use client';

import { useState } from 'react';

export default function ArticleCard({ article, likes, comments, onLike, onAddComment, onCopyToClipboard }) {
  const [showComments, setShowComments] = useState(false);
  const [showShare, setShowShare] = useState(false);
  const [commentText, setCommentText] = useState('');
  const [copySuccess, setCopySuccess] = useState(false);

  const handlePostComment = () => {
    if (commentText.trim()) {
      onAddComment(commentText.trim());
      setCommentText('');
    }
  };

  const handleCopyLink = async () => {
    const success = await onCopyToClipboard(article.url);
    if (success) {
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    }
  };

  const formatDate = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="article-container">
      <div className="article-box">
        <div 
          className="article-title" 
          onClick={() => window.open(article.url, '_blank')}
        >
          {article.title}
        </div>
        <div className="article-meta">
          <span className="source-badge">📰 {article.source}</span>
          <span>📅 {article.published}</span>
          <span className="score-badge">⭐ {article.score}/10</span>
        </div>
        <div className="article-summary">{article.summary}</div>
      </div>

      <div className="interaction-bar">
        <button 
          className="btn btn-like" 
          onClick={onLike}
        >
          ❤️ Like ({likes})
        </button>
        <button 
          className="btn btn-comment" 
          onClick={() => setShowComments(!showComments)}
        >
          💬 Comments ({comments.length})
        </button>
        <button 
          className="btn btn-share" 
          onClick={() => setShowShare(!showShare)}
        >
          🔗 Share
        </button>
        <button 
          className="btn btn-read" 
          onClick={() => window.open(article.url, '_blank')}
        >
          📖 Read Full Article
        </button>
      </div>

      {showShare && (
        <div className="share-section">
          <h3>🔗 Share Options</h3>
          <div className="share-buttons">
            <button className="btn btn-copy" onClick={handleCopyLink}>
              📋 Copy Link
            </button>
            <a 
              href={`https://twitter.com/intent/tweet?text=Check out this article: ${article.title} - ${article.url}`}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-twitter"
            >
              🐦 Share on Twitter
            </a>
            <a 
              href={`https://www.linkedin.com/sharing/share-offsite/?url=${article.url}`}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-linkedin"
            >
              💼 Share on LinkedIn
            </a>
          </div>
          {copySuccess && (
            <div className="share-success">
              ✅ Link copied to clipboard!
            </div>
          )}
        </div>
      )}

      {showComments && (
        <div className="comment-section">
          <h3>💬 Comments</h3>
          
          {comments.length > 0 ? (
            <div className="comments-list">
              {comments.map(comment => (
                <div key={comment.id} className="comment-item">
                  <div className="comment-author">{comment.author}</div>
                  <div className="comment-time">{formatDate(comment.timestamp)}</div>
                  <div className="comment-text">{comment.text}</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="no-comments">
              No comments yet. Be the first to comment!
            </div>
          )}

          <div className="add-comment">
            <strong>Add a comment:</strong>
            <textarea
              className="comment-input"
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
              placeholder="Share your thoughts about this article..."
              rows="3"
            />
            <button 
              className="btn btn-post-comment" 
              onClick={handlePostComment}
              disabled={!commentText.trim()}
            >
              Post Comment
            </button>
          </div>
        </div>
      )}

      <div className="article-divider"></div>
    </div>
  );
}
