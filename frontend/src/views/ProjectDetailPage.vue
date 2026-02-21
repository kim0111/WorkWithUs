<template>
  <div v-if="project" class="page container">
    <!-- Header -->
    <div class="detail-header">
      <div>
        <div class="detail-meta">
          <span class="badge" :class="statusBadge">{{ project.status }}</span>
          <span v-if="project.is_student_project" class="badge badge-teal">Student Project</span>
        </div>
        <h1>{{ project.title }}</h1>
        <div class="detail-info">
          <span><span class="material-icons-round">person</span>Owner #{{ project.owner_id }}</span>
          <span><span class="material-icons-round">group</span>{{ project.max_participants }} spots</span>
          <span v-if="project.deadline"><span class="material-icons-round">schedule</span>{{ fmtDate(project.deadline) }}</span>
          <span><span class="material-icons-round">calendar_today</span>{{ fmtDate(project.created_at) }}</span>
        </div>
      </div>
      <div v-if="isOwner" class="detail-actions">
        <select class="input select" :value="project.status" @change="changeStatus($event.target.value)">
          <option value="open">Open</option><option value="in_progress">In Progress</option><option value="closed">Closed</option>
        </select>
        <button class="btn btn-danger btn-sm" @click="deleteProject"><span class="material-icons-round">delete</span>Delete</button>
      </div>
      <div v-if="auth.isStudent && project.status === 'open' && !isOwner && !myApp" class="detail-actions">
        <button class="btn btn-primary" @click="scrollToApply">
          <span class="material-icons-round">send</span>Apply Now
        </button>
      </div>
      <div v-if="myApp" class="detail-actions">
        <span class="badge" :class="appStatusBadge(myApp.status)">{{ myApp.status }}</span>
      </div>
    </div>

    <!-- Description & Skills -->
    <section class="detail-section">
      <h2>Description</h2>
      <div class="detail-desc">{{ project.description }}</div>
      <div v-if="project.required_skills?.length" class="skills-list">
        <span v-for="s in project.required_skills" :key="s.id" class="skill-tag">{{ s.name }}</span>
      </div>
    </section>

    <!-- Project Files (ТЗ / Attachments) -->
    <section class="detail-section">
      <h2><span class="material-icons-round">attach_file</span>Project Files</h2>
      <div v-if="attachments.length" class="files-list">
        <div v-for="f in attachments" :key="f.id" class="file-item">
          <span class="material-icons-round">description</span>
          <div class="file-info">
            <span class="file-name">{{ f.filename }}</span>
            <span class="file-meta">{{ formatSize(f.file_size) }} &middot; {{ fmtDate(f.created_at) }}</span>
          </div>
          <button class="btn btn-ghost btn-sm" @click="downloadFile(f.id)"><span class="material-icons-round">download</span></button>
          <button v-if="isOwner || isAdmin" class="btn btn-ghost btn-sm" @click="delFile(f.id)"><span class="material-icons-round">close</span></button>
        </div>
      </div>
      <p v-else class="text-muted">No files attached</p>
      <FileUpload v-if="isOwner" @file="uploadAttachment" accept="*" />
    </section>

    <!-- Student Submissions -->
    <section v-if="isOwner || isApplicant" class="detail-section">
      <h2><span class="material-icons-round">cloud_upload</span>Submissions</h2>
      <div v-if="submissions.length" class="files-list">
        <div v-for="f in submissions" :key="f.id" class="file-item">
          <span class="material-icons-round">assignment_turned_in</span>
          <div class="file-info">
            <span class="file-name">{{ f.filename }}</span>
            <span class="file-meta">{{ formatSize(f.file_size) }} &middot; {{ fmtDate(f.created_at) }}</span>
          </div>
          <button class="btn btn-ghost btn-sm" @click="downloadFile(f.id)"><span class="material-icons-round">download</span></button>
        </div>
      </div>
      <p v-else class="text-muted">No submissions yet</p>
      <FileUpload v-if="isApplicant" @file="uploadSubmission" accept="*" />
    </section>

    <!-- Apply Section (students only) -->
    <section id="apply-section" v-if="auth.isStudent && project.status === 'open' && !isOwner && !myApp" class="detail-section">
      <h2>Apply to this Project</h2>
      <form @submit.prevent="apply" class="apply-form">
        <textarea class="input" v-model="coverLetter" rows="4" placeholder="Cover letter (optional)..."></textarea>
        <button type="submit" class="btn btn-primary" :disabled="applying">{{ applying ? 'Applying...' : 'Submit Application' }}</button>
      </form>
    </section>

    <!-- My Application Status (applicant view) -->
    <section v-if="myApp" class="detail-section">
      <h2>Your Application</h2>
      <div class="app-status-card">
        <div class="app-status-row">
          <span class="badge" :class="appStatusBadge(myApp.status)">{{ myApp.status }}</span>
          <span class="text-muted">{{ fmtDate(myApp.updated_at) }}</span>
        </div>
        <p v-if="myApp.cover_letter" class="text-secondary">{{ myApp.cover_letter }}</p>
        <p v-if="myApp.revision_note" class="revision-note">
          <span class="material-icons-round">edit_note</span>Revision: {{ myApp.revision_note }}
        </p>

        <!-- Applicant workflow actions -->
        <div class="app-actions">
          <button v-if="myApp.status === 'accepted'" class="btn btn-primary btn-sm" @click="updateMyApp('in_progress')">
            <span class="material-icons-round">play_arrow</span>Start Working
          </button>
          <div v-if="myApp.status === 'in_progress' || myApp.status === 'revision_requested'" class="submit-work">
            <input class="input" v-model="submitNote" placeholder="Submission note..." />
            <button class="btn btn-primary btn-sm" @click="updateMyApp('submitted', submitNote)">
              <span class="material-icons-round">send</span>Submit Work
            </button>
          </div>
        </div>

        <!-- Chat link -->
        <button v-if="myApp.status !== 'rejected'"
                class="btn btn-secondary btn-sm" @click="openChat">
          <span class="material-icons-round">chat</span>Message Owner
        </button>
      </div>
    </section>

    <!-- Applications List (owner view) -->
    <section v-if="isOwner" class="detail-section">
      <h2>Applications ({{ applications.length }})</h2>
      <div v-if="applications.length" class="apps-list">
        <div v-for="a in applications" :key="a.id" class="app-card">
          <div class="app-card-header">
            <router-link :to="`/profile/${a.applicant_id}`" class="app-user-link">
              <div class="av-sm">{{ String(a.applicant_id).charAt(0) }}</div>
              User #{{ a.applicant_id }}
            </router-link>
            <span class="badge" :class="appStatusBadge(a.status)">{{ a.status }}</span>
          </div>
          <p v-if="a.cover_letter" class="text-secondary app-cl">{{ a.cover_letter }}</p>
          <p v-if="a.submission_note" class="text-secondary"><strong>Submission:</strong> {{ a.submission_note }}</p>

          <!-- Owner workflow actions -->
          <div class="app-actions">
            <template v-if="a.status === 'pending'">
              <button class="btn btn-primary btn-sm" @click="updateApp(a.id, 'accepted')">Accept</button>
              <button class="btn btn-danger btn-sm" @click="updateApp(a.id, 'rejected')">Reject</button>
            </template>
            <template v-if="a.status === 'submitted'">
              <button class="btn btn-primary btn-sm" @click="updateApp(a.id, 'approved')">
                <span class="material-icons-round">check</span>Approve
              </button>
              <div class="revision-input">
                <input class="input" v-model="revisionNotes[a.id]" placeholder="Revision note..." />
                <button class="btn btn-outline btn-sm" @click="updateApp(a.id, 'revision_requested', revisionNotes[a.id])">
                  Request Revision
                </button>
              </div>
            </template>
            <template v-if="a.status === 'approved'">
              <button class="btn btn-primary btn-sm" @click="updateApp(a.id, 'completed')">
                <span class="material-icons-round">done_all</span>Mark Completed
              </button>
            </template>

            <!-- Review after completion -->
            <template v-if="a.status === 'completed' || a.status === 'approved'">
              <div v-if="!reviewedApps.has(a.id)" class="review-form">
                <h4>Leave Review</h4>
                <div class="star-select">
                  <button v-for="n in 5" :key="n" class="star-btn" :class="{ active: (reviewData[a.id]?.rating || 0) >= n }"
                          @click="setRating(a.id, n)">★</button>
                </div>
                <input class="input" v-model="reviewComments[a.id]" placeholder="Comment..." />
                <button class="btn btn-primary btn-sm" @click="submitReview(a.id, a.applicant_id)">
                  Submit Review
                </button>
              </div>
              <span v-else class="text-muted">✓ Reviewed</span>
            </template>

            <!-- Chat with applicant -->
            <button v-if="a.status !== 'rejected'" class="btn btn-ghost btn-sm"
                    @click="openChatWith(a.applicant_id)">
              <span class="material-icons-round">chat</span>Chat
            </button>
          </div>
        </div>
      </div>
      <div v-else class="empty-state"><span class="material-icons-round">inbox</span><h3>No applications yet</h3></div>
    </section>
  </div>
  <div v-else class="loading-center"><div class="spinner"></div></div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { projectsAPI, applicationsAPI, filesAPI, reviewsAPI, chatAPI } from '@/api'
