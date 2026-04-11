<template>
  <div ref="pickerEl" class="skill-picker">
    <div class="skill-chips">
      <span v-for="s in skills" :key="s.id" class="skill-chip">
        {{ s.name }}
        <button v-if="editable" class="chip-remove" @click="removeSkill(s.id)">&times;</button>
      </span>
      <button v-if="editable" class="add-skill-btn" @click="showDropdown = !showDropdown">+ Add skill</button>
    </div>

    <div v-if="showDropdown" class="skill-dropdown">
      <input
        ref="searchInput"
        class="input skill-search"
        v-model="search"
        placeholder="Search skills..."
        @keydown.escape="showDropdown = false"
      />
      <div class="skill-options">
        <button
          v-for="s in filtered"
          :key="s.id"
          class="skill-option"
          @click="addSkill(s.id)"
        >{{ s.name }}</button>
        <button v-if="search.trim() && !exactMatch" class="skill-option skill-create" @click="createAndAdd">
          Create "{{ search.trim() }}"
        </button>
        <div v-if="!filtered.length && !search.trim()" class="skill-empty">No skills available</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onUnmounted } from 'vue'
import { skillsAPI, usersAPI } from '@/api'
import { useToastStore } from '@/stores/toast'

const props = defineProps({
  skills: { type: Array, default: () => [] },
  userId: { type: Number, required: true },
  editable: { type: Boolean, default: false },
})

const emit = defineEmits(['updated'])

const toast = useToastStore()
const allSkills = ref([])
const search = ref('')
const showDropdown = ref(false)
const searchInput = ref(null)
const pickerEl = ref(null)

function onClickOutside(e) {
  if (pickerEl.value && !pickerEl.value.contains(e.target)) {
    showDropdown.value = false
  }
}

const filtered = computed(() => {
  const currentIds = new Set(props.skills.map(s => s.id))
  let list = allSkills.value.filter(s => !currentIds.has(s.id))
  if (search.value.trim()) {
    const q = search.value.toLowerCase()
    list = list.filter(s => s.name.toLowerCase().includes(q))
  }
  return list
})

const exactMatch = computed(() => {
  const q = search.value.trim().toLowerCase()
  return allSkills.value.some(s => s.name.toLowerCase() === q)
})

watch(showDropdown, async (open) => {
  if (open) {
    try { allSkills.value = (await skillsAPI.list()).data } catch {}
    await nextTick()
    searchInput.value?.focus()
    document.addEventListener('click', onClickOutside, true)
  } else {
    search.value = ''
    document.removeEventListener('click', onClickOutside, true)
  }
})

onUnmounted(() => {
  document.removeEventListener('click', onClickOutside, true)
})

async function addSkill(skillId) {
  try {
    await usersAPI.addSkill(props.userId, skillId)
    showDropdown.value = false
    emit('updated')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Failed to add skill')
  }
}

async function removeSkill(skillId) {
  try {
    await usersAPI.removeSkill(props.userId, skillId)
    emit('updated')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Failed to remove skill')
  }
}

async function createAndAdd() {
  try {
    const { data } = await skillsAPI.create({ name: search.value.trim() })
    await addSkill(data.id)
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Failed to create skill')
  }
}
</script>

<style scoped>
.skill-picker {
  position: relative;
}
.skill-chips {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.skill-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  background: var(--accent-light);
  color: var(--accent-text);
  border-radius: 16px;
  font-size: 0.8125rem;
}
.chip-remove {
  background: none;
  border: none;
  color: var(--accent-text);
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  padding: 0;
  opacity: 0.7;
}
.chip-remove:hover {
  opacity: 1;
}
.add-skill-btn {
  background: transparent;
  border: 1px dashed var(--gray-300);
  color: var(--gray-500);
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 0.8125rem;
  font-family: var(--font);
  cursor: pointer;
  transition: all 0.15s ease;
}
.add-skill-btn:hover {
  border-color: var(--accent);
  color: var(--accent-text);
}
.skill-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 8px;
  width: 280px;
  background: var(--white);
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  z-index: 50;
  overflow: hidden;
}
.skill-search {
  border: none;
  border-bottom: 1px solid var(--gray-200);
  border-radius: 0;
  font-size: 0.8125rem;
}
.skill-search:focus {
  box-shadow: none;
}
.skill-options {
  max-height: 200px;
  overflow-y: auto;
}
.skill-option {
  display: block;
  width: 100%;
  padding: 8px 12px;
  background: none;
  border: none;
  text-align: left;
  font-family: var(--font);
  font-size: 0.8125rem;
  color: var(--gray-700);
  cursor: pointer;
}
.skill-option:hover {
  background: var(--gray-100);
}
.skill-create {
  color: var(--accent-text);
  font-weight: 500;
}
.skill-empty {
  padding: 12px;
  text-align: center;
  color: var(--gray-400);
  font-size: 0.8125rem;
}
</style>
