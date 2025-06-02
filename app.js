// Mock data from the provided JSON
const mockData = {
  "systemStatus": {
    "overall": "running",
    "services": [
      {"name": "Content Scraper", "status": "running", "lastRun": "2025-06-02T14:30:00Z", "success": 95},
      {"name": "AI Processor", "status": "running", "lastRun": "2025-06-02T14:25:00Z", "success": 98},
      {"name": "Distributor", "status": "warning", "lastRun": "2025-06-02T14:20:00Z", "success": 87},
      {"name": "Monitoring", "status": "running", "lastRun": "2025-06-02T14:35:00Z", "success": 100}
    ]
  },
  "contentSources": [
    {"id": 1, "name": "FDA Medical Device Updates", "type": "RSS", "url": "https://fda.gov/feeds/medical-devices.xml", "status": "active", "articles": 42},
    {"id": 2, "name": "Maritime Hydrogen News", "type": "HTML", "url": "https://maritime-executive.com/hydrogen", "status": "active", "articles": 18},
    {"id": 3, "name": "Neurotech Patents", "type": "API", "url": "https://patents.uspto.gov/api/neurotech", "status": "paused", "articles": 7}
  ],
  "recentActivity": [
    {"time": "14:30", "action": "Scraped 5 new articles from FDA Medical Device Updates", "type": "success"},
    {"time": "14:25", "action": "AI processed 3 articles, enhanced content generated", "type": "info"},
    {"time": "14:20", "action": "Published to LinkedIn - 'New FDA Approval for Dental Implants'", "type": "success"},
    {"time": "14:15", "action": "Twitter rate limit exceeded, retrying in 15 minutes", "type": "warning"},
    {"time": "14:10", "action": "Generated affiliate links for 2 SaaS recommendations", "type": "info"}
  ],
  "metrics": {
    "articlesProcessed": 1847,
    "platformsPublished": 4,
    "monthlyRevenue": 2340,
    "subscriberGrowth": 15.7
  },
  "contentLibrary": [
    {
      "id": 1, "title": "Revolutionary 3D Printed Prosthetic Receives FDA Approval", 
      "source": "FDA Medical Device Updates", "status": "enhanced", 
      "scrapedAt": "2025-06-02T14:30:00Z", "platforms": ["LinkedIn", "Twitter"],
      "summary": "The FDA has approved a breakthrough 3D printed prosthetic device that offers improved mobility and reduced cost..."
    },
    {
      "id": 2, "title": "Hydrogen Fuel Cells Powering New Maritime Vessels", 
      "source": "Maritime Hydrogen News", "status": "processing", 
      "scrapedAt": "2025-06-02T14:25:00Z", "platforms": [],
      "summary": "A new generation of hydrogen-powered vessels is revolutionizing maritime transportation..."
    }
  ],
  "distributionPlatforms": [
    {"name": "LinkedIn", "status": "connected", "posts": 89, "engagement": "4.2%"},
    {"name": "Twitter", "status": "rate_limited", "posts": 156, "engagement": "2.8%"},
    {"name": "Medium", "status": "connected", "posts": 23, "engagement": "6.1%"},
    {"name": "Substack", "status": "disconnected", "posts": 0, "engagement": "0%"}
  ],
  "monetization": {
    "subscriptions": {"basic": 67, "pro": 23, "enterprise": 4},
    "affiliateRevenue": 1580,
    "sponsoredPosts": 3,
    "totalRevenue": 2340
  }
};

// Application state
let currentTheme = 'light';
let currentSection = 'dashboard';

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
  initializeNavigation();
  initializeThemeToggle();
  loadDashboardData();
  loadContentSources();
  loadContentLibrary();
  loadDistributionPlatforms();
  loadScrapingLogs();
  initializeMonetizationChart();
  
  // Set initial theme based on system preference
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    currentTheme = 'dark';
    document.documentElement.setAttribute('data-color-scheme', 'dark');
    updateThemeIcon();
  }
});

// Navigation functionality
function initializeNavigation() {
  const navLinks = document.querySelectorAll('.nav-link');
  
  navLinks.forEach(link => {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      const targetSection = this.getAttribute('data-section');
      navigateToSection(targetSection);
    });
  });
}

