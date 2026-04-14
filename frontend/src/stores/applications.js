import { defineStore } from 'pinia'
import { ref } from 'vue'
import { applicationsAPI } from '@/api'

export const useApplicationsStore = defineStore('applications', () => {
  const myApps = ref([])
  const byProject = ref({})
  const loading = ref(false)
  const error = ref(null)

  async function fetchMy() {
    loading.value = true
    try {
      const { data } = await applicationsAPI.my()
      myApps.value = data
    } catch (err) {
      error.value = err
      console.error('applications.fetchMy failed', err)
    } finally {
      loading.value = false
    }
  }

  async function fetchByProject(projectId) {
    loading.value = true
    try {
      const { data } = await applicationsAPI.byProject(projectId)
      byProject.value[projectId] = data
    } catch (err) {
      error.value = err
      console.error('applications.fetchByProject failed', err)
    } finally {
      loading.value = false
    }
  }

  async function apply(payload) {
    const { data } = await applicationsAPI.apply(payload)
    myApps.value.unshift(data)
    return data
  }

  async function invite(payload) {
    const { data } = await applicationsAPI.invite(payload)
    return data
  }

  async function updateStatus(id, payload) {
    const { data } = await applicationsAPI.updateStatus(id, payload)
    const i = myApps.value.findIndex(a => a.id === id)
    if (i !== -1) myApps.value[i] = data
    for (const pid in byProject.value) {
      const j = byProject.value[pid].findIndex(a => a.id === id)
      if (j !== -1) byProject.value[pid][j] = data
    }
    return data
  }

  return { myApps, byProject, loading, error, fetchMy, fetchByProject, apply, invite, updateStatus }
})