import FileUpload from '@/components/FileUpload.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const project = ref(null)
const applications = ref([])
const myApp = ref(null)
const attachments = ref([])
const submissions = ref([])
const coverLetter = ref('')
const applying = ref(false)
const submitNote = ref('')
const revisionNotes = reactive({})
const reviewData = reactive({})
const reviewComments = reactive({})
const reviewedApps = ref(new Set())

const isOwner = computed(() => auth.user && project.value?.owner_id === auth.user.id)
const isAdmin = computed(() => auth.isAdmin)
const isApplicant = computed(() => !!myApp.value && ['accepted', 'in_progress', 'submitted', 'revision_requested'].includes(myApp.value.status))

const statusBadge = computed(() => ({ open: 'badge-success', in_progress: 'badge-warning', closed: 'badge-danger' }[project.value?.status]))

function appStatusBadge(s) {
  return { pending: 'badge-info', accepted: 'badge-success', rejected: 'badge-danger', in_progress: 'badge-warning',
    submitted: 'badge-accent', revision_requested: 'badge-warning', approved: 'badge-success', completed: 'badge-teal' }[s] || 'badge-info'
}

function fmtDate(d) { return d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '' }
function formatSize(b) { if (!b) return ''; if (b < 1024) return b + 'B'; if (b < 1048576) return (b / 1024).toFixed(1) + 'KB'; return (b / 1048576).toFixed(1) + 'MB' }

