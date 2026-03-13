<template>
  <div class="home">
    <section class="hero">
      <div class="hero-content container">
        <span class="hero-label">Student & Company Platform</span>
        <h1 class="hero-title">Connect talent<br>with opportunity</h1>
        <p class="hero-subtitle">Students collaborate with companies on real projects. Build your portfolio, gain experience, and get reviewed by industry professionals.</p>
        <div class="hero-actions">
          <router-link to="/register" class="btn btn-primary btn-lg">Get Started<span class="material-icons-round">arrow_forward</span></router-link>
          <router-link to="/projects" class="btn btn-secondary btn-lg">Browse Projects</router-link>
        </div>
        <div class="hero-stats">
          <div class="stat"><span class="stat-num">500+</span><span class="stat-text">Students</span></div>
          <div class="stat-sep"></div>
          <div class="stat"><span class="stat-num">120+</span><span class="stat-text">Companies</span></div>
          <div class="stat-sep"></div>
          <div class="stat"><span class="stat-num">340+</span><span class="stat-text">Projects</span></div>
        </div>
      </div>
    </section>

    <section class="features container">
      <div class="section-head">
        <h2>How It Works</h2>
        <p>Three roles, one platform</p>
      </div>
      <div class="features-grid">
        <div v-for="(f,i) in features" :key="i" class="feature-card">
          <div class="feature-icon"><span class="material-icons-round">{{ f.icon }}</span></div>
          <h3>{{ f.title }}</h3>
          <p>{{ f.desc }}</p>
        </div>
      </div>
    </section>

    <footer class="site-footer container">
      <span class="footer-brand">NexusHub</span>
      <span class="footer-note">&copy; 2026 &mdash; Built with FastAPI + Vue.js</span>
    </footer>
  </div>
</template>
<script setup>
const features = [
  { icon: 'school', title: 'Students', desc: 'Browse projects, apply, build your portfolio and earn ratings from companies.' },
  { icon: 'business', title: 'Companies', desc: 'Publish projects, review applications, manage workflow, and leave reviews.' },
  { icon: 'chat', title: 'Real-time Chat', desc: 'WebSocket messaging between students and project owners.' },
  { icon: 'upload_file', title: 'File Sharing', desc: 'Upload project briefs, submit work via S3-compatible storage.' },
  { icon: 'star_outline', title: 'Reviews', desc: 'Both parties rate each other after project completion.' },
  { icon: 'lock', title: 'Secure', desc: 'JWT authentication, role-based access, admin moderation.' },
]
</script>
<style scoped>
.hero { padding: 6rem 0 4rem; }
.hero-content { max-width: 640px; }
.hero-label {
  display: inline-block; padding: 4px 12px; margin-bottom: 1.5rem;
  background: var(--accent-light); color: var(--accent-text);
  border-radius: var(--radius-full); font-size: .75rem; font-weight: 600;
}
.hero-title { font-size: clamp(2rem, 5vw, 3rem); font-weight: 700; line-height: 1.15; margin-bottom: 1.25rem; color: var(--gray-900); }
.hero-subtitle { font-size: 1rem; color: var(--gray-500); line-height: 1.7; margin-bottom: 2rem; }
.hero-actions { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 3rem; }
.hero-stats { display: flex; align-items: center; gap: 24px; }
.stat-num { font-size: 1.5rem; font-weight: 700; color: var(--gray-900); display: block; }
.stat-text { font-size: .75rem; color: var(--gray-400); text-transform: uppercase; letter-spacing: .06em; }
.stat-sep { width: 1px; height: 32px; background: var(--gray-200); }

.features { padding: 4rem 0; }
.section-head { margin-bottom: 2rem; }
.section-head p { color: var(--gray-500); margin-top: 4px; font-size: .875rem; }
.features-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
.feature-card {
  padding: 24px; background: var(--white); border: 1px solid var(--gray-200);
  border-radius: var(--radius-lg); transition: border-color .15s ease;
}
.feature-card:hover { border-color: var(--gray-300); }
.feature-icon {
  width: 40px; height: 40px; border-radius: var(--radius-md); background: var(--gray-100);
  display: flex; align-items: center; justify-content: center; margin-bottom: 12px;
}
.feature-icon .material-icons-round { font-size: 20px; color: var(--gray-600); }
.feature-card h3 { margin-bottom: 6px; font-size: .9375rem; }
.feature-card p { color: var(--gray-500); font-size: .8125rem; line-height: 1.6; }

.site-footer { padding: 2rem 0; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--gray-200); }
.footer-brand { font-weight: 600; font-size: .875rem; color: var(--gray-900); }
.footer-note { font-size: .75rem; color: var(--gray-400); }

@media (max-width: 768px) {
  .hero-stats { flex-direction: column; gap: 12px; align-items: flex-start; }
  .stat-sep { display: none; }
  .site-footer { flex-direction: column; gap: 8px; }
}
</style>
