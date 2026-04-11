<template>
  <div v-if="project" class="page container">
    <!-- Header -->
    <div class="detail-header">
      <div>
        <div class="detail-badges">
          <StatusBadge :status="project.status" size="md" />
          <span v-if="project.is_student_project" class="badge badge-teal">Student Project</span>
        </div>
        <h1>{{ project.title }}</h1>
        <div class="detail-meta">
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
        <button class="btn btn-danger btn-sm" @click="showDeleteConfirm = true"><span class="material-icons-round">delete</span>Delete</button>
      </div>
      <div v-if="auth.isStudent && project.status === 'open' && !isOwner && !myApp" class="detail-actions">
        <button class="btn btn-primary" @click="scrollToApply">
          <span class="material-icons-round">send</span>Apply Now
        </button>
      </div>
      <div v-if="myApp" class="detail-actions">
        <StatusBadge :status="myApp.status" />
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

    <!-- Project Files -->
    <section class="detail-section">
      <h2>Project Files</h2>
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

    <!-- Submissions -->
    <section v-if="isOwner || isApplicant" class="detail-section">
      <h2>Submissions</h2>
      <div v-if="submissions.length" class="files-list">
        <div v-for="f in submissions" :key="f.id" class="file-item">
          <span class="material-icons-round">task</span>
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

    <!-- Apply -->
    <section id="apply-section" v-if="auth.isStudent && project.status === 'open' && !isOwner && !myApp" class="detail-section">
      <h2>Apply to this Project</h2>
      <form @submit.prevent="apply" class="apply-form">
        <textarea class="input" v-model="coverLetter" rows="4" placeholder="Cover letter (optional)..."></textarea>
        <button type="submit" class="btn btn-primary" :disabled="applying">{{ applying ? 'Applying...' : 'Submit Application' }}</button>
      </form>
    </section>

    <!-- My Application Status -->
    <section v-if="myApp" class="detail-section">
      <h2>Your Application</h2>
      <div class="app-status-card">
        <div class="app-status-row">
          <StatusBadge :status="myApp.status" />
          <span class="text-muted">{{ fmtDate(myApp.updated_at) }}</span>
        </div>
        <p v-if="myApp.cover_letter" class="text-secondary">{{ myApp.cover_letter }}</p>
        <p v-if="myApp.revision_note" class="revision-note">
          <span class="material-icons-round">edit_note</span>Revision: {{ myApp.revision_note }}
        </p>
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
        <button v-if="myApp.status !== 'rejected'" class="btn btn-secondary btn-sm" @click="openChat">
          <span class="material-icons-round">chat_bubble_outline</span>Message Owner
        </button>
      </div>
    </section>

    <!-- Applications List (owner) -->
    <section v-if="isOwner" class="detail-section">
      <h2>Applications ({{ applications.length }})</h2>
      <div v-if="applications.length" class="apps-list">
        <div v-for="a in applications" :key="a.id" class="app-card">
          <div class="app-card-header">
            <router-link :to="`/profile/${a.applicant_id}`" class="app-user-link">
              <div class="av-sm">{{ String(a.applicant_id).charAt(0) }}</div>
              User #{{ a.applicant_id }}
            </router-link>
            <StatusBadge :status="a.status" />
          </div>
          <p v-if="a.cover_letter" class="text-secondary app-cl">{{ a.cover_letter }}</p>
          <p v-if="a.submission_note" class="text-secondary"><strong>Submission:</strong> {{ a.submission_note }}</p>
          <div class="app-actions">
            <template v-if="a.status === 'pending'">
              <button class="btn btn-primary btn-sm" @click="updateApp(a.id, 'accepted')">Accept</button>
              <button class="btn btn-danger btn-sm" @click="updateApp(a.id, 'rejected')">Reject</button>
            </template>
            <template v-if="a.status === 'submitted'">
              <button class="btn btn-primary btn-sm" @click="updateApp(a.id, 'approved')">Approve</button>
              <div class="revision-input">
                <input class="input" v-model="revisionNotes[a.id]" placeholder="Revision note..." />
                <button class="btn btn-outline btn-sm" @click="updateApp(a.id, 'revision_requested', revisionNotes[a.id])">Request Revision</button>
              </div>
            </template>
            <template v-if="a.status === 'approved'">
              <button class="btn btn-primary btn-sm" @click="updateApp(a.id, 'completed')">Mark Completed</button>
            </template>
            <template v-if="a.status === 'completed' || a.status === 'approved'">
              <div v-if="!reviewedApps.has(a.id)" class="review-form">
                <h4>Leave Review</h4>
                <div class="star-select">
                  <button v-for="n in 5" :key="n" class="star-btn" :class="{ active: (reviewData[a.id]?.rating || 0) >= n }" @click="setRating(a.id, n)">&#9733;</button>
                </div>
                <input class="input" v-model="reviewComments[a.id]" placeholder="Comment..." />
                <button class="btn btn-primary btn-sm" @click="submitReview(a.id, a.applicant_id)">Submit Review</button>
              </div>
              <span v-else class="text-muted">Reviewed</span>
            </template>
            <button v-if="a.status !== 'rejected'" class="btn btn-ghost btn-sm" @click="openChatWith(a.applicant_id)">
              <span class="material-icons-round">chat_bubble_outline</span>Chat
            </button>
          </div>
        </div>
      </div>
      <EmptyState v-else icon="inbox" title="No applications yet" subtitle="Applications will appear here when students apply" />
    </section>
    <ConfirmDialog
      v-model="showDeleteConfirm"
      title="Delete Project"
      message="Delete this project permanently? This cannot be undone."
      @confirm="deleteProject"
    />
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
import StatusBadge from '@/components/StatusBadge.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import EmptyState from '@/components/EmptyState.vue'

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
const showDeleteConfirm = ref(false)

