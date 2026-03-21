<script setup lang="ts">
/**
 * StoryLine – 单条剧情行的渲染
 * 根据 type 自动选择旁白/对话/选择的显示样式
 */
import TypeWriter from './TypeWriter.vue'

const props = defineProps<{
  type: 'narration' | 'dialogue' | 'choice'
  text: string
  speaker?: string
  animate?: boolean
}>()

const emit = defineEmits<{
  done: []
}>()
</script>

<template>
  <div class="story-line" :class="`story-line--${type}`">
    <!-- 对话：带说话人 -->
    <template v-if="type === 'dialogue' && speaker">
      <div class="story-line__speaker">{{ speaker }}</div>
      <div class="story-line__bubble">
        <TypeWriter v-if="animate" :text="text" :speed="35" @done="emit('done')" />
        <span v-else v-html="text.replace(/\n/g, '<br>')"></span>
      </div>
    </template>

    <!-- 旁白 -->
    <template v-else-if="type === 'narration'">
      <div class="story-line__narration">
        <TypeWriter v-if="animate" :text="text" :speed="30" @done="emit('done')" />
        <span v-else v-html="text.replace(/\n/g, '<br>')"></span>
      </div>
    </template>

    <!-- 旁白式对话（无说话人） -->
    <template v-else-if="type === 'dialogue'">
      <div class="story-line__narration story-line__narration--inner">
        <TypeWriter v-if="animate" :text="text" :speed="30" @done="emit('done')" />
        <span v-else v-html="text.replace(/\n/g, '<br>')"></span>
      </div>
    </template>

    <!-- 选择项 -->
    <template v-else-if="type === 'choice'">
      <div class="story-line__choice">
        {{ text }}
      </div>
    </template>
  </div>
</template>

<style scoped>
.story-line {
  margin-bottom: var(--space-md);
  animation: fade-in var(--duration-normal) var(--ease-out) both;
}

.story-line__speaker {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--cinnabar);
  margin-bottom: 2px;
  padding-left: var(--space-sm);
}

.story-line__bubble {
  background: rgba(192, 48, 48, 0.05);
  border-left: 3px solid var(--cinnabar);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  padding: var(--space-sm) var(--space-md);
  color: var(--ink-dark);
  line-height: 1.7;
}

.story-line__narration {
  color: var(--ink-mid);
  line-height: 1.8;
  padding: 0 var(--space-xs);
}

.story-line__narration--inner {
  color: var(--ink-light);
  font-style: italic;
}

.story-line__choice {
  background: var(--paper-dark);
  border: 1px solid var(--paper-deeper);
  border-radius: var(--radius-sm);
  padding: var(--space-sm) var(--space-md);
  color: var(--gold);
  cursor: pointer;
  transition: border-color var(--duration-fast);
}

.story-line__choice:active {
  border-color: var(--gold);
}
</style>
