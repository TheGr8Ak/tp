'use client';

import { useState, useEffect, useCallback } from 'react';
import './globals.css';
import ArticleCard from '../components/ArticleCard';
import Sidebar from '../components/Sidebar';

export default function Home() {
  const [articles, setArticles] = useState([]);
  const [likes, setLikes] = useState({});
  const [comments, setComments] = useState({});
  const [userName, setUserName] = useState('Anonymous User');
  const [loading, setLoading] = useState(true);
  const [fileUsed, setFileUsed] = useState('');
  const [error, setError] = useState(null);

  // Embedded fallback data - EXACT COPY from your Streamlit
  const FALLBACK_DATA = `HYBRID TECH NEWS SCRAPER RESULTS - 2025-10-09 21:09:52
====================================================================================================
Total Articles: 50 | Sources: 11
Average Relevance Score: 6.1/10
====================================================================================================

ARTICLE #1
--------------------------------------------------------------------------------
TITLE: Accelerating Business
SOURCE: Financial Times Tech
PUBLISHED: Thu, 09 Oct 2025 04:03:58 GMT
URL: https://www.ft.com/reports/accelerating-business
GEMINI SCORE: 10/10

SUMMARY:
This article discusses how six companies are utilizing AI to innovate and address the evolving needs of businesses within the legal industry, suggesting a focus on technology adoption in a B2B context.

CONTENT PREVIEW:
Please enable JavaScript to proceed.

====================================================================================================

ARTICLE #2
--------------------------------------------------------------------------------
TITLE: India pilots AI chatbot-led e-commerce with ChatGPT, Gemini, Claude in the mix
SOURCE: TechCrunch
PUBLISHED: Thu, 09 Oct 2025 14:46:53 +0000
URL: https://techcrunch.com/2025/10/09/india-pilots-ai-chatbot-led-e-commerce-with-chatgpt-gemini-claude-in-the-mix/
GEMINI SCORE: 9/10

SUMMARY:
India is piloting AI-powered e-commerce, enabling users to shop and pay through chatbots like ChatGPT. This initiative explores the potential of AI in revolutionizing the online shopping experience.

CONTENT PREVIEW:
India has kicked off a pilot to let consumers shop and pay directly through AI chatbots, with OpenAI's ChatGPT leading the rollout and integrations with Google's Gemini and Anthropic's Claude in development.

====================================================================================================`;

  // Load persistent data from localStorage
  useEffect(() => {
    const savedLikes = localStorage.getItem('news_likes');
    const savedComments = localStorage.getItem('news_comments');
    const savedUserName = localStorage.getItem('user_name');

    if (savedLikes) setLikes(JSON.parse(savedLikes));
    if (savedComments) setComments(JSON.parse(savedComments));
    if (savedUserName) setUserName(savedUserName);
  }, []);

  // Save to localStorage whenever likes or comments change
  useEffect(() => {
    localStorage.setItem('news_likes', JSON.stringify(likes));
    localStorage.setItem('news_comments', JSON.stringify(comments));
  }, [likes, comments]);

  useEffect(() => {
    localStorage.setItem('user_name', userName);
  }, [userName]);

  // Parse articles - EXACT LOGIC from your Streamlit
  // Parse articles - HANDLES BOTH WINDOWS AND UNIX LINE ENDINGS
const parseArticles = useCallback((content) => {
  console.log('🔧 Parsing articles from content...');
  
  // Normalize line endings to Unix style first
  const normalizedContent = content.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
  
  const articles = [];
  const sections = normalizedContent.split('====================================================================================================');

  sections.forEach((section, index) => {
    if (section.includes('ARTICLE #') && section.includes('TITLE:')) {
      try {
        const articleNumMatch = section.match(/ARTICLE #(\d+)/);
        const titleMatch = section.match(/TITLE: (.+)/);
        const sourceMatch = section.match(/SOURCE: (.+)/);
        const publishedMatch = section.match(/PUBLISHED: (.+)/);
        const urlMatch = section.match(/URL: (.+)/);
        const summaryMatch = section.match(/SUMMARY:\n([\s\S]+?)\n\n/);
        const scoreMatch = section.match(/GEMINI SCORE: (.+?)\/10/);

        if (titleMatch && sourceMatch && urlMatch) {
          const articleId = articleNumMatch 
            ? `article_${articleNumMatch[1]}` 
            : `article_${articles.length}`;

          const article = {
            id: articleId,
            num: articleNumMatch ? parseInt(articleNumMatch[1]) : articles.length,
            title: titleMatch[1].trim(),
            source: sourceMatch[1].trim(),
            published: publishedMatch ? publishedMatch[1].trim() : 'Unknown',
            url: urlMatch[1].trim(),
            summary: summaryMatch ? summaryMatch[1].trim() : 'No summary available',
            score: scoreMatch ? 
              (scoreMatch[1] === 'N/A' ? 5 : parseInt(scoreMatch[1])) : 5
          };
          articles.push(article);
          console.log(`✅ Parsed article ${articles.length}: ${article.title.substring(0, 50)}...`);
        }
      } catch (e) {
        console.error('❌ Error parsing article section:', e);
      }
    }
  });

  console.log(`📊 Total articles parsed: ${articles.length}`);
  return articles;
}, []);


  // Load news from file - reads from YOUR file
  const loadNewsFromFile = useCallback(async () => {
    const possibleFiles = [
      'hybrid_tech_news.txt'
    ];

    let content = null;
    let usedFile = null;

    // Try to load from public folder
    for (const filename of possibleFiles) {
      try {
        const response = await fetch(`/${filename}`);
        if (response.ok) {
          content = await response.text();
          usedFile = filename;
          break;
        }
      } catch (e) {
        console.error(`Error reading ${filename}:`, e);
      }
    }

    // Fallback to embedded data
    if (!content) {
      content = FALLBACK_DATA;
      usedFile = 'embedded data';
    }

    return { content, usedFile };
  }, [FALLBACK_DATA]);

  // Load articles on mount
  useEffect(() => {
    const loadArticles = async () => {
      try {
        setLoading(true);
        const { content, usedFile } = await loadNewsFromFile();
        const parsedArticles = parseArticles(content);
        setArticles(parsedArticles);
        setFileUsed(usedFile);
        setLoading(false);
      } catch (err) {
        setError('Failed to load articles');
        setLoading(false);
      }
    };

    loadArticles();
  }, [loadNewsFromFile, parseArticles]);

  // Handle like
  const handleLike = useCallback((articleId) => {
    setLikes(prev => ({
      ...prev,
      [articleId]: (prev[articleId] || 0) + 1
    }));
  }, []);

  // Add comment
  const addComment = useCallback((articleId, commentText) => {
    const newComment = {
      id: generateUUID(),
      author: userName,
      text: commentText,
      timestamp: new Date().toISOString()
    };

    setComments(prev => ({
      ...prev,
      [articleId]: [...(prev[articleId] || []), newComment]
    }));
  }, [userName]);

  // Generate UUID
  const generateUUID = () => {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  };

  // Copy to clipboard
  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (err) {
      console.error('Failed to copy:', err);
      return false;
    }
  };

  // Refresh data
  const refreshData = () => {
    const savedLikes = localStorage.getItem('news_likes');
    const savedComments = localStorage.getItem('news_comments');
    if (savedLikes) setLikes(JSON.parse(savedLikes));
    if (savedComments) setComments(JSON.parse(savedComments));
  };

  // Calculate stats
  const totalLikes = Object.values(likes).reduce((sum, count) => sum + count, 0);
  const totalComments = Object.values(comments).reduce((sum, arr) => sum + arr.length, 0);

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading articles...</p>
      </div>
    );
  }

  if (error) {
    return <div className="error-container">{error}</div>;
  }

  return (
    <div className="app-container">
      <Sidebar
        userName={userName}
        setUserName={setUserName}
        totalLikes={totalLikes}
        totalComments={totalComments}
        onRefresh={refreshData}
      />

      <div className="main-content">
        <header className="main-header">
          <h1>🚀 Interactive Tech News Feed</h1>
          <p>Like • Comment • Share • Latest Tech News</p>
        </header>

        <div className="success-message">
          ✅ Loaded {articles.length} articles from {fileUsed}
        </div>

        <div className="articles-header">
          <h2>📰 Latest News Articles</h2>
          <p className="articles-subtitle">*Like, comment, and share articles below*</p>
        </div>

        <div className="articles-list">
          {articles.map(article => (
            <ArticleCard
              key={article.id}
              article={article}
              likes={likes[article.id] || 0}
              comments={comments[article.id] || []}
              onLike={() => handleLike(article.id)}
              onAddComment={(text) => addComment(article.id, text)}
              onCopyToClipboard={copyToClipboard}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
