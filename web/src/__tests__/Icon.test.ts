import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Icon from '@/components/Icon.vue'

describe('Icon.vue', () => {
  it('renders with name prop', () => {
    const wrapper = mount(Icon, {
      props: { name: 'chat', size: 18 },
    })
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.find('svg').exists()).toBe(true)
  })

  it('sets correct size style', () => {
    const wrapper = mount(Icon, {
      props: { name: 'chat', size: 24 },
    })
    const span = wrapper.find('.icon')
    expect(span.attributes('style')).toContain('24px')
  })
})