async function load() {
  const id = route.params.id
  try {
    project.value = (await projectsAPI.get(id)).data
    try { attachments.value = (await filesAPI.list(id, 'attachment')).data } catch {}
    try { submissions.value = (await filesAPI.list(id, 'submission')).data } catch {}
    if (isOwner.value || auth.isAdmin) {
      try { applications.value = (await applicationsAPI.byProject(id)).data } catch {}
    }
    if (auth.isStudent) {
      try {
        const mine = (await applicationsAPI.my()).data
        myApp.value = mine.find(a => a.project_id === Number(id)) || null
      } catch {}
    }
  } catch { router.push('/projects') }
}

async function apply() {
  applying.value = true
  try {
    await applicationsAPI.apply({ project_id: project.value.id, cover_letter: coverLetter.value || null })
    toast.success('Application submitted!')
    await load()
  } catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
  finally { applying.value = false }
}

async function updateApp(id, status, note) {
  try {
    await applicationsAPI.updateStatus(id, { status, note: note || null })
    toast.success(`Status updated: ${status}`)
    await load()
  } catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
}

async function updateMyApp(status, note) {
  if (!myApp.value) return
  await updateApp(myApp.value.id, status, note)
  submitNote.value = ''
}

async function changeStatus(status) {
  try {
    await projectsAPI.update(project.value.id, { status })
    project.value.status = status
    toast.success('Status updated')
  } catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
}

async function deleteProject() {
  if (!confirm('Delete this project permanently?')) return
  try { await projectsAPI.delete(project.value.id); toast.success('Deleted'); router.push('/projects') }
  catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
}

async function uploadAttachment(file) {
  try {
    await filesAPI.upload(project.value.id, file, 'attachment')
    toast.success('File uploaded')
    attachments.value = (await filesAPI.list(project.value.id, 'attachment')).data
  } catch (e) { toast.error(e.response?.data?.detail || 'Upload failed') }
}

async function uploadSubmission(file) {
  try {
    await filesAPI.upload(project.value.id, file, 'submission')
    toast.success('Submission uploaded')
    submissions.value = (await filesAPI.list(project.value.id, 'submission')).data
  } catch (e) { toast.error(e.response?.data?.detail || 'Upload failed') }
}

async function downloadFile(id) {
  try {
    const { data } = await filesAPI.download(id)
    window.open(data.download_url, '_blank')
  } catch { toast.error('Download failed') }
}

async function delFile(id) {
  try { await filesAPI.delete(id); toast.success('File deleted'); await load() }
  catch { toast.error('Delete failed') }
}

function setRating(appId, n) { reviewData[appId] = { rating: n } }

