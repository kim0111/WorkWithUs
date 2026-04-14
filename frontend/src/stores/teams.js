import { defineStore } from 'pinia'
import { ref } from 'vue'
import { teamsAPI } from '@/api'

export const useTeamsStore = defineStore('teams', () => {
  const byProject = ref({})
  const myTeams = ref([])
  const loading = ref(false)

  async function fetchByProject(projectId) {
    loading.value = true
    try {
      const { data } = await teamsAPI.byProject(projectId)
      byProject.value[projectId] = data
    } catch (err) {
      console.error('teams.fetchByProject failed', err)
    } finally {
      loading.value = false
    }
  }

  async function fetchMy() {
    loading.value = true
    try {
      const { data } = await teamsAPI.my()
      myTeams.value = data
    } catch (err) {
      console.error('teams.fetchMy failed', err)
    } finally {
      loading.value = false
    }
  }

  async function addMember(projectId, payload) {
    const { data } = await teamsAPI.addMember(projectId, payload)
    if (!byProject.value[projectId]) byProject.value[projectId] = []
    byProject.value[projectId].push(data)
    return data
  }

  async function updateMember(projectId, userId, payload) {
    const { data } = await teamsAPI.updateMember(projectId, userId, payload)
    const list = byProject.value[projectId] || []
    const i = list.findIndex(m => m.user_id === userId)
    if (i !== -1) list[i] = data
    return data
  }

  async function removeMember(projectId, userId) {
    await teamsAPI.removeMember(projectId, userId)
    const list = byProject.value[projectId] || []
    byProject.value[projectId] = list.filter(m => m.user_id !== userId)
  }

  return { byProject, myTeams, loading, fetchByProject, fetchMy, addMember, updateMember, removeMember }
})
