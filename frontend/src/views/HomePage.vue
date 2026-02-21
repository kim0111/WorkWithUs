<template>
  <div class="home">
    <section class="hero">
      <div class="hero-bg"><div class="hero-grain"></div><div class="hero-gradient"></div><div class="hero-grid"></div></div>
      <div class="hero-content container">
        <div class="hero-badge"><span class="material-icons-round">bolt</span>Open Platform for Collaboration</div>
        <h1 class="hero-title">Where <em>Talent</em> meets<br><span class="accent-text">Opportunity</span></h1>
        <p class="hero-subtitle">Connect with companies, build your portfolio, and showcase your skills. Students collaborate with industry on real-world projects.</p>
        <div class="hero-actions">
          <router-link to="/register" class="btn btn-primary btn-lg">Get Started<span class="material-icons-round">arrow_forward</span></router-link>
          <router-link to="/projects" class="btn btn-secondary btn-lg">Browse Projects</router-link>
        </div>
        <div class="hero-stats">
          <div><span class="sv">500+</span><span class="sl">Students</span></div>
          <div class="sd"></div>
          <div><span class="sv">120+</span><span class="sl">Companies</span></div>
          <div class="sd"></div>
          <div><span class="sv">340+</span><span class="sl">Projects</span></div>
        </div>
      </div>
    </section>
    <section class="features container">
      <div class="sh"><h2>How It Works</h2><p>Three roles, one unified platform</p></div>
      <div class="features-grid">
        <div v-for="(f,i) in features" :key="i" class="feature-card">
          <div class="fi" :style="{background:f.bg}"><span class="material-icons-round">{{f.icon}}</span></div>
          <h3>{{f.title}}</h3><p>{{f.desc}}</p>
        </div>
      </div>
    </section>
    <footer class="ftr container">
      <span style="font-family:var(--font-display);font-weight:700">NexusHub</span>
      <span style="font-size:.82rem;color:var(--text-muted)">&copy; 2026 — FastAPI + Vue.js + MongoDB + Redis + MinIO</span>
    </footer>
  </div>
</template>
<script setup>
const features = [
  {icon:'school',title:'Students',desc:'Browse projects, apply, build your portfolio and earn ratings.',bg:'var(--accent-dim)'},
  {icon:'business',title:'Companies',desc:'Publish projects, review apps, manage workflow, leave reviews.',bg:'var(--teal-dim)'},
  {icon:'chat',title:'Real-time Chat',desc:'WebSocket messaging between students and project owners.',bg:'rgba(96,165,250,.12)'},
  {icon:'cloud_upload',title:'File Sharing',desc:'Upload project briefs, submit work via MinIO S3 storage.',bg:'rgba(192,132,252,.12)'},
  {icon:'rate_review',title:'Bidirectional Reviews',desc:'Both parties rate each other after project completion.',bg:'rgba(251,191,36,.12)'},
  {icon:'shield',title:'Secure Platform',desc:'JWT + Redis blacklist, RBAC, admin moderation.',bg:'rgba(74,222,128,.12)'},
]
</script>
<style scoped>
.hero{position:relative;min-height:100vh;display:flex;align-items:center;overflow:hidden}
.hero-bg{position:absolute;inset:0}.hero-grain{position:absolute;inset:0;opacity:.5}
.hero-gradient{position:absolute;inset:0;background:radial-gradient(ellipse 60% 50% at 20% 40%,rgba(232,168,56,.08) 0%,transparent 70%),radial-gradient(ellipse 40% 40% at 80% 60%,rgba(62,207,180,.05) 0%,transparent 70%)}
.hero-grid{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.02) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.02) 1px,transparent 1px);background-size:60px 60px;mask-image:radial-gradient(ellipse at center,black 30%,transparent 70%)}
.hero-content{position:relative;z-index:1;padding:6rem 0}
.hero-badge{display:inline-flex;align-items:center;gap:8px;padding:6px 16px;background:var(--accent-dim);border:1px solid rgba(232,168,56,.2);border-radius:var(--radius-full);font-size:.82rem;font-weight:600;color:var(--accent);margin-bottom:2rem;animation:fu .6s var(--ease) both}
.hero-badge .material-icons-round{font-size:16px}
.hero-title{font-size:clamp(2.5rem,6vw,4.5rem);font-weight:700;line-height:1.1;margin-bottom:1.5rem;animation:fu .6s var(--ease) .1s both}
.hero-title em{font-style:italic;color:var(--text-secondary)}.accent-text{color:var(--accent)}
.hero-subtitle{font-size:1.15rem;color:var(--text-secondary);max-width:560px;line-height:1.7;margin-bottom:2.5rem;animation:fu .6s var(--ease) .2s both}
.hero-actions{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:4rem;animation:fu .6s var(--ease) .3s both}
.hero-stats{display:flex;align-items:center;gap:32px;animation:fu .6s var(--ease) .4s both}
.sv{font-family:var(--font-display);font-size:1.8rem;font-weight:700;display:block}
.sl{font-size:.82rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.08em}
.sd{width:1px;height:40px;background:var(--border-strong)}
@keyframes fu{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:translateY(0)}}
.features{padding:6rem 2rem}.sh{text-align:center;margin-bottom:3rem}.sh p{color:var(--text-secondary);margin-top:8px}
.features-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:20px}
.feature-card{padding:28px;background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-lg);transition:all .3s var(--ease)}
.feature-card:hover{transform:translateY(-3px);border-color:var(--border-strong);box-shadow:var(--shadow-md)}
.fi{width:48px;height:48px;border-radius:var(--radius-md);display:flex;align-items:center;justify-content:center;margin-bottom:16px}
.fi .material-icons-round{font-size:24px;color:var(--text-primary)}
.feature-card h3{margin-bottom:8px;font-size:1.1rem}.feature-card p{color:var(--text-secondary);font-size:.9rem;line-height:1.6}
.ftr{padding:2rem;display:flex;justify-content:space-between;align-items:center;border-top:1px solid var(--border)}
@media(max-width:768px){.hero-stats{flex-direction:column;gap:16px;align-items:flex-start}.sd{display:none}.ftr{flex-direction:column;gap:12px}}
</style>