async function submitReview(appId, revieweeId) {
  const rating = reviewData[appId]?.rating
  if (!rating) { toast.error('Please select a rating'); return }
  try {
    await reviewsAPI.create({
      reviewee_id: revieweeId, project_id: project.value.id,
      application_id: appId, rating, comment: reviewComments[appId] || null,
    })
    toast.success('Review submitted!')
    reviewedApps.value.add(appId)
  } catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
}

function scrollToApply() {
  document.getElementById('apply-section')?.scrollIntoView({ behavior: 'smooth' })
}

async function openChat() {
  try {
    const { data } = await chatAPI.createRoom(project.value.id, project.value.owner_id)
    router.push(`/chat/${data.id}`)
  } catch { toast.error('Cannot open chat') }
}

async function openChatWith(userId) {
  try {
    const { data } = await chatAPI.createRoom(project.value.id, userId)
    router.push(`/chat/${data.id}`)
  } catch { toast.error('Cannot open chat') }
}

onMounted(load)
</script>

<style scoped>
.page { padding: 2rem; }
.detail-header { display: flex; justify-content: space-between; align-items: flex-start; padding-bottom: 2rem; border-bottom: 1px solid var(--border); margin-bottom: 2rem; }
.detail-meta { display: flex; gap: 8px; margin-bottom: 8px; }
.detail-info { display: flex; gap: 20px; flex-wrap: wrap; margin-top: 12px; }
.detail-info > span { display: flex; align-items: center; gap: 6px; font-size: .85rem; color: var(--text-muted); }
.detail-info .material-icons-round { font-size: 16px; }
.detail-actions { display: flex; gap: 10px; align-items: center; }
.detail-section { margin-bottom: 2.5rem; }
.detail-section h2 { display: flex; align-items: center; gap: 8px; font-size: 1.3rem; margin-bottom: 1rem; }
.detail-section h2 .material-icons-round { font-size: 22px; color: var(--accent); }
.detail-desc { color: var(--text-secondary); line-height: 1.8; white-space: pre-wrap; margin-bottom: 1rem; }
.skills-list { display: flex; flex-wrap: wrap; gap: 8px; }

/* Files */
.files-list { display: flex; flex-direction: column; gap: 8px; margin-bottom: 1rem; }
.file-item { display: flex; align-items: center; gap: 12px; padding: 12px 16px; background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-md); }
.file-item > .material-icons-round { font-size: 24px; color: var(--accent); }
.file-info { flex: 1; }
.file-name { font-weight: 500; font-size: .9rem; display: block; }
.file-meta { font-size: .78rem; color: var(--text-muted); }

/* Apply */
.apply-form { display: flex; flex-direction: column; gap: 12px; max-width: 600px; }

/* Application status */
.app-status-card { padding: 20px; background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); display: flex; flex-direction: column; gap: 12px; }
.app-status-row { display: flex; justify-content: space-between; align-items: center; }
.revision-note { display: flex; align-items: center; gap: 8px; color: var(--warning); font-size: .9rem; padding: 10px 14px; background: rgba(251, 191, 36, .06); border-radius: var(--radius-md); }
.submit-work { display: flex; gap: 10px; align-items: center; }

/* Applications list */
.apps-list { display: flex; flex-direction: column; gap: 14px; }
.app-card { padding: 20px; background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); }
.app-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.app-user-link { display: flex; align-items: center; gap: 10px; text-decoration: none; color: var(--text-primary); font-weight: 500; }
.av-sm { width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, var(--accent), #d4822a); display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: .8rem; color: var(--text-inverse); }
.app-cl { font-size: .9rem; margin-bottom: 8px; }
.app-actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 12px; align-items: center; }
.revision-input { display: flex; gap: 8px; align-items: center; }
.revision-input .input { min-width: 200px; }

/* Review */
.review-form { display: flex; flex-direction: column; gap: 8px; padding: 14px; background: var(--bg-secondary); border-radius: var(--radius-md); border: 1px solid var(--border); }
.review-form h4 { font-size: .9rem; font-family: var(--font-body); }
.star-select { display: flex; gap: 4px; }
.star-btn { background: none; border: none; font-size: 1.5rem; cursor: pointer; color: var(--text-muted); transition: color .15s; }
.star-btn.active { color: var(--accent); }
.star-btn:hover { color: var(--accent); }

.text-muted { color: var(--text-muted); font-size: .9rem; }
.text-secondary { color: var(--text-secondary); font-size: .9rem; }
.loading-center { display: flex; justify-content: center; padding: 6rem; }

@media (max-width: 768px) {
  .detail-header { flex-direction: column; gap: 1rem; }
  .detail-actions { width: 100%; }
  .submit-work { flex-direction: column; }
  .revision-input { flex-direction: column; }
}
</style>
