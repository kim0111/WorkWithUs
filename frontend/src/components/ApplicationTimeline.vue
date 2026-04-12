<template>
  <ol v-if="history?.length" class="timeline">
    <li
      v-for="(entry, i) in history"
      :key="i"
      class="tl-item"
      :class="{ 'tl-last': i === history.length - 1 }"
    >
      <span
        class="tl-dot"
        :style="{ backgroundColor: dotColor(entry.status, i === history.length - 1) }"
      ></span>
      <div class="tl-content">
        <div class="tl-row">
          <span class="tl-status">{{ STATUS_LABELS[entry.status] || entry.status }}</span>
          <span class="tl-time">{{ formatTimestamp(entry.timestamp) }}</span>
        </div>
        <div class="tl-actor">by {{ entry.actor_name }}</div>
        <blockquote v-if="entry.note" class="tl-note">{{ entry.note }}</blockquote>
      </div>
    </li>
  </ol>
</template>

<script setup>
defineProps({
  history: { type: Array, required: true },
})

const STATUS_LABELS = {
  pending: 'Pending',
  accepted: 'Accepted',
  rejected: 'Rejected',
  in_progress: 'In Progress',
  submitted: 'Submitted',
  revision_requested: 'Revision Requested',
  approved: 'Approved',
  completed: 'Completed',
}

const STATUS_COLORS = {
  pending: 'var(--gray-400)',
  accepted: 'var(--success)',
  rejected: 'var(--danger)',
  in_progress: 'var(--info)',
  submitted: 'var(--accent)',
  revision_requested: 'var(--warning)',
  approved: 'var(--success)',
  completed: 'var(--success)',
}

function dotColor(status, isLast) {
  return isLast ? (STATUS_COLORS[status] || 'var(--gray-400)') : 'var(--gray-300)'
}

function formatTimestamp(iso) {
  if (!iso) return ''
  try {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short', day: 'numeric', year: 'numeric',
      hour: 'numeric', minute: '2-digit',
    }).format(new Date(iso))
  } catch {
    return iso
  }
}
</script>

<style scoped>
.timeline {
  list-style: none;
  padding: 0;
  margin: 0;
  position: relative;
}
.tl-item {
  position: relative;
  padding-left: 28px;
  padding-bottom: 20px;
}
.tl-item:not(.tl-last)::before {
  content: '';
  position: absolute;
  left: 6px;
  top: 16px;
  bottom: 0;
  width: 2px;
  background: var(--gray-200);
}
.tl-dot {
  position: absolute;
  left: 0;
  top: 4px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid var(--white);
  box-shadow: 0 0 0 1px var(--gray-200);
}
.tl-content { display: flex; flex-direction: column; gap: 2px; }
.tl-row { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }
.tl-status { font-size: .875rem; font-weight: 600; color: var(--gray-900); }
.tl-time { font-size: .75rem; color: var(--gray-500); white-space: nowrap; }
.tl-actor { font-size: .8125rem; color: var(--gray-500); }
.tl-note {
  margin: 6px 0 0;
  padding: 6px 10px;
  border-left: 2px solid var(--gray-200);
  background: var(--gray-50);
  color: var(--gray-700);
  font-size: .8125rem;
  font-style: italic;
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
}
</style>