function navigateToSection(sectionId) {
  // Hide all sections
  const sections = document.querySelectorAll('.content-section');
  sections.forEach(section => section.classList.remove('active'));
  
  // Show target section
  const targetSection = document.getElementById(sectionId);
  if (targetSection) {
    targetSection.classList.add('active');
  }
  
  // Update navigation
  const navLinks = document.querySelectorAll('.nav-link');
  navLinks.forEach(link => link.classList.remove('active'));
  
  const activeLink = document.querySelector(`[data-section="${sectionId}"]`);
  if (activeLink) {
    activeLink.classList.add('active');
  }
  
  currentSection = sectionId;
}

// Theme toggle functionality
function initializeThemeToggle() {
  const themeToggle = document.getElementById('themeToggle');
  
  themeToggle.addEventListener('click', function() {
    currentTheme = currentTheme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-color-scheme', currentTheme);
    updateThemeIcon();
  });
}

function updateThemeIcon() {
  const themeIcon = document.querySelector('.theme-icon');
  themeIcon.textContent = currentTheme === 'light' ? '🌙' : '☀️';
}

// Load dashboard data
function loadDashboardData() {
  loadServiceStatus();
  loadRecentActivity();
  updateSystemStatus();
}

function loadServiceStatus() {
  const serviceList = document.getElementById('serviceList');
  const services = mockData.systemStatus.services;
  
  serviceList.innerHTML = services.map(service => {
    const statusClass = service.status === 'running' ? 'success' : 
                       service.status === 'warning' ? 'warning' : 'error';
    const lastRun = new Date(service.lastRun).toLocaleTimeString();
    
    return `
      <div class="service-item">
        <div class="service-info">
          <div class="service-name">${service.name}</div>
          <div class="service-details">Last run: ${lastRun} • Success: ${service.success}%</div>
        </div>
        <span class="status status--${statusClass}">${service.status}</span>
      </div>
    `;
  }).join('');
}

function loadRecentActivity() {
  const activityFeed = document.getElementById('activityFeed');
  const activities = mockData.recentActivity;
  
  activityFeed.innerHTML = activities.map(activity => `
    <div class="activity-item ${activity.type}">
      <div class="activity-time">${activity.time}</div>
      <div class="activity-text">${activity.action}</div>
    </div>
  `).join('');
}

function updateSystemStatus() {
  const systemStatusElement = document.getElementById('systemStatus');
  const status = mockData.systemStatus.overall;
  const statusClass = status === 'running' ? 'success' : 
                     status === 'warning' ? 'warning' : 'error';
  
  systemStatusElement.className = `status status--${statusClass}`;
  systemStatusElement.textContent = status === 'running' ? 'System Running' : 
                                   status === 'warning' ? 'System Warning' : 'System Error';
}

// Load content sources
function loadContentSources() {
  const sourcesTable = document.getElementById('sourcesTable');
  const sources = mockData.contentSources;
  
  const tableHTML = `
    <table>
      <thead>
        <tr>
          <th>Source Name</th>
          <th>Type</th>
          <th>Status</th>
          <th>Articles</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        ${sources.map(source => {
          const statusClass = source.status === 'active' ? 'success' : 
                             source.status === 'paused' ? 'warning' : 'error';
          return `
            <tr>
              <td>${source.name}</td>
              <td>${source.type}</td>
              <td><span class="status status--${statusClass}">${source.status}</span></td>
              <td>${source.articles}</td>
              <td>
                <div class="source-actions">
                  <button class="btn btn--sm btn--secondary" onclick="editSource(${source.id})">Edit</button>
                  <button class="btn btn--sm btn--outline" onclick="toggleSource(${source.id})">
                    ${source.status === 'active' ? 'Pause' : 'Resume'}
                  </button>
                </div>
              </td>
            </tr>
          `;
        }).join('')}
      </tbody>
    </table>
  `;
  
  sourcesTable.innerHTML = tableHTML;
}

