import { defineStore } from 'pinia'
import { ref } from 'vue'
import { projectsAPI } from '@/api'

export const useProjectsStore = defineStore('projects', () => {
  const items = ref([])
  const total = ref(0)
  const currentProject = ref(null)
  const loading = ref(false)
  const detailLoading = ref(false)

  async function fetchList(params = {}) {
    loading.value = true
    try {
      const { data } = await projectsAPI.list(params)
      items.value = data.items
      total.value = data.total
    } catch {} finally {
      loading.value = false
    }
  }

  async function fetchOne(id) {
    detailLoading.value = true
    try {
      currentProject.value = (await projectsAPI.get(id)).data
    } catch (e) {
      currentProject.value = null
      throw e
    } finally {
      detailLoading.value = false
    }
  }

  async function create(data) {
    const res = await projectsAPI.create(data)
    return res.data
  }

  async function update(id, data) {
    const res = await projectsAPI.update(id, data)
    if (currentProject.value && currentProject.value.id === Number(id)) {
      Object.assign(currentProject.value, res.data)
    }
    return res.data
  }

  async function remove(id) {
    await projectsAPI.delete(id)
    if (currentProject.value && currentProject.value.id === Number(id)) {
      currentProject.value = null
    }
  }

  return {
    items, total, currentProject, loading, detailLoading,
    fetchList, fetchOne, create, update, remove,
  }
})
