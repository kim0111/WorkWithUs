<template>
  <div class="home">
    <!-- Hero -->
    <section class="hero">
      <div class="hero-bg">
        <div class="hero-grain"></div>
        <div class="hero-gradient"></div>
        <div class="hero-grid"></div>
      </div>

      <div class="hero-content container">
        <div class="hero-badge">
          <span class="material-icons-round">bolt</span>
          Open Platform for Collaboration
        </div>

        <h1 class="hero-title">
          Where <em>Talent</em> meets<br>
          <span class="accent-text">Opportunity</span>
        </h1>

        <p class="hero-subtitle">
          Connect with companies, build your portfolio, and showcase your skills.
          A platform where students collaborate with industry on real-world projects.
        </p>

        <div class="hero-actions">
          <router-link to="/register" class="btn btn-primary btn-lg">
            Get Started
            <span class="material-icons-round">arrow_forward</span>
          </router-link>
          <router-link to="/projects" class="btn btn-secondary btn-lg">
            Browse Projects
          </router-link>
        </div>

        <div class="hero-stats">
          <div class="hero-stat">
            <span class="hero-stat-value">500+</span>
            <span class="hero-stat-label">Students</span>
          </div>
          <div class="hero-stat-divider"></div>
          <div class="hero-stat">
            <span class="hero-stat-value">120+</span>
            <span class="hero-stat-label">Companies</span>
          </div>
          <div class="hero-stat-divider"></div>
          <div class="hero-stat">
            <span class="hero-stat-value">340+</span>
            <span class="hero-stat-label">Projects</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Features -->
    <section class="features container">
      <div class="section-header">
        <h2>How It Works</h2>
        <p>Three roles, one unified platform</p>
      </div>

      <div class="features-grid">
        <div v-for="(feat, i) in features" :key="i" class="feature-card" :style="{ animationDelay: `${i * 0.1}s` }">
          <div class="feature-icon" :style="{ background: feat.color }">
            <span class="material-icons-round">{{ feat.icon }}</span>
          </div>
          <h3>{{ feat.title }}</h3>
          <p>{{ feat.desc }}</p>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="cta container">
      <div class="cta-card">
        <div class="cta-content">
          <h2>Ready to start building your future?</h2>
          <p>Join WorkWithUs today and connect with opportunities that matter.</p>
          <router-link to="/register" class="btn btn-primary btn-lg">
            Create Free Account
            <span class="material-icons-round">arrow_forward</span>
          </router-link>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="footer container">
      <div class="footer-brand">
        <span class="brand-icon">N</span>
        <span>WorkWithUs</span>
      </div>
      <p class="footer-copy">&copy; 2026 WorkWithUs Platform. Built with FastAPI & Vue.js</p>
    </footer>
  </div>
</template>

<script setup>
const features = [
  {
    icon: 'school',
    title: 'Students',
    desc: 'Browse projects, apply with a cover letter, build your portfolio and earn ratings from real company work.',
    color: 'var(--accent-dim)'
  },
  {
    icon: 'business',
    title: 'Companies',
    desc: 'Publish real-world projects, review student applications, hire talent, and leave reviews.',
    color: 'var(--teal-dim)'
  },
  {
    icon: 'groups',
    title: 'Industry Committee',
    desc: 'Oversee platform quality, evaluate student work, and ensure alignment with industry standards.',
    color: 'rgba(96, 165, 250, 0.12)'
  },
  {
    icon: 'workspace_premium',
    title: 'Portfolio & Ratings',
    desc: 'Every completed project adds to your portfolio. Earn ratings and reviews that showcase your skills.',
    color: 'rgba(192, 132, 252, 0.12)'
  },
  {
    icon: 'handshake',
    title: 'Student Collaboration',
    desc: 'Students can also publish their own tasks and get help from peers in the community.',
    color: 'rgba(251, 191, 36, 0.12)'
  },
  {
    icon: 'shield',
    title: 'Secure & Moderated',
    desc: 'Role-based access, JWT authentication, and admin moderation keep the platform safe.',
    color: 'rgba(74, 222, 128, 0.12)'
  }
]
</script>

<style scoped>
/* ── Hero ─────────────────────────────────────────── */