// Load content library
function loadContentLibrary() {
  const contentLibrary = document.getElementById('contentLibrary');
  const content = mockData.contentLibrary;
  
  contentLibrary.innerHTML = content.map(item => {
    const statusClass = item.status === 'enhanced' ? 'success' : 
                       item.status === 'processing' ? 'warning' : 'info';
    const scrapedDate = new Date(item.scrapedAt).toLocaleDateString();
    
    return `
      <div class="content-item card">
        <div class="content-title">${item.title}</div>
        <div class="content-meta">
          <span>${item.source}</span>
          <span>•</span>
          <span>${scrapedDate}</span>
          <span class="status status--${statusClass}">${item.status}</span>
        </div>
        <div class="content-summary">${item.summary}</div>
        <div class="content-platforms">
          ${item.platforms.map(platform => 
            `<span class="platform-tag">${platform}</span>`
          ).join('')}
          ${item.platforms.length === 0 ? '<span class="platform-tag" style="background-color: var(--color-text-secondary)">Not Published</span>' : ''}
        </div>
      </div>
    `;
  }).join('');
}

// Load distribution platforms
function loadDistributionPlatforms() {
  const platformsGrid = document.getElementById('platformsGrid');
  const platforms = mockData.distributionPlatforms;
  
  const platformIcons = {
    'LinkedIn': '💼',
    'Twitter': '🐦',
    'Medium': '📝',
    'Substack': '📧'
  };
  
  platformsGrid.innerHTML = platforms.map(platform => {
    const statusClass = platform.status === 'connected' ? 'success' : 
                       platform.status === 'rate_limited' ? 'warning' : 'error';
    
    return `
      <div class="platform-card card">
        <div class="platform-info">
          <span class="platform-icon">${platformIcons[platform.name] || '📱'}</span>
          <div class="platform-details">
            <h4>${platform.name}</h4>
            <div class="platform-stats">
              ${platform.posts} posts • ${platform.engagement} engagement
            </div>
          </div>
        </div>
        <div class="platform-status">
          <span class="status status--${statusClass}">${platform.status.replace('_', ' ')}</span>
        </div>
      </div>
    `;
  }).join('');
}

// Load scraping logs
function loadScrapingLogs() {
  const scrapingLogs = document.getElementById('scrapingLogs');
  
  const sampleLogs = [
    { timestamp: '14:35:42', level: 'info', message: 'Starting scheduled scraping job...' },
    { timestamp: '14:35:45', level: 'success', message: 'Connected to FDA Medical Device Updates RSS feed' },
    { timestamp: '14:35:47', level: 'info', message: 'Found 5 new articles to process' },
    { timestamp: '14:35:50', level: 'success', message: 'Article 1/5: "Revolutionary 3D Printed Prosthetic" processed' },
    { timestamp: '14:35:52', level: 'success', message: 'AI enhancement completed for article 1/5' },
    { timestamp: '14:35:55', level: 'warning', message: 'Rate limit approaching for Twitter API' },
    { timestamp: '14:35:58', level: 'info', message: 'Scraping job completed successfully' }
  ];
  
  scrapingLogs.innerHTML = sampleLogs.map(log => `
    <div class="log-entry">
      <span class="log-timestamp">[${log.timestamp}]</span>
      <span class="log-level ${log.level}">${log.level.toUpperCase()}</span>
      ${log.message}
    </div>
  `).join('');
}

// Initialize monetization chart
function initializeMonetizationChart() {
  const ctx = document.getElementById('revenueChart');
  if (!ctx) return;
  
  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Affiliate Revenue', 'Subscriptions', 'Sponsored Posts'],
      datasets: [{
        data: [
          mockData.monetization.affiliateRevenue,
          mockData.monetization.totalRevenue - mockData.monetization.affiliateRevenue - (mockData.monetization.sponsoredPosts * 500),
          mockData.monetization.sponsoredPosts * 500
        ],
        backgroundColor: ['#1FB8CD', '#FFC185', '#B4413C'],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            usePointStyle: true,
            padding: 20
          }
        }
      }
    }
  });
  
  // Load subscription stats
  loadSubscriptionStats();
}

function loadSubscriptionStats() {
  const subscriptionStats = document.getElementById('subscriptionStats');
  const subs = mockData.monetization.subscriptions;
  
  subscriptionStats.innerHTML = `
    <div class="subscription-tier">
      <span class="tier-name">Basic Plan</span>
      <span class="tier-count">${subs.basic}</span>
    </div>
    <div class="subscription-tier">
      <span class="tier-name">Pro Plan</span>
      <span class="tier-count">${subs.pro}</span>
    </div>
    <div class="subscription-tier">
      <span class="tier-name">Enterprise Plan</span>
      <span class="tier-count">${subs.enterprise}</span>
    </div>
  `;
}

