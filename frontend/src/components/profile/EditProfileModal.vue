<template>
  <BaseModal :modelValue="modelValue" @update:modelValue="$emit('update:modelValue', $event)" title="Edit Profile" maxWidth="520px">
    <form @submit.prevent="save" class="edit-form">
      <FormField label="Full Name">
        <input class="input" v-model="form.full_name" />
      </FormField>
      <FormField label="Bio">
        <textarea class="input" v-model="form.bio" rows="3"></textarea>
      </FormField>

      <template v-if="role === 'company'">
        <FormField label="Company Name">
          <input class="input" v-model="profileForm.company_name" />
        </FormField>
        <FormField label="Industry">
          <input class="input" v-model="profileForm.industry" />
        </FormField>
        <FormField label="Website">
          <input class="input" v-model="profileForm.website" placeholder="https://..." />
        </FormField>
        <FormField label="Description">
          <textarea class="input" v-model="profileForm.description" rows="3"></textarea>
        </FormField>
        <FormField label="Location">
          <input class="input" v-model="profileForm.location" />
        </FormField>
      </template>

      <template v-if="role === 'student'">
        <FormField label="University">
          <input class="input" v-model="profileForm.university" />
        </FormField>
        <FormField label="Major">
          <input class="input" v-model="profileForm.major" />
        </FormField>
        <FormField label="Graduation Year">
          <input class="input" type="number" v-model.number="profileForm.graduation_year" />
        </FormField>
      </template>

      <div class="form-actions">
        <button type="button" class="btn btn-secondary" @click="$emit('update:modelValue', false)">Cancel</button>
        <button type="submit" class="btn btn-primary" :disabled="saving">{{ saving ? 'Saving...' : 'Save Changes' }}</button>
      </div>
    </form>
  </BaseModal>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import { usersAPI } from '@/api'
import { useToastStore } from '@/stores/toast'
import BaseModal from '@/components/BaseModal.vue'
import FormField from '@/components/FormField.vue'

const props = defineProps({
  modelValue: { type: Boolean, required: true },
  user: { type: Object, required: true },
  profile: { type: Object, default: null },
  role: { type: String, required: true },
})

const emit = defineEmits(['update:modelValue', 'saved'])

const toast = useToastStore()
const saving = ref(false)

const form = reactive({ full_name: '', bio: '' })
const profileForm = reactive({
  company_name: '',
  industry: '',
  website: '',
  description: '',
  location: '',
  university: '',
  major: '',
  graduation_year: null,
})

watch(() => props.modelValue, (open) => {
  if (open) {
    form.full_name = props.user.full_name || ''
    form.bio = props.user.bio || ''
    if (props.role === 'company' && props.profile) {
      profileForm.company_name = props.profile.company_name || ''
      profileForm.industry = props.profile.industry || ''
      profileForm.website = props.profile.website || ''
      profileForm.description = props.profile.description || ''
      profileForm.location = props.profile.location || ''
    }
    if (props.role === 'student' && props.profile) {
      profileForm.university = props.profile.university || ''
      profileForm.major = props.profile.major || ''
      profileForm.graduation_year = props.profile.graduation_year || null
    }
  }
})

async function save() {
  saving.value = true
  try {
    await usersAPI.update(props.user.id, { full_name: form.full_name, bio: form.bio })

    if (props.role === 'company') {
      await usersAPI.updateCompanyProfile(props.user.id, {
        company_name: profileForm.company_name,
        industry: profileForm.industry,
        website: profileForm.website,
        description: profileForm.description,
        location: profileForm.location,
      })
    }
    if (props.role === 'student') {
      await usersAPI.updateStudentProfile(props.user.id, {
        university: profileForm.university,
        major: profileForm.major,
        graduation_year: profileForm.graduation_year,
      })
    }

    toast.success('Profile updated')
    emit('update:modelValue', false)
    emit('saved')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Failed to save')
  }
  saving.value = false
}
</script>

<style scoped>
.edit-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 8px;
}
</style>
