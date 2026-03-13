<template>
  <div class="file-upload">
    <label class="upload-area" :class="{ dragging }" @dragover.prevent="dragging=true" @dragleave="dragging=false" @drop.prevent="onDrop">
      <input type="file" ref="fileInput" @change="onSelect" :accept="accept" hidden />
      <span class="material-icons-round">upload_file</span>
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
.upload-area {
  display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 24px;
  border: 1.5px dashed var(--gray-300); border-radius: var(--radius-lg);
  cursor: pointer; transition: all .15s ease; text-align: center; background: var(--white);
}
.upload-area:hover, .upload-area.dragging { border-color: var(--accent); background: var(--accent-light); }
.upload-area .material-icons-round { font-size: 28px; color: var(--gray-400); }
.upload-text { font-size: .8125rem; color: var(--gray-600); font-weight: 500; }
.upload-hint { font-size: .75rem; color: var(--gray-400); }
</style>
