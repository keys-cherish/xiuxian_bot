<script setup lang="ts">
import IcStar from '~icons/mdi/star-four-points'
import IcPlus from '~icons/mdi/plus-circle-outline'
import IcArrowUp from '~icons/mdi/arrow-up-bold'
import { usePlayerStore } from '@/stores/player'
import { getSkills, learnSkill, equipSkill, unequipSkill, upgradeSkill } from '@/api/client'

interface Skill {
  skill_id: string
  name: string
  desc: string
  level: number
  max_level: number
  equipped: boolean
  slot: number | null
  mastery: number
  type: string
  learnable: boolean
  upgradable: boolean
  upgrade_cost: Record<string, number>
}

const player = usePlayerStore()
const skills = ref<Skill[]>([])
const loading = ref(true)
const msg = ref('')
const acting = ref(false)

onMounted(async () => {
  if (!player.loaded && player.userId) await player.init()
  await load()
})

async function load() {
  if (!player.userId) return
  loading.value = true
  try {
    const r = await getSkills(player.userId)
    skills.value = r.skills || []
  } catch { skills.value = [] }
  loading.value = false
}

const equipped = computed(() => skills.value.filter(s => s.equipped))
const unequipped = computed(() => skills.value.filter(s => !s.equipped && !s.learnable))
const learnable = computed(() => skills.value.filter(s => s.learnable))

async function doLearn(s: Skill) {
  if (acting.value) return
  acting.value = true; msg.value = ''
  try {
    const r = await learnSkill(player.userId, s.skill_id)
    msg.value = r.message || '学习成功'
    await load(); await player.init(true)
  } catch (e: any) { msg.value = e?.body?.message || '学习失败' }
  finally { acting.value = false }
}

async function doEquip(s: Skill) {
  if (acting.value) return
  acting.value = true; msg.value = ''
  try {
    const slot = equipped.value.length
    const r = await equipSkill(player.userId, s.skill_id, slot)
    msg.value = r.message || '装备成功'
    await load()
  } catch (e: any) { msg.value = e?.body?.message || '装备失败' }
  finally { acting.value = false }
}

async function doUnequip(s: Skill) {
  if (acting.value || s.slot == null) return
  acting.value = true; msg.value = ''
  try {
    const r = await unequipSkill(player.userId, s.slot)
    msg.value = r.message || '卸下成功'
    await load()
  } catch (e: any) { msg.value = e?.body?.message || '卸下失败' }
  finally { acting.value = false }
}

async function doUpgrade(s: Skill) {
  if (acting.value) return
  acting.value = true; msg.value = ''
  try {
    const r = await upgradeSkill(player.userId, s.skill_id)
    msg.value = r.message || '升级成功'
    await load(); await player.init(true)
  } catch (e: any) { msg.value = e?.body?.message || '升级失败' }
  finally { acting.value = false }
}

const TYPE_LABELS: Record<string, string> = {
  attack: '攻击', defense: '防御', support: '辅助', passive: '被动', buff: '增益',
}
</script>

<template>
  <div class="skill-page">
    <h2 class="page-title"><IcStar class="icon" /> 功法</h2>
    <p v-if="msg" class="msg card fade-in" @click="msg=''">{{ msg }}</p>

    <div v-if="loading" class="page-loading"><div class="loading-spinner"></div></div>

    <template v-else>
      <!-- 已装备 -->
      <section v-if="equipped.length" class="card card--decorated">
        <h3 class="section-title">已装备</h3>
        <div class="skill-list">
          <div v-for="s in equipped" :key="s.skill_id" class="skill-item">
            <div class="skill-head">
              <span class="skill-name">{{ s.name }}</span>
              <span class="skill-tag">{{ TYPE_LABELS[s.type] || s.type }}</span>
              <span class="skill-level text-gold">Lv.{{ s.level }}</span>
            </div>
            <p class="skill-desc">{{ s.desc }}</p>
            <div class="skill-actions">
              <button v-if="s.upgradable" class="btn btn-ghost" :disabled="acting" @click="doUpgrade(s)"><IcArrowUp class="icon" /> 升级</button>
              <button class="btn btn-ghost" :disabled="acting" @click="doUnequip(s)">卸下</button>
            </div>
          </div>
        </div>
      </section>

      <!-- 已学未装备 -->
      <section v-if="unequipped.length" class="card">
        <h3 class="section-title">已学功法</h3>
        <div class="skill-list">
          <div v-for="s in unequipped" :key="s.skill_id" class="skill-item">
            <div class="skill-head">
              <span class="skill-name">{{ s.name }}</span>
              <span class="skill-tag">{{ TYPE_LABELS[s.type] || s.type }}</span>
              <span class="skill-level">Lv.{{ s.level }}</span>
            </div>
            <p class="skill-desc">{{ s.desc }}</p>
            <div class="skill-actions">
              <button class="btn btn-primary" :disabled="acting" @click="doEquip(s)">装备</button>
              <button v-if="s.upgradable" class="btn btn-ghost" :disabled="acting" @click="doUpgrade(s)"><IcArrowUp class="icon" /> 升级</button>
            </div>
          </div>
        </div>
      </section>

      <!-- 可学 -->
      <section v-if="learnable.length" class="card">
        <h3 class="section-title">可学功法</h3>
        <div class="skill-list">
          <div v-for="s in learnable" :key="s.skill_id" class="skill-item skill-item--learnable">
            <div class="skill-head">
              <span class="skill-name">{{ s.name }}</span>
              <span class="skill-tag">{{ TYPE_LABELS[s.type] || s.type }}</span>
            </div>
            <p class="skill-desc">{{ s.desc }}</p>
            <button class="btn btn-cinnabar" :disabled="acting" @click="doLearn(s)"><IcPlus class="icon" /> 学习</button>
          </div>
        </div>
      </section>

      <div v-if="!skills.length" class="page-empty"><p>暂无功法数据</p></div>
    </template>
  </div>
</template>

<style scoped>
.skill-page { padding: var(--space-lg); padding-bottom: 86px; display: flex; flex-direction: column; gap: var(--space-md); }
.page-title { font-size: 1.05rem; display: flex; align-items: center; gap: var(--space-sm); }
.icon { width: 1rem; height: 1rem; }
.page-loading, .page-empty { display: flex; align-items: center; justify-content: center; min-height: 40vh; color: var(--ink-light); }
.msg { text-align: center; font-size: .85rem; cursor: pointer; }
.section-title { font-size: .9rem; margin-bottom: var(--space-sm); }

.skill-list { display: flex; flex-direction: column; gap: var(--space-sm); }
.skill-item { background: var(--paper-dark); border-radius: var(--radius-sm); padding: var(--space-md); }
.skill-item--learnable { border: 1px dashed var(--paper-shadow); }
.skill-head { display: flex; align-items: center; gap: var(--space-sm); margin-bottom: 4px; }
.skill-name { font-weight: 700; font-size: .88rem; color: var(--ink-dark); }
.skill-tag { font-size: .65rem; padding: 1px 6px; border-radius: 2px; background: var(--paper-deeper); color: var(--ink-mid); }
.skill-level { font-size: .75rem; font-family: var(--font-mono); }
.skill-desc { font-size: .76rem; color: var(--ink-light); line-height: 1.5; margin-bottom: var(--space-sm); }
.skill-actions { display: flex; gap: var(--space-xs); }
</style>
