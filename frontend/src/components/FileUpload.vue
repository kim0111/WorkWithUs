<template>
  <div class="file-upload">
    <label class="upload-area" :class="{ dragging }" @dragover.prevent="dragging=true" @dragleave="dragging=false" @drop.prevent="onDrop">
      <input type="file" ref="fileInput" @change="onSelect" :accept="accept" hidden />
      <span class="material-icons-round">cloud_upload</span>
      <span class="upload-text">{{ uploading ? 'Uploading...' : 'Drop file or click to upload' }}</span>
      <span class="upload-hint">Max {{ maxSizeMb }}MB</span>
    </label>
  </div>
</template>
<script setup>
import { ref } from 'vue'
const props = defineProps({ accept: { type: String, default: '*' }, maxSizeMb: { type: Number, default: 50 } })
const emit = defineEmits(['file'])
const dragging = ref(false)
const uploading = ref(false)
const fileInput = ref(null)
function onSelect(e) { handle(e.target.files[0]) }
function onDrop(e) { dragging.value = false; handle(e.dataTransfer.files[0]) }
function handle(f) { if (f) emit('file', f) }
</script>
<style scoped>
.upload-area{display:flex;flex-direction:column;align-items:center;gap:8px;padding:32px;border:2px dashed var(--border-strong);border-radius:var(--radius-lg);cursor:pointer;transition:all .2s var(--ease);text-align:center}
.upload-area:hover,.upload-area.dragging{border-color:var(--accent);background:var(--accent-dim)}
.upload-area .material-icons-round{font-size:32px;color:var(--text-muted)}
.upload-text{font-size:.9rem;color:var(--text-secondary);font-weight:500}
.upload-hint{font-size:.75rem;color:var(--text-muted)}
</style>