// Modal functionality
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
    document.body.style.overflow = '';
  }
}

// Close modal when clicking outside
document.addEventListener('click', function(e) {
  if (e.target.classList.contains('modal')) {
    closeModal(e.target.id);
  }
});

// Source management functions
function editSource(sourceId) {
  alert(`Edit source ${sourceId} - This would open an edit modal in a real application`);
}

function toggleSource(sourceId) {
  const source = mockData.contentSources.find(s => s.id === sourceId);
  if (source) {
    source.status = source.status === 'active' ? 'paused' : 'active';
    loadContentSources();
  }
}

// Scraping functions
function refreshScrapingLogs() {
  loadScrapingLogs();
  showNotification('Logs refreshed', 'info');
}

function startScraping() {
  showNotification('Scraping job started', 'success');
  // In a real app, this would trigger the actual scraping process
}

// Utility functions
function showNotification(message, type = 'info') {
  // Create notification element
  const notification = document.createElement('div');
  notification.className = `notification notification--${type}`;
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 12px 16px;
    background-color: var(--color-${type === 'success' ? 'success' : type === 'error' ? 'error' : 'info'});
    color: white;
    border-radius: 8px;
    z-index: 9999;
    transform: translateX(100%);
    transition: transform 0.3s ease;
  `;
  notification.textContent = message;
  
  document.body.appendChild(notification);
  
  // Show notification
  setTimeout(() => {
    notification.style.transform = 'translateX(0)';
  }, 100);
  
  // Hide notification after 3 seconds
  setTimeout(() => {
    notification.style.transform = 'translateX(100%)';
    setTimeout(() => {
      document.body.removeChild(notification);
    }, 300);
  }, 3000);
}

// Search and filter functionality
document.addEventListener('DOMContentLoaded', function() {
  const contentSearch = document.getElementById('contentSearch');
  const statusFilter = document.getElementById('statusFilter');
  
  if (contentSearch) {
    contentSearch.addEventListener('input', filterContent);
  }
  
  if (statusFilter) {
    statusFilter.addEventListener('change', filterContent);
  }
});

function filterContent() {
  const searchTerm = document.getElementById('contentSearch')?.value.toLowerCase() || '';
  const statusFilter = document.getElementById('statusFilter')?.value || '';
  
  const contentItems = document.querySelectorAll('.content-item');
  
  contentItems.forEach(item => {
    const title = item.querySelector('.content-title')?.textContent.toLowerCase() || '';
    const summary = item.querySelector('.content-summary')?.textContent.toLowerCase() || '';
    const status = item.querySelector('.status')?.textContent.toLowerCase() || '';
    
    const matchesSearch = title.includes(searchTerm) || summary.includes(searchTerm);
    const matchesStatus = !statusFilter || status.includes(statusFilter.toLowerCase());
    
    item.style.display = matchesSearch && matchesStatus ? 'block' : 'none';
  });
}

// Auto-refresh functionality for real-time updates
function startAutoRefresh() {
  setInterval(() => {
    if (currentSection === 'dashboard') {
      // Simulate real-time updates
      updateRecentActivity();
    }
  }, 30000); // Refresh every 30 seconds
}

function updateRecentActivity() {
  // Add a new random activity to simulate real-time updates
  const activities = [
    'New article scraped from Maritime Hydrogen News',
    'AI content enhancement completed',
    'Published to LinkedIn successfully',
    'Affiliate link generated for SaaS tool',
    'Twitter post scheduled for publication'
  ];
  
  const randomActivity = activities[Math.floor(Math.random() * activities.length)];
  const currentTime = new Date().toLocaleTimeString('en-US', { 
    hour12: false, 
    hour: '2-digit', 
    minute: '2-digit' 
  });
  
  const newActivity = {
    time: currentTime,
    action: randomActivity,
    type: Math.random() > 0.7 ? 'warning' : Math.random() > 0.5 ? 'info' : 'success'
  };
  
  mockData.recentActivity.unshift(newActivity);
  mockData.recentActivity = mockData.recentActivity.slice(0, 5); // Keep only 5 recent activities
  
  loadRecentActivity();
}

// Start auto-refresh when the page loads
document.addEventListener('DOMContentLoaded', function() {
  setTimeout(startAutoRefresh, 5000); // Start auto-refresh after 5 seconds
});