.hero {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  overflow: hidden;
}

.hero-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.hero-grain {
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
  opacity: 0.5;
}

.hero-gradient {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 60% 50% at 20% 40%, rgba(232, 168, 56, 0.08) 0%, transparent 70%),
    radial-gradient(ellipse 40% 40% at 80% 60%, rgba(62, 207, 180, 0.05) 0%, transparent 70%);
}

.hero-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
  background-size: 60px 60px;
  mask-image: radial-gradient(ellipse at center, black 30%, transparent 70%);
}

.hero-content {
  position: relative;
  z-index: 1;
  padding: 6rem 0;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  background: var(--accent-dim);
  border: 1px solid rgba(232, 168, 56, 0.2);
  border-radius: var(--radius-full);
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--accent);
  margin-bottom: 2rem;
  animation: fadeUp 0.6s var(--ease) both;
}

.hero-badge .material-icons-round {
  font-size: 16px;
}

.hero-title {
  font-size: clamp(2.5rem, 6vw, 4.5rem);
  font-weight: 700;
  line-height: 1.1;
  margin-bottom: 1.5rem;
  animation: fadeUp 0.6s var(--ease) 0.1s both;
}

.hero-title em {
  font-style: italic;
  color: var(--text-secondary);
}

.accent-text {
  color: var(--accent);
  position: relative;
}

.hero-subtitle {
  font-size: 1.15rem;
  color: var(--text-secondary);
  max-width: 560px;
  line-height: 1.7;
  margin-bottom: 2.5rem;
  animation: fadeUp 0.6s var(--ease) 0.2s both;
}

.hero-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 4rem;
  animation: fadeUp 0.6s var(--ease) 0.3s both;
}

.hero-stats {
  display: flex;
  align-items: center;
  gap: 32px;
  animation: fadeUp 0.6s var(--ease) 0.4s both;
}

.hero-stat-value {
  font-family: var(--font-display);
  font-size: 1.8rem;
  font-weight: 700;
  display: block;
}

.hero-stat-label {
  font-size: 0.82rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 500;
}

.hero-stat-divider {
  width: 1px;
  height: 40px;
  background: var(--border-strong);
}

@keyframes fadeUp {
  from {
    opacity: 0;
    transform: translateY(24px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ── Features ────────────────────────────────────── */

.features {
  padding: 6rem 2rem;
}

.section-header {
  text-align: center;
  margin-bottom: 3rem;
}

.section-header p {
  color: var(--text-secondary);
  margin-top: 8px;
  font-size: 1rem;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.feature-card {
  padding: 28px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  transition: all 0.3s var(--ease);
}

.feature-card:hover {
  transform: translateY(-3px);
  border-color: var(--border-strong);
  box-shadow: var(--shadow-md);
}

.feature-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.feature-icon .material-icons-round {
  font-size: 24px;
  color: var(--text-primary);
}

.feature-card h3 {
  margin-bottom: 8px;
  font-size: 1.1rem;
}

.feature-card p {
  color: var(--text-secondary);
  font-size: 0.9rem;
  line-height: 1.6;
}

/* ── CTA ─────────────────────────────────────────── */

.cta {
  padding: 4rem 2rem 6rem;
}

.cta-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: 4rem;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.cta-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at center, var(--accent-glow), transparent 70%);
}

.cta-content {
  position: relative;
  z-index: 1;
}

.cta-content h2 {
  margin-bottom: 12px;
  font-size: 2rem;
}

.cta-content p {
  color: var(--text-secondary);
  margin-bottom: 2rem;
  font-size: 1.05rem;
}

/* ── Footer ──────────────────────────────────────── */

.footer {
  padding: 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid var(--border);
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-display);
  font-weight: 700;
}

.footer .brand-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: var(--accent);
  color: var(--text-inverse);
  border-radius: var(--radius-sm);
  font-family: var(--font-display);
  font-weight: 800;
  font-size: 0.9rem;
}

.footer-copy {
  font-size: 0.82rem;
  color: var(--text-muted);
}

@media (max-width: 768px) {
  .hero-stats {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  .hero-stat-divider { display: none; }
  .cta-card { padding: 2rem; }
  .footer { flex-direction: column; gap: 12px; }
}
</style>