const isOwner = computed(() => auth.user && project.value?.owner_id === auth.user.id)
const isAdmin = computed(() => auth.isAdmin)
const isApplicant = computed(() => !!myApp.value && ['accepted', 'in_progress', 'submitted', 'revision_requested'].includes(myApp.value.status))

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
  showDeleteConfirm.value = false
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

async function downloadFile(fileId) {
  try {
    const response = await filesAPI.download(fileId)
    const disposition = response.headers['content-disposition'] || ''
    const match = disposition.match(/filename="?(.+?)"?$/)
    const filename = match ? match[1] : 'download'
    const url = URL.createObjectURL(response.data)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
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
.page { padding: 2rem 24px; }
.detail-header { display: flex; justify-content: space-between; align-items: flex-start; padding-bottom: 1.5rem; border-bottom: 1px solid var(--gray-200); margin-bottom: 1.5rem; }
.detail-badges { display: flex; gap: 6px; margin-bottom: 8px; }
.detail-meta { display: flex; gap: 16px; flex-wrap: wrap; margin-top: 10px; }
.detail-meta > span { display: flex; align-items: center; gap: 4px; font-size: .8125rem; color: var(--gray-400); }
.detail-meta .material-icons-round { font-size: 15px; }
.detail-actions { display: flex; gap: 8px; align-items: center; }
.detail-section { margin-bottom: 2rem; overflow: hidden; }
.detail-section h2 { font-size: 1.1rem; margin-bottom: .75rem; }
.detail-desc { color: var(--gray-600); line-height: 1.7; white-space: pre-wrap; overflow-wrap: break-word; word-break: break-word; margin-bottom: .75rem; font-size: .875rem; }
.skills-list { display: flex; flex-wrap: wrap; gap: 6px; }

.files-list { display: flex; flex-direction: column; gap: 6px; margin-bottom: .75rem; }
.file-item { display: flex; align-items: center; gap: 10px; padding: 10px 14px; background: var(--white); border: 1px solid var(--gray-200); border-radius: var(--radius-md); }
.file-item > .material-icons-round { font-size: 20px; color: var(--accent); }
.file-info { flex: 1; }
.file-name { font-weight: 500; font-size: .8125rem; display: block; }
.file-meta { font-size: .75rem; color: var(--gray-400); }

.apply-form { display: flex; flex-direction: column; gap: 10px; max-width: 560px; }

.app-status-card { padding: 16px; background: var(--white); border: 1px solid var(--gray-200); border-radius: var(--radius-lg); display: flex; flex-direction: column; gap: 10px; }
.app-status-row { display: flex; justify-content: space-between; align-items: center; }
.revision-note { display: flex; align-items: center; gap: 6px; color: var(--warning); font-size: .8125rem; padding: 8px 12px; background: var(--warning-light); border-radius: var(--radius-md); }
.submit-work { display: flex; gap: 8px; align-items: center; }

.apps-list { display: flex; flex-direction: column; gap: 12px; }
.app-card { padding: 16px; background: var(--white); border: 1px solid var(--gray-200); border-radius: var(--radius-lg); }
.app-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.app-user-link { display: flex; align-items: center; gap: 8px; text-decoration: none; color: var(--gray-900); font-weight: 500; font-size: .875rem; }
.av-sm { width: 28px; height: 28px; border-radius: 50%; background: var(--accent); display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: .7rem; color: white; }
.app-cl { font-size: .8125rem; margin-bottom: 6px; }
.app-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; align-items: center; }
.revision-input { display: flex; gap: 6px; align-items: center; }
.revision-input .input { min-width: 180px; }

.review-form { display: flex; flex-direction: column; gap: 6px; padding: 12px; background: var(--gray-50); border-radius: var(--radius-md); border: 1px solid var(--gray-200); }
.review-form h4 { font-size: .8125rem; }
.star-select { display: flex; gap: 2px; }
.star-btn { background: none; border: none; font-size: 1.25rem; cursor: pointer; color: var(--gray-300); transition: color .1s; }
.star-btn.active { color: var(--warning); }
.star-btn:hover { color: var(--warning); }

.text-muted { color: var(--gray-400); font-size: .8125rem; }
.text-secondary { color: var(--gray-600); font-size: .8125rem; }
.loading-center { display: flex; justify-content: center; padding: 6rem; }

@media (max-width: 768px) {
  .detail-header { flex-direction: column; gap: .75rem; }
  .submit-work { flex-direction: column; }
  .revision-input { flex-direction: column; }
}
</style>
