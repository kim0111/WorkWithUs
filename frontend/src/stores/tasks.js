import { defineStore } from 'pinia'
import { ref } from 'vue'
import { tasksAPI } from '@/api'

export const TASK_COLUMNS = [
  { id: 'todo', label: 'To Do' },
  { id: 'in_progress', label: 'In Progress' },
  { id: 'review', label: 'Review' },
  { id: 'done', label: 'Done' },
]

export const TASK_PRIORITIES = ['low', 'medium', 'high']

export const useTasksStore = defineStore('tasks', () => {
  const byProject = ref({})
  const loading = ref(false)
  const error = ref(null)

  function _list(projectId) {
    if (!byProject.value[projectId]) byProject.value[projectId] = []
    return byProject.value[projectId]
  }

  async function fetchByProject(projectId, filters = {}) {
    loading.value = true
    error.value = null
    try {
      const params = {}
      if (filters.assignee_id != null) params.assignee_id = filters.assignee_id
      if (filters.priority) params.priority = filters.priority
      if (filters.deadline_before) params.deadline_before = filters.deadline_before
      const { data } = await tasksAPI.list(projectId, params)
      byProject.value[projectId] = data
      return data
    } catch (err) {
      error.value = err
      console.error('tasks.fetchByProject failed', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function create(projectId, payload) {
    const { data } = await tasksAPI.create(projectId, payload)
    _list(projectId).push(data)
    return data
  }

  function _patchLocal(projectId, task) {
    const list = _list(projectId)
    const i = list.findIndex(t => t.id === task.id)
    if (i !== -1) list[i] = task
    else list.push(task)
  }

  async function update(projectId, taskId, payload) {
    const { data } = await tasksAPI.update(taskId, payload)
    _patchLocal(projectId, data)
    return data
  }

  // Optimistic column move: patch locally first, roll back on failure.
  async function moveTask(projectId, taskId, newStatus) {
    const list = _list(projectId)
    const i = list.findIndex(t => t.id === taskId)
    if (i === -1) return
    const prevStatus = list[i].status
    if (prevStatus === newStatus) return
    list[i] = { ...list[i], status: newStatus }
    try {
      const { data } = await tasksAPI.update(taskId, { status: newStatus })
      list[i] = data
    } catch (err) {
      list[i] = { ...list[i], status: prevStatus }
      throw err
    }
  }

  async function remove(projectId, taskId) {
    await tasksAPI.delete(taskId)
    byProject.value[projectId] = _list(projectId).filter(t => t.id !== taskId)
  }

  async function listComments(taskId) {
    const { data } = await tasksAPI.listComments(taskId)
    return data
  }

  async function addComment(taskId, content) {
    const { data } = await tasksAPI.addComment(taskId, { content })
    return data
  }

  async function listActivity(taskId) {
    const { data } = await tasksAPI.listActivity(taskId)
    return data
  }

  return {
    byProject, loading, error,
    fetchByProject, create, update, moveTask, remove,
    listComments, addComment, listActivity,
  }
})
